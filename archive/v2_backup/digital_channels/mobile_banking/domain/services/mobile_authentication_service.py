"""
Authentication service for Mobile Banking domain.
Contains domain business logic for authentication.
"""
from typing import Optional
from uuid import UUID
import hashlib
import os

from ..entities.mobile_user import MobileBankingUser, MobileUserStatus
from ..entities.mobile_session import MobileBankingSession

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class MobileAuthenticationService:
    """Domain service for authentication business rules and logic."""
    
    @staticmethod
    def verify_password(user: MobileBankingUser, password: str) -> bool:
        """
        Verify if the provided password matches the user's stored password.
        
        Args:
            user: The user whose password to check
            password: The password to verify
            
        Returns:
            Boolean indicating if the password is correct
        """
        # Hash the provided password with the user's salt
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            user.credentials.salt.encode('utf-8'),
            100000  # Number of iterations
        ).hex()
        
        # Compare with stored hash
        return password_hash == user.credentials.password_hash
    
    @staticmethod
    def verify_mpin(user: MobileBankingUser, mpin: str) -> bool:
        """
        Verify if the provided MPIN matches the user's stored MPIN.
        
        Args:
            user: The user whose MPIN to check
            mpin: The MPIN to verify
            
        Returns:
            Boolean indicating if the MPIN is correct
        """
        if not user.credentials.mpin:
            return False
        
        # In a real implementation, the MPIN would be hashed
        # For this example, we're doing a simple comparison
        return mpin == user.credentials.mpin
    
    @staticmethod
    def can_login(user: MobileBankingUser) -> bool:
        """
        Check if a user is allowed to login based on their status.
        
        Args:
            user: The user to check
            
        Returns:
            Boolean indicating if the user can login
        """
        # Only active users can login
        return user.status == MobileUserStatus.ACTIVE
    
    @staticmethod
    def generate_password_hash(password: str) -> tuple[str, str]:
        """
        Generate a secure password hash with a random salt.
        
        Args:
            password: The password to hash
            
        Returns:
            Tuple containing (password_hash, salt)
        """
        # Generate a random salt
        salt = os.urandom(32).hex()
        
        # Hash the password with the salt
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # Number of iterations
        ).hex()
        
        return password_hash, salt
    
    @staticmethod
    def is_session_valid(session: MobileBankingSession) -> bool:
        """
        Check if a session is valid and not expired.
        
        Args:
            session: The session to check
            
        Returns:
            Boolean indicating if the session is valid
        """
        return session.is_valid()
    
    @staticmethod
    def should_prompt_password_change(user: MobileBankingUser, max_days: int = 90) -> bool:
        """
        Check if the user should be prompted to change their password.
        
        Args:
            user: The user to check
            max_days: Maximum days a password can be used before change prompt
            
        Returns:
            Boolean indicating if the user should change their password
        """
        from datetime import datetime, timedelta
        
        password_age = datetime.now() - user.credentials.last_password_change
        return password_age > timedelta(days=max_days)
    
    @staticmethod
    def should_prompt_mpin_change(user: MobileBankingUser, max_days: int = 180) -> bool:
        """
        Check if the user should be prompted to change their MPIN.
        
        Args:
            user: The user to check
            max_days: Maximum days an MPIN can be used before change prompt
            
        Returns:
            Boolean indicating if the user should change their MPIN
        """
        from datetime import datetime, timedelta
        
        if not user.credentials.mpin or not user.credentials.mpin_last_change:
            return False
            
        mpin_age = datetime.now() - user.credentials.mpin_last_change
        return mpin_age > timedelta(days=max_days)
    
    @staticmethod
    def is_biometric_enabled(user: MobileBankingUser, device_id: str) -> bool:
        """
        Check if biometric authentication is enabled for a specific device.
        
        Args:
            user: The user to check
            device_id: The device ID to check
            
        Returns:
            Boolean indicating if biometric authentication is enabled
        """
        for device in user.registered_devices:
            if device.device_id == device_id:
                return device.biometric_enabled
        
        return False
