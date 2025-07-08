"""
API Endpoint entity for the admin dashboard.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class HttpMethod(Enum):
    """HTTP Methods supported by API endpoints."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


@dataclass
class ApiEndpoint:
    """API Endpoint entity representing an API endpoint in the CBS system."""
    id: str
    path: str
    module_id: str
    method: HttpMethod
    enabled: bool
    auth_required: bool
    rate_limit: Optional[int] = None  # requests per minute
    description: Optional[str] = None
    last_accessed: Optional[str] = None
    success_count: int = 0
    error_count: int = 0
