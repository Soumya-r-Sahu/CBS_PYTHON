"""
Exceptions related to external payment gateways.
"""


class GatewayError(Exception):
    """Base class for all gateway-related exceptions."""
    pass


class GatewayConnectionError(GatewayError):
    """Raised when there's an error connecting to the gateway."""
    pass


class GatewayTimeoutError(GatewayError):
    """Raised when the gateway doesn't respond in time."""
    pass


class GatewayAuthenticationError(GatewayError):
    """Raised when authentication with the gateway fails."""
    pass


class GatewayValidationError(GatewayError):
    """Raised when the gateway rejects the request due to validation errors."""
    pass


class GatewayProcessingError(GatewayError):
    """Raised when the gateway fails to process the transaction."""
    pass
