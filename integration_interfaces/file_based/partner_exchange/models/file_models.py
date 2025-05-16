"""
Partner File Exchange Models - Core Banking System

This module defines data models for partner file exchanges.
"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime



# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
@dataclass
class PartnerFileEntry:
    """Represents a single entry in a partner exchange file"""
    transaction_id: str
    partner_id: str
    amount: float
    status: str
    timestamp: str

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            "transaction_id": self.transaction_id,
            "partner_id": self.partner_id,
            "amount": self.amount,
            "status": self.status,
            "timestamp": self.timestamp
        }


@dataclass
class PartnerFile:
    """Represents a partner exchange file and its metadata"""
    filename: str
    partner_id: str
    file_type: str  # settlement, reconciliation, etc.
    created_at: datetime
    entries: List[PartnerFileEntry]
    processed: bool = False
    error: Optional[str] = None
