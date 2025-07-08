"""
End-to-End Encryption Service for CBS Platform V2.0
Provides comprehensive encryption for API communications, data at rest, and sensitive operations.
"""

import asyncio
import base64
import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
import hashlib
import hmac

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import aioredis
import aioboto3

# Configure logging
logger = logging.getLogger(__name__)

class EncryptionKeyManager:
    """Manages encryption keys with rotation and secure storage."""
    
    def __init__(self, 
                 master_key: str,
                 key_rotation_hours: int = 24,
                 backup_count: int = 5):
        self.master_key = master_key.encode() if isinstance(master_key, str) else master_key
        self.key_rotation_hours = key_rotation_hours
        self.backup_count = backup_count
        self.current_key_id = None
        self.encryption_keys = {}
        self.signing_keys = {}
        self.last_rotation = None
        
    async def initialize(self):
        """Initialize the key manager with initial keys."""
        try:
            # Generate initial encryption key
            await self._generate_new_encryption_key()
            
            # Generate initial signing key
            await self._generate_new_signing_key()
            
            logger.info("🔐 Encryption key manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize key manager: {str(e)}")
            raise
    
    async def _generate_new_encryption_key(self) -> str:
        """Generate a new encryption key and set it as current."""
        key_id = f"enc_{int(time.time())}_{secrets.token_hex(8)}"
        
        # Derive key from master key with unique salt
        salt = secrets.token_bytes(32)
        kdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=f"CBS_ENCRYPTION_{key_id}".encode(),
            backend=default_backend()
        )
        derived_key = kdf.derive(self.master_key)
        
        # Create Fernet key
        fernet_key = base64.urlsafe_b64encode(derived_key)
        
        self.encryption_keys[key_id] = {
            "key": fernet_key,
            "salt": salt,
            "created_at": datetime.utcnow(),
            "type": "symmetric"
        }
        
        self.current_key_id = key_id
        self.last_rotation = datetime.utcnow()
        
        # Clean up old keys (keep only recent ones)
        await self._cleanup_old_keys()
        
        logger.info(f"🔑 Generated new encryption key: {key_id}")
        return key_id
    
    async def _generate_new_signing_key(self) -> str:
        """Generate a new RSA key pair for signing and verification."""
        key_id = f"sign_{int(time.time())}_{secrets.token_hex(8)}"
        
        # Generate RSA key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        # Serialize keys
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        self.signing_keys[key_id] = {
            "private_key": private_pem,
            "public_key": public_pem,
            "created_at": datetime.utcnow(),
            "type": "asymmetric"
        }
        
        logger.info(f"🔏 Generated new signing key: {key_id}")
        return key_id
    
    async def _cleanup_old_keys(self):
        """Remove old encryption keys, keeping only recent ones."""
        sorted_keys = sorted(
            self.encryption_keys.items(),
            key=lambda x: x[1]["created_at"],
            reverse=True
        )
        
        # Keep only the most recent keys
        keys_to_keep = dict(sorted_keys[:self.backup_count])
        removed_count = len(self.encryption_keys) - len(keys_to_keep)
        
        self.encryption_keys = keys_to_keep
        
        if removed_count > 0:
            logger.info(f"🧹 Cleaned up {removed_count} old encryption keys")
    
    async def get_current_key(self) -> Tuple[str, bytes]:
        """Get the current encryption key."""
        if not self.current_key_id or self.current_key_id not in self.encryption_keys:
            await self._generate_new_encryption_key()
        
        key_data = self.encryption_keys[self.current_key_id]
        return self.current_key_id, key_data["key"]
    
    async def get_key_by_id(self, key_id: str) -> Optional[bytes]:
        """Get a specific encryption key by ID."""
        if key_id in self.encryption_keys:
            return self.encryption_keys[key_id]["key"]
        return None
    
    async def should_rotate_keys(self) -> bool:
        """Check if keys should be rotated based on time."""
        if not self.last_rotation:
            return True
        
        rotation_interval = timedelta(hours=self.key_rotation_hours)
        return datetime.utcnow() - self.last_rotation >= rotation_interval
    
    async def rotate_keys(self):
        """Rotate encryption keys."""
        logger.info("🔄 Starting key rotation...")
        await self._generate_new_encryption_key()
        await self._generate_new_signing_key()
        logger.info("✅ Key rotation completed")


class DataEncryptor:
    """Handles data encryption and decryption operations."""
    
    def __init__(self, key_manager: EncryptionKeyManager):
        self.key_manager = key_manager
    
    async def encrypt_data(self, data: Union[str, bytes, Dict[str, Any]], 
                          key_id: Optional[str] = None) -> Dict[str, Any]:
        """Encrypt data with optional key specification."""
        try:
            # Convert data to JSON string if it's a dict
            if isinstance(data, dict):
                data_str = json.dumps(data, separators=(',', ':'))
            elif isinstance(data, bytes):
                data_str = data.decode('utf-8')
            else:
                data_str = str(data)
            
            # Get encryption key
            if key_id:
                encryption_key = await self.key_manager.get_key_by_id(key_id)
                if not encryption_key:
                    raise ValueError(f"Key {key_id} not found")
                current_key_id = key_id
            else:
                current_key_id, encryption_key = await self.key_manager.get_current_key()
            
            # Encrypt data
            fernet = Fernet(encryption_key)
            encrypted_data = fernet.encrypt(data_str.encode('utf-8'))
            
            # Create encrypted package
            encrypted_package = {
                "encrypted_data": base64.b64encode(encrypted_data).decode('utf-8'),
                "key_id": current_key_id,
                "algorithm": "Fernet",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "2.0"
            }
            
            return encrypted_package
            
        except Exception as e:
            logger.error(f"Data encryption failed: {str(e)}")
            raise
    
    async def decrypt_data(self, encrypted_package: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """Decrypt data from encrypted package."""
        try:
            # Get the encryption key
            key_id = encrypted_package["key_id"]
            encryption_key = await self.key_manager.get_key_by_id(key_id)
            
            if not encryption_key:
                raise ValueError(f"Encryption key {key_id} not found")
            
            # Decrypt data
            fernet = Fernet(encryption_key)
            encrypted_data = base64.b64decode(encrypted_package["encrypted_data"])
            decrypted_bytes = fernet.decrypt(encrypted_data)
            decrypted_str = decrypted_bytes.decode('utf-8')
            
            # Try to parse as JSON, return string if it fails
            try:
                return json.loads(decrypted_str)
            except json.JSONDecodeError:
                return decrypted_str
                
        except Exception as e:
            logger.error(f"Data decryption failed: {str(e)}")
            raise
    
    async def encrypt_sensitive_fields(self, data: Dict[str, Any], 
                                     sensitive_fields: List[str]) -> Dict[str, Any]:
        """Encrypt specific fields in a dictionary."""
        result = data.copy()
        encrypted_fields = []
        
        current_key_id, _ = await self.key_manager.get_current_key()
        
        for field in sensitive_fields:
            if field in result and result[field] is not None:
                # Encrypt the field
                encrypted_field = await self.encrypt_data(result[field])
                result[field] = encrypted_field
                encrypted_fields.append(field)
        
        # Add metadata about encryption
        if encrypted_fields:
            result["_encryption_metadata"] = {
                "encrypted_fields": encrypted_fields,
                "encryption_version": "2.0",
                "key_id": current_key_id
            }
        
        return result
    
    async def decrypt_sensitive_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt previously encrypted fields in a dictionary."""
        if "_encryption_metadata" not in data:
            return data
        
        result = data.copy()
        metadata = result.pop("_encryption_metadata")
        encrypted_fields = metadata.get("encrypted_fields", [])
        
        for field in encrypted_fields:
            if field in result and isinstance(result[field], dict):
                # Decrypt the field
                result[field] = await self.decrypt_data(result[field])
        
        return result


class RequestSigner:
    """Handles request signing and verification for integrity."""
    
    def __init__(self, key_manager: EncryptionKeyManager):
        self.key_manager = key_manager
    
    async def sign_request(self, request_data: Dict[str, Any]) -> str:
        """Sign a request with current signing key."""
        try:
            # Serialize request data
            request_str = json.dumps(request_data, sort_keys=True, separators=(',', ':'))
            
            # Get current signing key (we'll use HMAC for simplicity)
            current_key_id, encryption_key = await self.key_manager.get_current_key()
            
            # Create HMAC signature
            signature = hmac.new(
                encryption_key,
                request_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return f"{current_key_id}:{signature}"
            
        except Exception as e:
            logger.error(f"Request signing failed: {str(e)}")
            raise
    
    async def verify_signature(self, request_data: Dict[str, Any], signature: str) -> bool:
        """Verify a request signature."""
        try:
            # Parse signature
            if ':' not in signature:
                return False
            
            key_id, sig_value = signature.split(':', 1)
            
            # Get the key
            encryption_key = await self.key_manager.get_key_by_id(key_id)
            if not encryption_key:
                return False
            
            # Serialize request data
            request_str = json.dumps(request_data, sort_keys=True, separators=(',', ':'))
            
            # Verify HMAC signature
            expected_signature = hmac.new(
                encryption_key,
                request_str.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(sig_value, expected_signature)
            
        except Exception as e:
            logger.error(f"Signature verification failed: {str(e)}")
            return False


class EndToEndEncryptionService:
    """
    Comprehensive encryption service for CBS Platform V2.0.
    Provides end-to-end encryption, key management, and secure communication.
    """
    
    def __init__(self, 
                 encryption_key: str,
                 key_rotation_hours: int = 24,
                 redis_url: Optional[str] = None):
        
        self.key_manager = EncryptionKeyManager(
            master_key=encryption_key,
            key_rotation_hours=key_rotation_hours
        )
        
        self.data_encryptor = DataEncryptor(self.key_manager)
        self.request_signer = RequestSigner(self.key_manager)
        
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_client = None
        
        # Background task for key rotation
        self.key_rotation_task = None
        self.running = False
    
    async def initialize(self):
        """Initialize the encryption service."""
        try:
            # Initialize key manager
            await self.key_manager.initialize()
            
            # Initialize Redis for caching (optional)
            try:
                self.redis_client = await aioredis.from_url(self.redis_url)
                await self.redis_client.ping()
                logger.info("📦 Redis cache connected for encryption service")
            except Exception as e:
                logger.warning(f"Redis not available for encryption cache: {str(e)}")
                self.redis_client = None
            
            # Start background key rotation
            self.running = True
            self.key_rotation_task = asyncio.create_task(self._key_rotation_worker())
            
            logger.info("🔐 End-to-end encryption service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {str(e)}")
            raise
    
    async def cleanup(self):
        """Clean up encryption service resources."""
        self.running = False
        
        if self.key_rotation_task:
            self.key_rotation_task.cancel()
            try:
                await self.key_rotation_task
            except asyncio.CancelledError:
                pass
        
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("🧹 Encryption service cleanup complete")
    
    async def _key_rotation_worker(self):
        """Background worker for automatic key rotation."""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Check every hour
                
                if await self.key_manager.should_rotate_keys():
                    await self.key_manager.rotate_keys()
                    logger.info("🔄 Automatic key rotation completed")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Key rotation worker error: {str(e)}")
    
    # Public API methods
    
    async def encrypt_request_body(self, body_data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt a request body for secure transmission."""
        try:
            # Add request metadata
            request_data = {
                "data": body_data,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": secrets.token_hex(16)
            }
            
            # Encrypt the data
            encrypted_package = await self.data_encryptor.encrypt_data(request_data)
            
            # Sign the request
            signature = await self.request_signer.sign_request(encrypted_package)
            encrypted_package["signature"] = signature
            
            return encrypted_package
            
        except Exception as e:
            logger.error(f"Request body encryption failed: {str(e)}")
            raise
    
    async def decrypt_request_body(self, encrypted_body: bytes, key_id: str) -> str:
        """Decrypt a request body."""
        try:
            # Parse encrypted package
            encrypted_package = json.loads(encrypted_body.decode('utf-8'))
            
            # Verify signature if present
            if "signature" in encrypted_package:
                signature = encrypted_package.pop("signature")
                if not await self.request_signer.verify_signature(encrypted_package, signature):
                    raise ValueError("Request signature verification failed")
            
            # Decrypt the data
            decrypted_data = await self.data_encryptor.decrypt_data(encrypted_package)
            
            # Extract the actual data
            if isinstance(decrypted_data, dict) and "data" in decrypted_data:
                return json.dumps(decrypted_data["data"])
            else:
                return json.dumps(decrypted_data)
                
        except Exception as e:
            logger.error(f"Request body decryption failed: {str(e)}")
            raise
    
    async def encrypt_response(self, response_data: Dict[str, Any], 
                             client_key: Optional[str] = None) -> Dict[str, Any]:
        """Encrypt a response for secure transmission."""
        try:
            # Add response metadata
            full_response = {
                "data": response_data,
                "timestamp": datetime.utcnow().isoformat(),
                "encrypted": True
            }
            
            # Encrypt the response
            encrypted_package = await self.data_encryptor.encrypt_data(full_response)
            
            # If client key is provided, add an additional layer
            if client_key:
                # This would implement client-specific encryption
                # For now, we'll add a flag indicating client encryption is available
                encrypted_package["client_encryption_available"] = True
            
            return encrypted_package
            
        except Exception as e:
            logger.error(f"Response encryption failed: {str(e)}")
            raise
    
    async def decrypt_response(self, encrypted_response: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt a response."""
        try:
            # Decrypt the response
            decrypted_data = await self.data_encryptor.decrypt_data(encrypted_response)
            
            # Extract the actual data
            if isinstance(decrypted_data, dict) and "data" in decrypted_data:
                return decrypted_data["data"]
            else:
                return decrypted_data
                
        except Exception as e:
            logger.error(f"Response decryption failed: {str(e)}")
            raise
    
    async def encrypt_sensitive_data(self, data: Dict[str, Any], 
                                   sensitive_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Encrypt sensitive fields in data."""
        if sensitive_fields:
            return await self.data_encryptor.encrypt_sensitive_fields(data, sensitive_fields)
        else:
            # Encrypt the entire data structure
            encrypted_package = await self.data_encryptor.encrypt_data(data)
            return {"encrypted_data": encrypted_package}
    
    async def decrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in data."""
        if "_encryption_metadata" in data:
            return await self.data_encryptor.decrypt_sensitive_fields(data)
        elif "encrypted_data" in data:
            # Decrypt the entire data structure
            return await self.data_encryptor.decrypt_data(data["encrypted_data"])
        else:
            return data
    
    async def get_public_key(self) -> str:
        """Get the current public key for client-side encryption setup."""
        # For now, return the current key ID (in production, this would be an actual public key)
        current_key_id, _ = await self.key_manager.get_current_key()
        return base64.b64encode(f"public_key_for_{current_key_id}".encode()).decode()
    
    async def get_current_key_id(self) -> str:
        """Get the current encryption key ID."""
        current_key_id, _ = await self.key_manager.get_current_key()
        return current_key_id
    
    async def get_key_expiry(self) -> str:
        """Get the expiry time of the current key."""
        if self.key_manager.last_rotation:
            expiry = self.key_manager.last_rotation + timedelta(hours=self.key_manager.key_rotation_hours)
            return expiry.isoformat()
        return datetime.utcnow().isoformat()
    
    async def get_encryption_status(self) -> Dict[str, Any]:
        """Get the current status of the encryption service."""
        current_key_id, _ = await self.key_manager.get_current_key()
        
        return {
            "active": True,
            "current_key_id": current_key_id,
            "key_count": len(self.key_manager.encryption_keys),
            "last_rotation": self.key_manager.last_rotation.isoformat() if self.key_manager.last_rotation else None,
            "next_rotation": await self.get_key_expiry(),
            "redis_connected": self.redis_client is not None
        }


# Factory function for easy initialization
async def create_encryption_service(encryption_key: str, 
                                  key_rotation_hours: int = 24,
                                  redis_url: Optional[str] = None) -> EndToEndEncryptionService:
    """
    Create and initialize an encryption service.
    
    Args:
        encryption_key: Master encryption key
        key_rotation_hours: Hours between key rotations
        redis_url: Redis URL for caching (optional)
        
    Returns:
        Initialized encryption service
    """
    service = EndToEndEncryptionService(
        encryption_key=encryption_key,
        key_rotation_hours=key_rotation_hours,
        redis_url=redis_url
    )
    
    await service.initialize()
    return service
