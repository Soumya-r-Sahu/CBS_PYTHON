"""
Mobile session entity in the Mobile Banking domain.
This entity represents a user session with security attributes.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4


class MobileSessionStatus(Enum):
    """Status of a Mobile Banking session."""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


@dataclass
class MobileBankingSession:
    """Mobile Banking session entity with security attributes."""
    
    # Identity attributes
    session_id: UUID
    user_id: UUID
    
    # Security attributes
    device_id: str
    app_version: str
    os_type: str
    os_version: str
    ip_address: Optional[str]
    
    # State attributes
    created_at: datetime
    last_activity: datetime
    status: MobileSessionStatus
    expires_at: datetime
    
    # Optional attributes
    location: Optional[str] = None
    biometric_used: bool = False
    
    @classmethod
    def create(cls, user_id: UUID, device_id: str, app_version: str, os_type: str, os_version: str,
               ip_address: Optional[str] = None, biometric_used: bool = False,
               session_timeout_minutes: int = 30) -> 'MobileBankingSession':
        """
        Create a new Mobile Banking session.
        
        Args:
            user_id: ID of the session user
            device_id: ID of the mobile device
            app_version: Version of the mobile app
            os_type: OS type (iOS, Android, etc.)
            os_version: OS version
            ip_address: IP address of the client (optional)
            biometric_used: Whether biometric authentication was used
            session_timeout_minutes: Session timeout in minutes
            
        Returns:
            New MobileBankingSession instance
        """
        now = datetime.now()
        
        return cls(
            session_id=uuid4(),
            user_id=user_id,
            device_id=device_id,
            app_version=app_version,
            os_type=os_type,
            os_version=os_version,
            ip_address=ip_address,
            created_at=now,
            last_activity=now,
            status=MobileSessionStatus.ACTIVE,
            expires_at=now + timedelta(minutes=session_timeout_minutes),
            biometric_used=biometric_used
        )
    
    def is_valid(self) -> bool:
        """
        Check if the session is valid (active and not expired).
        
        Returns:
            Boolean indicating if the session is valid
        """
        if self.status != MobileSessionStatus.ACTIVE:
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
        self.status = MobileSessionStatus.TERMINATED
    
    def expire(self) -> None:
        """Mark the session as expired."""
        self.status = MobileSessionStatus.EXPIRED
    
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
