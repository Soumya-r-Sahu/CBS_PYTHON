"""
Access Control Module for Core Banking System

This module handles access control, including role-based access control (RBAC),
permission management, and access tokens.
"""

import os
import time
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Configure logger
logger = logging.getLogger(__name__)

# Roles and their permissions
ROLE_PERMISSIONS = {
    "admin": ["read", "write", "update", "delete", "manage_users", "view_logs", "manage_system"],
    "manager": ["read", "write", "update", "view_logs", "approve_transactions"],
    "teller": ["read", "write", "process_transactions"],
    "customer": ["view_own_account", "make_transactions", "update_profile"],
    "guest": ["view_public_info"]
}

# Active tokens (in production, store these in a database)
ACTIVE_TOKENS = {}


def check_access(user_id: str, role: str, required_permission: str) -> bool:
    """
    Check if a user has the required permission.
    
    Args:
        user_id (str): User identifier
        role (str): User's role
        required_permission (str): Permission to check
        
    Returns:
        bool: True if the user has the permission, False otherwise
    """
    # Get permissions for the role
    if role not in ROLE_PERMISSIONS:
        logger.warning(f"Unknown role: {role} for user: {user_id}")
        return False
    
    permissions = ROLE_PERMISSIONS[role]
    
    # Check if the role has the required permission
    has_permission = required_permission in permissions
    if not has_permission:
        logger.info(f"Access denied: User {user_id} with role {role} attempted to use {required_permission}")
    
    return has_permission


def create_token(user_id: str, role: str, expiration_minutes: int = 60) -> str:
    """
    Create an access token for a user.
    
    Args:
        user_id (str): User identifier
        role (str): User's role
        expiration_minutes (int): Token expiration time in minutes
        
    Returns:
        str: Access token
    """
    # Generate a unique token
    token = str(uuid.uuid4())
    
    # Calculate expiration time
    expiration = datetime.now() + timedelta(minutes=expiration_minutes)
    
    # Store token data
    ACTIVE_TOKENS[token] = {
        "user_id": user_id,
        "role": role,
        "expiration": expiration,
        "created_at": datetime.now()
    }
    
    logger.info(f"Token created for user {user_id} with role {role}")
    
    return token


def validate_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate an access token.
    
    Args:
        token (str): Token to validate
        
    Returns:
        Optional[Dict[str, Any]]: Token data if valid, None if invalid
    """
    # Check if token exists
    if token not in ACTIVE_TOKENS:
        logger.warning(f"Invalid token attempt: {token}")
        return None
    
    token_data = ACTIVE_TOKENS[token]
    
    # Check if token has expired
    if datetime.now() > token_data["expiration"]:
        logger.info(f"Expired token used for user {token_data['user_id']}")
        # Remove expired token
        del ACTIVE_TOKENS[token]
        return None
    
    return token_data


def revoke_token(token: str) -> bool:
    """
    Revoke an access token.
    
    Args:
        token (str): Token to revoke
        
    Returns:
        bool: True if token was revoked, False if token not found
    """
    if token in ACTIVE_TOKENS:
        user_id = ACTIVE_TOKENS[token]["user_id"]
        del ACTIVE_TOKENS[token]
        logger.info(f"Token revoked for user {user_id}")
        return True
    
    logger.warning(f"Attempted to revoke non-existent token: {token}")
    return False


def clean_expired_tokens() -> int:
    """
    Clean up expired tokens.
    
    Returns:
        int: Number of tokens removed
    """
    current_time = datetime.now()
    tokens_to_remove = [
        token for token, data in ACTIVE_TOKENS.items() 
        if current_time > data["expiration"]
    ]
    
    for token in tokens_to_remove:
        del ACTIVE_TOKENS[token]
    
    if tokens_to_remove:
        logger.info(f"Cleaned {len(tokens_to_remove)} expired tokens")
    
    return len(tokens_to_remove)


def get_user_permissions(role: str) -> List[str]:
    """
    Get a list of permissions for a specific role.
    
    Args:
        role (str): Role to get permissions for
        
    Returns:
        List[str]: List of permissions
    """
    return ROLE_PERMISSIONS.get(role, [])
