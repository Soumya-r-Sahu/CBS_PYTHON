"""
Digital Channels Module - Error Handler

This module provides standardized error handling for the Digital Channels module,
extending the centralized error handling system.

Tags: error_handling, digital_channels
AI-Metadata:
    component_type: error_handler
    module: digital_channels
    criticality: high
"""

import logging
import traceback
from typing import Dict, Any, Optional, Union, Tuple
from http import HTTPStatus

# Import central error handling
from utils.error_handling import CBSError, ValidationError as BaseValidationError, handle_exception

# Configure logger
logger = logging.getLogger(__name__)

class DigitalChannelsError(CBSError):
    """Base exception class for all digital channels errors"""
    
    def __init__(self, 
                 message: str, 
                 error_code: str = "DIGITAL_CHANNELS_ERROR", 
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
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            context=context,
            details=details
        )

# Legacy compatibility
ServiceError = DigitalChannelsError

class ChannelValidationError(BaseValidationError):
    """Error raised during channel-specific data validation."""
    
    def __init__(self, 
                message: str, 
                field: Optional[str] = None,
                channel: Optional[str] = None,
                error_code: str = "CHANNEL_VALIDATION_ERROR", 
                status_code: int = HTTPStatus.BAD_REQUEST,
                context: Optional[Dict[str, Any]] = None,
                details: Optional[str] = None):
        """
        Initialize a channel validation error.
        
        Args:
            message: Human-readable error message
            field: The field that failed validation
            channel: The specific channel (mobile, internet, atm)
            error_code: Machine-readable error code
            status_code: HTTP status code
            context: Additional context information
            details: Detailed error information
        """
        context = context or {}
        if channel:
            context["channel"] = channel
            
        super().__init__(
            message=message,
            field=field,
            error_code=error_code,
            status_code=status_code,
            context=context,
            details=details
        )

class AuthenticationError(ServiceError):
    """Exception raised for authentication errors"""
    
    def __init__(self, 
                 message: str = "Authentication failed", 
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize an authentication error

        Args:
            message: Human-readable error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=HTTPStatus.UNAUTHORIZED,
            details=details
        )

class AuthorizationError(ServiceError):
    """Exception raised for authorization errors"""
    
    def __init__(self, 
                 message: str = "Not authorized to perform this action", 
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize an authorization error

        Args:
            message: Human-readable error message
            details: Additional error details
        """
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=HTTPStatus.FORBIDDEN,
            details=details
        )

class ResourceNotFoundError(ServiceError):
    """Exception raised when a requested resource is not found"""
    
    def __init__(self, 
                 resource_type: str,
                 resource_id: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a resource not found error

        Args:
            resource_type: Type of resource that was not found
            resource_id: ID of the resource that was not found
            details: Additional error details
        """
        error_details = details or {}
        error_details["resource_type"] = resource_type
        if resource_id:
            error_details["resource_id"] = resource_id
            message = f"{resource_type} with ID '{resource_id}' not found"
        else:
            message = f"{resource_type} not found"
            
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=HTTPStatus.NOT_FOUND,
            details=error_details
        )

def handle_exception(exc: Exception) -> Dict[str, Any]:
    """
    Handle an exception and return a standardized error response

    Args:
        exc: The exception to handle

    Returns:
        A standardized error response dictionary
    """
    if isinstance(exc, ServiceError):
        logger.warning(
            f"Service error: {exc.error_code} - {exc.message}",
            extra={"error_details": exc.details}
        )
        
        return {
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            },
            "status_code": exc.status_code
        }
    else:
        logger.error(
            f"Unexpected error: {str(exc)}",
            exc_info=True
        )
        
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred"
            },
            "status_code": HTTPStatus.INTERNAL_SERVER_ERROR
        }

def log_error(error_message: str, exc: Optional[Exception] = None, level: str = "error", **kwargs) -> None:
    """
    Log an error with consistent formatting

    Args:
        error_message: The error message to log
        exc: The exception that occurred (if any)
        level: The log level to use (debug, info, warning, error, critical)
        **kwargs: Additional context information to include in the log
    """
    log_data = {
        "message": error_message,
        **kwargs
    }
    
    if exc:
        log_data["exception"] = str(exc)
        log_data["traceback"] = traceback.format_exc()
    
    log_fn = getattr(logger, level.lower())
    log_fn(error_message, extra={"log_data": log_data})
