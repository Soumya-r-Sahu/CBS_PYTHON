"""
API Logging Models - Core Banking System

This module defines data models for API logging.
"""
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, Any, Optional, List



# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
@dataclass
class ApiLogEntry:
    """Represents a single API log entry"""
    timestamp: str
    endpoint: str
    request: Dict[str, Any]
    response: Dict[str, Any]
    status: str
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return asdict(self)


@dataclass
class ApiLogSummary:
    """Summary statistics for API logs"""
    total_requests: int
    success_count: int
    error_count: int
    avg_duration_ms: float
    min_duration_ms: int
    max_duration_ms: int
    period_start: datetime
    period_end: datetime
    endpoints: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ApiErrorGroup:
    """Group of similar API errors"""
    error_type: str
    count: int
    first_occurrence: datetime
    last_occurrence: datetime
    endpoints: List[str]
    sample_errors: List[Dict[str, Any]]
