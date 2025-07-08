"""
Common validation utilities for the Core Banking System.

This module consolidates validation functions from across the system
to reduce code duplication and promote consistency.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
import re
import logging

# Configure logger
logger = logging.getLogger(__name__)

def validate_amount(amount: Union[float, str], max_limit: float = 1000000.0) -> Tuple[bool, str, float]:
    """
    Validate a transaction amount.
    
    Args:
        amount: The amount to validate
        max_limit: The maximum allowed limit
        
    Returns:
        Tuple of (is_valid, error_message, normalized_amount)
    """
    try:
        # Convert to float if it's a string
        if isinstance(amount, str):
            amount = float(amount.replace(',', ''))
        
        # Check if amount is positive
        if amount <= 0:
            return False, "Amount must be greater than zero", 0.0
        
        # Check if amount exceeds maximum limit
        if amount > max_limit:
            return False, f"Amount exceeds maximum limit of {max_limit}", 0.0
        
        return True, "", amount
    except ValueError:
        return False, "Invalid amount format", 0.0

def validate_upi_id(upi_id: str) -> Tuple[bool, str]:
    """
    Validate a UPI ID format.
    
    Args:
        upi_id: The UPI ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not upi_id:
        return False, "UPI ID cannot be empty"
    
    # UPI ID pattern: username@provider
    pattern = r'^[a-zA-Z0-9\._-]+@[a-zA-Z][a-zA-Z0-9]+$'
    
    if not re.match(pattern, upi_id):
        return False, "Invalid UPI ID format. Format should be username@provider"
    
    return True, ""

def validate_mobile_number(mobile: str) -> Tuple[bool, str]:
    """
    Validate a mobile number format.
    
    Args:
        mobile: The mobile number to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not mobile:
        return False, "Mobile number cannot be empty"
    
    # Strip any spaces or special characters
    mobile = re.sub(r'[^0-9]', '', mobile)
    
    # Check if mobile number is 10 digits (without country code)
    if len(mobile) == 10:
        return True, ""
    
    # Check if mobile number is 12 digits with 91 country code
    if len(mobile) == 12 and mobile.startswith("91"):
        return True, ""
    
    return False, "Invalid mobile number format"

def validate_account_number(account_number: str) -> Tuple[bool, str]:
    """
    Validate an account number format.
    
    Args:
        account_number: The account number to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not account_number:
        return False, "Account number cannot be empty"
    
    # Strip any spaces or special characters
    account_number = re.sub(r'[^0-9]', '', account_number)
    
    # Check if account number is between 10 and 16 digits
    if len(account_number) < 10 or len(account_number) > 16:
        return False, "Account number should be between 10 and 16 digits"
    
    return True, ""

def validate_ifsc_code(ifsc_code: str) -> Tuple[bool, str]:
    """
    Validate an IFSC code format.
    
    Args:
        ifsc_code: The IFSC code to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not ifsc_code:
        return False, "IFSC code cannot be empty"
    
    # IFSC code pattern: 4 letters representing bank, followed by 0, followed by 6 alphanumeric characters
    pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
    
    # Convert to uppercase and remove spaces
    ifsc_code = ifsc_code.strip().upper().replace(" ", "")
    
    if not re.match(pattern, ifsc_code):
        return False, "Invalid IFSC code format"
    
    return True, ""
