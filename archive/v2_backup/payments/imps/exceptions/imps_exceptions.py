"""
IMPS Payment Exceptions - Core Banking System

This module defines exceptions for IMPS payments.
"""


class IMPSException(Exception):
    """Base exception class for IMPS payment processing."""
    def __init__(self, message: str = "IMPS payment processing error"):
        self.message = message
        super().__init__(self.message)


class IMPSValidationError(IMPSException):
    """Exception raised for validation errors in IMPS payments."""
    def __init__(self, message: str = "Invalid IMPS payment details"):
        super().__init__(message)


class IMPSLimitExceeded(IMPSValidationError):
    """Exception raised when payment limits are exceeded."""
    def __init__(self, message: str = "IMPS payment limit exceeded"):
        super().__init__(message)


class IMPSInvalidAccount(IMPSValidationError):
    """Exception raised for invalid account details."""
    def __init__(self, message: str = "Invalid account details for IMPS payment"):
        super().__init__(message)


class IMPSInvalidIFSC(IMPSValidationError):
    """Exception raised for invalid IFSC code."""
    def __init__(self, message: str = "Invalid IFSC code for IMPS payment"):
        super().__init__(message)


class IMPSInvalidMMID(IMPSValidationError):
    """Exception raised for invalid MMID (Mobile Money Identifier)."""
    def __init__(self, message: str = "Invalid MMID for IMPS payment"):
        super().__init__(message)


class IMPSInvalidMobileNumber(IMPSValidationError):
    """Exception raised for invalid mobile number."""
    def __init__(self, message: str = "Invalid mobile number for IMPS payment"):
        super().__init__(message)


class IMPSConnectionError(IMPSException):
    """Exception raised for connection issues with IMPS network (NPCI)."""
    def __init__(self, message: str = "Failed to connect to IMPS network"):
        super().__init__(message)


class IMPSTimeoutError(IMPSException):
    """Exception raised for timeouts in IMPS processing."""
    def __init__(self, message: str = "IMPS operation timed out"):
        super().__init__(message)


class IMPSProcessingError(IMPSException):
    """Exception raised for errors during IMPS processing."""
    def __init__(self, message: str = "Error processing IMPS payment"):
        super().__init__(message)


class IMPSTransactionNotFound(IMPSException):
    """Exception raised when a transaction cannot be found."""
    def __init__(self, transaction_id: str):
        message = f"IMPS transaction not found: {transaction_id}"
        super().__init__(message)


class IMPSInsufficientFundsError(IMPSException):
    """Exception raised when account has insufficient funds."""
    def __init__(self, message: str = "Insufficient funds for IMPS payment"):
        super().__init__(message)


class IMPSDuplicateTransactionError(IMPSException):
    """Exception raised for duplicate transactions."""
    def __init__(self, message: str = "Duplicate IMPS transaction detected"):
        super().__init__(message)
