# CBS_PYTHON Unified Error Handling Framework

## Introduction

This document outlines the unified error handling system implemented in CBS_PYTHON to provide a consistent approach to exception handling and error reporting throughout the application. The framework is designed to make error handling more maintainable, user friendly, and easier to debug.

## Core Components

### Base Exception Class

The foundation of our error handling framework is the `CBSException` class located in `utils/unified_error_handling.py`. All domain-specific exceptions inherit from this base class:

```python
class CBSException(Exception):
    """Base exception for all CBS exceptions."""
    
    def __init__(self, message, error_code=None, details=None):
        self.message = message
        self.error_code = error_code or ErrorCodes.GENERAL_ERROR
        self.details = details or {}
        super().__init__(self.message)
        
    def to_dict(self):
        """Convert exception to a dictionary for API responses."""
        return {
            "error": {
                "message": self.message,
                "code": self.error_code,
                "details": self.details,
                "type": self.__class__.__name__
            }
        }
```

### Centralized Error Codes

All error codes are centralized in the `ErrorCodes` class to ensure consistency and avoid duplication:

```python
class ErrorCodes:
    """Centralized error codes for the entire system."""
    
    # General Errors
    GENERAL_ERROR = "E0001"
    CONFIGURATION_ERROR = "E0002"
    SERVICE_UNAVAILABLE = "E0003"
    
    # Validation Errors
    VALIDATION_ERROR = "E1001"
    INVALID_INPUT = "E1002"
    MISSING_REQUIRED_FIELD = "E1003"
    
    # Authentication/Authorization Errors
    AUTHENTICATION_ERROR = "E2001"
    UNAUTHORIZED_ACCESS = "E2002"
    TOKEN_EXPIRED = "E2003"
    INSUFFICIENT_PERMISSIONS = "E2004"
    
    # Database Errors
    DATABASE_ERROR = "E3001"
    RECORD_NOT_FOUND = "E3002"
    DUPLICATE_RECORD = "E3003"
    INTEGRITY_ERROR = "E3004"
    
    # Transaction Errors
    TRANSACTION_ERROR = "E4001"
    INSUFFICIENT_FUNDS = "E4002"
    INVALID_ACCOUNT = "E4003"
    TRANSACTION_LIMIT_EXCEEDED = "E4004"
```

## Specialized Exception Types

The framework provides specialized exceptions for different error cases:

### Validation Exceptions

```python
class ValidationException(CBSException):
    """Exception raised for validation errors."""
    
    def __init__(self, message, field=None, constraint=None, details=None):
        super().__init__(
            message=message,
            error_code=ErrorCodes.VALIDATION_ERROR,
            details={
                **(details or {}),
                "field": field,
                "constraint": constraint
            }
        )
```

### Not Found Exceptions

```python
class NotFoundException(CBSException):
    """Exception raised when a resource is not found."""
    
    def __init__(self, message, resource_type=None, resource_id=None, details=None):
        super().__init__(
            message=message,
            error_code=ErrorCodes.RECORD_NOT_FOUND,
            details={
                **(details or {}),
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )
```

### Authentication Exceptions

```python
class AuthenticationException(CBSException):
    """Exception raised for authentication errors."""
    
    def __init__(self, message, details=None):
        super().__init__(
            message=message,
            error_code=ErrorCodes.AUTHENTICATION_ERROR,
            details=details
        )
```

### Authorization Exceptions

```python
class AuthorizationException(CBSException):
    """Exception raised for authorization errors."""
    
    def __init__(self, message, required_permission=None, details=None):
        super().__init__(
            message=message,
            error_code=ErrorCodes.UNAUTHORIZED_ACCESS,
            details={
                **(details or {}),
                "required_permission": required_permission
            }
        )
```

### Database Exceptions

```python
class DatabaseException(CBSException):
    """Exception raised for database errors."""
    
    def __init__(self, message, operation=None, details=None):
        super().__init__(
            message=message,
            error_code=ErrorCodes.DATABASE_ERROR,
            details={
                **(details or {}),
                "operation": operation
            }
        )
```

### Transaction Exceptions

```python
class TransactionException(CBSException):
    """Exception raised for transaction errors."""
    
    def __init__(self, message, transaction_id=None, details=None):
        super().__init__(
            message=message,
            error_code=ErrorCodes.TRANSACTION_ERROR,
            details={
                **(details or {}),
                "transaction_id": transaction_id
            }
        )
```

## Exception Handling Utilities

The framework provides utilities for consistent exception handling:

### Exception Handler Decorator

```python
def exception_handler(func):
    """Decorator for consistent exception handling."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except CBSException as e:
            logger.error(f"CBS Exception: {e.message}", extra={
                "error_code": e.error_code,
                "details": e.details,
                "exception_type": e.__class__.__name__
            })
            return e.to_dict(), 400
        except Exception as e:
            logger.exception("Unhandled exception")
            return {
                "error": {
                    "message": "An unexpected error occurred",
                    "code": ErrorCodes.GENERAL_ERROR,
                    "type": "UnhandledException"
                }
            }, 500
    return wrapper
```

### Context Manager for Database Operations

```python
class DatabaseExceptionHandler:
    """Context manager for handling database exceptions."""
    
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False
            
        if issubclass(exc_type, SQLAlchemyError):
            raise DatabaseException(
                message="Database operation failed",
                operation=self._get_operation_from_stack(),
                details={"original_error": str(exc_val)}
            ) from exc_val
            
        return False
        
    def _get_operation_from_stack(self):
        # Implementation to determine the database operation from stack trace
        pass
```

## Integration with API Layer

The error handling framework integrates seamlessly with the API layer:

```python
@app.errorhandler(CBSException)
def handle_cbs_exception(e):
    """Handle CBS exceptions in Flask app."""
    return jsonify(e.to_dict()), 400
    
@app.errorhandler(Exception)
def handle_general_exception(e):
    """Handle general exceptions in Flask app."""
    logger.exception("Unhandled exception")
    return jsonify({
        "error": {
            "message": "An unexpected error occurred",
            "code": ErrorCodes.GENERAL_ERROR,
            "type": "UnhandledException"
        }
    }), 500
```

## Best Practices for Using the Error Handling Framework

1. **Use Specific Exceptions**: Always use the most specific exception type for the error condition.
2. **Provide Detailed Messages**: Include enough detail in error messages to help troubleshoot the issue.
3. **Add Contextual Information**: Use the `details` parameter to provide contextual information about the error.
4. **Centralize Error Codes**: Add new error codes to the `ErrorCodes` class instead of hardcoding them.
5. **Consistent API Responses**: Use the `to_dict()` method for consistent API error responses.
6. **Log Appropriate Details**: Ensure that exceptions are properly logged with relevant context.
7. **Handle Exceptions at Appropriate Levels**: Catch exceptions at the level where they can be properly handled.

## Migration from Legacy Error Handling

When migrating from legacy error handling to the new framework:

1. **Identify Legacy Exceptions**: Identify all custom exceptions in the codebase.
2. **Create Mapping**: Map legacy exception types to the new framework's types.
3. **Create Adapters**: Implement adapter classes if needed for backwards compatibility.
4. **Update Handlers**: Update all error handlers to use the new exception types.
5. **Update API Responses**: Ensure API responses use the standardized format.

```python
# Adapter example for legacy exceptions
def adapt_legacy_exception(exception):
    """Convert legacy exceptions to the new format."""
    if isinstance(exception, LegacyValidationError):
        return ValidationException(
            message=exception.message,
            field=exception.field_name,
            constraint=exception.constraint
        )
    elif isinstance(exception, LegacyNotFoundException):
        return NotFoundException(
            message=exception.message,
            resource_type=exception.entity_type,
            resource_id=exception.entity_id
        )
    else:
        return CBSException(
            message=str(exception),
            error_code=ErrorCodes.GENERAL_ERROR
        )
```

## Conclusion

The unified error handling framework provides a consistent approach to exception handling and error reporting throughout the CBS_PYTHON application. By centralizing error codes, providing specialized exception types, and offering utilities for consistent handling, the framework makes error handling more maintainable and user-friendly.

Last updated: May 23, 2025
