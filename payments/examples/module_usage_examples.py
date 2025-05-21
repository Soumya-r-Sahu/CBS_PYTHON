"""
Payments Module Usage Examples

This module provides examples of how to use the payments module
for common payment processing scenarios.

Usage:
    python -m payments.examples.module_usage_examples

Tags: payments, examples, usage, tutorial
AI-Metadata:
    component_type: examples
    purpose: demonstration
    usage_pattern: reference
"""

import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the payments module
try:
    from payments.module_interface import get_module_instance
except ImportError:
    logger.error("Failed to import payments module. Make sure it's in your Python path.")
    raise

def example_basic_payment():
    """
    Example of processing a basic payment transfer
    """
    logger.info("--- Basic Payment Example ---")
    
    # Get payments module instance
    payments = get_module_instance()
    
    # Create payment data
    payment_data = {
        "amount": 100.00,
        "currency": "USD",
        "source_account": "ACC123456",
        "destination_account": "ACC789012",
        "type": "transfer",
        "description": "Basic payment example",
        "reference_id": f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": datetime.now().isoformat()
    }
    
    # Validate the payment data first
    logger.info("Validating payment data...")
    validation_result = payments.validate_payment(payment_data)
    
    if not validation_result.get("valid", False):
        logger.error(f"Payment validation failed: {validation_result.get('errors', [])}")
        return False
    
    # Process the payment
    logger.info("Processing payment...")
    result = payments.process_payment(payment_data)
    
    # Check the result
    if result.get("success", False):
        logger.info(f"Payment successful. Transaction ID: {result.get('transaction_id')}")
        logger.info(f"Confirmation ID: {result.get('confirmation_id')}")
        return True
    else:
        logger.error(f"Payment failed: {result.get('error', 'Unknown error')}")
        return False

def example_card_payment():
    """
    Example of processing a card payment
    """
    logger.info("--- Card Payment Example ---")
    
    # Get payments module instance
    payments = get_module_instance()
    
    # Create card payment data
    card_payment_data = {
        "amount": 75.50,
        "currency": "USD",
        "type": "card",
        "card_number": "4111111111111111",  # Test card number
        "expiry_month": 12,
        "expiry_year": 2025,
        "cvv": "123",
        "cardholder_name": "John Doe",
        "description": "Card payment example",
        "reference_id": f"CARD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": datetime.now().isoformat()
    }
    
    # Process the card payment
    logger.info("Processing card payment...")
    result = payments.process_payment(card_payment_data)
    
    # Check the result
    if result.get("success", False):
        logger.info(f"Card payment successful. Transaction ID: {result.get('transaction_id')}")
        logger.info(f"Authorization code: {result.get('card_auth_code')}")
        return True
    else:
        logger.error(f"Card payment failed: {result.get('error', 'Unknown error')}")
        return False

def example_payment_with_insufficient_funds():
    """
    Example showing handling of insufficient funds error
    """
    logger.info("--- Insufficient Funds Example ---")
    
    # Get payments module instance
    payments = get_module_instance()
    
    # Create payment data with amount that will exceed available balance
    payment_data = {
        "amount": 1000000.00,  # Very high amount to trigger insufficient funds
        "currency": "USD",
        "source_account": "ACC123456",
        "destination_account": "ACC789012",
        "type": "transfer",
        "description": "Insufficient funds example",
        "reference_id": f"INSF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": datetime.now().isoformat()
    }
    
    # Process the payment (expecting failure)
    logger.info("Processing payment with insufficient funds...")
    result = payments.process_payment(payment_data)
    
    # Check the result
    if not result.get("success", False):
        error = result.get("error", {})
        if error.get("code") == "INSUFFICIENT_FUNDS":
            logger.info("Payment correctly failed due to insufficient funds.")
            logger.info(f"Error details: {error.get('details', {})}")
            return True
        else:
            logger.warning(f"Payment failed but for unexpected reason: {error.get('message', 'Unknown error')}")
            return False
    else:
        logger.error("Payment unexpectedly succeeded when it should have failed!")
        return False

def example_refund_processing():
    """
    Example of processing a refund
    """
    logger.info("--- Refund Processing Example ---")
    
    # Get payments module instance
    payments = get_module_instance()
    
    # First, make a payment to refund
    payment_data = {
        "amount": 50.00,
        "currency": "USD",
        "source_account": "ACC123456",
        "destination_account": "ACC789012",
        "type": "transfer",
        "description": "Payment for refund example",
        "reference_id": f"REFPAY-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info("Making initial payment...")
    payment_result = payments.process_payment(payment_data)
    
    if not payment_result.get("success", False):
        logger.error(f"Initial payment failed: {payment_result.get('error', 'Unknown error')}")
        return False
    
    transaction_id = payment_result.get("transaction_id")
    logger.info(f"Payment successful. Transaction ID: {transaction_id}")
    
    # Create refund data
    refund_data = {
        "amount": 50.00,
        "currency": "USD",
        "original_transaction_id": transaction_id,
        "reason": "Customer requested refund",
        "reference_id": f"REF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": datetime.now().isoformat()
    }
    
    # Process the refund
    logger.info("Processing refund...")
    refund_result = payments.process_refund(refund_data)
    
    # Check the result
    if refund_result.get("success", False):
        logger.info(f"Refund successful. Refund ID: {refund_result.get('refund_id')}")
        return True
    else:
        logger.error(f"Refund failed: {refund_result.get('error', 'Unknown error')}")
        return False

def example_mobile_payment():
    """
    Example of processing a mobile payment
    """
    logger.info("--- Mobile Payment Example ---")
    
    # Get payments module instance
    payments = get_module_instance()
    
    # Create mobile payment data
    mobile_payment_data = {
        "amount": 25.00,
        "currency": "USD",
        "type": "mobile",
        "mobile_number": "+15551234567",
        "payment_method": "mobile_wallet",
        "wallet_provider": "PayApp",
        "description": "Mobile payment example",
        "reference_id": f"MOB-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "timestamp": datetime.now().isoformat()
    }
    
    # Process the mobile payment
    logger.info("Processing mobile payment...")
    result = payments.process_payment(mobile_payment_data)
    
    # Check the result
    if result.get("success", False):
        logger.info(f"Mobile payment successful. Transaction ID: {result.get('transaction_id')}")
        return True
    else:
        logger.error(f"Mobile payment failed: {result.get('error', 'Unknown error')}")
        return False

def run_examples():
    """Run all payment examples"""
    example_results = []
    
    # Run all examples and collect results
    example_results.append(("Basic Payment", example_basic_payment()))
    example_results.append(("Card Payment", example_card_payment()))
    example_results.append(("Insufficient Funds", example_payment_with_insufficient_funds()))
    example_results.append(("Refund Processing", example_refund_processing()))
    example_results.append(("Mobile Payment", example_mobile_payment()))
    
    # Print summary
    logger.info("\n--- Examples Summary ---")
    for name, result in example_results:
        status = "SUCCESS" if result else "FAILURE"
        logger.info(f"{name}: {status}")

if __name__ == "__main__":
    # Run all examples
    run_examples()
