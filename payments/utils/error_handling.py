"""
Error Handling Utilities for Payments Module

This module provides standardized error handling utilities for the payments module.
It implements a consistent approach to error handling, logging, and error response generation.

Tags: payments, error_handling, exceptions, logging
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

# Import central error handling
from utils.error_handling import CBSError, ValidationError as BaseValidationError, handle_exception, PaymentError as BasePaymentError

# Configure logger
logger = logging.getLogger(__name__)

class ModulePaymentError(BasePaymentError):
    """Base exception class for all payment service errors"""
    
    def __init__(self, 
                 message: str, 
                 payment_id: Optional[str] = None,
                 transaction_type: Optional[str] = None,
                 error_code: str = "PAYMENT_ERROR", 
                 status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
                 context: Optional[Dict[str, Any]] = None,
                 details: Optional[str] = None):
        """
        Initialize a payment error.
        
        Args:
            message: Human-readable error message
            payment_id: The payment ID related to the error
            transaction_type: The type of transaction (NEFT, RTGS, UPI, etc.)
            error_code: Machine-readable error code
            status_code: HTTP status code
            context: Additional context information
            details: Detailed error information
        """
        context = context or {}
        if transaction_type:
            context["transaction_type"] = transaction_type
            
        super().__init__(
            message=message,
            payment_id=payment_id,
            error_code=error_code,
            status_code=status_code,
            context=context,
            details=details
        )

# Legacy compatibility
PaymentError = ModulePaymentError

class PaymentValidationError(BaseValidationError):
    """Exception raised for payment validation errors"""
    
    def __init__(self, 
                 message: str, 
                 field: Optional[str] = None,
                 payment_type: Optional[str] = None,
                 error_code: str = "PAYMENT_VALIDATION_ERROR", 
                 status_code: int = HTTPStatus.BAD_REQUEST,
                 context: Optional[Dict[str, Any]] = None,
                 details: Optional[str] = None):
        """
        Initialize a payment validation error.
        
        Args:
            message: Human-readable error message
            field: The field that failed validation
            payment_type: The type of payment being validated
            error_code: Machine-readable error code
            status_code: HTTP status code
            context: Additional context information
            details: Detailed error information
        """
        context = context or {}
        if payment_type:
            context["payment_type"] = payment_type
            
        super().__init__(
            message=message,
            field=field,
            error_code=error_code,
            status_code=status_code,
            context=context,
            details=details
        )

class InsufficientFundsError(PaymentError):
    """Exception raised when a payment fails due to insufficient funds"""
    
    def __init__(self, 
                 account_number: str,
                 required_amount: float,
                 available_balance: float,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize an insufficient funds error

        Args:
            account_number: The account number with insufficient funds
            required_amount: The amount that was required for the payment
            available_balance: The available balance in the account
            details: Additional error details
        """
        error_details = details or {}
        error_details.update({
            "account_number": account_number,
            "required_amount": required_amount,
            "available_balance": available_balance,
            "shortfall": required_amount - available_balance
        })
        
        message = f"Insufficient funds in account {account_number}. " \
                 f"Required: {required_amount}, Available: {available_balance}"
            
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_FUNDS",
            status_code=HTTPStatus.PAYMENT_REQUIRED,
            details=error_details
        )

class PaymentProcessingError(PaymentError):
    """Exception raised when a payment fails during processing"""
    
    def __init__(self, 
                 message: str,
                 payment_id: Optional[str] = None,
                 payment_gateway: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a payment processing error

        Args:
            message: Human-readable error message
            payment_id: ID of the payment that failed
            payment_gateway: The payment gateway that was used
            details: Additional error details
        """
        error_details = details or {}
        if payment_id:
            error_details["payment_id"] = payment_id
        if payment_gateway:
            error_details["payment_gateway"] = payment_gateway
            
        super().__init__(
            message=message,
            error_code="PAYMENT_PROCESSING_ERROR",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            details=error_details
        )

class PaymentNotFoundError(PaymentError):
    """Exception raised when a payment is not found"""
    
    def __init__(self, 
                 payment_id: str,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a payment not found error

        Args:
            payment_id: ID of the payment that was not found
            details: Additional error details
        """
        error_details = details or {}
        error_details["payment_id"] = payment_id
            
        super().__init__(
            message=f"Payment with ID {payment_id} not found",
            error_code="PAYMENT_NOT_FOUND",
            status_code=HTTPStatus.NOT_FOUND,
            details=error_details
        )

def handle_payment_exception(exc: Exception) -> Dict[str, Any]:
    """
    Handle a payment exception and return a standardized error response

    Args:
        exc: The exception to handle

    Returns:
        A standardized error response dictionary
    
    AI-Metadata:
        purpose: Convert exceptions to standardized responses
        criticality: high
        error_handling: log_and_return_response
    """
    if isinstance(exc, PaymentError):
        # Log the payment-specific error
        logger.warning(
            f"Payment error: {exc.error_code} - {exc.message}",
            extra={"error_details": exc.details}
        )
        
        return {
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now().isoformat()
            },
            "status_code": exc.status_code
        }
    else:
        # Log the unexpected error
        logger.error(
            f"Unexpected payment error: {str(exc)}",
            exc_info=True
        )
        
        return {
            "success": False,
            "error": {
                "code": "INTERNAL_PAYMENT_ERROR",
                "message": "An unexpected error occurred while processing the payment",
                "timestamp": datetime.now().isoformat()
            },
            "status_code": HTTPStatus.INTERNAL_SERVER_ERROR
        }

def log_payment_error(error_message: str, 
                     payment_id: Optional[str] = None,
                     exc: Optional[Exception] = None, 
                     level: str = "error", 
                     **kwargs) -> None:
    """
    Log a payment error with consistent formatting

    Args:
        error_message: The error message to log
        payment_id: The payment ID related to the error
        exc: The exception that occurred (if any)
        level: The log level to use (debug, info, warning, error, critical)
        **kwargs: Additional context information to include in the log
    
    AI-Metadata:
        purpose: Standardized error logging
        criticality: medium
    """
    log_data = {
        "message": error_message,
        "timestamp": datetime.now().isoformat(),
        **kwargs
    }
    
    if payment_id:
        log_data["payment_id"] = payment_id
    
    if exc:
        log_data["exception"] = str(exc)
        log_data["traceback"] = traceback.format_exc()
    
    log_fn = getattr(logger, level.lower())
    log_fn(error_message, extra={"log_data": log_data})
