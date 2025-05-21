"""
Centralized Error Handling for Core Banking System

This module provides standardized error handling utilities for all CBS modules.
It implements a consistent approach to error handling, logging, and error response generation.

Tags: error_handling, exceptions, logging
AI-Metadata:
    component_type: error_handler
    criticality: high
    purpose: standardized_error_handling
    impact_on_failure: inconsistent_error_responses
"""

import logging
import traceback
from typing import Dict, Any, Optional, Union
from http import HTTPStatus
import json
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

class CBSError(Exception):
    """Base exception class for all Core Banking System errors"""
    
    def __init__(self, 
                 message: str, 
                 error_code: str = "CBS_ERROR", 
                 status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
                 context: Optional[Dict[str, Any]] = None,
                 details: Optional[str] = None):
        """
        Initialize the error.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            status_code: HTTP status code (useful for API responses)
            context: Additional context information
            details: Detailed error information
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.context = context or {}
        self.details = details
        self.timestamp = datetime.now().isoformat()
        
        # Call the base class constructor
        super().__init__(message)
        
        # Log the error when it''s created
        self._log_error()
    
    def _log_error(self) -> None:
        """Log the error with context information."""
        error_info = self.to_dict()
        logger.error(
            f"Error {self.error_code}: {self.message}",
            extra={"error_details": error_info}
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "status": self.status_code,
                "timestamp": self.timestamp,
                "details": self.details,
                **self.context
            }
        }
    
    def to_json(self) -> str:
        """Convert error to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# Module-specific errors that inherit from the base class
class ValidationError(CBSError):
    """Error raised during data validation."""
    
    def __init__(self, 
                message: str, 
                field: Optional[str] = None,
                error_code: str = "VALIDATION_ERROR", 
                status_code: int = HTTPStatus.BAD_REQUEST,
                context: Optional[Dict[str, Any]] = None,
                details: Optional[str] = None):
        """
        Initialize a validation error.
        
        Args:
            message: Human-readable error message
            field: The field that failed validation
            error_code: Machine-readable error code
            status_code: HTTP status code
            context: Additional context information
            details: Detailed error information
        """
        context = context or {}
        if field:
            context["field"] = field
            
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            context=context,
            details=details
        )


class DatabaseError(CBSError):
    """Error raised during database operations."""
    
    def __init__(self, 
                message: str, 
                query: Optional[str] = None,
                error_code: str = "DATABASE_ERROR", 
                status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
                context: Optional[Dict[str, Any]] = None,
                details: Optional[str] = None):
        """
        Initialize a database error.
        
        Args:
            message: Human-readable error message
            query: The query that caused the error (sanitized)
            error_code: Machine-readable error code
            status_code: HTTP status code
            context: Additional context information
            details: Detailed error information
        """
        context = context or {}
        if query:
            # Sanitize query before logging - remove potential sensitive data
            sanitized_query = query.replace("''", "[?]").replace('"', "[?]")
            context["query"] = sanitized_query
            
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            context=context,
            details=details
        )


class ConfigError(CBSError):
    """Error raised during configuration operations."""
    
    def __init__(self, 
                message: str, 
                config_key: Optional[str] = None,
                error_code: str = "CONFIG_ERROR", 
                status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
                context: Optional[Dict[str, Any]] = None,
                details: Optional[str] = None):
        """
        Initialize a configuration error.
        
        Args:
            message: Human-readable error message
            config_key: The configuration key that caused the error
            error_code: Machine-readable error code
            status_code: HTTP status code
            context: Additional context information
            details: Detailed error information
        """
        context = context or {}
        if config_key:
            context["config_key"] = config_key
            
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            context=context,
            details=details
        )


class AuthenticationError(CBSError):
    """Error raised during authentication operations."""
    
    def __init__(self, 
                message: str = "Authentication failed", 
                error_code: str = "AUTH_ERROR", 
                status_code: int = HTTPStatus.UNAUTHORIZED,
                context: Optional[Dict[str, Any]] = None,
                details: Optional[str] = None):
        """
        Initialize an authentication error.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            status_code: HTTP status code
            context: Additional context information
            details: Detailed error information
        """
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            context=context,
            details=details
        )


class AuthorizationError(CBSError):
    """Error raised during authorization operations."""
    
    def __init__(self, 
                message: str = "Access denied", 
                resource: Optional[str] = None,
                error_code: str = "ACCESS_DENIED", 
                status_code: int = HTTPStatus.FORBIDDEN,
                context: Optional[Dict[str, Any]] = None,
                details: Optional[str] = None):
        """
        Initialize an authorization error.
        
        Args:
            message: Human-readable error message
            resource: The resource being accessed
            error_code: Machine-readable error code
            status_code: HTTP status code
            context: Additional context information
            details: Detailed error information
        """
        context = context or {}
        if resource:
            context["resource"] = resource
            
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            context=context,
            details=details
        )


class PaymentError(CBSError):
    """Error raised during payment operations."""
    
    def __init__(self, 
                message: str, 
                payment_id: Optional[str] = None,
                error_code: str = "PAYMENT_ERROR", 
                status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
                context: Optional[Dict[str, Any]] = None,
                details: Optional[str] = None):
        """
        Initialize a payment error.
        
        Args:
            message: Human-readable error message
            payment_id: The payment ID related to the error
            error_code: Machine-readable error code
            status_code: HTTP status code
            context: Additional context information
            details: Detailed error information
        """
        context = context or {}
        if payment_id:
            context["payment_id"] = payment_id
            
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            context=context,
            details=details
        )


class ComplianceError(CBSError):
    """Error raised during compliance operations."""
    
    def __init__(self, 
                message: str, 
                rule_id: Optional[str] = None,
                error_code: str = "COMPLIANCE_ERROR", 
                status_code: int = HTTPStatus.PRECONDITION_FAILED,
                context: Optional[Dict[str, Any]] = None,
                details: Optional[str] = None):
        """
        Initialize a compliance error.
        
        Args:
            message: Human-readable error message
            rule_id: The compliance rule ID related to the error
            error_code: Machine-readable error code
            status_code: HTTP status code
            context: Additional context information
            details: Detailed error information
        """
        context = context or {}
        if rule_id:
            context["rule_id"] = rule_id
            
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            context=context,
            details=details
        )


def handle_exception(func):
    """
    Decorator to catch and handle exceptions.
    
    This decorator wraps a function and handles any exceptions raised by it,
    converting them to CBSError objects for consistent error handling.
    
    Args:
        func: The function to wrap
        
    Returns:
        The wrapped function
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CBSError:
            # Re-raise CBSErrors as they''re already handled
            raise
        except Exception as e:
            # Convert other exceptions to CBSErrors
            error_message = str(e)
            error_details = traceback.format_exc()
            logger.error(f"Unhandled exception in {func.__name__}: {error_message}")
            raise CBSError(
                message=f"An unexpected error occurred: {error_message}",
                error_code="UNHANDLED_ERROR",
                details=error_details
            )
    
    return wrapper
