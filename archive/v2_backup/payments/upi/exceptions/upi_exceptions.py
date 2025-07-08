"""
UPI Payment Exceptions Module.

Custom exceptions for UPI payment processing.
"""


class UpiBaseException(Exception):
    """Base exception for UPI module"""
    def __init__(self, message="UPI operation failed", code=None, details=None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class UpiValidationError(UpiBaseException):
    """Exception raised for validation errors in UPI operations"""
    def __init__(self, message="Validation failed for UPI operation", code="VALIDATION_ERROR", details=None):
        super().__init__(message, code, details)


class UpiRegistrationError(UpiBaseException):
    """Exception raised for UPI registration errors"""
    def __init__(self, message="UPI registration failed", code="REGISTRATION_ERROR", details=None):
        super().__init__(message, code, details)


class UpiAlreadyRegisteredError(UpiRegistrationError):
    """Exception raised when UPI ID is already registered"""
    def __init__(self, upi_id, message=None, code="ALREADY_REGISTERED", details=None):
        message = message or f"UPI ID '{upi_id}' is already registered"
        details = details or {"upi_id": upi_id}
        super().__init__(message, code, details)


class UpiTransactionError(UpiBaseException):
    """Exception raised for UPI transaction errors"""
    def __init__(self, message="UPI transaction failed", code="TRANSACTION_ERROR", details=None):
        super().__init__(message, code, details)


class UpiAmountExceedsLimitError(UpiTransactionError):
    """Exception raised when transaction amount exceeds limit"""
    def __init__(self, amount, limit, message=None, code="AMOUNT_EXCEEDS_LIMIT", details=None):
        message = message or f"Transaction amount {amount} exceeds the limit of {limit}"
        details = details or {"amount": amount, "limit": limit}
        super().__init__(message, code, details)


class UpiInvalidAccountError(UpiTransactionError):
    """Exception raised when account is invalid or inactive"""
    def __init__(self, upi_id, message=None, code="INVALID_ACCOUNT", details=None):
        message = message or f"Invalid or inactive UPI account: {upi_id}"
        details = details or {"upi_id": upi_id}
        super().__init__(message, code, details)


class UpiInsufficientFundsError(UpiTransactionError):
    """Exception raised when there are insufficient funds for transaction"""
    def __init__(self, message="Insufficient funds for UPI transaction", code="INSUFFICIENT_FUNDS", details=None):
        super().__init__(message, code, details)


class UpiGatewayError(UpiTransactionError):
    """Exception raised for UPI gateway communication errors"""
    def __init__(self, message="UPI gateway communication error", code="GATEWAY_ERROR", details=None):
        super().__init__(message, code, details)


class UpiTimeoutError(UpiGatewayError):
    """Exception raised when UPI gateway times out"""
    def __init__(self, message="UPI gateway timeout", code="GATEWAY_TIMEOUT", details=None):
        super().__init__(message, code, details)


class UpiNotFoundError(UpiBaseException):
    """Exception raised when UPI resource is not found"""
    def __init__(self, resource_id, resource_type="transaction", message=None, code="NOT_FOUND", details=None):
        message = message or f"{resource_type.capitalize()} with ID '{resource_id}' not found"
        details = details or {
            "resource_id": resource_id,
            "resource_type": resource_type
        }
        super().__init__(message, code, details)
