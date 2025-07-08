"""
RTGS Payment Validators - Core Banking System

This module provides validation functions for RTGS payments.
"""
import re
import logging
from typing import Dict, Any
from datetime import datetime, time

from ..models.rtgs_model import RTGSTransaction, RTGSPaymentDetails
from ..exceptions.rtgs_exceptions import (
    RTGSValidationError,
    RTGSLimitExceeded,
    RTGSAmountBelowMinimum,
    RTGSInvalidAccount,
    RTGSInvalidIFSC
)
from ..config.rtgs_config import rtgs_config

# Configure logger
logger = logging.getLogger(__name__)


class RTGSValidator:
    """Validator for RTGS payments."""
    
    def __init__(self):
        """Initialize validator with configuration."""
        self.minimum_amount = rtgs_config.get("minimum_amount", 200000.0)
        self.maximum_amount = rtgs_config.get("maximum_amount", 100000000.0)
        self.daily_limit = rtgs_config.get("daily_limit_per_customer", 50000000.0)
    
    def validate_transaction(self, transaction: RTGSTransaction) -> bool:
        """
        Validate a complete RTGS transaction.
        
        Args:
            transaction: RTGS transaction to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            RTGSValidationError: If validation fails
        """
        payment_details = transaction.payment_details
        
        # Validate account numbers
        self.validate_account_number(payment_details.sender_account_number)
        self.validate_account_number(payment_details.beneficiary_account_number)
        
        # Validate IFSC codes
        self.validate_ifsc_code(payment_details.sender_ifsc_code)
        self.validate_ifsc_code(payment_details.beneficiary_ifsc_code)
        
        # Validate amount
        self.validate_amount(payment_details.amount)
        
        # Validate account types
        self.validate_account_type(payment_details.sender_account_type)
        self.validate_account_type(payment_details.beneficiary_account_type)
        
        # Validate names
        if not payment_details.sender_name or len(payment_details.sender_name) < 2:
            raise RTGSValidationError("Invalid sender name")
            
        if not payment_details.beneficiary_name or len(payment_details.beneficiary_name) < 2:
            raise RTGSValidationError("Invalid beneficiary name")
        
        # Validate purpose code if provided
        if payment_details.purpose_code:
            self.validate_purpose_code(payment_details.purpose_code)
        
        logger.debug(f"RTGS transaction validated: {transaction.transaction_id}")
        return True
    
    def validate_account_number(self, account_number: str) -> bool:
        """
        Validate account number.
        
        Args:
            account_number: Account number to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            RTGSInvalidAccount: If account number is invalid
        """
        # Basic validation: non-empty, alphanumeric, reasonable length
        if not account_number:
            raise RTGSInvalidAccount("Account number is required")
            
        if len(account_number) < 6 or len(account_number) > 22:
            raise RTGSInvalidAccount(f"Account number length invalid: {len(account_number)}")
            
        if not account_number.isalnum():
            raise RTGSInvalidAccount("Account number should contain only letters and numbers")
        
        return True
    
    def validate_ifsc_code(self, ifsc_code: str) -> bool:
        """
        Validate IFSC code.
        
        Args:
            ifsc_code: IFSC code to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            RTGSInvalidIFSC: If IFSC code is invalid
        """
        # IFSC code format: 4 letters (bank code) + 0 + 6 alphanumeric chars (branch code)
        ifsc_pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
        
        if not ifsc_code:
            raise RTGSInvalidIFSC("IFSC code is required")
            
        if not re.match(ifsc_pattern, ifsc_code):
            raise RTGSInvalidIFSC(f"Invalid IFSC code format: {ifsc_code}")
        
        return True
    
    def validate_amount(self, amount: float) -> bool:
        """
        Validate transaction amount.
        
        Args:
            amount: Transaction amount to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            RTGSValidationError: If amount is invalid
            RTGSAmountBelowMinimum: If amount is below minimum
            RTGSLimitExceeded: If amount exceeds maximum
        """
        if amount <= 0:
            raise RTGSValidationError("Amount must be positive")
            
        if amount < self.minimum_amount:
            raise RTGSAmountBelowMinimum(
                f"Amount ({amount}) below minimum RTGS amount ({self.minimum_amount})")
            
        if amount > self.maximum_amount:
            raise RTGSLimitExceeded(
                f"Amount ({amount}) exceeds maximum RTGS amount ({self.maximum_amount})")
        
        return True
    
    def validate_daily_limit(self, customer_id: str, amount: float) -> bool:
        """
        Validate customer's daily transaction limit.
        
        Args:
            customer_id: Customer ID
            amount: Transaction amount
            
        Returns:
            bool: True if within limit
            
        Raises:
            RTGSLimitExceeded: If daily limit would be exceeded
        """
        # TODO: Implement actual daily limit check from repository
        # For now, just validate against maximum
        if amount > self.daily_limit:
            raise RTGSLimitExceeded(f"Amount exceeds daily limit: {self.daily_limit}")
        
        return True
    
    def validate_account_type(self, account_type: str) -> bool:
        """
        Validate account type.
        
        Args:
            account_type: Account type to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            RTGSValidationError: If account type is invalid
        """
        valid_account_types = ["SAVINGS", "CURRENT", "CASH_CREDIT", "LOAN", "NRE", "NRO"]
        
        if not account_type:
            raise RTGSValidationError("Account type is required")
            
        if account_type not in valid_account_types:
            raise RTGSValidationError(f"Invalid account type: {account_type}")
        
        return True
    
    def validate_purpose_code(self, purpose_code: str) -> bool:
        """
        Validate purpose code as per RBI guidelines.
        
        Args:
            purpose_code: Purpose code to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            RTGSValidationError: If purpose code is invalid
        """
        # Purpose codes should follow RBI guidelines
        valid_purpose_codes = [
            "CORT", "INTC", "TREA", "CASH", "DIVI", "GOVT", "HEDG", "INTC",
            "LOAN", "PENS", "SALA", "SECU", "SSBE", "SUPP", "TAXS", "TRAD"
        ]
        
        if purpose_code and purpose_code not in valid_purpose_codes:
            raise RTGSValidationError(f"Invalid purpose code: {purpose_code}")
        
        return True
