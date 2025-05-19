"""
ATM Session Entity

This module defines the ATM Session entity for the Core Banking System.
"""

import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



@dataclass
class AtmSession:
    """Value object representing an ATM session"""
    
    session_token: str
    card_number: str
    account_id: int
    expiry_time: float
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def is_valid(self) -> bool:
        """Check if the session is still valid"""
        return time.time() < self.expiry_time
    
    def remaining_time(self) -> int:
        """Get remaining session time in seconds"""
        if not self.is_valid():
            return 0
        return int(self.expiry_time - time.time())
    
    @staticmethod
    def create(card_number: str, account_id: int, expiry_seconds: int = 300) -> 'AtmSession':
        """Create a new ATM session"""
        return AtmSession(
            session_token=str(uuid.uuid4()),
            card_number=card_number,
            account_id=account_id,
            expiry_time=time.time() + expiry_seconds
        )
    
    def extend_session(self, seconds: int = 300) -> None:
        """Extend session validity period"""
        self.expiry_time = time.time() + seconds
