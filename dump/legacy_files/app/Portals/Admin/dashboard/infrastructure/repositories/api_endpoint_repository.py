"""
API endpoint repository implementation.
"""
from typing import Dict, List, Optional, Any
from django.db.models import Q
from dashboard.domain.entities.api_endpoint import ApiEndpoint as ApiEndpointEntity, HttpMethod as HttpMethodEntity
from dashboard.application.interfaces.repositories import ApiEndpointRepository
from dashboard.models import ApiEndpoint as ApiEndpointModel, HttpMethod


class DjangoApiEndpointRepository(ApiEndpointRepository):
    """Django implementation of the ApiEndpointRepository interface."""

    def get_all_endpoints(self) -> List[ApiEndpointEntity]:
        """Get all API endpoints."""
        endpoints = ApiEndpointModel.objects.all()
        return [self._to_entity(endpoint) for endpoint in endpoints]
    
    def get_endpoint_by_id(self, endpoint_id: str) -> Optional[ApiEndpointEntity]:
        """Get an API endpoint by its ID."""
        try:
            endpoint = ApiEndpointModel.objects.get(id=endpoint_id)
            return self._to_entity(endpoint)
        except ApiEndpointModel.DoesNotExist:
            return None
    
    def get_endpoints_by_module(self, module_id: str) -> List[ApiEndpointEntity]:
        """Get all API endpoints for a specific module."""
        endpoints = ApiEndpointModel.objects.filter(module_id=module_id)
        return [self._to_entity(endpoint) for endpoint in endpoints]
    
    def create_endpoint(self, endpoint: ApiEndpointEntity) -> ApiEndpointEntity:
        """Create a new API endpoint."""
        model = ApiEndpointModel(
            id=endpoint.id,
            path=endpoint.path,
            module_id=endpoint.module_id,
            method=endpoint.method.value,
            enabled=endpoint.enabled,
            auth_required=endpoint.auth_required,
            rate_limit=endpoint.rate_limit,
            description=endpoint.description
        )
        model.save()
        return self._to_entity(model)
    
    def update_endpoint(self, endpoint: ApiEndpointEntity) -> ApiEndpointEntity:
        """Update an existing API endpoint."""
        try:
            model = ApiEndpointModel.objects.get(id=endpoint.id)
            model.path = endpoint.path
            model.module_id = endpoint.module_id
            model.method = endpoint.method.value
            model.enabled = endpoint.enabled
            model.auth_required = endpoint.auth_required
            model.rate_limit = endpoint.rate_limit
            model.description = endpoint.description
            model.save()
            return self._to_entity(model)
        except ApiEndpointModel.DoesNotExist:
            return None
    
    def delete_endpoint(self, endpoint_id: str) -> bool:
        """Delete an API endpoint by its ID."""
        try:
            endpoint = ApiEndpointModel.objects.get(id=endpoint_id)
            endpoint.delete()
            return True
        except ApiEndpointModel.DoesNotExist:
            return False
    
    def toggle_endpoint(self, endpoint_id: str, enabled: bool) -> Optional[ApiEndpointEntity]:
        """Enable or disable an API endpoint."""
        try:
            endpoint = ApiEndpointModel.objects.get(id=endpoint_id)
            endpoint.enabled = enabled
            endpoint.save()
            return self._to_entity(endpoint)
        except ApiEndpointModel.DoesNotExist:
            return None
    
    def _to_entity(self, model: ApiEndpointModel) -> ApiEndpointEntity:
        """Convert a Django model to a domain entity."""
        return ApiEndpointEntity(
            id=model.id,
            path=model.path,
            module_id=model.module.id,
            method=HttpMethodEntity(model.method),
            enabled=model.enabled,
            auth_required=model.auth_required,
            rate_limit=model.rate_limit,
            description=model.description,
            last_accessed=model.last_accessed.isoformat() if model.last_accessed else None,
            success_count=model.success_count,
            error_count=model.error_count
        )
