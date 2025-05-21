"""
Authentication Module for Security Package

This module provides authentication and authorization functions for the API gateway.
"""

import logging
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union, List

# Configure logger
logger = logging.getLogger(__name__)

# Constants for JWT configuration
SECRET_KEY = "your-secret-key-here"  # In production, this should be loaded from environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user based on credentials
    
    Args:
        username: User's username
        password: User's password
        
    Returns:
        Dict containing user information if valid, None otherwise
    """
    # In a real implementation, this would verify against a database
    # This is a placeholder implementation
    
    try:
        # Simulate database lookup
        from security.password_manager import verify_password
        
        # Example hardcoded users for demo purposes
        mock_users = {
            "admin": {
                "id": "1",
                "username": "admin",
                "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # "password"
                "password_salt": "salt",
                "roles": ["admin"]
            },
            "user": {
                "id": "2",
                "username": "user",
                "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # "password"
                "password_salt": "salt",
                "roles": ["user"]
            }
        }
        
        # Find the user
        user = mock_users.get(username)
        
        if not user:
            logger.warning(f"Authentication failed: User {username} not found")
            return None
        
        # In a real implementation, we would use proper password verification
        # For demo, we use a simple check
        if verify_password(password, user["password_hash"], user["password_salt"]):
            logger.info(f"User {username} authenticated successfully")
            return {
                "id": user["id"],
                "username": user["username"],
                "roles": user["roles"]
            }
        else:
            logger.warning(f"Authentication failed: Invalid password for user {username}")
            return None
            
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return None


def create_access_token(
    user_id: Union[str, int], 
    username: str,
    roles: list = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a new JWT access token
    
    Args:
        user_id: User ID
        username: Username
        roles: List of user roles
        expires_delta: Token expiration time
        
    Returns:
        JWT token string
    """
    roles = roles or []
    expires = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    
    # Create token payload
    payload = {
        "sub": str(user_id),
        "username": username,
        "roles": roles,
        "exp": expires.timestamp(),
        "iat": datetime.utcnow().timestamp()
    }
    
    # Encode the token
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def verify_auth_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token to verify
        
    Returns:
        Dict containing token payload if valid, None otherwise
    """
    try:
        # Decode and validate the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if token is expired
        if "exp" not in payload or datetime.utcnow().timestamp() > payload["exp"]:
            logger.warning(f"Expired token received: {payload.get('sub', 'unknown')}")
            return None
        
        return payload
    except jwt.PyJWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return None


def verify_permissions(user_info: Dict[str, Any], required_permissions: List[str]) -> bool:
    """
    Verify if a user has the required permissions
    
    Args:
        user_info: User information dictionary
        required_permissions: List of required permissions/roles
        
    Returns:
        True if user has permission, False otherwise
    """
    # If no permissions required, always allow
    if not required_permissions:
        return True
        
    # Admin role has all permissions
    if "admin" in user_info.get("roles", []):
        return True
        
    # Check if user has any of the required permissions
    for permission in required_permissions:
        if permission in user_info.get("roles", []):
            return True
            
    logger.warning(f"Permission denied: User {user_info.get('username')} tried to access a protected resource")
    return False
