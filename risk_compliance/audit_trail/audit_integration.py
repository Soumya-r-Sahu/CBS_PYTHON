"""
Integration module for injecting Audit Trail capabilities across the Core Banking System

This module provides decorators and utility functions to easily integrate
audit logging throughout the codebase with minimal changes to existing functions.
"""

import functools
import inspect
import os
import sys
from typing import Dict, Any, Callable, Optional

# Add current directory to path to ensure local imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


# Import audit_trail_manager (using relative import)
from .audit_trail_manager import audit_trail


def audit_decorator(event_type: str, 
                  entity_type: Optional[str] = None,
                  description_template: Optional[str] = None):
    """
    Decorator to automatically audit a function call
    
    Args:
        event_type (str): Type of event to log
        entity_type (str, optional): Type of entity being acted upon
        description_template (str, optional): Template string for description
    
    Example:
        @audit_decorator("account_create", entity_type="account")
        def create_account(user_id, account_details):
            # Function implementation
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get user ID from args or kwargs
            user_id = None
            entity_id = None
            metadata = {}
            
            # Inspect function signature to find user_id or similar parameters
            signature = inspect.signature(func)
            param_names = list(signature.parameters.keys())
            
            # Check if user_id is a parameter and extract it
            user_id_params = ["user_id", "customer_id", "employee_id", "userId"]
            for idx, param_name in enumerate(param_names):
                if param_name in user_id_params and idx < len(args):
                    user_id = args[idx]
                    break
            
            # Check kwargs if not found in args
            if user_id is None:
                for param_name in user_id_params:
                    if param_name in kwargs:
                        user_id = kwargs[param_name]
                        break
            
            # Try to identify entity_id
            entity_id_params = ["account_id", "customer_id", "transaction_id", 
                              "loan_id", "card_id", "id"]
            if entity_type:
                entity_param = f"{entity_type}_id"
                # Look for entity ID parameter
                for idx, param_name in enumerate(param_names):
                    if (param_name == entity_param or param_name in entity_id_params) and idx < len(args):
                        entity_id = args[idx]
                        break
                
                # Check kwargs if not found in args
                if entity_id is None:
                    for param_name in [entity_param] + entity_id_params:
                        if param_name in kwargs:
                            entity_id = kwargs[param_name]
                            break
            
            # Collect metadata from function parameters
            for idx, param_name in enumerate(param_names):
                # Skip user_id and entity_id to avoid duplication
                if param_name in user_id_params + entity_id_params:
                    continue
                    
                # Add other parameters to metadata
                if idx < len(args):
                    # Only add primitive types or strings to metadata
                    value = args[idx]
                    if isinstance(value, (int, float, str, bool)):
                        metadata[param_name] = value
            
            # Add kwargs to metadata
            for k, v in kwargs.items():
                if k not in user_id_params + entity_id_params and isinstance(v, (int, float, str, bool)):
                    metadata[k] = v
            
            # Generate description from template if provided
            description = None
            if description_template:
                try:
                    # Use user_id and entity_id as default context
                    context = {"user_id": user_id, "entity_id": entity_id}
                    context.update({k: v for k, v in metadata.items() if isinstance(v, (int, float, str, bool))})
                    description = description_template.format(**context)
                except (KeyError, ValueError):
                    # Fall back to function name if template formatting fails
                    description = f"{event_type} - {func.__name__}"
            
            # Default description based on function name
            if not description:
                description = f"{event_type} - {func.__name__}"
            
            # Call the function
            try:
                result = func(*args, **kwargs)
                
                # Log successful event
                status = "SUCCESS"
                # Extract entity_id from result if not already set
                if not entity_id and isinstance(result, dict) and "id" in result:
                    entity_id = result["id"]
                elif not entity_id and hasattr(result, "id"):
                    entity_id = result.id
                
                # Add result status to metadata if available
                if isinstance(result, dict) and "status" in result:
                    status = result["status"]
                
                audit_trail.log_event(
                    event_type=event_type,
                    user_id=user_id,
                    description=description,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    status=status,
                    metadata=metadata
                )
                
                return result
            
            except Exception as e:
                # Log failed event
                audit_trail.log_event(
                    event_type=event_type,
                    user_id=user_id,
                    description=description,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    status="FAILED",
                    metadata={
                        **metadata,
                        "error": str(e),
                        "error_type": e.__class__.__name__
                    }
                )
                
                # Re-raise the exception
                raise
        
        return wrapper
    
    return decorator


# Shorthand decorators for common operations
def audit_transaction(description_template=None):
    """Decorator for auditing transaction operations"""
    return audit_decorator("transaction", entity_type="transaction", 
                         description_template=description_template)

def audit_account_change(description_template=None):
    """Decorator for auditing account operations"""
    return audit_decorator("account_change", entity_type="account",
                         description_template=description_template)

def audit_customer_change(description_template=None):
    """Decorator for auditing customer profile operations"""
    return audit_decorator("customer_change", entity_type="customer",
                         description_template=description_template)

def audit_security_event(description_template=None):
    """Decorator for auditing security events"""
    return audit_decorator("security_event", 
                         description_template=description_template)


# Custom audit event function for manual integration
def log_audit_event(event_type: str, user_id: str, description: str = None,
                  entity_type: str = None, entity_id: str = None,
                  metadata: Dict[str, Any] = None):
    """
    Log an audit event manually
    
    Args:
        event_type (str): Type of event
        user_id (str): ID of the user performing the action
        description (str, optional): Description of the event
        entity_type (str, optional): Type of entity being acted upon
        entity_id (str, optional): ID of the entity being acted upon
        metadata (Dict, optional): Additional data about the event
    """
    return audit_trail.log_event(
        event_type=event_type,
        user_id=user_id,
        description=description,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata=metadata
    )