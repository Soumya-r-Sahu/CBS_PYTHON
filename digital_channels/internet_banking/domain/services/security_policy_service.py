"""
Security domain service for the Internet Banking domain.
Contains security-related business rules and validations.
"""
from datetime import datetime, timedelta
from typing import List

from ..entities.user import InternetBankingUser
from ..entities.session import InternetBankingSession


class SecurityPolicyService:
    """Domain service for security policy rules and validations."""
    
    @staticmethod
    def is_secure_password(password: str) -> tuple[bool, str]:
        """
        Check if a password meets security requirements.
        
        Args:
            password: The password to check
            
        Returns:
            Tuple of (is_secure, reason)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(char.isupper() for char in password):
            return False, "Password must contain at least one uppercase letter"
            
        if not any(char.islower() for char in password):
            return False, "Password must contain at least one lowercase letter"
            
        if not any(char.isdigit() for char in password):
            return False, "Password must contain at least one number"
            
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?/"
        if not any(char in special_chars for char in password):
            return False, "Password must contain at least one special character"
            
        return True, ""
    
    @staticmethod
    def detect_suspicious_activity(
        user: InternetBankingUser, 
        session: InternetBankingSession,
        known_devices: List[str],
        known_locations: List[str]
    ) -> tuple[bool, str]:
        """
        Detect suspicious activity based on user behavior.
        
        Args:
            user: The user to check
            session: The current session
            known_devices: List of known device IDs for this user
            known_locations: List of known locations for this user
            
        Returns:
            Tuple of (is_suspicious, reason)
        """
        # Check if device is known
        if session.device_id and session.device_id not in known_devices and len(known_devices) > 0:
            return True, "Login from new device detected"
        
        # Check if location is known (if we have location info)
        if session.location and session.location not in known_locations and len(known_locations) > 0:
            return True, "Login from new location detected"
            
        return False, ""
    
    @staticmethod
    def should_enforce_additional_authentication(user: InternetBankingUser, activity_risk_level: str) -> bool:
        """
        Determine if additional authentication should be required.
        
        Args:
            user: The user to check
            activity_risk_level: Risk level of the current activity (low, medium, high)
            
        Returns:
            Boolean indicating if additional authentication is needed
        """
        # Always require additional authentication for high-risk activities
        if activity_risk_level == "high":
            return True
            
        # For medium-risk activities, require if there's suspicious activity history
        if activity_risk_level == "medium" and user.credentials.failed_login_attempts > 2:
            return True
            
        return False
    
    @staticmethod
    def is_within_transaction_limits(
        user: InternetBankingUser, 
        transaction_amount: float,
        daily_limit: float,
        daily_spent: float
    ) -> bool:
        """
        Check if a transaction is within the user's limits.
        
        Args:
            user: The user making the transaction
            transaction_amount: Amount of the transaction
            daily_limit: User's daily transaction limit
            daily_spent: Amount already spent today
            
        Returns:
            Boolean indicating if the transaction is within limits
        """
        # Check if this transaction would exceed daily limit
        return (daily_spent + transaction_amount) <= daily_limit
