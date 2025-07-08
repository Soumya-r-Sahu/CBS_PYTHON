"""
Module entity for the admin dashboard.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class ModuleStatus(Enum):
    """Status of a CBS module."""
    INSTALLED = "installed"
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
    MAINTENANCE = "maintenance"
    FAILED = "failed"


@dataclass
class FeatureFlag:
    """Feature flag entity."""
    name: str
    description: str
    enabled: bool
    module_id: str
    affects_endpoints: List[str]
    id: Optional[str] = None


@dataclass
class Module:
    """Module entity representing a CBS system module."""
    id: str
    name: str
    version: str
    status: ModuleStatus
    dependencies: List[str] = field(default_factory=list)
    features: Dict[str, FeatureFlag] = field(default_factory=dict)
    description: Optional[str] = None
    last_modified: Optional[str] = None
