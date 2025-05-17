"""
Session entity in the Internet Banking domain.
This entity represents a user session with security attributes.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class SessionStatus(Enum):
    """Status of an Internet Banking session."""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


@dataclass
class InternetBankingSession:
    """Internet Banking session entity with security attributes."""
    
    # Identity attributes
    session_id: UUID
    user_id: UUID
    
    # Security attributes
    ip_address: str
    user_agent: str
    device_id: Optional[str]
    
    # State attributes
    created_at: datetime
    last_activity: datetime
    status: SessionStatus
    expires_at: datetime
    
    # Optional attributes
    location: Optional[str] = None
    
    @classmethod
    def create(cls, user_id: UUID, ip_address: str, user_agent: str, 
               device_id: Optional[str] = None, session_timeout_minutes: int = 30) -> 'InternetBankingSession':
        """
        Create a new Internet Banking session.
        
        Args:
            user_id: ID of the session user
            ip_address: IP address of the client
            user_agent: User agent string from the client
            device_id: Optional device identifier
            session_timeout_minutes: Session timeout in minutes
            
        Returns:
            New InternetBankingSession instance
        """
        now = datetime.now()
        
        return cls(
            session_id=uuid4(),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            created_at=now,
            last_activity=now,
            status=SessionStatus.ACTIVE,
            expires_at=now + timedelta(minutes=session_timeout_minutes)
        )
    
    def is_valid(self) -> bool:
        """
        Check if the session is valid (active and not expired).
        
        Returns:
            Boolean indicating if the session is valid
        """
        if self.status != SessionStatus.ACTIVE:
            return False
        
        return datetime.now() < self.expires_at
    
    def update_activity(self, session_timeout_minutes: int = 30) -> None:
        """
        Update the session's last activity timestamp and extend expiration.
        
        Args:
            session_timeout_minutes: Session timeout in minutes
        """
        now = datetime.now()
        self.last_activity = now
        self.expires_at = now + timedelta(minutes=session_timeout_minutes)
    
    def terminate(self) -> None:
        """Terminate the session."""
        self.status = SessionStatus.TERMINATED
    
    def expire(self) -> None:
        """Mark the session as expired."""
        self.status = SessionStatus.EXPIRED
    
    def update_ip_address(self, new_ip_address: str) -> None:
        """
        Update the IP address associated with the session.
        
        Args:
            new_ip_address: New IP address
        """
        self.ip_address = new_ip_address
    
    def update_location(self, location: str) -> None:
        """
        Update the location information for the session.
        
        Args:
            location: Location information
        """
        self.location = location
