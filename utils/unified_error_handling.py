"""
Unified Error Handling Framework for CBS_PYTHON

This module provides a consistent approach to error handling across all modules.
It consolidates existing patterns into a single, robust framework that can be used
throughout the system.
"""

import logging
import traceback
import functools
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional, Union, Type, Callable, List, Tuple
from http import HTTPStatus

# Configure logger
logger = logging.getLogger(__name__)

# Error code definitions
class ErrorCodes:
    """Centralized error codes for the entire system"""
    
    # General errors
    GENERAL_ERROR = "GENERAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    
    # Domain-specific errors
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    ACCOUNT_CLOSED = "ACCOUNT_CLOSED"
    ACCOUNT_BLOCKED = "ACCOUNT_BLOCKED"
    DUPLICATE_ENTRY = "DUPLICATE_ENTRY"
    INVALID_TRANSACTION = "INVALID_TRANSACTION"
    LIMIT_EXCEEDED = "LIMIT_EXCEEDED"
    
    # Technical errors
    DATABASE_ERROR = "DATABASE_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"


# Base exception class
class CBSException(Exception):
    """Base exception for all Core Banking System exceptions"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = ErrorCodes.GENERAL_ERROR,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the exception
        
        Args:
            message: Human-readable error message
            error_code: Error code from ErrorCodes class
            status_code: HTTP status code for API responses
            details: Additional error details
        """
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
        
        # Call the base class constructor
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": {
                "message": self.message,
                "code": self.error_code,
                "status": self.status_code,
                "timestamp": self.timestamp,
                "details": self.details
            }
        }


# Domain-specific exception classes
class ValidationException(CBSException):
    """Exception for validation errors"""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_code: str = ErrorCodes.VALIDATION_ERROR
    ):
        """
        Initialize validation exception
        
        Args:
            message: Error message
            field: Name of the field that failed validation
            details: Additional validation error details
            error_code: Error code
        """
        validation_details = details or {}
        if field:
            validation_details["field"] = field
            
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.BAD_REQUEST,
            details=validation_details
        )


class NotFoundException(CBSException):
    """Exception for resource not found errors"""
    
    def __init__(
        self, 
        message: str, 
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        error_code: str = ErrorCodes.NOT_FOUND
    ):
        """
        Initialize not found exception
        
        Args:
            message: Error message
            resource_type: Type of resource that was not found
            resource_id: ID of resource that was not found
            error_code: Error code
        """
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
            
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.NOT_FOUND,
            details=details
        )


class AuthorizationException(CBSException):
    """Exception for authorization errors"""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = ErrorCodes.UNAUTHORIZED
    ):
        """
        Initialize authorization exception
        
        Args:
            message: Error message
            error_code: Error code
        """
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.UNAUTHORIZED
        )


class BusinessRuleException(CBSException):
    """Exception for business rule violations"""
    
    def __init__(
        self, 
        message: str, 
        rule: Optional[str] = None,
        error_code: str = ErrorCodes.GENERAL_ERROR
    ):
        """
        Initialize business rule exception
        
        Args:
            message: Error message
            rule: Business rule that was violated
            error_code: Error code
        """
        details = {}
        if rule:
            details["rule"] = rule
            
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.BAD_REQUEST,
            details=details
        )


class InsufficientFundsException(BusinessRuleException):
    """Exception for insufficient funds errors"""
    
    def __init__(
        self, 
        message: str, 
        account_id: Optional[str] = None,
        required_amount: Optional[float] = None,
        available_balance: Optional[float] = None
    ):
        """
        Initialize insufficient funds exception
        
        Args:
            message: Error message
            account_id: ID of the account with insufficient funds
            required_amount: Amount that was required for the transaction
            available_balance: Available balance in the account
        """
        details = {}
        if account_id:
            details["account_id"] = account_id
        if required_amount is not None:
            details["required_amount"] = required_amount
        if available_balance is not None:
            details["available_balance"] = available_balance
            
        super().__init__(
            message=message,
            rule="sufficient_funds_required",
            error_code=ErrorCodes.INSUFFICIENT_FUNDS
        )


class ExternalServiceException(CBSException):
    """Exception for external service errors"""
    
    def __init__(
        self, 
        message: str, 
        service_name: Optional[str] = None,
        operation: Optional[str] = None,
        error_code: str = ErrorCodes.EXTERNAL_SERVICE_ERROR
    ):
        """
        Initialize external service exception
        
        Args:
            message: Error message
            service_name: Name of the external service
            operation: Operation that was being performed
            error_code: Error code
        """
        details = {}
        if service_name:
            details["service_name"] = service_name
        if operation:
            details["operation"] = operation
            
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            details=details
        )


# Decorator for exception handling with retries
def handle_exceptions(
    logger_instance=None, 
    retry_count: int = 0, 
    retry_delay: float = 1.0,
    allowed_exceptions: List[Type[Exception]] = None,
    error_map: Dict[Type[Exception], Callable[[Exception], Any]] = None
):
    """
    Decorator for handling exceptions with optional retry logic
    
    Args:
        logger_instance: Logger instance (defaults to module logger)
        retry_count: Number of retries for allowed exceptions
        retry_delay: Delay between retries in seconds
        allowed_exceptions: List of exception types that trigger retry
        error_map: Mapping of exception types to handler functions
        
    Returns:
        Decorator function
    """
    log = logger_instance or logger
    error_map = error_map or {}
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            allowed = allowed_exceptions or [Exception]
            last_exception = None
            
            for attempt in range(retry_count + 1):
                try:
                    return func(*args, **kwargs)
                except tuple(allowed) as exc:
                    last_exception = exc
                    
                    # Check if we have a specific handler for this exception
                    for exc_type, handler in error_map.items():
                        if isinstance(exc, exc_type):
                            if attempt < retry_count:
                                log.warning(
                                    f"Exception in {func.__name__} (attempt {attempt+1}/{retry_count+1}): {str(exc)}"
                                )
                                time.sleep(retry_delay)
                            else:
                                return handler(exc)
                    
                    # Default handling if no specific handler found
                    if attempt < retry_count:
                        log.warning(
                            f"Exception in {func.__name__} (attempt {attempt+1}/{retry_count+1}): {str(exc)}"
                        )
                        time.sleep(retry_delay)
                except Exception as exc:
                    # Non-allowed exceptions are not retried
                    log.error(f"Unhandled exception in {func.__name__}: {str(exc)}", exc_info=True)
                    
                    # Check if we have a specific handler for this exception
                    for exc_type, handler in error_map.items():
                        if isinstance(exc, exc_type):
                            return handler(exc)
                    
                    # Re-raise unhandled exceptions
                    raise
            
            # If all retries failed
            if last_exception:
                # Log the final error
                log.error(f"All {retry_count+1} attempts failed for {func.__name__}: {str(last_exception)}")
                
                # If it's our CBSException, handle it properly
                if isinstance(last_exception, CBSException):
                    return {
                        "success": False,
                        "error": last_exception.to_dict()["error"]
                    }
                
                # Return a generic error response
                return {
                    "success": False,
                    "error": {
                        "message": str(last_exception),
                        "code": ErrorCodes.GENERAL_ERROR,
                        "status": HTTPStatus.INTERNAL_SERVER_ERROR
                    }
                }
        
        return wrapper
    
    return decorator


# Helper function for logging method calls (useful for debugging and auditing)
def log_method_call(logger_instance=None, level=logging.DEBUG):
    """
    Decorator for logging method calls with parameters and return values
    
    Args:
        logger_instance: Logger instance (defaults to module logger)
        level: Logging level
        
    Returns:
        Decorator function
    """
    log = logger_instance or logger
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Format the arguments for logging
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            
            # Log the method call
            log.log(level, f"Calling {func.__name__}({signature})")
            
            # Call the function
            try:
                result = func(*args, **kwargs)
                
                # Log the return value (truncate if too long)
                result_repr = repr(result)
                if len(result_repr) > 200:
                    result_repr = result_repr[:200] + "..."
                    
                log.log(level, f"{func.__name__} returned {result_repr}")
                return result
            except Exception as e:
                log.log(level, f"{func.__name__} raised {type(e).__name__}: {str(e)}")
                raise
        
        return wrapper
    
    return decorator


# Helper function to format exceptions for API responses
def format_exception_response(exc: Exception) -> Dict[str, Any]:
    """
    Format an exception as a standardized API response
    
    Args:
        exc: The exception to format
        
    Returns:
        Dictionary containing the error response
    """
    if isinstance(exc, CBSException):
        return exc.to_dict()
    
    # Default error response for non-CBS exceptions
    return {
        "error": {
            "message": str(exc),
            "code": ErrorCodes.GENERAL_ERROR,
            "status": HTTPStatus.INTERNAL_SERVER_ERROR,
            "timestamp": datetime.now().isoformat()
        }
    }
