"""
Security Centralized Utilities

This module provides common utilities and helper functions for all components
of the Security module. Centralizing these utilities reduces code duplication
and ensures consistent security implementations across the system.
"""

import logging
import datetime
import uuid
import os
import re
import json
import base64
import hashlib
import secrets
import string
from typing import Dict, List, Optional, Any, Union, Tuple
import hmac
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

# Setup logging
logger = logging.getLogger(__name__)

# Constants
PASSWORD_MIN_LENGTH = 12
PASSWORD_COMPLEXITY_REGEX = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]+$'
OTP_LENGTH = 6
TOKEN_EXPIRY_MINUTES = 15
FERNET_KEY_PATH = os.getenv('FERNET_KEY_PATH', 'security/keys/fernet_key.key')


class SecurityException(Exception):
    """Base exception class for all Security exceptions"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AuthenticationException(SecurityException):
    """Exception raised for authentication errors"""
    pass


class AuthorizationException(SecurityException):
    """Exception raised for authorization errors"""
    pass


class EncryptionException(SecurityException):
    """Exception raised for encryption/decryption errors"""
    pass


# Password utilities
class PasswordUtils:
    """Password handling utilities"""
    
    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """
        Validate if a password meets security requirements
        
        Args:
            password: Password to validate
            
        Returns:
            True if password meets requirements, False otherwise
        """
        if not password or len(password) < PASSWORD_MIN_LENGTH:
            return False
            
        # Check for complexity requirements
        # At least one uppercase, one lowercase, one digit, one special character
        return bool(re.match(PASSWORD_COMPLEXITY_REGEX, password))
    
    @staticmethod
    def generate_password_hash(password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
        """
        Generate a secure hash for password storage
        
        Args:
            password: Password to hash
            salt: Optional salt, generated if not provided
            
        Returns:
            Tuple of (password_hash, salt)
        """
        if salt is None:
            salt = os.urandom(32)  # 32 bytes salt
            
        # Use PBKDF2 with SHA256 for secure password hashing
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        hash_bytes = kdf.derive(password.encode('utf-8'))
        password_hash = base64.b64encode(hash_bytes).decode('utf-8')
        
        return password_hash, salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: bytes) -> bool:
        """
        Verify a password against a stored hash
        
        Args:
            password: Password to verify
            stored_hash: Previously stored password hash
            salt: Salt used during hashing
            
        Returns:
            True if password is correct, False otherwise
        """
        # Hash the password with the same salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        hash_bytes = kdf.derive(password.encode('utf-8'))
        password_hash = base64.b64encode(hash_bytes).decode('utf-8')
        
        # Compare with stored hash
        return hmac.compare_digest(password_hash, stored_hash)
    
    @staticmethod
    def generate_strong_password(length: int = 16) -> str:
        """
        Generate a strong random password
        
        Args:
            length: Length of the password
            
        Returns:
            Secure random password
        """
        if length < 12:
            length = 12  # Enforce minimum length
            
        # Define character sets
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        special = "@$!%*?&"
        
        # Ensure at least one character from each set
        password = [
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Fill the rest with random characters from all sets
        all_chars = uppercase + lowercase + digits + special
        password.extend(secrets.choice(all_chars) for _ in range(length - 4))
        
        # Shuffle the password characters
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)


# Token generation and validation
class TokenUtils:
    """Token handling utilities"""
    
    @staticmethod
    def generate_token() -> str:
        """
        Generate a secure random token
        
        Returns:
            Secure random token
        """
        # Generate 32 bytes of random data
        token_bytes = secrets.token_bytes(32)
        # Convert to URL-safe base64 without padding
        return base64.urlsafe_b64encode(token_bytes).decode('utf-8').rstrip('=')
    
    @staticmethod
    def generate_token_with_expiry(
        user_id: str,
        purpose: str,
        expiry_minutes: int = TOKEN_EXPIRY_MINUTES
    ) -> Dict[str, Any]:
        """
        Generate a token with expiry information
        
        Args:
            user_id: User identifier
            purpose: Purpose of the token (e.g., "password_reset")
            expiry_minutes: Minutes until the token expires
            
        Returns:
            Dictionary with token details
        """
        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=expiry_minutes)
        token = TokenUtils.generate_token()
        
        return {
            "token": token,
            "user_id": user_id,
            "purpose": purpose,
            "expiry": expiry_time.isoformat(),
            "created_at": datetime.datetime.now().isoformat()
        }
    
    @staticmethod
    def validate_token_expiry(token_data: Dict[str, Any]) -> bool:
        """
        Check if a token has expired
        
        Args:
            token_data: Token data including expiry time
            
        Returns:
            True if token is still valid, False if expired
        """
        if "expiry" not in token_data:
            return False
            
        try:
            expiry_time = datetime.datetime.fromisoformat(token_data["expiry"])
            return datetime.datetime.now() < expiry_time
        except (ValueError, TypeError):
            return False


# OTP generation and validation
class OTPUtils:
    """One-Time Password utilities"""
    
    @staticmethod
    def generate_numeric_otp(length: int = OTP_LENGTH) -> str:
        """
        Generate a numeric OTP
        
        Args:
            length: Length of the OTP
            
        Returns:
            Numeric OTP as string
        """
        # Generate random digits
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    @staticmethod
    def generate_alphanumeric_otp(length: int = OTP_LENGTH) -> str:
        """
        Generate an alphanumeric OTP
        
        Args:
            length: Length of the OTP
            
        Returns:
            Alphanumeric OTP as string
        """
        # Use alphanumeric characters, excluding ambiguous ones
        alphabet = '23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz'
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    @staticmethod
    def generate_otp_with_expiry(
        user_id: str,
        minutes: int = 10
    ) -> Dict[str, Any]:
        """
        Generate OTP with expiry information
        
        Args:
            user_id: User identifier
            minutes: Minutes until OTP expires
            
        Returns:
            Dictionary with OTP details
        """
        expiry_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        otp = OTPUtils.generate_numeric_otp()
        
        return {
            "otp": otp,
            "user_id": user_id,
            "expiry": expiry_time.isoformat(),
            "created_at": datetime.datetime.now().isoformat(),
            "attempts_left": 3
        }


# Encryption utilities
class EncryptionUtils:
    """Data encryption utilities"""
    
    @staticmethod
    def get_or_create_encryption_key() -> bytes:
        """
        Get the encryption key or create a new one
        
        Returns:
            Encryption key as bytes
        """
        key_path = FERNET_KEY_PATH
        
        # Check if key exists
        if os.path.exists(key_path):
            with open(key_path, 'rb') as key_file:
                key = key_file.read()
        else:
            # Generate a new key
            key = Fernet.generate_key()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(key_path), exist_ok=True)
            
            # Save key to file
            with open(key_path, 'wb') as key_file:
                key_file.write(key)
                
        return key
    
    @staticmethod
    def encrypt_data(data: str) -> str:
        """
        Encrypt data using Fernet symmetric encryption
        
        Args:
            data: String data to encrypt
            
        Returns:
            Encrypted data as base64 string
        """
        try:
            key = EncryptionUtils.get_or_create_encryption_key()
            cipher = Fernet(key)
            encrypted_data = cipher.encrypt(data.encode('utf-8'))
            return encrypted_data.decode('utf-8')
        except Exception as e:
            raise EncryptionException(f"Encryption failed: {str(e)}")
    
    @staticmethod
    def decrypt_data(encrypted_data: str) -> str:
        """
        Decrypt data using Fernet symmetric encryption
        
        Args:
            encrypted_data: Encrypted data as base64 string
            
        Returns:
            Decrypted data as string
        """
        try:
            key = EncryptionUtils.get_or_create_encryption_key()
            cipher = Fernet(key)
            decrypted_data = cipher.decrypt(encrypted_data.encode('utf-8'))
            return decrypted_data.decode('utf-8')
        except Exception as e:
            raise EncryptionException(f"Decryption failed: {str(e)}")
    
    @staticmethod
    def hash_data(data: str) -> str:
        """
        Create a one-way hash of data
        
        Args:
            data: Data to hash
            
        Returns:
            Hash as hexadecimal string
        """
        return hashlib.sha256(data.encode('utf-8')).hexdigest()


# Audit logging for security events
def security_audit_log(
    action: str,
    user_id: str,
    status: str = "SUCCESS",
    details: Dict = None,
    ip_address: str = None,
    resource: str = None
) -> None:
    """
    Log a security audit event
    
    Args:
        action: Security action performed
        user_id: ID of user performing the action
        status: Status of the action ("SUCCESS" or "FAILURE")
        details: Additional details about the action
        ip_address: IP address of the user
        resource: Resource being accessed
    """
    timestamp = datetime.datetime.now().isoformat()
    
    log_data = {
        "timestamp": timestamp,
        "action": action,
        "user_id": user_id,
        "status": status
    }
    
    if ip_address:
        log_data["ip_address"] = ip_address
        
    if resource:
        log_data["resource"] = resource
        
    if details:
        log_data["details"] = details
        
    logger.info(f"SECURITY_AUDIT: {json.dumps(log_data)}")


# Token blacklisting
class TokenBlacklist:
    """Manager for blacklisted tokens"""
    
    _blacklisted_tokens = set()
    
    @classmethod
    def add_to_blacklist(cls, token: str, reason: str = "logout") -> None:
        """
        Add a token to the blacklist
        
        Args:
            token: Token to blacklist
            reason: Reason for blacklisting
        """
        cls._blacklisted_tokens.add(token)
        logger.info(f"Token blacklisted: reason={reason}")
    
    @classmethod
    def is_blacklisted(cls, token: str) -> bool:
        """
        Check if a token is blacklisted
        
        Args:
            token: Token to check
            
        Returns:
            True if token is blacklisted, False otherwise
        """
        return token in cls._blacklisted_tokens
    
    @classmethod
    def clear_blacklist(cls) -> None:
        """Clear the token blacklist (for testing only)"""
        cls._blacklisted_tokens.clear()


# Rate limiting for security operations
class RateLimiter:
    """Simple rate limiter for security operations"""
    
    # Track attempts by ip_address/operation
    _attempt_counters = {}
    
    @classmethod
    def check_rate_limit(
        cls,
        key: str,
        operation: str,
        max_attempts: int = 5,
        window_minutes: int = 15
    ) -> bool:
        """
        Check if operation is within rate limits
        
        Args:
            key: Identifier for the actor (IP, user_id)
            operation: Operation being performed
            max_attempts: Maximum allowed attempts
            window_minutes: Time window in minutes
            
        Returns:
            True if within limits, False if limit exceeded
        """
        current_time = datetime.datetime.now()
        counter_key = f"{key}:{operation}"
        
        # Initialize counter if needed
        if counter_key not in cls._attempt_counters:
            cls._attempt_counters[counter_key] = {
                "count": 0,
                "reset_time": current_time + datetime.timedelta(minutes=window_minutes)
            }
        
        counter = cls._attempt_counters[counter_key]
        
        # Reset counter if window expired
        if current_time > counter["reset_time"]:
            counter["count"] = 0
            counter["reset_time"] = current_time + datetime.timedelta(minutes=window_minutes)
        
        # Check if limit exceeded
        if counter["count"] >= max_attempts:
            return False
        
        # Increment counter
        counter["count"] += 1
        return True
        
    @classmethod
    def reset_counter(cls, key: str, operation: str) -> None:
        """
        Reset rate limit counter for a key/operation
        
        Args:
            key: Identifier for the actor
            operation: Operation being performed
        """
        counter_key = f"{key}:{operation}"
        if counter_key in cls._attempt_counters:
            cls._attempt_counters[counter_key]["count"] = 0
