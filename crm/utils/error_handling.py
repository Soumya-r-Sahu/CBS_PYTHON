"""
CRM Error Handling Utilities

This module provides error handling utilities for the CRM module.
It includes custom exceptions, error loggers, and exception handlers.
"""

import logging
import traceback
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger(__name__)

class CrmError(Exception):
    """Base exception for CRM module errors"""
    def __init__(self, message: str, error_code: str = "CRM_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class CustomerDataError(CrmError):
    """Exception raised for customer data errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CRM_CUSTOMER_DATA_ERROR", details)

class CampaignError(CrmError):
    """Exception raised for campaign errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CRM_CAMPAIGN_ERROR", details)

class LeadError(CrmError):
    """Exception raised for lead management errors"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CRM_LEAD_ERROR", details)

def handle_exception(exception: Exception) -> Dict[str, Any]:
    """
    Handle exceptions by creating a formatted error response
    
    Args:
        exception: The exception to handle
        
    Returns:
        Dict containing error details formatted for API response
    """
    if isinstance(exception, CrmError):
        logger.error(f"CRM Error: {exception.message} ({exception.error_code})")
        return {
            "error": True,
            "error_code": exception.error_code,
            "message": exception.message,
            "details": exception.details
        }
    else:
        error_id = "CRM_UNEXPECTED_ERROR"
        logger.error(f"Unexpected error in CRM module: {str(exception)}")
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
    logger.error(f"CRM: {message}")
    if kwargs:
        logger.debug(f"Context: {kwargs}")
