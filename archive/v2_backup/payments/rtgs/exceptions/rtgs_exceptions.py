"""
RTGS Payment Exceptions - Core Banking System

This module defines exceptions for RTGS payments.
"""


class RTGSException(Exception):
    """Base exception class for RTGS payment processing."""
    def __init__(self, message: str = "RTGS payment processing error"):
        self.message = message
        super().__init__(self.message)


class RTGSValidationError(RTGSException):
    """Exception raised for validation errors in RTGS payments."""
    def __init__(self, message: str = "Invalid RTGS payment details"):
        super().__init__(message)


class RTGSLimitExceeded(RTGSValidationError):
    """Exception raised when payment limits are exceeded."""
    def __init__(self, message: str = "RTGS payment limit exceeded"):
        super().__init__(message)


class RTGSAmountBelowMinimum(RTGSValidationError):
    """Exception raised when payment amount is below the minimum threshold."""
    def __init__(self, message: str = "RTGS payment amount below minimum threshold"):
        super().__init__(message)


class RTGSInvalidAccount(RTGSValidationError):
    """Exception raised for invalid account details."""
    def __init__(self, message: str = "Invalid account details for RTGS payment"):
        super().__init__(message)


class RTGSInvalidIFSC(RTGSValidationError):
    """Exception raised for invalid IFSC code."""
    def __init__(self, message: str = "Invalid IFSC code for RTGS payment"):
        super().__init__(message)


class RTGSConnectionError(RTGSException):
    """Exception raised for connection issues with RTGS network."""
    def __init__(self, message: str = "Failed to connect to RTGS network"):
        super().__init__(message)


class RTGSTimeoutError(RTGSException):
    """Exception raised for timeouts in RTGS processing."""
    def __init__(self, message: str = "RTGS operation timed out"):
        super().__init__(message)


class RTGSProcessingError(RTGSException):
    """Exception raised for errors during RTGS processing."""
    def __init__(self, message: str = "Error processing RTGS payment"):
        super().__init__(message)


class RTGSTransactionNotFound(RTGSException):
    """Exception raised when a transaction cannot be found."""
    def __init__(self, transaction_id: str):
        message = f"RTGS transaction not found: {transaction_id}"
        super().__init__(message)
