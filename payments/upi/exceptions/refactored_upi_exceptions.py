"""
Refactored UPI Exceptions Module

This module provides UPI-specific exceptions using the unified error handling framework.
"""

from utils.unified_error_handling import (
    CBSException, ValidationException, BusinessRuleException, 
    NotFoundException, ErrorCodes
)
from http import HTTPStatus

# Define UPI-specific error codes
class UpiErrorCodes:
    """UPI-specific error codes"""
    UPI_VALIDATION_ERROR = "UPI_VALIDATION_ERROR"
    UPI_REGISTRATION_ERROR = "UPI_REGISTRATION_ERROR"
    UPI_ALREADY_REGISTERED = "UPI_ALREADY_REGISTERED"
    UPI_TRANSACTION_ERROR = "UPI_TRANSACTION_ERROR"
    UPI_AMOUNT_EXCEEDS_LIMIT = "UPI_AMOUNT_EXCEEDS_LIMIT"
    UPI_INVALID_ACCOUNT = "UPI_INVALID_ACCOUNT"
    UPI_INVALID_PIN = "UPI_INVALID_PIN"
    UPI_DAILY_LIMIT_EXCEEDED = "UPI_DAILY_LIMIT_EXCEEDED"
    UPI_INVALID_QR = "UPI_INVALID_QR"
    UPI_EXPIRED_SESSION = "UPI_EXPIRED_SESSION"
    UPI_NETWORK_ERROR = "UPI_NETWORK_ERROR"
    UPI_SERVICE_UNAVAILABLE = "UPI_SERVICE_UNAVAILABLE"


class UpiValidationException(ValidationException):
    """Exception for UPI validation errors"""
    
    def __init__(
        self, 
        message: str, 
        field: str = None,
        details: dict = None,
        error_code: str = UpiErrorCodes.UPI_VALIDATION_ERROR
    ):
        """
        Initialize UPI validation exception
        
        Args:
            message: Error message
            field: Field that failed validation
            details: Additional validation details
            error_code: Error code
        """
        super().__init__(
            message=message,
            field=field,
            details=details,
            error_code=error_code
        )


class UpiRegistrationException(BusinessRuleException):
    """Exception for UPI registration errors"""
    
    def __init__(
        self, 
        message: str, 
        details: dict = None,
        error_code: str = UpiErrorCodes.UPI_REGISTRATION_ERROR
    ):
        """
        Initialize UPI registration exception
        
        Args:
            message: Error message
            details: Additional registration details
            error_code: Error code
        """
        super().__init__(
            message=message,
            rule="upi_registration",
            error_code=error_code,
            details=details
        )


class UpiAlreadyRegisteredException(UpiRegistrationException):
    """Exception for already registered UPI ID"""
    
    def __init__(
        self, 
        upi_id: str,
        message: str = None,
        details: dict = None
    ):
        """
        Initialize UPI already registered exception
        
        Args:
            upi_id: UPI ID that is already registered
            message: Error message (optional)
            details: Additional details (optional)
        """
        message = message or f"UPI ID '{upi_id}' is already registered"
        details = details or {}
        details["upi_id"] = upi_id
        
        super().__init__(
            message=message,
            details=details,
            error_code=UpiErrorCodes.UPI_ALREADY_REGISTERED
        )


class UpiTransactionException(BusinessRuleException):
    """Exception for UPI transaction errors"""
    
    def __init__(
        self, 
        message: str, 
        transaction_id: str = None,
        details: dict = None,
        error_code: str = UpiErrorCodes.UPI_TRANSACTION_ERROR
    ):
        """
        Initialize UPI transaction exception
        
        Args:
            message: Error message
            transaction_id: ID of the transaction
            details: Additional transaction details
            error_code: Error code
        """
        details = details or {}
        if transaction_id:
            details["transaction_id"] = transaction_id
            
        super().__init__(
            message=message,
            rule="upi_transaction",
            error_code=error_code,
            details=details
        )


class UpiAmountExceedsLimitException(UpiTransactionException):
    """Exception for transaction amount exceeding limit"""
    
    def __init__(
        self, 
        amount: float, 
        limit: float,
        transaction_id: str = None,
        message: str = None,
        details: dict = None
    ):
        """
        Initialize amount exceeds limit exception
        
        Args:
            amount: Transaction amount
            limit: Maximum limit
            transaction_id: ID of the transaction
            message: Error message (optional)
            details: Additional details (optional)
        """
        message = message or f"Transaction amount {amount} exceeds the limit of {limit}"
        details = details or {}
        details.update({
            "amount": amount,
            "limit": limit
        })
        
        super().__init__(
            message=message,
            transaction_id=transaction_id,
            details=details,
            error_code=UpiErrorCodes.UPI_AMOUNT_EXCEEDS_LIMIT
        )


class UpiInvalidAccountException(UpiValidationException):
    """Exception for invalid account in UPI transaction"""
    
    def __init__(
        self, 
        account_id: str,
        message: str = None,
        details: dict = None
    ):
        """
        Initialize invalid account exception
        
        Args:
            account_id: ID of the invalid account
            message: Error message (optional)
            details: Additional details (optional)
        """
        message = message or f"Invalid account '{account_id}' for UPI transaction"
        details = details or {}
        details["account_id"] = account_id
        
        super().__init__(
            message=message,
            field="account_id",
            details=details,
            error_code=UpiErrorCodes.UPI_INVALID_ACCOUNT
        )


class UpiInvalidPinException(UpiValidationException):
    """Exception for invalid UPI PIN"""
    
    def __init__(
        self, 
        message: str = "Invalid UPI PIN provided",
        attempts_left: int = None,
        details: dict = None
    ):
        """
        Initialize invalid PIN exception
        
        Args:
            message: Error message
            attempts_left: Number of attempts left before lockout
            details: Additional details (optional)
        """
        details = details or {}
        if attempts_left is not None:
            details["attempts_left"] = attempts_left
            
        super().__init__(
            message=message,
            field="upi_pin",
            details=details,
            error_code=UpiErrorCodes.UPI_INVALID_PIN
        )


class UpiDailyLimitExceededException(UpiTransactionException):
    """Exception for exceeding daily transaction limit"""
    
    def __init__(
        self, 
        daily_total: float, 
        daily_limit: float,
        message: str = None,
        details: dict = None
    ):
        """
        Initialize daily limit exceeded exception
        
        Args:
            daily_total: Total transactions for the day
            daily_limit: Daily limit
            message: Error message (optional)
            details: Additional details (optional)
        """
        message = message or f"Daily transaction limit of {daily_limit} exceeded (current total: {daily_total})"
        details = details or {}
        details.update({
            "daily_total": daily_total,
            "daily_limit": daily_limit
        })
        
        super().__init__(
            message=message,
            details=details,
            error_code=UpiErrorCodes.UPI_DAILY_LIMIT_EXCEEDED
        )


class UpiServiceUnavailableException(CBSException):
    """Exception for UPI service unavailability"""
    
    def __init__(
        self, 
        message: str = "UPI service is currently unavailable",
        retry_after: int = None,
        details: dict = None
    ):
        """
        Initialize service unavailable exception
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retry
            details: Additional details (optional)
        """
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
            
        super().__init__(
            message=message,
            error_code=UpiErrorCodes.UPI_SERVICE_UNAVAILABLE,
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            details=details
        )
