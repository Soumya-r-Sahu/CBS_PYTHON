"""
Authentication token service for the Internet Banking domain.
"""
import hmac
import hashlib
import base64
import json
import time
from typing import Optional, Dict, Any
from uuid import UUID

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class TokenService:
    """Service for generating and validating authentication tokens."""
    
    def __init__(self, secret_key: str, token_expiry_seconds: int = 3600):
        """
        Initialize the token service.
        
        Args:
            secret_key: Secret key for signing tokens
            token_expiry_seconds: Expiry time for tokens in seconds
        """
        self._secret_key = secret_key
        self._token_expiry_seconds = token_expiry_seconds
    
    def generate_token(self, user_id: UUID, session_id: UUID, additional_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate an authentication token.
        
        Args:
            user_id: ID of the user
            session_id: ID of the session
            additional_data: Optional additional data to include in the token
            
        Returns:
            Authentication token
        """
        # Create payload
        payload = {
            "user_id": str(user_id),
            "session_id": str(session_id),
            "issued_at": int(time.time()),
            "expires_at": int(time.time() + self._token_expiry_seconds)
        }
        
        # Add additional data if provided
        if additional_data:
            payload.update(additional_data)
        
        # Encode payload
        payload_json = json.dumps(payload)
        payload_base64 = base64.b64encode(payload_json.encode('utf-8')).decode('utf-8')
        
        # Generate signature
        signature = hmac.new(
            self._secret_key.encode('utf-8'),
            payload_base64.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Create token
        token = f"{payload_base64}.{signature}"
        
        return token
    
    def validate_token(self, token: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate an authentication token.
        
        Args:
            token: The token to validate
            
        Returns:
            Tuple of (is_valid, payload)
        """
        try:
            # Split token into payload and signature
            payload_base64, signature = token.split('.')
            
            # Verify signature
            expected_signature = hmac.new(
                self._secret_key.encode('utf-8'),
                payload_base64.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if signature != expected_signature:
                return False, None
            
            # Decode payload
            payload_json = base64.b64decode(payload_base64).decode('utf-8')
            payload = json.loads(payload_json)
            
            # Check expiry
            if payload.get('expires_at', 0) < int(time.time()):
                return False, None
            
            return True, payload
        except Exception:
            return False, None
    
    def refresh_token(self, token: str) -> Optional[str]:
        """
        Refresh an authentication token.
        
        Args:
            token: The token to refresh
            
        Returns:
            New refreshed token, or None if the token is invalid
        """
        is_valid, payload = self.validate_token(token)
        
        if not is_valid or payload is None:
            return None
        
        # Generate a new token with the same data but new expiry
        user_id = UUID(payload['user_id'])
        session_id = UUID(payload['session_id'])
        
        # Remove standard fields for additional_data
        additional_data = payload.copy()
        for field in ['user_id', 'session_id', 'issued_at', 'expires_at']:
            additional_data.pop(field, None)
        
        return self.generate_token(user_id, session_id, additional_data)
