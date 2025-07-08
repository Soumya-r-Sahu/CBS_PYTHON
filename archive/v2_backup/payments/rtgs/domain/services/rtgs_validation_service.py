"""
RTGS transaction validation domain service.
This service handles business rules for validating RTGS transactions.
"""
from typing import Optional
from ..entities.rtgs_transaction import RTGSPaymentDetails


class RTGSValidationService:
    """Domain service for validating RTGS transactions."""
    
    def __init__(self, per_transaction_limit: float = 100000000.0):
        """
        Initialize the validation service.
        
        Args:
            per_transaction_limit: Maximum amount per transaction (default: 10 crores)
        """
        self.per_transaction_limit = per_transaction_limit
        self.min_transaction_limit = 200000.0  # 2 lakhs minimum for RTGS
    
    def validate_transaction_limits(self, amount: float) -> bool:
        """
        Validate if a transaction amount is within allowed limits.
        
        Args:
            amount: The transaction amount
            
        Returns:
            bool: True if valid, False otherwise
        """
        if amount <= 0:
            return False
            
        if amount < self.min_transaction_limit:
            return False
            
        if amount > self.per_transaction_limit:
            return False
            
        return True
    
    def validate_ifsc_code(self, ifsc_code: str) -> bool:
        """
        Validate IFSC code format.
        
        Args:
            ifsc_code: The IFSC code to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not ifsc_code or len(ifsc_code) != 11:
            return False
            
        # First 4 characters should be letters (bank code)
        if not ifsc_code[:4].isalpha() or not ifsc_code[:4].isupper():
            return False
            
        # 5th character should be 0 (reserved)
        if ifsc_code[4] != '0':
            return False
            
        # Last 6 characters should be alphanumeric (branch code)
        if not ifsc_code[5:].isalnum():
            return False
            
        return True
    
    def validate_payment_details(self, payment_details: RTGSPaymentDetails) -> Optional[str]:
        """
        Validate all payment details.
        
        Args:
            payment_details: The payment details to validate
            
        Returns:
            Optional[str]: Error message if invalid, None if valid
        """
        if not payment_details.sender_account_number or len(payment_details.sender_account_number) < 5:
            return "Invalid sender account number"
            
        if not self.validate_ifsc_code(payment_details.sender_ifsc_code):
            return "Invalid sender IFSC code"
            
        if not payment_details.beneficiary_account_number or len(payment_details.beneficiary_account_number) < 5:
            return "Invalid beneficiary account number"
            
        if not self.validate_ifsc_code(payment_details.beneficiary_ifsc_code):
            return "Invalid beneficiary IFSC code"
            
        if not self.validate_transaction_limits(payment_details.amount):
            if payment_details.amount < self.min_transaction_limit:
                return f"Transaction amount below minimum threshold of {self.min_transaction_limit} for RTGS"
            else:
                return f"Transaction amount exceeds limit of {self.per_transaction_limit}"
            
        if not payment_details.sender_name or not payment_details.beneficiary_name:
            return "Sender and beneficiary names are required"
            
        return None
