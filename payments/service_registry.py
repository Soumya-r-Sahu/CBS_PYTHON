"""
Service Registration for Payments Module

This module handles the registration of payment services with the central
service registry, enabling other modules to discover and use payment services.
"""

import logging
from utils.lib.service_registry import ServiceRegistry

# Configure logger
logger = logging.getLogger(__name__)

def register_payment_services():
    """
    Register payment module services with the service registry
    
    Description:
        This function registers all payment-related services with the
        central service registry, making them available to other modules
        in a loosely coupled way.
    """
    registry = ServiceRegistry()
    
    # Import payment services
    from payments.processors.payment_processor import PaymentProcessor
    from payments.processors.card_processor import CardProcessor
    from payments.validators.payment_validator import validate_payment
    
    # Create service instances
    payment_processor = PaymentProcessor()
    card_processor = CardProcessor()
    
    # Register payment processor
    registry.register(
        "payment.processor", 
        payment_processor, 
        version="1.2.0",
        module_name="payments"
    )
    
    # Register card processor
    registry.register(
        "payment.card_processor", 
        card_processor, 
        version="1.1.0",
        module_name="payments"
    )
    
    # Register validation function
    registry.register(
        "payment.validate", 
        validate_payment,
        version="1.0.0", 
        module_name="payments"
    )
    
    # Register individual operations as services
    registry.register(
        "payment.process", 
        payment_processor.process_payment,
        version="1.2.0", 
        module_name="payments"
    )
    
    registry.register(
        "payment.refund", 
        payment_processor.process_refund,
        version="1.1.0", 
        module_name="payments"
    )
    
    # Register fallbacks for graceful degradation
    def payment_fallback(payment_data):
        """Fallback when payment module is unavailable"""
        logger.warning("Using payment fallback - payment module unavailable")
        return {
            "success": False,
            "message": "Payment processing temporarily unavailable",
            "error_code": "MODULE_UNAVAILABLE",
            "payment_info": {
                "amount": payment_data.get("amount", 0),
                "timestamp": payment_data.get("timestamp", "")
            }
        }
    
    def card_payment_fallback(card_data):
        """Fallback when card payment module is unavailable"""
        logger.warning("Using card payment fallback - payment module unavailable")
        return {
            "success": False,
            "message": "Card payment processing temporarily unavailable",
            "error_code": "MODULE_UNAVAILABLE"
        }
    
    def refund_fallback(refund_data):
        """Fallback when refund processing is unavailable"""
        logger.warning("Using refund fallback - payment module unavailable")
        return {
            "success": False,
            "message": "Refund processing temporarily unavailable",
            "error_code": "MODULE_UNAVAILABLE"
        }
    
    # Register the fallback implementations
    registry.register_fallback("payment.process", payment_fallback)
    registry.register_fallback("payment.card_processor", card_payment_fallback)
    registry.register_fallback("payment.refund", refund_fallback)
    
    logger.info("Payment services registered successfully")
    return True

# Register services when this module is imported
register_payment_services()
