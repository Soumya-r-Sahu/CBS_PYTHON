"""
Authentication domain service for the Internet Banking domain.
Contains core business logic for user authentication.
"""
from typing import Optional
from uuid import UUID
import hashlib
import os

from ..entities.user import InternetBankingUser, UserStatus
from ..entities.session import InternetBankingSession


class AuthenticationService:
    """Domain service for authentication business rules and logic."""
    
    @staticmethod
    def verify_password(user: InternetBankingUser, password: str) -> bool:
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
    def can_login(user: InternetBankingUser) -> bool:
        """
        Check if a user is allowed to login based on their status.
        
        Args:
            user: The user to check
            
        Returns:
            Boolean indicating if the user can login
        """
        # Only active users can login
        return user.status == UserStatus.ACTIVE
    
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
    def is_session_valid(session: InternetBankingSession) -> bool:
        """
        Check if a session is valid and not expired.
        
        Args:
            session: The session to check
            
        Returns:
            Boolean indicating if the session is valid
        """
        return session.is_valid()
    
    @staticmethod
    def should_prompt_password_change(user: InternetBankingUser, max_days: int = 90) -> bool:
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
