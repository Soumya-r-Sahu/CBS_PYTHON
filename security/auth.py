"""
Authentication Module for Core Banking System

This module handles user authentication including login, token verification,
multi-factor authentication, and session management.
"""

import os
import time
import hashlib
import logging
import jwt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

# Configure logger
logger = logging.getLogger(__name__)

# JWT secret key - in production this should be stored securely
JWT_SECRET = os.environ.get("JWT_SECRET", "development_secret_key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 3600  # 1 hour in seconds


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash a password using SHA-256 with salt.
    
    Args:
        password (str): The password to hash
        salt (str, optional): Salt to use, if None a new salt is generated
        
    Returns:
        Tuple[str, str]: (hashed_password, salt)
    """
    if salt is None:
        salt = os.urandom(32).hex()
    
    # Combine password and salt
    salted_password = password + salt

    # Hash the salted password
    hashed_password = hashlib.sha256(salted_password.encode()).hexdigest()
    return hashed_password, salt


def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """
    Verify a password against a hash and salt.

    Args:
        password (str): The password to verify
        hashed_password (str): The hashed password to compare against
        salt (str): The salt used during hashing

    Returns:
        bool: True if the password matches, False otherwise
    """
    return hash_password(password, salt)[0] == hashed_password


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user with username and password.
    
    Args:
        username (str): The username
        password (str): The password
        
    Returns:
        Optional[Dict[str, Any]]: User data if authenticated, None otherwise
    """
    # In a real application, this would query the database
    # For demonstration, we'll use a mock user
    from database.db_manager import get_db_session
    from database.models import User
    
    try:
        session = get_db_session()
        user = session.query(User).filter(User.username == username).first()
        
        if not user:
            logger.warning(f"Authentication failed: User {username} not found")
            return None
        
        if not verify_password(password, user.password_hash, user.password_salt):
            logger.warning(f"Authentication failed: Invalid password for user {username}")
            return None
        
        logger.info(f"User {username} authenticated successfully")
        
        # Return user data (without sensitive information)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active
        }
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return None
    finally:
        session.close()


def create_auth_token(user_data: Dict[str, Any]) -> str:
    """
    Create a JWT authentication token for a user.
    
    Args:
        user_data (Dict[str, Any]): User data to encode in the token
        
    Returns:
        str: JWT token
    """
    # Set token expiration
    expiration = datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
    
    # Create token payload
    payload = {
        "sub": str(user_data["id"]),
        "username": user_data["username"],
        "role": user_data["role"],
        "exp": expiration.timestamp()
    }
    
    # Encode token
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return token


def generate_jwt(payload: Dict[str, Any], expiration: int = JWT_EXPIRATION) -> str:
    """
    Generate a JWT token.

    Args:
        payload (Dict[str, Any]): The payload to include in the token
        expiration (int): Expiration time in seconds

    Returns:
        str: The generated JWT token
    """
    payload["exp"] = datetime.utcnow() + timedelta(seconds=expiration)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a JWT token.

    Args:
        token (str): The JWT token to verify

    Returns:
        Optional[Dict[str, Any]]: The decoded payload if valid, None otherwise
    """
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired.")
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token.")
    return None


def verify_auth_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT authentication token.
    
    Args:
        token (str): The JWT token to verify
        
    Returns:
        Optional[Dict[str, Any]]: Decoded token data if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Check if token has expired
        if "exp" in payload and time.time() > payload["exp"]:
            logger.warning(f"Token expired for user {payload.get('username')}")
            return None
        
        return payload
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None


def verify_permissions(token_data: Dict[str, Any], required_role: str) -> bool:
    """
    Verify if the user has the required role/permission.
    
    Args:
        token_data (Dict[str, Any]): Decoded token data
        required_role (str): The role required for access
        
    Returns:
        bool: True if user has the required role, False otherwise
    """
    user_role = token_data.get("role", "")
    
    # Admin has access to everything
    if user_role == "admin":
        return True
    
    # Check if user has the required role
    return user_role == required_role


def initiate_password_reset(email: str) -> bool:
    """
    Initiate password reset process for a user.
    
    Args:
        email (str): The user's email
        
    Returns:
        bool: True if reset initiated successfully, False otherwise
    """
    # In a real application, this would:
    # 1. Check if the email exists in the database
    # 2. Generate a unique reset token
    # 3. Store the token with an expiry time
    # 4. Send an email with the reset link
    
    logger.info(f"Password reset initiated for email: {email}")
    return True


if __name__ == "__main__":
    # Example usage
    hashed, salt = hash_password("secure_password")
    print(f"Hashed password: {hashed}")
    print(f"Salt: {salt}")
    
    # Verify password
    is_valid = verify_password("secure_password", hashed, salt)
    print(f"Password valid: {is_valid}")
