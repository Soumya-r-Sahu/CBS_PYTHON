"""
NEFT Exceptions - Core Banking System

This module defines custom exceptions for the NEFT payment system.
"""


class NEFTException(Exception):
    """Base exception for all NEFT-related errors."""
    pass


class NEFTValidationError(NEFTException):
    """Exception raised when NEFT transaction data is invalid."""
    pass


class NEFTAccountError(NEFTException):
    """Exception raised for account-related issues."""
    pass


class NEFTLimitExceeded(NEFTException):
    """Exception raised when transaction exceeds permitted limits."""
    pass


class NEFTConnectionError(NEFTException):
    """Exception raised when connection to NEFT system fails."""
    pass


class NEFTTimeoutError(NEFTException):
    """Exception raised when NEFT request times out."""
    pass


class NEFTProcessingError(NEFTException):
    """Exception raised during NEFT transaction processing."""
    pass


class NEFTReturnedError(NEFTException):
    """Exception raised when NEFT transaction is returned by beneficiary bank."""
    def __init__(self, message, return_code=None, return_reason=None):
        self.return_code = return_code
        self.return_reason = return_reason
        super().__init__(message)
