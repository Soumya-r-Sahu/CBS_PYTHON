"""
Test script for the centralized utilities.

This script demonstrates and tests the functionality of the centralized utilities.
It serves as both a test and an example of how to use the utilities.
"""

import logging
import json
import sys
from pathlib import Path
from typing import Dict, Any
from http import HTTPStatus

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import centralized utilities
try:
    from utils import (
        # Validators
        validate_account_number, validate_amount, validate_date, validate_email,
        validate_mobile_number, validate_ifsc_code, validate_card_number,
        
        # Error handling
        CBSError, ValidationError, DatabaseError, PaymentError,
        handle_exception
    )
    logger.info("Successfully imported centralized utilities")
except ImportError as e:
    logger.error(f"Error importing centralized utilities: {e}")
    raise

def test_validators():
    """Test the centralized validators."""
    logger.info("Testing centralized validators...")
    
    # Test account number validation
    test_cases = [
        {"validator": "Account Number", "input": "1234567890", "expected": True},
        {"validator": "Account Number", "input": "12345", "expected": False},
        {"validator": "Account Number", "input": "abcdefghij", "expected": False},
        
        {"validator": "Amount", "input": "1000.50", "expected": True},
        {"validator": "Amount", "input": "-100", "expected": False},
        {"validator": "Amount", "input": "abc", "expected": False},
        
        {"validator": "Email", "input": "test@example.com", "expected": True},
        {"validator": "Email", "input": "test.example.com", "expected": False},
        {"validator": "Email", "input": "", "expected": False},
        
        {"validator": "IFSC Code", "input": "ABCD0123456", "expected": True},
        {"validator": "IFSC Code", "input": "ABCD123456", "expected": False},
        {"validator": "IFSC Code", "input": "", "expected": False},
        
        {"validator": "Card Number", "input": "4111111111111111", "expected": True},
        {"validator": "Card Number", "input": "4111111111111112", "expected": False},
        {"validator": "Card Number", "input": "411111", "expected": False},
    ]
    
    # Run test cases
    for test in test_cases:
        validator_name = test["validator"]
        test_input = test["input"]
        expected = test["expected"]
        
        if validator_name == "Account Number":
            result, error_msg = validate_account_number(test_input)
        elif validator_name == "Amount":
            result, error_msg, _ = validate_amount(test_input)
        elif validator_name == "Email":
            result, error_msg = validate_email(test_input)
        elif validator_name == "IFSC Code":
            result, error_msg = validate_ifsc_code(test_input)
        elif validator_name == "Card Number":
            result, error_msg = validate_card_number(test_input)
        else:
            logger.warning(f"Unknown validator: {validator_name}")
            continue
        
        if result == expected:
            logger.info(f"✅ {validator_name} validation passed for input '{test_input}'")
            if not result:
                logger.info(f"   Error message: {error_msg}")
        else:
            logger.error(f"❌ {validator_name} validation failed for input '{test_input}'")
            logger.error(f"   Expected: {expected}, Got: {result}")
            if not result:
                logger.error(f"   Error message: {error_msg}")

def test_error_handling():
    """Test the centralized error handling."""
    logger.info("Testing centralized error handling...")
    
    # Test base error
    try:
        raise CBSError(
            message="Test error",
            error_code="TEST_ERROR",
            status_code=HTTPStatus.BAD_REQUEST,
            context={"test": "context"},
            details="Detailed error information"
        )
    except CBSError as e:
        logger.info(f"✅ CBSError raised successfully: {e.message}")
        logger.info(f"   Error dict: {json.dumps(e.to_dict(), indent=2)}")
    
    # Test validation error
    try:
        raise ValidationError(
            message="Invalid input",
            field="test_field",
            error_code="VALIDATION_ERROR",
            status_code=HTTPStatus.BAD_REQUEST
        )
    except ValidationError as e:
        logger.info(f"✅ ValidationError raised successfully: {e.message}")
        logger.info(f"   Error dict: {json.dumps(e.to_dict(), indent=2)}")
    
    # Test payment error
    try:
        raise PaymentError(
            message="Payment failed",
            payment_id="12345",
            error_code="PAYMENT_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR
        )
    except PaymentError as e:
        logger.info(f"✅ PaymentError raised successfully: {e.message}")
        logger.info(f"   Error dict: {json.dumps(e.to_dict(), indent=2)}")
    
    # Test exception handler
    @handle_exception
    def test_function():
        raise ValueError("Test value error")
    
    try:
        test_function()
    except CBSError as e:
        logger.info(f"✅ handle_exception decorator worked: {e.message}")
        logger.info(f"   Original error converted to CBSError")

def main():
    """Run the tests."""
    logger.info("Starting centralized utilities test...")
    
    try:
        # Test validators
        test_validators()
        
        # Test error handling
        test_error_handling()
        
        logger.info("All tests completed successfully!")
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        raise

if __name__ == "__main__":
    main()
