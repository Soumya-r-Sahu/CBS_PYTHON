"""
JWT implementation of TokenService for authentication token management.
"""

import time
import jwt
from typing import Dict, Optional, Set

from security.authentication.domain.services.token_service import TokenService
from security.common.security_utils import SecurityException


class JWTTokenService(TokenService):
    """JWT implementation of TokenService."""
    
    def __init__(self, secret_key: str, token_expiry_minutes: int = 60):
        """Initialize the token service.
        
        Args:
            secret_key: Secret key for signing JWT tokens
            token_expiry_minutes: Token validity period in minutes (default: 60)
        """
        self.secret_key = secret_key
        self.token_expiry_minutes = token_expiry_minutes
        self.blacklisted_tokens: Set[str] = set()
    
    def generate_token(self, user_id: str, additional_claims: Optional[Dict] = None) -> str:
        """Generate a new JWT authentication token.
        
        Args:
            user_id: The user ID to include in the token
            additional_claims: Additional claims to include in the token payload
            
        Returns:
            Generated JWT token string
        """
        # Set default payload
        payload = {
            "sub": user_id,
            "iat": int(time.time()),
            "exp": int(time.time() + self.token_expiry_minutes * 60)
        }
        
        # Add additional claims if provided
        if additional_claims:
            payload.update(additional_claims)
            
        # Generate and return token
        return jwt.encode(payload, self.secret_key, algorithm="HS256")
    
    def validate_token(self, token: str) -> Dict:
        """Validate a JWT token and return its payload.
        
        Args:
            token: The JWT token to validate
            
        Returns:
            Token payload as dictionary
            
        Raises:
            SecurityException: If token is invalid, expired or blacklisted
        """
        if self.is_token_blacklisted(token):
            raise SecurityException("Token has been revoked")
            
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise SecurityException("Token has expired")
        except jwt.InvalidTokenError:
            raise SecurityException("Invalid token")
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted (revoked).
        
        Args:
            token: The token to check
            
        Returns:
            True if blacklisted, False otherwise
        """
        return token in self.blacklisted_tokens
    
    def blacklist_token(self, token: str) -> None:
        """Add a token to the blacklist (revoke it).
        
        Args:
            token: The token to blacklist
        """
        self.blacklisted_tokens.add(token)
