"""
Validator Migration Adapter for CBS_PYTHON

This module provides adapters to help migrate from the old validator approach
to the new refactored validators gradually, without breaking existing code.
"""

from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from decimal import Decimal

# Import old validator functions
from utils.validators import (
    validate_account_number,
    validate_amount,
    validate_ifsc_code,
    validate_card_number,
    validate_payment_reference,
    validate_email,
    validate_mobile_number
)

# Import new validators
from utils.common.refactored_validators import (
    Validator,
    PatternValidator,
    RangeValidator,
    ACCOUNT_NUMBER_VALIDATOR,
    CARD_NUMBER_VALIDATOR,
    IFSC_CODE_VALIDATOR,
    EMAIL_VALIDATOR,
    MOBILE_NUMBER_VALIDATOR
)


class LegacyValidatorAdapter:
    """
    Adapter to use new validators with the legacy function signature.
    
    This allows gradual migration from the old validation functions to the
    new validator classes without breaking existing code.
    """
    
    @staticmethod
    def adapt_account_number(account_number: str) -> Tuple[bool, Optional[str]]:
        """
        Adapt the account number validator to match legacy signature.
        
        Args:
            account_number: The account number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return ACCOUNT_NUMBER_VALIDATOR.validate(account_number)
    
    @staticmethod
    def adapt_amount(
        amount: Union[float, str, Decimal],
        min_limit: float = 0.01,
        max_limit: float = 10000000.0
    ) -> Tuple[bool, Optional[str], float]:
        """
        Adapt the amount validator to match legacy signature.
        
        Args:
            amount: The amount to validate
            min_limit: The minimum allowed amount
            max_limit: The maximum allowed amount
            
        Returns:
            Tuple of (is_valid, error_message, normalized_amount)
        """
        try:
            # Convert to float if it's a string or Decimal
            if isinstance(amount, str):
                # Remove commas and other formatting
                clean_amount = amount.replace(',', '')
                normalized_amount = float(clean_amount)
            elif isinstance(amount, Decimal):
                normalized_amount = float(amount)
            else:
                normalized_amount = float(amount)
            
            # Validate using the new validator
            validator = RangeValidator(min_value=min_limit, max_value=max_limit)
            is_valid, error = validator.validate(normalized_amount)
            
            return is_valid, error, normalized_amount
        except (ValueError, TypeError):
            return False, "Invalid amount format", 0.0
    
    @staticmethod
    def adapt_ifsc_code(ifsc_code: str) -> Tuple[bool, Optional[str]]:
        """
        Adapt the IFSC code validator to match legacy signature.
        
        Args:
            ifsc_code: The IFSC code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return IFSC_CODE_VALIDATOR.validate(ifsc_code)
    
    @staticmethod
    def adapt_card_number(card_number: str) -> Tuple[bool, Optional[str]]:
        """
        Adapt the card number validator to match legacy signature.
        
        Args:
            card_number: The card number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return CARD_NUMBER_VALIDATOR.validate(card_number)
    
    @staticmethod
    def adapt_email(email: str) -> Tuple[bool, Optional[str]]:
        """
        Adapt the email validator to match legacy signature.
        
        Args:
            email: The email to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return EMAIL_VALIDATOR.validate(email)
    
    @staticmethod
    def adapt_mobile_number(mobile: str) -> Tuple[bool, Optional[str]]:
        """
        Adapt the mobile number validator to match legacy signature.
        
        Args:
            mobile: The mobile number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return MOBILE_NUMBER_VALIDATOR.validate(mobile)


class ModuleAdapters:
    """
    Collection of module-specific adapters to help with migration.
    
    This class demonstrates how to adapt validators for specific
    modules or use cases in the codebase.
    """
    
    class Payments:
        """Adapters for payments module"""
        
        @staticmethod
        def validate_transaction(transaction_data: Dict[str, Any]) -> List[Tuple[str, str]]:
            """
            Validate payment transaction data.
            
            Args:
                transaction_data: Transaction data dictionary
                
            Returns:
                List of (field_name, error_message) tuples for invalid fields
            """
            errors = []
            
            # Validate account number
            if "account_number" in transaction_data:
                is_valid, error = ACCOUNT_NUMBER_VALIDATOR.validate(transaction_data["account_number"])
                if not is_valid:
                    errors.append(("account_number", error))
            
            # Validate amount
            if "amount" in transaction_data:
                amount_validator = RangeValidator(min_value=1.0, max_value=1000000.0)
                is_valid, error = amount_validator.validate(transaction_data["amount"])
                if not is_valid:
                    errors.append(("amount", error))
            
            # Validate reference
            if "reference" in transaction_data:
                reference_validator = PatternValidator(
                    pattern=r'^[A-Za-z0-9-]{6,30}$',
                    error_message="Invalid payment reference format"
                )
                is_valid, error = reference_validator.validate(transaction_data["reference"])
                if not is_valid:
                    errors.append(("reference", error))
            
            return errors
    
    class Customer:
        """Adapters for customer module"""
        
        @staticmethod
        def validate_customer_data(customer_data: Dict[str, Any]) -> List[Tuple[str, str]]:
            """
            Validate customer data.
            
            Args:
                customer_data: Customer data dictionary
                
            Returns:
                List of (field_name, error_message) tuples for invalid fields
            """
            errors = []
            
            # Validate email
            if "email" in customer_data:
                is_valid, error = EMAIL_VALIDATOR.validate(customer_data["email"])
                if not is_valid:
                    errors.append(("email", error))
            
            # Validate mobile number
            if "mobile" in customer_data:
                is_valid, error = MOBILE_NUMBER_VALIDATOR.validate(customer_data["mobile"])
                if not is_valid:
                    errors.append(("mobile", error))
            
            return errors
