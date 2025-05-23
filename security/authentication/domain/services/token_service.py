"""
Token service interface that defines contract for JWT token operations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional


class TokenService(ABC):
    """Interface for token generation and validation."""
    
    @abstractmethod
    def generate_token(self, user_id: str, additional_claims: Optional[Dict] = None) -> str:
        """Generate a new authentication token.
        
        Args:
            user_id: The user ID to include in the token
            additional_claims: Additional claims to include in the token payload
            
        Returns:
            Generated token string
        """
        pass
    
    @abstractmethod
    def validate_token(self, token: str) -> Dict:
        """Validate a token and return its payload.
        
        Args:
            token: The token to validate
            
        Returns:
            Token payload as dictionary
            
        Raises:
            SecurityException: If token is invalid or expired
        """
        pass
    
    @abstractmethod
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if a token is blacklisted (revoked).
        
        Args:
            token: The token to check
            
        Returns:
            True if blacklisted, False otherwise
        """
        pass
    
    @abstractmethod
    def blacklist_token(self, token: str) -> None:
        """Add a token to the blacklist (revoke it).
        
        Args:
            token: The token to blacklist
        """
        pass
