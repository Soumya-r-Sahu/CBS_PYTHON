"""
HR_ERP Error Handling Utilities

This module provides error handling utilities for the HR_ERP module.
It includes custom exceptions, error loggers, and exception handlers.
"""

import logging
import traceback
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger(__name__)

class HrErpError(Exception):
    """Base exception for HR_ERP module errors"""
    def __init__(self, message: str, error_code: str = "HR_ERP_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class EmployeeDataError(HrErpError):
    """Exception raised for employee data errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "HR_EMPLOYEE_DATA_ERROR", details)

class PayrollError(HrErpError):
    """Exception raised for payroll processing errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "HR_PAYROLL_ERROR", details)

class LeaveManagementError(HrErpError):
    """Exception raised for leave management errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "HR_LEAVE_ERROR", details)

class ResourceError(HrErpError):
    """Exception raised for resource management errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "ERP_RESOURCE_ERROR", details)

def handle_exception(exception: Exception) -> Dict[str, Any]:
    """
    Handle exceptions by creating a formatted error response
    
    Args:
        exception: The exception to handle
        
    Returns:
        Dict containing error details formatted for API response
    """
    if isinstance(exception, HrErpError):
        logger.error(f"HR_ERP Error: {exception.message} ({exception.error_code})")
        return {
            "error": True,
            "error_code": exception.error_code,
            "message": exception.message,
            "details": exception.details
        }
    else:
        error_id = "HR_ERP_UNEXPECTED_ERROR"
        logger.error(f"Unexpected error in HR_ERP module: {str(exception)}")
        logger.debug(traceback.format_exc())
        return {
            "error": True,
            "error_code": error_id,
            "message": str(exception),
            "details": {"type": exception.__class__.__name__}
        }

def log_error(message: str, **kwargs) -> None:
    """
    Log an error with additional context
    
    Args:
        message: Error message to log
        kwargs: Additional context information
    """
    logger.error(f"HR_ERP: {message}")
    if kwargs:
        logger.debug(f"Context: {kwargs}")
