"""
System Health entity for the admin dashboard.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class HealthStatus(Enum):
    """Health status indicators."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class SystemHealth:
    """System Health entity representing the health status of a system component."""
    id: str
    component: str  # Module name or system component
    status: HealthStatus
    timestamp: str
    metrics: Dict[str, float] = field(default_factory=dict)
    details: Optional[Dict] = None
    alerts: List[str] = field(default_factory=list)
