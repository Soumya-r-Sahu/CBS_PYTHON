"""
NEFT Validators - Core Banking System

This module provides validation functions for NEFT payments.
"""
import re
from datetime import datetime
import logging
from typing import Optional, Dict, Any

from ..models.neft_model import NEFTPaymentDetails, NEFTTransaction
from ..exceptions.neft_exceptions import NEFTValidationError, NEFTLimitExceeded
from ..config.neft_config import neft_config

# Configure logger
logger = logging.getLogger(__name__)


class NEFTValidator:
    """Validator for NEFT transactions."""
    
    @staticmethod
    def validate_account_number(account_number: str) -> None:
        """
        Validate bank account number.
        
        Args:
            account_number: Account number to validate
            
        Raises:
            NEFTValidationError: If account number is invalid
        """
        if not account_number:
            raise NEFTValidationError("Account number cannot be empty")
        
        # Remove spaces and check if it's only digits
        cleaned = account_number.replace(" ", "")
        if not cleaned.isdigit():
            raise NEFTValidationError("Account number must contain only digits")
        
        # Check length (typically between 9 to 18 digits in India)
        if len(cleaned) < 9 or len(cleaned) > 18:
            raise NEFTValidationError("Account number length must be between 9 and 18 digits")

    @staticmethod
    def validate_ifsc_code(ifsc_code: str) -> None:
        """
        Validate IFSC code.
        
        Args:
            ifsc_code: IFSC code to validate
            
        Raises:
            NEFTValidationError: If IFSC code is invalid
        """
        if not ifsc_code:
            raise NEFTValidationError("IFSC code cannot be empty")
        
        # IFSC code format: First 4 characters are alphabets (bank code),
        # 5th character is 0 (reserved), last 6 characters are alphanumeric (branch code)
        pattern = r"^[A-Z]{4}0[A-Z0-9]{6}$"
        if not re.match(pattern, ifsc_code):
            raise NEFTValidationError(
                "Invalid IFSC code format. Should be 11 characters: "
                "first 4 alphabets, then '0', then 6 alphanumeric characters"
            )

    @staticmethod
    def validate_amount(amount: float) -> None:
        """
        Validate transaction amount.
        
        Args:
            amount: Amount to validate
            
        Raises:
            NEFTValidationError: If amount is invalid
            NEFTLimitExceeded: If amount exceeds limits
        """
        if amount <= 0:
            raise NEFTValidationError("Amount must be greater than zero")
        
        min_amount = neft_config.get("min_transaction_amount", 1.0)
        max_amount = neft_config.get("max_transaction_amount", 2500000.0)
        
        if amount < min_amount:
            raise NEFTValidationError(f"Amount must be at least {min_amount}")
        
        if amount > max_amount:
            raise NEFTLimitExceeded(
                f"Transaction amount {amount} exceeds maximum allowed limit of {max_amount}"
            )

    @staticmethod
    def validate_transaction(transaction: NEFTTransaction) -> None:
        """
        Validate an entire NEFT transaction.
        
        Args:
            transaction: NEFT transaction to validate
            
        Raises:
            NEFTValidationError: If transaction is invalid
        """
        if not transaction.transaction_id:
            raise NEFTValidationError("Transaction ID cannot be empty")
        
        payment_details = transaction.payment_details
        
        # Validate sender details
        NEFTValidator.validate_account_number(payment_details.sender_account_number)
        NEFTValidator.validate_ifsc_code(payment_details.sender_ifsc_code)
        
        # Validate beneficiary details
        NEFTValidator.validate_account_number(payment_details.beneficiary_account_number)
        NEFTValidator.validate_ifsc_code(payment_details.beneficiary_ifsc_code)
        
        # Validate amount
        NEFTValidator.validate_amount(payment_details.amount)
        
        # Validate sender name
        if not payment_details.sender_name or len(payment_details.sender_name) < 2:
            raise NEFTValidationError("Sender name must be provided")
        
        # Validate beneficiary name
        if not payment_details.beneficiary_name or len(payment_details.beneficiary_name) < 2:
            raise NEFTValidationError("Beneficiary name must be provided")
        
        # Validate reference
        if not payment_details.payment_reference:
            raise NEFTValidationError("Payment reference must be provided")
        
        logger.debug(f"NEFT transaction validated successfully: {transaction.transaction_id}")


    @staticmethod
    def validate_daily_limit(customer_id: str, amount: float) -> bool:
        """
        Check if transaction exceeds customer's daily NEFT limit.
        
        Args:
            customer_id: Customer ID
            amount: Transaction amount
            
        Returns:
            bool: True if within limit, False otherwise
            
        Raises:
            NEFTLimitExceeded: If daily limit would be exceeded
        """
        # In a real implementation, this would check the database for
        # today's cumulative NEFT transactions for this customer
        
        # Placeholder implementation
        max_daily_limit = neft_config.get("max_daily_amount", 10000000.0)
        daily_usage = 0.0  # This would be fetched from database
        
        if daily_usage + amount > max_daily_limit:
            remaining = max_daily_limit - daily_usage
            raise NEFTLimitExceeded(
                f"Transaction of {amount} would exceed daily limit. "
                f"Remaining limit: {remaining}"
            )
        
        return True
