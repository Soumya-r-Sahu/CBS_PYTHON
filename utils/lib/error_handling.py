"""
Unified Error Handling Module

This module provides a centralized error handling system for the CBS_PYTHON system.
It defines standard exceptions, error codes, and error handling utilities.
"""

import logging
import traceback
import datetime
import sys
from typing import Dict, Any, Optional, List, Type, Callable

# Import service registry for module registration
from utils.lib.service_registry import ServiceRegistry

# Configure logger
logger = logging.getLogger(__name__)

# Define standard error codes
ERROR_CODES = {
    # General errors
    "GENERAL_ERROR": {"code": "GEN-001", "http_status": 500},
    "CONFIG_ERROR": {"code": "GEN-002", "http_status": 500},
    "NOT_IMPLEMENTED": {"code": "GEN-003", "http_status": 501},
    "VALIDATION_ERROR": {"code": "GEN-004", "http_status": 400},
    
    # Authentication/authorization errors
    "AUTH_REQUIRED": {"code": "AUTH-001", "http_status": 401},
    "ACCESS_DENIED": {"code": "AUTH-002", "http_status": 403},
    "INVALID_CREDENTIALS": {"code": "AUTH-003", "http_status": 401},
    "TOKEN_EXPIRED": {"code": "AUTH-004", "http_status": 401},
    
    # Database errors
    "DB_CONNECTION_ERROR": {"code": "DB-001", "http_status": 500},
    "DB_QUERY_ERROR": {"code": "DB-002", "http_status": 500},
    "DB_RECORD_NOT_FOUND": {"code": "DB-003", "http_status": 404},
    "DB_DUPLICATE_RECORD": {"code": "DB-004", "http_status": 409},
    
    # Module errors
    "MODULE_NOT_FOUND": {"code": "MOD-001", "http_status": 500},
    "MODULE_UNAVAILABLE": {"code": "MOD-002", "http_status": 503},
    "MODULE_DEPENDENCY_ERROR": {"code": "MOD-003", "http_status": 500},
    
    # Business logic errors
    "INSUFFICIENT_FUNDS": {"code": "BIZ-001", "http_status": 400},
    "ACCOUNT_LOCKED": {"code": "BIZ-002", "http_status": 403},
    "LIMIT_EXCEEDED": {"code": "BIZ-003", "http_status": 400},
    "INVALID_OPERATION": {"code": "BIZ-004", "http_status": 400},
}

class CbsError(Exception):
    """
    Base exception class for all CBS_PYTHON exceptions
    
    Attributes:
        error_code (str): Standard error code identifier
        message (str): Human-readable error message
        details (dict, optional): Additional error details
        http_status (int): HTTP status code for API responses
    """
    
    def __init__(self, error_code="GENERAL_ERROR", message=None, details=None, http_status=None):
        """
        Initialize a CBS error
        
        Args:
            error_code (str): Standard error code identifier
            message (str, optional): Human-readable error message
            details (dict, optional): Additional error details
            http_status (int, optional): HTTP status code override
        """
        if error_code in ERROR_CODES:
            code_info = ERROR_CODES[error_code]
            self.error_code = code_info["code"]
            self.http_status = http_status or code_info.get("http_status", 500)
        else:
            self.error_code = error_code
            self.http_status = http_status or 500
            
        self.message = message or f"An error occurred: {error_code}"
        self.details = details or {}
        
        # Initialize standard Exception
        super().__init__(self.message)
    
    def to_dict(self):
        """
        Convert exception to dictionary representation
        
        Returns:
            dict: Dictionary representation of the error
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    def __str__(self):
        """String representation of the error"""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.error_code}: {self.message} ({details_str})"
        return f"{self.error_code}: {self.message}"

# Define specific exception types
class ValidationError(CbsError):
    """Exception raised for validation errors"""
    def __init__(self, message=None, details=None):
        super().__init__("VALIDATION_ERROR", message or "Validation error", details)
        
class AuthenticationError(CbsError):
    """Exception raised for authentication failures"""
    def __init__(self, message=None, details=None):
        super().__init__("AUTH_REQUIRED", message or "Authentication required", details)
        
class AuthorizationError(CbsError):
    """Exception raised for authorization failures"""
    def __init__(self, message=None, details=None):
        super().__init__("ACCESS_DENIED", message or "Access denied", details)
        
class DatabaseError(CbsError):
    """Exception raised for database errors"""
    def __init__(self, error_code="DB_QUERY_ERROR", message=None, details=None):
        super().__init__(error_code, message or "Database error", details)
        
class RecordNotFoundError(DatabaseError):
    """Exception raised when a database record is not found"""
    def __init__(self, message=None, details=None):
        super().__init__("DB_RECORD_NOT_FOUND", message or "Record not found", details)
        
class ModuleError(CbsError):
    """Exception raised for module-related errors"""
    def __init__(self, error_code="MODULE_UNAVAILABLE", message=None, details=None):
        super().__init__(error_code, message or "Module error", details)
        
class BusinessLogicError(CbsError):
    """Exception raised for business logic errors"""
    def __init__(self, error_code="INVALID_OPERATION", message=None, details=None):
        super().__init__(error_code, message or "Business logic error", details)
        
class InsufficientFundsError(BusinessLogicError):
    """Exception raised when an account has insufficient funds"""
    def __init__(self, message=None, details=None):
        super().__init__("INSUFFICIENT_FUNDS", message or "Insufficient funds", details)

class AppError(CbsError):
    """Exception raised for general application errors
    
    This is an alias for CbsError maintained for backward compatibility.
    """
    def __init__(self, error_code="GENERAL_ERROR", message=None, details=None, http_status=None):
        super().__init__(error_code, message or "Application error", details, http_status)

class ErrorHandler:
    """
    Centralized error handling utility
    
    Description:
        This class provides centralized error handling capabilities for
        capturing, logging, and formatting errors in a consistent way
        across the system.
    
    Usage:
        # Create an error handler
        error_handler = ErrorHandler()
        
        # Handle an exception
        try:
            # Some operation
            result = process_payment(payment_data)
        except Exception as e:
            error_response = error_handler.handle_exception(e)
            return error_response
    """
    
    def __init__(self):
        """Initialize error handler"""
        self.error_callbacks = {}
        
    def register_error_callback(self, error_type: Type[Exception], callback: Callable):
        """
        Register a callback for a specific error type
        
        Args:
            error_type (Type[Exception]): Exception type to handle
            callback (Callable): Callback function to execute
        """
        self.error_callbacks[error_type] = callback
        
    def handle_exception(self, exception: Exception, log_level=logging.ERROR) -> Dict[str, Any]:
        """
        Handle an exception centrally
        
        Args:
            exception (Exception): The exception to handle
            log_level (int): Logging level to use
            
        Returns:
            dict: Formatted error response
        """
        # Check for registered callbacks
        for error_type, callback in self.error_callbacks.items():
            if isinstance(exception, error_type):
                try:
                    return callback(exception)
                except Exception as callback_error:
                    logger.error(f"Error in error callback: {str(callback_error)}")
        
        # Get traceback information
        tb = traceback.format_exc()
        
        # Log the error
        logger.log(log_level, f"Error: {str(exception)}\n{tb}")
        
        # Format the error response
        if isinstance(exception, CbsError):
            # Use the structured error information
            error_response = exception.to_dict()
        else:
            # Create a generic error response
            error_response = {
                "error_code": ERROR_CODES["GENERAL_ERROR"]["code"],
                "message": str(exception),
                "details": {
                    "type": exception.__class__.__name__
                },
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        return error_response
        
    def format_validation_errors(self, validation_errors: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Format validation errors into a standard structure
        
        Args:
            validation_errors (dict): Dictionary of field validation errors
            
        Returns:
            dict: Formatted validation error response
        """
        return {
            "error_code": ERROR_CODES["VALIDATION_ERROR"]["code"],
            "message": "Validation failed",
            "details": {
                "validation_errors": validation_errors
            },
            "timestamp": datetime.datetime.now().isoformat()
        }

# Register error handling with service registry
def register_error_handling_services():
    """Register error handling services with the service registry"""
    registry = ServiceRegistry()
    
    # Register error handler
    error_handler = ErrorHandler()
    registry.register("error.handler", error_handler, "utils")
    
    # Register individual error handling services
    registry.register("error.handle_exception", error_handler.handle_exception, "utils")
    registry.register("error.format_validation_errors", error_handler.format_validation_errors, "utils")
    
    logger.info("Error handling services registered")

# Initialize registration on module import
register_error_handling_services()
