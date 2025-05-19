"""
Admin Domain Layer for Core Banking System

This module defines the core domain entities for the Admin module.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

class ModuleStatus(Enum):
    """Status options for a module"""
    INSTALLED = "installed"
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
    MAINTENANCE = "maintenance"
    FAILED = "failed"

@dataclass
class Module:
    """Core entity representing a system module"""
    id: str
    name: str
    version: str
    status: ModuleStatus
    dependencies: List[str]
    features: Dict[str, 'FeatureFlag'] = field(default_factory=dict)

@dataclass
class ApiEndpoint:
    """Core entity representing an API endpoint"""
    id: str
    path: str
    module_id: str
    method: str  # GET, POST, etc.
    enabled: bool
    rate_limit: Optional[int] = None  # requests per minute
    auth_required: bool = True
    
@dataclass
class FeatureFlag:
    """Core entity representing a feature flag"""
    name: str
    description: str
    enabled: bool
    module_id: str
    affects_endpoints: List[str] = field(default_factory=list)
