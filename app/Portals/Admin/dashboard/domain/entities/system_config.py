"""
System Configuration entity for the admin dashboard.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ConfigType(Enum):
    """Types of configuration settings."""
    SYSTEM = "system"
    MODULE = "module"
    API = "api"
    FEATURE = "feature"
    SECURITY = "security"
    PERFORMANCE = "performance"


@dataclass
class SystemConfig:
    """System Configuration entity representing configurable settings in the CBS system."""
    id: str
    key: str
    value: Any
    type: ConfigType
    module_id: Optional[str] = None
    description: Optional[str] = None
    is_sensitive: bool = False
    allowed_values: Optional[Dict[str, Any]] = None
    last_modified: Optional[str] = None
    modified_by: Optional[str] = None
