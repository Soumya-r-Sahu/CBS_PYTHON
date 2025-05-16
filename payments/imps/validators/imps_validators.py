"""
IMPS Payment Validators - Core Banking System

This module provides validation functions for IMPS payments.
"""
import re
import logging
from typing import Dict, Any, Optional

from ..models.imps_model import IMPSTransaction, IMPSPaymentDetails, IMPSType
from ..exceptions.imps_exceptions import (
    IMPSValidationError,
    IMPSLimitExceeded,
    IMPSInvalidAccount,
    IMPSInvalidIFSC,
    IMPSInvalidMMID,
    IMPSInvalidMobileNumber
)
from ..config.imps_config import imps_config

# Configure logger
logger = logging.getLogger(__name__)


class IMPSValidator:
    """Validator for IMPS payments."""
    
    def __init__(self):
        """Initialize validator with configuration."""
        self.minimum_amount = imps_config.get("minimum_amount", 1.0)
        self.maximum_amount = imps_config.get("maximum_amount", 500000.0)
        self.daily_limit = imps_config.get("daily_limit_per_customer", 1000000.0)
    
    def validate_transaction(self, transaction: IMPSTransaction) -> bool:
        """
        Validate a complete IMPS transaction.
        
        Args:
            transaction: IMPS transaction to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            IMPSValidationError: If validation fails
        """
        payment_details = transaction.payment_details
        
        # Validate amount
        self.validate_amount(payment_details.amount)
        
        # Validate account numbers
        self.validate_account_number(payment_details.sender_account_number)
        self.validate_account_number(payment_details.beneficiary_account_number)
        
        # Validate IFSC codes
        self.validate_ifsc_code(payment_details.sender_ifsc_code)
        self.validate_ifsc_code(payment_details.beneficiary_ifsc_code)
        
        # Validate mobile numbers if provided
        if payment_details.sender_mobile_number:
            self.validate_mobile_number(payment_details.sender_mobile_number)
            
        if payment_details.beneficiary_mobile_number:
            self.validate_mobile_number(payment_details.beneficiary_mobile_number)
        
        # Validate MMID if provided
        if payment_details.sender_mmid:
            self.validate_mmid(payment_details.sender_mmid)
            
        if payment_details.beneficiary_mmid:
            self.validate_mmid(payment_details.beneficiary_mmid)
        
        # Validate names
        if not payment_details.sender_name or len(payment_details.sender_name) < 2:
            raise IMPSValidationError("Invalid sender name")
            
        if not payment_details.beneficiary_name or len(payment_details.beneficiary_name) < 2:
            raise IMPSValidationError("Invalid beneficiary name")
        
        # Validate transaction type specific fields
        if payment_details.imps_type == IMPSType.P2P:
            # For P2P, we need mobile and MMID
            if not payment_details.sender_mobile_number or not payment_details.sender_mmid:
                raise IMPSValidationError("Sender mobile number and MMID required for P2P transfers")
                
            if not payment_details.beneficiary_mobile_number or not payment_details.beneficiary_mmid:
                raise IMPSValidationError("Beneficiary mobile number and MMID required for P2P transfers")
        
        logger.debug(f"IMPS transaction validated: {transaction.transaction_id}")
        return True
    
    def validate_account_number(self, account_number: str) -> bool:
        """
        Validate account number.
        
        Args:
            account_number: Account number to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            IMPSInvalidAccount: If account number is invalid
        """
        # Basic validation: non-empty, alphanumeric, reasonable length
        if not account_number:
            raise IMPSInvalidAccount("Account number is required")
            
        if len(account_number) < 6 or len(account_number) > 22:
            raise IMPSInvalidAccount(f"Account number length invalid: {len(account_number)}")
            
        if not account_number.isalnum():
            raise IMPSInvalidAccount("Account number should contain only letters and numbers")
        
        return True
    
    def validate_ifsc_code(self, ifsc_code: str) -> bool:
        """
        Validate IFSC code.
        
        Args:
            ifsc_code: IFSC code to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            IMPSInvalidIFSC: If IFSC code is invalid
        """
        # IFSC code format: 4 letters (bank code) + 0 + 6 alphanumeric chars (branch code)
        ifsc_pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
        
        if not ifsc_code:
            raise IMPSInvalidIFSC("IFSC code is required")
            
        if not re.match(ifsc_pattern, ifsc_code):
            raise IMPSInvalidIFSC(f"Invalid IFSC code format: {ifsc_code}")
        
        return True
    
    def validate_amount(self, amount: float) -> bool:
        """
        Validate transaction amount.
        
        Args:
            amount: Transaction amount to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            IMPSValidationError: If amount is invalid
            IMPSLimitExceeded: If amount exceeds maximum
        """
        if amount <= 0:
            raise IMPSValidationError("Amount must be positive")
            
        if amount < self.minimum_amount:
            raise IMPSValidationError(
                f"Amount ({amount}) below minimum IMPS amount ({self.minimum_amount})")
            
        if amount > self.maximum_amount:
            raise IMPSLimitExceeded(
                f"Amount ({amount}) exceeds maximum IMPS amount ({self.maximum_amount})")
        
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
            IMPSLimitExceeded: If daily limit would be exceeded
        """
        # TODO: Implement actual daily limit check from repository
        # For now, just validate against maximum
        if amount > self.daily_limit:
            raise IMPSLimitExceeded(f"Amount exceeds daily limit: {self.daily_limit}")
        
        return True
    
    def validate_mobile_number(self, mobile_number: str) -> bool:
        """
        Validate mobile number.
        
        Args:
            mobile_number: Mobile number to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            IMPSInvalidMobileNumber: If mobile number is invalid
        """
        # Indian mobile number pattern (10 digits, optionally prefixed with +91 or 0)
        mobile_pattern = r'^(?:\+91|0)?[6-9]\d{9}$'
        
        if not mobile_number:
            raise IMPSInvalidMobileNumber("Mobile number is required")
            
        if not re.match(mobile_pattern, mobile_number):
            raise IMPSInvalidMobileNumber(f"Invalid mobile number format: {mobile_number}")
        
        return True
    
    def validate_mmid(self, mmid: str) -> bool:
        """
        Validate MMID (Mobile Money Identifier).
        
        Args:
            mmid: MMID to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            IMPSInvalidMMID: If MMID is invalid
        """
        # MMID is a 7-digit number
        mmid_pattern = r'^\d{7}$'
        
        if not mmid:
            raise IMPSInvalidMMID("MMID is required")
            
        if not re.match(mmid_pattern, mmid):
            raise IMPSInvalidMMID(f"Invalid MMID format: {mmid}")
        
        return True
