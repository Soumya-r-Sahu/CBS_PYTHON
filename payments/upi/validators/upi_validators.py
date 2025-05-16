"""
UPI Payment Validators Module.

Validation functions for UPI payment processing.
"""
import re
import logging
from typing import Dict, Any, Union, Optional, List

from ..exceptions.upi_exceptions import UpiValidationError

# Set up logging
logger = logging.getLogger(__name__)


def validate_upi_id(upi_id: str) -> bool:
    """
    Validate UPI ID format.
    
    Args:
        upi_id: UPI ID to validate
        
    Returns:
        bool: True if UPI ID is valid
        
    Raises:
        UpiValidationError: If UPI ID is invalid
    """
    # UPI ID format: [username/mobile]@[psp/bank]
    # e.g. johndoe@okicici, 9876543210@ybl
    pattern = r'^[a-zA-Z0-9_.]{3,30}@[a-zA-Z]{3,10}$'
    
    if not re.match(pattern, upi_id):
        error_msg = f"Invalid UPI ID format: {upi_id}"
        logger.warning(error_msg)
        raise UpiValidationError(error_msg, details={"upi_id": upi_id})
    
    return True


def validate_amount(amount: Union[float, str], max_limit: float = 100000.0) -> float:
    """
    Validate transaction amount.
    
    Args:
        amount: Transaction amount
        max_limit: Maximum allowed amount
        
    Returns:
        float: Validated amount
        
    Raises:
        UpiValidationError: If amount is invalid
    """
    try:
        # Convert to float if string
        if isinstance(amount, str):
            amount = float(amount)
        
        # Check if amount is positive
        if amount <= 0:
            raise UpiValidationError(
                "Transaction amount must be positive",
                details={"amount": amount}
            )
        
        # Check if amount exceeds limit
        if amount > max_limit:
            raise UpiValidationError(
                f"Transaction amount exceeds maximum limit of {max_limit}",
                details={"amount": amount, "max_limit": max_limit}
            )
        
        return amount
        
    except ValueError:
        raise UpiValidationError(
            "Invalid amount format",
            details={"amount": amount}
        )


def validate_mobile_number(mobile: str) -> bool:
    """
    Validate mobile number format.
    
    Args:
        mobile: Mobile number to validate
        
    Returns:
        bool: True if mobile number is valid
        
    Raises:
        UpiValidationError: If mobile number is invalid
    """
    # Mobile number should be 10 digits without country code
    if not re.match(r'^[6-9]\d{9}$', mobile):
        error_msg = f"Invalid mobile number format: {mobile}"
        logger.warning(error_msg)
        raise UpiValidationError(error_msg, details={"mobile": mobile})
    
    return True


def validate_account_number(account_number: str) -> bool:
    """
    Validate account number format.
    
    Args:
        account_number: Account number to validate
        
    Returns:
        bool: True if account number is valid
        
    Raises:
        UpiValidationError: If account number is invalid
    """
    # Account numbers are typically 10-16 digits
    if not re.match(r'^\d{10,16}$', account_number):
        error_msg = f"Invalid account number format: {account_number}"
        logger.warning(error_msg)
        raise UpiValidationError(error_msg, details={"account_number": account_number})
    
    return True


def validate_registration_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate UPI registration data.
    
    Args:
        data: Registration data dictionary
        
    Returns:
        Dict: Validated registration data
        
    Raises:
        UpiValidationError: If registration data is invalid
    """
    required_fields = ['upi_id', 'account_number', 'mobile_number', 'name']
    
    # Check if all required fields are present
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise UpiValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            details={"missing_fields": missing_fields}
        )
    
    # Validate individual fields
    validate_upi_id(data['upi_id'])
    validate_account_number(data['account_number'])
    validate_mobile_number(data['mobile_number'])
    
    # Validate name (should be at least 3 characters)
    if len(data['name']) < 3:
        raise UpiValidationError(
            "Name should be at least 3 characters long",
            details={"name": data['name']}
        )
    
    return data


def validate_transaction_data(data: Dict[str, Any], max_limit: float = 100000.0) -> Dict[str, Any]:
    """
    Validate UPI transaction data.
    
    Args:
        data: Transaction data dictionary
        max_limit: Maximum allowed amount
        
    Returns:
        Dict: Validated transaction data
        
    Raises:
        UpiValidationError: If transaction data is invalid
    """
    required_fields = ['payer_upi_id', 'payee_upi_id', 'amount']
    
    # Check if all required fields are present
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise UpiValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            details={"missing_fields": missing_fields}
        )
    
    # Validate individual fields
    validate_upi_id(data['payer_upi_id'])
    validate_upi_id(data['payee_upi_id'])
    amount = validate_amount(data['amount'], max_limit)
    
    # Update validated amount
    data['amount'] = amount
    
    return data
