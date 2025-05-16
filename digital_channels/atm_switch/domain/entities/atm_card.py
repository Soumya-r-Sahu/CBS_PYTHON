"""
ATM Card Entity

This module defines the ATM Card entity for the Core Banking System.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal


@dataclass
class AtmCard:
    """Entity representing an ATM card"""
    
    card_number: str
    account_id: int
    expiry_date: datetime
    is_active: bool = True
    failed_pin_attempts: int = 0
    status: Literal["ACTIVE", "BLOCKED", "EXPIRED", "SUSPENDED"] = "ACTIVE"
    last_used_at: Optional[datetime] = None
    
    def is_valid(self) -> bool:
        """Check if card is valid and active"""
        return (self.is_active and 
                self.status == "ACTIVE" and 
                datetime.now() < self.expiry_date)
    
    def is_blocked(self) -> bool:
        """Check if card is blocked"""
        return self.status == "BLOCKED"
    
    def is_expired(self) -> bool:
        """Check if card is expired"""
        return datetime.now() >= self.expiry_date
    
    def increment_failed_attempts(self) -> None:
        """Increment failed PIN attempts"""
        self.failed_pin_attempts += 1
        if self.failed_pin_attempts >= 3:
            self.status = "BLOCKED"
    
    def reset_failed_attempts(self) -> None:
        """Reset failed PIN attempts"""
        self.failed_pin_attempts = 0
    
    def record_usage(self) -> None:
        """Record card usage timestamp"""
        self.last_used_at = datetime.now()
