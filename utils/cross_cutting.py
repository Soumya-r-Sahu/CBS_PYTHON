"""
Cross-Cutting Concerns Module

This module provides functionality for cross-cutting concerns like
error handling, logging, and security that span multiple domains.
"""
import logging
import os
from datetime import datetime
from functools import wraps
from typing import Callable, Dict, Any, Type, List, Optional

# Configure logging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = os.environ.get('CBS_LOG_LEVEL', 'INFO').upper()
LOG_FILE = os.environ.get('CBS_LOG_FILE', 'cbs_system.log')

# Create logger
logger = logging.getLogger('cbs_system')
logger.setLevel(getattr(logging, LOG_LEVEL))

# Create file handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(getattr(logging, LOG_LEVEL))

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(getattr(logging, LOG_LEVEL))

# Create formatter and add to handlers
formatter = logging.Formatter(LOG_FORMAT)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


class ErrorCodes:
    """Error codes for the banking system"""
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


class BusinessException(Exception):
    """Base exception for business rule violations"""
    
    def __init__(self, message: str, error_code: str = ErrorCodes.GENERAL_ERROR, 
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a business exception.
        
        Args:
            message: Human-readable error message
            error_code: Error code from ErrorCodes class
            details: Additional error details
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(self.message)


class ValidationException(BusinessException):
    """Exception for validation errors"""
    
    def __init__(self, message: str, validation_errors: Dict[str, str]):
        """
        Initialize a validation exception.
        
        Args:
            message: Human-readable error message
            validation_errors: Dictionary of field-specific validation errors
        """
        super().__init__(message, ErrorCodes.VALIDATION_ERROR, {"validation_errors": validation_errors})
        self.validation_errors = validation_errors


class NotFoundException(BusinessException):
    """Exception for not found errors"""
    
    def __init__(self, message: str, entity_type: str, entity_id: str):
        """
        Initialize a not found exception.
        
        Args:
            message: Human-readable error message
            entity_type: Type of entity that wasn't found
            entity_id: ID of entity that wasn't found
        """
        super().__init__(message, ErrorCodes.NOT_FOUND, {
            "entity_type": entity_type,
            "entity_id": entity_id
        })


def log_method_call(logger: logging.Logger):
    """
    Decorator for logging method calls.
    
    Args:
        logger: Logger instance to use
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator


def handle_exceptions(error_map: Dict[Type[Exception], Callable[[Exception], Any]] = None):
    """
    Decorator for handling exceptions and converting them to standard responses.
    
    Args:
        error_map: Mapping of exception types to handler functions
        
    Returns:
        Decorator function
    """
    error_map = error_map or {}
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Check if we have a specific handler for this exception type
                for exc_type, handler in error_map.items():
                    if isinstance(e, exc_type):
                        return handler(e)
                
                # Default handling for BusinessException
                if isinstance(e, BusinessException):
                    logger.warning(f"Business exception in {func.__name__}: {str(e)}")
                    return {
                        "success": False,
                        "message": e.message,
                        "error_code": e.error_code,
                        "details": e.details
                    }
                
                # Default handling for other exceptions
                logger.error(f"Unhandled exception in {func.__name__}: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "message": "An unexpected error occurred",
                    "error_code": ErrorCodes.GENERAL_ERROR
                }
        return wrapper
    return decorator


# Example usage in a use case:
"""
from utils.cross_cutting import log_method_call, handle_exceptions, logger, BusinessException, ValidationException

class MyUseCase:
    @log_method_call(logger)
    @handle_exceptions()
    def execute(self, request):
        # Method implementation
        if not self._validate(request):
            raise ValidationException("Invalid request", {"field": "error message"})
        
        # Business logic
        return {"success": True, "data": result}
"""
