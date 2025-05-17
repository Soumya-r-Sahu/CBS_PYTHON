"""
User entity in the Internet Banking domain.
This entity represents an Internet Banking user with authentication credentials.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4


class UserStatus(Enum):
    """Status of an Internet Banking user."""
    ACTIVE = "active"
    LOCKED = "locked"
    PENDING_ACTIVATION = "pending_activation"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


@dataclass
class UserCredential:
    """Credential information for a user."""
    username: str
    password_hash: str
    salt: str
    last_password_change: datetime
    failed_login_attempts: int = 0
    
    def record_login_attempt(self, success: bool) -> None:
        """
        Record a login attempt.
        
        Args:
            success: Whether the login was successful
        """
        if success:
            self.failed_login_attempts = 0
        else:
            self.failed_login_attempts += 1


@dataclass
class InternetBankingUser:
    """Internet Banking user entity with domain logic."""
    
    # Identity attributes
    user_id: UUID
    customer_id: UUID
    
    # Profile attributes
    email: str
    phone_number: str
    
    # Security attributes
    credentials: UserCredential
    status: UserStatus
    
    # Audit attributes
    created_at: datetime
    last_login: Optional[datetime] = None
    registered_devices: List[str] = None
    
    @classmethod
    def create(cls, customer_id: UUID, email: str, phone_number: str, 
               username: str, password_hash: str, salt: str) -> 'InternetBankingUser':
        """
        Create a new Internet Banking user.
        
        Args:
            customer_id: ID of the associated customer
            email: Email address
            phone_number: Phone number
            username: Username for login
            password_hash: Hashed password
            salt: Salt used for password hashing
            
        Returns:
            New InternetBankingUser instance
        """
        now = datetime.now()
        
        credentials = UserCredential(
            username=username,
            password_hash=password_hash,
            salt=salt,
            last_password_change=now,
            failed_login_attempts=0
        )
        
        return cls(
            user_id=uuid4(),
            customer_id=customer_id,
            email=email,
            phone_number=phone_number,
            credentials=credentials,
            status=UserStatus.PENDING_ACTIVATION,
            created_at=now,
            registered_devices=[]
        )
    
    def activate(self) -> None:
        """Activate the user account."""
        if self.status != UserStatus.PENDING_ACTIVATION:
            raise ValueError(f"Cannot activate user with status: {self.status}")
        
        self.status = UserStatus.ACTIVE
    
    def lock(self) -> None:
        """Lock the user account."""
        if self.status not in [UserStatus.ACTIVE, UserStatus.PENDING_ACTIVATION]:
            raise ValueError(f"Cannot lock user with status: {self.status}")
        
        self.status = UserStatus.LOCKED
    
    def suspend(self) -> None:
        """Suspend the user account."""
        if self.status not in [UserStatus.ACTIVE, UserStatus.LOCKED]:
            raise ValueError(f"Cannot suspend user with status: {self.status}")
        
        self.status = UserStatus.SUSPENDED
    
    def reactivate(self) -> None:
        """Reactivate a locked or suspended user account."""
        if self.status not in [UserStatus.LOCKED, UserStatus.SUSPENDED, UserStatus.INACTIVE]:
            raise ValueError(f"Cannot reactivate user with status: {self.status}")
        
        self.status = UserStatus.ACTIVE
    
    def deactivate(self) -> None:
        """Deactivate the user account."""
        if self.status == UserStatus.INACTIVE:
            raise ValueError("User is already inactive")
        
        self.status = UserStatus.INACTIVE
    
    def record_login(self, successful: bool, device_id: Optional[str] = None) -> None:
        """
        Record a login attempt.
        
        Args:
            successful: Whether the login was successful
            device_id: ID of the device used for login
        """
        self.credentials.record_login_attempt(successful)
        
        if successful:
            self.last_login = datetime.now()
            
            if device_id and device_id not in self.registered_devices:
                self.registered_devices.append(device_id)
        
        # Auto-lock after 5 failed attempts
        if self.credentials.failed_login_attempts >= 5 and self.status == UserStatus.ACTIVE:
            self.lock()
    
    def update_email(self, new_email: str) -> None:
        """
        Update the user's email address.
        
        Args:
            new_email: New email address
        """
        if not new_email or '@' not in new_email:
            raise ValueError("Invalid email format")
        
        self.email = new_email
    
    def update_phone(self, new_phone: str) -> None:
        """
        Update the user's phone number.
        
        Args:
            new_phone: New phone number
        """
        if not new_phone:
            raise ValueError("Phone number cannot be empty")
        
        self.phone_number = new_phone
    
    def change_password(self, new_password_hash: str, new_salt: str) -> None:
        """
        Change the user's password.
        
        Args:
            new_password_hash: New hashed password
            new_salt: New salt used for password hashing
        """
        self.credentials.password_hash = new_password_hash
        self.credentials.salt = new_salt
        self.credentials.last_password_change = datetime.now()
        self.credentials.failed_login_attempts = 0
