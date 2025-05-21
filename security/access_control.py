"""
Access Control Module for Core Banking System

This module provides access control functionalities, including role-based 
access control, permission checking, and token management.
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional, Set, Union
from datetime import datetime, timedelta

# Import JWT utilities
from security.common.auth import create_access_token

# Configure logger
logger = logging.getLogger(__name__)


def check_access(user_id: Union[str, int], resource: str, action: str, 
                 context: Optional[Dict[str, Any]] = None) -> bool:
    """
    Check if a user has access to perform an action on a resource
    
    Args:
        user_id: User ID
        resource: Resource being accessed (e.g., "accounts", "transactions")
        action: Action being performed (e.g., "read", "write", "delete")
        context: Optional contextual information for fine-grained access control
        
    Returns:
        True if access is granted, False otherwise
    """
    try:
        # In a real implementation, this would check against a database
        # or access control service. For now, we'll use a simple mock.
        
        # Example hardcoded permissions
        user_permissions = {
            "1": {  # Admin user
                "resources": ["*"],
                "actions": ["*"]
            },
            "2": {  # Manager
                "resources": ["accounts", "transactions", "customers"],
                "actions": ["read", "write"]
            },
            "3": {  # Teller
                "resources": ["accounts", "transactions"],
                "actions": ["read", "write"]
            },
            "4": {  # Customer service
                "resources": ["customers", "accounts"],
                "actions": ["read"]
            }
        }
        
        # Convert user_id to string for dictionary lookup
        user_id_str = str(user_id)
        
        # Check if user exists in permissions
        if user_id_str not in user_permissions:
            logger.warning(f"User {user_id} not found in permissions")
            return False
        
        user_perms = user_permissions[user_id_str]
        
        # Check resource access
        has_resource_access = False
        if "*" in user_perms["resources"] or resource in user_perms["resources"]:
            has_resource_access = True
        
        # Check action permission
        has_action_permission = False
        if "*" in user_perms["actions"] or action in user_perms["actions"]:
            has_action_permission = True
        
        # Combined check
        has_access = has_resource_access and has_action_permission
        
        # Log access check
        if has_access:
            logger.info(f"Access granted for user {user_id} to {action} on {resource}")
        else:
            logger.warning(f"Access denied for user {user_id} to {action} on {resource}")
        
        return has_access
        
    except Exception as e:
        logger.error(f"Error checking access: {str(e)}")
        # Default to denying access on error
        return False


def create_token(user_id: Union[str, int], username: str, 
                roles: Optional[List[str]] = None,
                expires_in_minutes: int = 30) -> str:
    """
    Create an access token for a user
    
    Args:
        user_id: User ID
        username: Username
        roles: User roles
        expires_in_minutes: Token expiration time in minutes
        
    Returns:
        JWT token string
    """
    try:
        # Call the actual token creation function
        token = create_access_token(
            user_id=user_id,
            username=username,
            roles=roles or [],
            expires_delta=timedelta(minutes=expires_in_minutes)
        )
        
        logger.info(f"Created token for user {username} with expiration {expires_in_minutes} minutes")
        return token
        
    except Exception as e:
        logger.error(f"Error creating token: {str(e)}")
        raise


def get_user_permissions(user_id: Union[str, int]) -> Dict[str, Any]:
    """
    Get all permissions for a user
    
    Args:
        user_id: User ID
        
    Returns:
        Dictionary of user permissions
    """
    # In a real implementation, this would fetch from a database
    # For now, we'll use a simple mock
    
    # Example hardcoded permissions
    user_permissions = {
        "1": {  # Admin user
            "resources": ["*"],
            "actions": ["*"],
            "roles": ["admin"]
        },
        "2": {  # Manager
            "resources": ["accounts", "transactions", "customers"],
            "actions": ["read", "write"],
            "roles": ["manager"]
        },
        "3": {  # Teller
            "resources": ["accounts", "transactions"],
            "actions": ["read", "write"],
            "roles": ["teller"]
        },
        "4": {  # Customer service
            "resources": ["customers", "accounts"],
            "actions": ["read"],
            "roles": ["customer_service"]
        }
    }
    
    # Convert user_id to string for dictionary lookup
    user_id_str = str(user_id)
    
    # Return permissions or empty dict if user not found
    return user_permissions.get(user_id_str, {"resources": [], "actions": [], "roles": []})
