"""
API Versioning and Compatibility Layer for CBS_PYTHON V2.0

This module provides:
- API version management and routing
- Backward compatibility with V1 APIs
- Request/response transformation between versions
- Deprecation warnings and migration guides
- Feature flags for gradual rollout
"""

import json
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import re
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
import semver
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class VersioningStrategy(str, Enum):
    """API versioning strategies"""
    URI_PATH = "uri_path"          # /v1/customers, /v2/customers
    QUERY_PARAM = "query_param"    # /customers?version=v2
    HEADER = "header"              # Accept: application/vnd.api+json;version=2
    SUBDOMAIN = "subdomain"        # v2.api.example.com
    CONTENT_TYPE = "content_type"  # Content-Type: application/vnd.api.v2+json


class DeprecationStatus(str, Enum):
    """API deprecation status"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"
    RETIRED = "retired"


@dataclass
class APIVersion:
    """API version configuration"""
    version: str
    status: DeprecationStatus
    introduced_date: datetime
    deprecated_date: Optional[datetime] = None
    sunset_date: Optional[datetime] = None
    retirement_date: Optional[datetime] = None
    migration_guide_url: Optional[str] = None
    breaking_changes: List[str] = None
    features: List[str] = None
    compatibility_layer: bool = False


@dataclass
class EndpointVersion:
    """Endpoint-specific version configuration"""
    endpoint: str
    method: str
    version: str
    handler: Callable
    request_transformer: Optional[Callable] = None
    response_transformer: Optional[Callable] = None
    deprecated: bool = False
    sunset_date: Optional[datetime] = None
    migration_endpoint: Optional[str] = None


class VersionedRequest(BaseModel):
    """Versioned request wrapper"""
    version: str
    original_data: Dict[str, Any]
    transformed_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VersionedResponse(BaseModel):
    """Versioned response wrapper"""
    version: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    deprecation_warning: Optional[str] = None
    migration_info: Optional[Dict[str, Any]] = None


class RequestTransformer:
    """Request transformation between API versions"""
    
    def __init__(self):
        self.transformers: Dict[tuple, Callable] = {}
    
    def register_transformer(
        self,
        from_version: str,
        to_version: str,
        endpoint: str,
        method: str,
        transformer: Callable
    ):
        """Register a request transformer"""
        key = (from_version, to_version, endpoint, method)
        self.transformers[key] = transformer
        logger.info(
            "Request transformer registered",
            from_version=from_version,
            to_version=to_version,
            endpoint=endpoint,
            method=method
        )
    
    def transform(
        self,
        data: Dict[str, Any],
        from_version: str,
        to_version: str,
        endpoint: str,
        method: str
    ) -> Dict[str, Any]:
        """Transform request data between versions"""
        key = (from_version, to_version, endpoint, method)
        transformer = self.transformers.get(key)
        
        if transformer:
            try:
                return transformer(data)
            except Exception as e:
                logger.error(
                    "Request transformation failed",
                    error=str(e),
                    from_version=from_version,
                    to_version=to_version,
                    endpoint=endpoint
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Request transformation failed: {str(e)}"
                )
        
        # Return original data if no transformer found
        return data


class ResponseTransformer:
    """Response transformation between API versions"""
    
    def __init__(self):
        self.transformers: Dict[tuple, Callable] = {}
    
    def register_transformer(
        self,
        from_version: str,
        to_version: str,
        endpoint: str,
        method: str,
        transformer: Callable
    ):
        """Register a response transformer"""
        key = (from_version, to_version, endpoint, method)
        self.transformers[key] = transformer
        logger.info(
            "Response transformer registered",
            from_version=from_version,
            to_version=to_version,
            endpoint=endpoint,
            method=method
        )
    
    def transform(
        self,
        data: Dict[str, Any],
        from_version: str,
        to_version: str,
        endpoint: str,
        method: str
    ) -> Dict[str, Any]:
        """Transform response data between versions"""
        key = (from_version, to_version, endpoint, method)
        transformer = self.transformers.get(key)
        
        if transformer:
            try:
                return transformer(data)
            except Exception as e:
                logger.error(
                    "Response transformation failed",
                    error=str(e),
                    from_version=from_version,
                    to_version=to_version,
                    endpoint=endpoint
                )
                # For response transformation errors, log but don't fail
                return data
        
        # Return original data if no transformer found
        return data


class FeatureFlag:
    """Feature flag for gradual API rollout"""
    
    def __init__(self, name: str, enabled: bool = False, rollout_percentage: int = 0):
        self.name = name
        self.enabled = enabled
        self.rollout_percentage = rollout_percentage
        self.rules: List[Callable] = []
    
    def add_rule(self, rule: Callable[[Request], bool]):
        """Add a custom rule for feature enablement"""
        self.rules.append(rule)
    
    def is_enabled_for_request(self, request: Request) -> bool:
        """Check if feature is enabled for the request"""
        if not self.enabled:
            return False
        
        # Apply custom rules
        for rule in self.rules:
            if not rule(request):
                return False
        
        # Apply rollout percentage
        if self.rollout_percentage < 100:
            # Use request IP for consistent rollout
            ip_hash = hash(request.client.host) % 100
            return ip_hash < self.rollout_percentage
        
        return True


class APIVersionManager:
    """Comprehensive API version management"""
    
    def __init__(self, strategy: VersioningStrategy = VersioningStrategy.URI_PATH):
        self.strategy = strategy
        self.versions: Dict[str, APIVersion] = {}
        self.endpoints: Dict[str, List[EndpointVersion]] = {}
        self.request_transformer = RequestTransformer()
        self.response_transformer = ResponseTransformer()
        self.feature_flags: Dict[str, FeatureFlag] = {}
        self.default_version = "v2"
        self.supported_versions = ["v1", "v2"]
    
    def register_version(self, version: APIVersion):
        """Register an API version"""
        self.versions[version.version] = version
        logger.info("API version registered", version=version.version, status=version.status)
    
    def register_endpoint(self, endpoint_version: EndpointVersion):
        """Register a versioned endpoint"""
        key = f"{endpoint_version.method}:{endpoint_version.endpoint}"
        if key not in self.endpoints:
            self.endpoints[key] = []
        self.endpoints[key].append(endpoint_version)
        logger.info(
            "Versioned endpoint registered",
            endpoint=endpoint_version.endpoint,
            method=endpoint_version.method,
            version=endpoint_version.version
        )
    
    def add_feature_flag(self, flag: FeatureFlag):
        """Add a feature flag"""
        self.feature_flags[flag.name] = flag
        logger.info("Feature flag added", name=flag.name, enabled=flag.enabled)
    
    def extract_version(self, request: Request) -> str:
        """Extract API version from request"""
        if self.strategy == VersioningStrategy.URI_PATH:
            # Extract from URL path: /v2/customers -> v2
            path_parts = request.url.path.strip('/').split('/')
            if path_parts and path_parts[0].startswith('v'):
                version = path_parts[0]
                if version in self.supported_versions:
                    return version
        
        elif self.strategy == VersioningStrategy.QUERY_PARAM:
            # Extract from query parameter: ?version=v2
            version = request.query_params.get('version')
            if version and version in self.supported_versions:
                return version
        
        elif self.strategy == VersioningStrategy.HEADER:
            # Extract from Accept header: application/vnd.api+json;version=2
            accept_header = request.headers.get('accept', '')
            version_match = re.search(r'version=(\d+)', accept_header)
            if version_match:
                version = f"v{version_match.group(1)}"
                if version in self.supported_versions:
                    return version
        
        elif self.strategy == VersioningStrategy.CONTENT_TYPE:
            # Extract from Content-Type: application/vnd.api.v2+json
            content_type = request.headers.get('content-type', '')
            version_match = re.search(r'\.v(\d+)\+', content_type)
            if version_match:
                version = f"v{version_match.group(1)}"
                if version in self.supported_versions:
                    return version
        
        # Return default version if none found
        return self.default_version
    
    def get_endpoint_version(self, endpoint: str, method: str, version: str) -> Optional[EndpointVersion]:
        """Get specific endpoint version"""
        key = f"{method}:{endpoint}"
        endpoint_versions = self.endpoints.get(key, [])
        
        for ev in endpoint_versions:
            if ev.version == version:
                return ev
        
        return None
    
    def get_compatible_endpoint(self, endpoint: str, method: str, version: str) -> Optional[EndpointVersion]:
        """Get compatible endpoint version with fallback"""
        # Try exact version match first
        endpoint_version = self.get_endpoint_version(endpoint, method, version)
        if endpoint_version:
            return endpoint_version
        
        # Try compatibility layer
        key = f"{method}:{endpoint}"
        endpoint_versions = self.endpoints.get(key, [])
        
        # Sort by version (newest first)
        sorted_versions = sorted(
            endpoint_versions,
            key=lambda x: x.version,
            reverse=True
        )
        
        for ev in sorted_versions:
            api_version = self.versions.get(ev.version)
            if api_version and api_version.compatibility_layer:
                return ev
        
        return None
    
    def check_deprecation(self, version: str, endpoint: str = None) -> Optional[Dict[str, Any]]:
        """Check if version or endpoint is deprecated"""
        api_version = self.versions.get(version)
        if not api_version:
            return None
        
        now = datetime.utcnow()
        deprecation_info = {}
        
        if api_version.status == DeprecationStatus.DEPRECATED:
            deprecation_info = {
                "status": "deprecated",
                "deprecated_date": api_version.deprecated_date.isoformat() if api_version.deprecated_date else None,
                "sunset_date": api_version.sunset_date.isoformat() if api_version.sunset_date else None,
                "migration_guide_url": api_version.migration_guide_url,
                "message": f"API version {version} is deprecated"
            }
        
        elif api_version.status == DeprecationStatus.SUNSET:
            sunset_date = api_version.sunset_date
            if sunset_date and now >= sunset_date:
                deprecation_info = {
                    "status": "sunset",
                    "sunset_date": sunset_date.isoformat(),
                    "retirement_date": api_version.retirement_date.isoformat() if api_version.retirement_date else None,
                    "migration_guide_url": api_version.migration_guide_url,
                    "message": f"API version {version} has reached sunset date"
                }
        
        elif api_version.status == DeprecationStatus.RETIRED:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=f"API version {version} has been retired"
            )
        
        return deprecation_info if deprecation_info else None
    
    def create_versioned_response(
        self,
        data: Dict[str, Any],
        version: str,
        endpoint: str,
        method: str,
        target_version: str = None
    ) -> VersionedResponse:
        """Create versioned response with transformation"""
        target_version = target_version or version
        
        # Transform response if needed
        transformed_data = data
        if version != target_version:
            transformed_data = self.response_transformer.transform(
                data, version, target_version, endpoint, method
            )
        
        # Check deprecation
        deprecation_info = self.check_deprecation(target_version, endpoint)
        
        response = VersionedResponse(
            version=target_version,
            data=transformed_data,
            metadata={
                "original_version": version,
                "transformed": version != target_version,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        if deprecation_info:
            response.deprecation_warning = deprecation_info.get("message")
            response.migration_info = deprecation_info
        
        return response


# V1 to V2 Transformers
def transform_customer_request_v1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform customer request from V1 to V2 format"""
    # V1 used 'name' field, V2 uses 'first_name' and 'last_name'
    if 'name' in data and 'first_name' not in data:
        name_parts = data['name'].split(' ', 1)
        data['first_name'] = name_parts[0]
        data['last_name'] = name_parts[1] if len(name_parts) > 1 else ''
        del data['name']
    
    # V1 used 'dob', V2 uses 'date_of_birth'
    if 'dob' in data:
        data['date_of_birth'] = data['dob']
        del data['dob']
    
    # V1 used 'mobile', V2 uses 'phone'
    if 'mobile' in data:
        data['phone'] = data['mobile']
        del data['mobile']
    
    return data


def transform_customer_response_v2_to_v1(data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform customer response from V2 to V1 format"""
    # Combine first_name and last_name into name
    if 'first_name' in data and 'last_name' in data:
        data['name'] = f"{data['first_name']} {data['last_name']}".strip()
        del data['first_name']
        del data['last_name']
    
    # Transform date_of_birth to dob
    if 'date_of_birth' in data:
        data['dob'] = data['date_of_birth']
        del data['date_of_birth']
    
    # Transform phone to mobile
    if 'phone' in data:
        data['mobile'] = data['phone']
        del data['phone']
    
    # Remove V2-specific fields
    v2_only_fields = ['customer_number', 'kyc_status']
    for field in v2_only_fields:
        data.pop(field, None)
    
    return data


def transform_account_request_v1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform account request from V1 to V2 format"""
    # V1 used 'type', V2 uses 'account_type'
    if 'type' in data:
        data['account_type'] = data['type']
        del data['type']
    
    # V1 used 'owner_id', V2 uses 'customer_id'
    if 'owner_id' in data:
        data['customer_id'] = data['owner_id']
        del data['owner_id']
    
    return data


def transform_account_response_v2_to_v1(data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform account response from V2 to V1 format"""
    # Transform account_type to type
    if 'account_type' in data:
        data['type'] = data['account_type']
        del data['account_type']
    
    # Transform customer_id to owner_id
    if 'customer_id' in data:
        data['owner_id'] = data['customer_id']
        del data['customer_id']
    
    # Remove V2-specific fields
    v2_only_fields = ['account_number', 'available_balance', 'interest_rate']
    for field in v2_only_fields:
        data.pop(field, None)
    
    return data


def create_default_version_manager() -> APIVersionManager:
    """Create default API version manager with predefined configurations"""
    manager = APIVersionManager(VersioningStrategy.URI_PATH)
    
    # Register API versions
    v1 = APIVersion(
        version="v1",
        status=DeprecationStatus.DEPRECATED,
        introduced_date=datetime(2023, 1, 1),
        deprecated_date=datetime(2024, 6, 1),
        sunset_date=datetime(2024, 12, 31),
        retirement_date=datetime(2025, 6, 30),
        migration_guide_url="https://docs.cbs-platform.com/migration/v1-to-v2",
        breaking_changes=[
            "Customer name field split into first_name and last_name",
            "Account type field renamed to account_type",
            "New required fields for KYC compliance"
        ],
        compatibility_layer=True
    )
    
    v2 = APIVersion(
        version="v2",
        status=DeprecationStatus.ACTIVE,
        introduced_date=datetime(2024, 6, 1),
        features=[
            "Enhanced customer data model",
            "Improved account management",
            "Real-time transaction processing",
            "Advanced security features",
            "GraphQL support",
            "Webhook notifications"
        ]
    )
    
    manager.register_version(v1)
    manager.register_version(v2)
    
    # Register transformers
    manager.request_transformer.register_transformer(
        "v1", "v2", "/customers", "POST", transform_customer_request_v1_to_v2
    )
    manager.request_transformer.register_transformer(
        "v1", "v2", "/customers", "PUT", transform_customer_request_v1_to_v2
    )
    manager.request_transformer.register_transformer(
        "v1", "v2", "/accounts", "POST", transform_account_request_v1_to_v2
    )
    manager.request_transformer.register_transformer(
        "v1", "v2", "/accounts", "PUT", transform_account_request_v1_to_v2
    )
    
    manager.response_transformer.register_transformer(
        "v2", "v1", "/customers", "GET", transform_customer_response_v2_to_v1
    )
    manager.response_transformer.register_transformer(
        "v2", "v1", "/customers", "POST", transform_customer_response_v2_to_v1
    )
    manager.response_transformer.register_transformer(
        "v2", "v1", "/accounts", "GET", transform_account_response_v2_to_v1
    )
    manager.response_transformer.register_transformer(
        "v2", "v1", "/accounts", "POST", transform_account_response_v2_to_v1
    )
    
    # Add feature flags
    graphql_flag = FeatureFlag("graphql_api", enabled=True, rollout_percentage=100)
    manager.add_feature_flag(graphql_flag)
    
    webhooks_flag = FeatureFlag("webhook_notifications", enabled=True, rollout_percentage=50)
    # Add rule for webhook rollout - enable for premium customers
    webhooks_flag.add_rule(lambda req: req.headers.get("X-Customer-Tier") == "premium")
    manager.add_feature_flag(webhooks_flag)
    
    return manager


class VersioningMiddleware:
    """Middleware for API versioning"""
    
    def __init__(self, version_manager: APIVersionManager):
        self.version_manager = version_manager
    
    async def __call__(self, request: Request, call_next):
        """Process request through versioning middleware"""
        # Extract version from request
        version = self.version_manager.extract_version(request)
        request.state.api_version = version
        
        # Check deprecation
        deprecation_info = self.version_manager.check_deprecation(version)
        
        # Process request
        response = await call_next(request)
        
        # Add version headers
        response.headers["X-API-Version"] = version
        response.headers["X-Supported-Versions"] = ",".join(self.version_manager.supported_versions)
        
        # Add deprecation headers if applicable
        if deprecation_info:
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = deprecation_info.get("sunset_date", "")
            response.headers["Link"] = f'<{deprecation_info.get("migration_guide_url", "")}>; rel="alternate"'
        
        return response


# Usage example
if __name__ == "__main__":
    # Create version manager
    version_manager = create_default_version_manager()
    
    # Example: Handle versioned request
    from fastapi import FastAPI, Request
    
    app = FastAPI()
    
    @app.middleware("http")
    async def version_middleware(request: Request, call_next):
        middleware = VersioningMiddleware(version_manager)
        return await middleware(request, call_next)
    
    @app.post("/v1/customers")
    @app.post("/v2/customers")
    async def create_customer(request: Request, customer_data: dict):
        version = request.state.api_version
        
        # Transform request data if needed
        if version == "v1":
            customer_data = version_manager.request_transformer.transform(
                customer_data, "v1", "v2", "/customers", "POST"
            )
        
        # Process with V2 logic (always use latest internal version)
        # ... business logic here ...
        result = {"id": "123", "first_name": "John", "last_name": "Doe"}
        
        # Create versioned response
        versioned_response = version_manager.create_versioned_response(
            result, "v2", "/customers", "POST", version
        )
        
        return versioned_response
