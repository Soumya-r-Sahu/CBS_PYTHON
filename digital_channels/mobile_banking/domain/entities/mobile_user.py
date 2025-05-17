"""
Mobile user entity in the Mobile Banking domain.
This entity represents a Mobile Banking user with authentication credentials.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4


class MobileUserStatus(Enum):
    """Status of a Mobile Banking user."""
    ACTIVE = "active"
    LOCKED = "locked"
    PENDING_ACTIVATION = "pending_activation"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class DeviceStatus(Enum):
    """Status of a registered mobile device."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BLACKLISTED = "blacklisted"


@dataclass
class RegisteredDevice:
    """Device information for a mobile banking user."""
    device_id: str
    device_name: str
    device_model: str
    os_type: str
    os_version: str
    app_version: str
    registration_date: datetime
    status: DeviceStatus
    last_access_date: Optional[datetime] = None
    last_ip_address: Optional[str] = None
    biometric_enabled: bool = False
    pin_enabled: bool = False


@dataclass
class MobileCredential:
    """Credential information for a mobile user."""
    username: str
    password_hash: str
    salt: str
    last_password_change: datetime
    mpin: Optional[str] = None
    mpin_last_change: Optional[datetime] = None
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
    
    def update_mpin(self, new_mpin: str) -> None:
        """
        Update the mobile PIN.
        
        Args:
            new_mpin: New mobile PIN (already hashed)
        """
        self.mpin = new_mpin
        self.mpin_last_change = datetime.now()


@dataclass
class MobileBankingUser:
    """Mobile Banking user entity with domain logic."""
    
    # Identity attributes
    user_id: UUID
    customer_id: UUID
    
    # Profile attributes
    email: str
    phone_number: str
    
    # Security attributes
    credentials: MobileCredential
    status: MobileUserStatus
    
    # Device attributes
    registered_devices: List[RegisteredDevice]
    
    # Preferences attributes
    default_language: str
    notification_preferences: dict
    
    # Audit attributes
    created_at: datetime
    last_login: Optional[datetime] = None
    
    @classmethod
    def create(cls, customer_id: UUID, email: str, phone_number: str, 
               username: str, password_hash: str, salt: str,
               device_id: str, device_name: str, device_model: str,
               os_type: str, os_version: str, app_version: str) -> 'MobileBankingUser':
        """
        Create a new Mobile Banking user.
        
        Args:
            customer_id: ID of the associated customer
            email: Email address
            phone_number: Phone number
            username: Username for login
            password_hash: Hashed password
            salt: Salt used for password hashing
            device_id: ID of the device used for registration
            device_name: Name of the device
            device_model: Model of the device
            os_type: Operating system type
            os_version: Operating system version
            app_version: Mobile app version
            
        Returns:
            New MobileBankingUser instance
        """
        now = datetime.now()
        
        credentials = MobileCredential(
            username=username,
            password_hash=password_hash,
            salt=salt,
            last_password_change=now,
            failed_login_attempts=0
        )
        
        device = RegisteredDevice(
            device_id=device_id,
            device_name=device_name,
            device_model=device_model,
            os_type=os_type,
            os_version=os_version,
            app_version=app_version,
            registration_date=now,
            status=DeviceStatus.ACTIVE,
            last_access_date=now
        )
        
        return cls(
            user_id=uuid4(),
            customer_id=customer_id,
            email=email,
            phone_number=phone_number,
            credentials=credentials,
            status=MobileUserStatus.PENDING_ACTIVATION,
            registered_devices=[device],
            default_language="en",
            notification_preferences={
                "push_notifications": True,
                "sms_notifications": True,
                "email_notifications": True
            },
            created_at=now
        )
    
    def activate(self) -> None:
        """Activate the user account."""
        if self.status != MobileUserStatus.PENDING_ACTIVATION:
            raise ValueError(f"Cannot activate user with status: {self.status}")
        
        self.status = MobileUserStatus.ACTIVE
    
    def lock(self) -> None:
        """Lock the user account."""
        if self.status not in [MobileUserStatus.ACTIVE, MobileUserStatus.PENDING_ACTIVATION]:
            raise ValueError(f"Cannot lock user with status: {self.status}")
        
        self.status = MobileUserStatus.LOCKED
    
    def suspend(self) -> None:
        """Suspend the user account."""
        if self.status not in [MobileUserStatus.ACTIVE, MobileUserStatus.LOCKED]:
            raise ValueError(f"Cannot suspend user with status: {self.status}")
        
        self.status = MobileUserStatus.SUSPENDED
    
    def reactivate(self) -> None:
        """Reactivate a locked or suspended user account."""
        if self.status not in [MobileUserStatus.LOCKED, MobileUserStatus.SUSPENDED, MobileUserStatus.INACTIVE]:
            raise ValueError(f"Cannot reactivate user with status: {self.status}")
        
        self.status = MobileUserStatus.ACTIVE
    
    def deactivate(self) -> None:
        """Deactivate the user account."""
        if self.status == MobileUserStatus.INACTIVE:
            raise ValueError("User is already inactive")
        
        self.status = MobileUserStatus.INACTIVE
    
    def add_device(self, device: RegisteredDevice) -> None:
        """
        Add a new device to the user's registered devices.
        
        Args:
            device: The device to add
        """
        # Check if device already exists
        for existing_device in self.registered_devices:
            if existing_device.device_id == device.device_id:
                raise ValueError(f"Device with ID {device.device_id} is already registered")
        
        self.registered_devices.append(device)
    
    def remove_device(self, device_id: str) -> None:
        """
        Remove a device from the user's registered devices.
        
        Args:
            device_id: ID of the device to remove
        """
        self.registered_devices = [d for d in self.registered_devices if d.device_id != device_id]
    
    def update_device_status(self, device_id: str, status: DeviceStatus) -> None:
        """
        Update the status of a registered device.
        
        Args:
            device_id: ID of the device to update
            status: New status for the device
        """
        for device in self.registered_devices:
            if device.device_id == device_id:
                device.status = status
                return
        
        raise ValueError(f"Device with ID {device_id} not found")
    
    def record_login(self, successful: bool, device_id: Optional[str] = None, ip_address: Optional[str] = None) -> None:
        """
        Record a login attempt.
        
        Args:
            successful: Whether the login was successful
            device_id: ID of the device used for login
            ip_address: IP address used for login
        """
        self.credentials.record_login_attempt(successful)
        
        if successful:
            self.last_login = datetime.now()
            
            # Update device info if provided
            if device_id:
                for device in self.registered_devices:
                    if device.device_id == device_id:
                        device.last_access_date = datetime.now()
                        if ip_address:
                            device.last_ip_address = ip_address
                        break
        
        # Auto-lock after 5 failed attempts
        if self.credentials.failed_login_attempts >= 5 and self.status == MobileUserStatus.ACTIVE:
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
    
    def update_preferences(self, preferences: dict) -> None:
        """
        Update the user's notification preferences.
        
        Args:
            preferences: New notification preferences
        """
        self.notification_preferences.update(preferences)
    
    def set_language(self, language_code: str) -> None:
        """
        Set the user's preferred language.
        
        Args:
            language_code: Language code (e.g., 'en', 'es')
        """
        self.default_language = language_code
