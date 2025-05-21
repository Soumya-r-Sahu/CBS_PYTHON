"""
Centralized Security Operations

This module provides standardized security operations for all modules.
It serves as a centralization point for common security functions.

Author: cbs-core-dev
Version: 1.1.2
"""

import os
import logging
import hashlib
import secrets
import datetime
from typing import Optional, Dict, Any, List

# Try to import optional security libraries
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False

# Import service registry for module registration
from utils.lib.service_registry import ServiceRegistry

# Configure logger
logger = logging.getLogger(__name__)

class SecurityOperations:
    """
    Centralized security operations for all modules.
    
    Description:
        This class provides standardized security operations that can be used
        across all modules. It includes functions for encryption/decryption,
        password hashing, token generation, and other security-related tasks.
    
    Usage:
        # Get an instance with default configuration
        security_ops = SecurityOperations.get_instance()
        
        # Hash a password
        hashed_password = security_ops.hash_password("MySecurePassword123")
        
        # Verify a password
        is_valid = security_ops.verify_password("MySecurePassword123", hashed_password)
        
        # Encrypt sensitive data
        encrypted = security_ops.encrypt_data("Sensitive customer information")
        
        # Decrypt data
        decrypted = security_ops.decrypt_data(encrypted)
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """
        Get the singleton instance of SecurityOperations
        
        Returns:
            SecurityOperations: The singleton instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize security operations"""
        self._load_configuration()
        self._initialize_encryption_key()
    
    def _load_configuration(self):
        """Load security configuration from settings"""
        try:
            # For future enhancement: Load from unified config system
            from security.config import get_security_config
            self.config = get_security_config()
        except ImportError:
            logger.warning("Could not load security configuration, using defaults")
            self.config = {
                "password_hash_rounds": 12,
                "token_expiry_hours": 24,
                "encryption_key": os.environ.get("ENCRYPTION_KEY", None)
            }
    
    def _initialize_encryption_key(self):
        """Initialize encryption key for data encryption"""
        if not CRYPTOGRAPHY_AVAILABLE:
            logger.warning("Cryptography library not available, encryption features disabled")
            self.encryption_key = None
            return
            
        key = self.config.get("encryption_key")
        
        if key is None:
            logger.warning("No encryption key found, generating temporary key")
            key = Fernet.generate_key().decode()
            
        if isinstance(key, str):
            key = key.encode()
            
        try:
            self.fernet = Fernet(key)
            self.encryption_key = key
            logger.info("Encryption initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing encryption: {str(e)}")
            self.encryption_key = None
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password using a secure algorithm
        
        Args:
            password (str): The plain text password to hash
            
        Returns:
            str: The hashed password
            
        Raises:
            ValueError: If the password is empty or invalid
        """
        if not password:
            raise ValueError("Password cannot be empty")
            
        if BCRYPT_AVAILABLE:
            # Use bcrypt with configurable rounds
            rounds = self.config.get("password_hash_rounds", 12)
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds))
            return hashed.decode()
        else:
            # Fallback to pbkdf2_hmac with high iteration count
            salt = os.urandom(16)
            hashed = hashlib.pbkdf2_hmac(
                "sha256", 
                password.encode(), 
                salt, 
                100000
            )
            return f"pbkdf2:sha256:100000${salt.hex()}${hashed.hex()}"
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash
        
        Args:
            password (str): The plain text password to verify
            hashed_password (str): The hashed password to check against
            
        Returns:
            bool: True if the password matches, False otherwise
        """
        if not password or not hashed_password:
            return False
            
        if BCRYPT_AVAILABLE and hashed_password.startswith("$2"):
            # Verify using bcrypt
            try:
                return bcrypt.checkpw(password.encode(), hashed_password.encode())
            except Exception as e:
                logger.error(f"Error verifying password with bcrypt: {str(e)}")
                return False
        elif hashed_password.startswith("pbkdf2:"):
            # Verify using pbkdf2
            try:
                _, algorithm, iterations, salt_hash = hashed_password.split("$", 3)
                algorithm_name = algorithm.split(":")[1]
                iterations = int(iterations)
                salt, stored_hash = salt_hash.split("$")
                salt = bytes.fromhex(salt)
                stored_hash = bytes.fromhex(stored_hash)
                
                computed_hash = hashlib.pbkdf2_hmac(
                    algorithm_name,
                    password.encode(),
                    salt,
                    iterations
                )
                
                return secrets.compare_digest(computed_hash, stored_hash)
            except Exception as e:
                logger.error(f"Error verifying password with PBKDF2: {str(e)}")
                return False
        else:
            logger.error(f"Unsupported password hash format: {hashed_password[:10]}...")
            return False
    
    def generate_token(self, user_id: str, expiry_hours: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate a secure authentication token
        
        Args:
            user_id (str): The user ID to encode in the token
            expiry_hours (int, optional): Token expiry in hours
            
        Returns:
            dict: Token information including the token string and expiry
        """
        if expiry_hours is None:
            expiry_hours = self.config.get("token_expiry_hours", 24)
            
        # Generate a secure random token
        token = secrets.token_urlsafe(32)
        
        # Calculate expiration
        expiry = datetime.datetime.now() + datetime.timedelta(hours=expiry_hours)
        
        return {
            "token": token,
            "user_id": user_id,
            "expiry": expiry.isoformat(),
            "created": datetime.datetime.now().isoformat()
        }
    
    def encrypt_data(self, data: str) -> Optional[str]:
        """
        Encrypt sensitive data
        
        Args:
            data (str): The data to encrypt
            
        Returns:
            str: Encrypted data as a string, or None if encryption failed
        """
        if not CRYPTOGRAPHY_AVAILABLE or not self.encryption_key:
            logger.warning("Encryption not available, returning data unencrypted")
            return f"UNENCRYPTED:{data}"
            
        try:
            if isinstance(data, str):
                data = data.encode()
                
            encrypted = self.fernet.encrypt(data)
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {str(e)}")
            return None
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """
        Decrypt encrypted data
        
        Args:
            encrypted_data (str): The encrypted data to decrypt
            
        Returns:
            str: Decrypted data as a string, or None if decryption failed
        """
        if not encrypted_data:
            return None
            
        if encrypted_data.startswith("UNENCRYPTED:"):
            return encrypted_data[12:]
            
        if not CRYPTOGRAPHY_AVAILABLE or not self.encryption_key:
            logger.warning("Decryption not available")
            return None
            
        try:
            if isinstance(encrypted_data, str):
                encrypted_data = encrypted_data.encode()
                
            decrypted = self.fernet.decrypt(encrypted_data)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {str(e)}")
            return None
    
    # Alias methods for backward compatibility
    encrypt = encrypt_data
    decrypt = decrypt_data
    
    def sanitize_input(self, input_str: str) -> str:
        """
        Sanitize user input to prevent XSS attacks
        
        Args:
            input_str (str): The input string to sanitize
            
        Returns:
            str: Sanitized input string
        """
        if not input_str:
            return ""
            
        # Basic HTML tag removal
        replacements = {
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
            "/": "&#x2F;",
            "\\": "&#x5C;",
        }
        
        for char, replacement in replacements.items():
            input_str = input_str.replace(char, replacement)
            
        return input_str
    
    def sanitize_sql_input(self, input_str: str) -> str:
        """
        Sanitize SQL input to prevent SQL injection
        
        Args:
            input_str (str): The input string to sanitize
            
        Returns:
            str: Sanitized input string
            
        Note:
            This is a basic sanitization and should not replace using
            parameterized queries, which is the recommended approach.
        """
        if not input_str:
            return ""
            
        # Basic SQL injection prevention
        replacements = {
            "'": "''",
            "\\": "\\\\",
            ";": "",
            "--": "",
            "/*": "",
            "*/": ""
        }
        
        for char, replacement in replacements.items():
            input_str = input_str.replace(char, replacement)
            
        return input_str
        
# Register security operations with service registry
def register_security_services():
    """Register security services with the service registry"""
    registry = ServiceRegistry.get_instance()
    
    # Register security operations
    security_ops = SecurityOperations.get_instance()
    registry.register("security.operations", security_ops, "security")
    
    # Register individual security services for granular access
    registry.register("security.password_hash", security_ops.hash_password, "security")
    registry.register("security.password_verify", security_ops.verify_password, "security")
    registry.register("security.generate_token", security_ops.generate_token, "security")
    registry.register("security.encrypt", security_ops.encrypt_data, "security")
    registry.register("security.decrypt", security_ops.decrypt_data, "security")
    registry.register("security.sanitize_input", security_ops.sanitize_input, "security")
    registry.register("security.sanitize_sql", security_ops.sanitize_sql_input, "security")
    
    # Register fallbacks
    def fallback_hash_password(password):
        logger.warning("Using fallback password hashing (insecure)")
        return f"FALLBACK:{hashlib.sha256(password.encode()).hexdigest()}"
        
    def fallback_verify_password(password, hashed):
        if hashed.startswith("FALLBACK:"):
            hashed_input = f"FALLBACK:{hashlib.sha256(password.encode()).hexdigest()}"
            return hashed == hashed_input
        return False
        
    registry.register_fallback("security.password_hash", fallback_hash_password)
    registry.register_fallback("security.password_verify", fallback_verify_password)
    
    logger.info("Security services registered")

# Initialize registration on module import
register_security_services()
