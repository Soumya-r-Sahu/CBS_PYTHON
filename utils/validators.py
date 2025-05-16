"""
Input Validation Utilities for Core Banking System.

This module provides validators for various data types used in the banking system.
"""

import re
import logging
from datetime import datetime
from colorama import init, Fore, Style
from pathlib import Path
import sys

# Initialize colorama
init(autoreset=True)

# Use the import manager if available
try:
    # Add app/lib to path temporarily to import the import_manager
    lib_path = str(Path(__file__).parent.parent / "app" / "lib")
    if lib_path not in sys.path:
        # Commented out direct sys.path modification
        # sys.path.insert(0, lib_path)
        from utils.lib.packages import fix_path
        fix_path()
        
    # Import and use the centralized import manager
    from utils.lib.packages import fix_path
    fix_path()
except ImportError:
    # Fallback to direct path manipulation
    parent_dir = str(Path(__file__).parent.parent)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    print("Warning: Could not import centralized import manager, using direct sys.path modification")

# Configure logger
logger = logging.getLogger(__name__)

def is_valid_account_number(account_number):
    """
    Validate account number format.
    
    Args:
        account_number: The account number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not account_number:
        return False
        
    # Account number should be 8-16 characters, alphanumeric
    pattern = r'^[A-Z0-9]{8,16}$'
    return bool(re.match(pattern, str(account_number)))

def is_valid_email(email):
    """
    Validate email format.
    
    Args:
        email: The email to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
        
    # Simple email pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, str(email)))

def is_valid_phone(phone):
    """
    Validate phone number format.
    
    Args:
        phone: The phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not phone:
        return False
        
    # Remove any spaces, dashes, or parentheses
    phone = re.sub(r'[\s\-()]', '', str(phone))
    
    # Check for 10-15 digit phone number
    pattern = r'^[0-9]{10,15}$'
    return bool(re.match(pattern, phone))

def is_valid_name(name):
    """
    Validate name format.
    
    Args:
        name: The name to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not name:
        return False
        
    # Name should be 2-50 characters, letters, spaces, hyphens, and apostrophes
    pattern = r'^[A-Za-z\s\-\']{2,50}$'
    return bool(re.match(pattern, str(name)))

def is_valid_date(date_str, format="%Y-%m-%d"):
    """
    Validate date format.
    
    Args:
        date_str: The date string to validate
        format: The expected date format
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not date_str:
        return False
        
    try:
        datetime.strptime(str(date_str), format)
        return True
    except ValueError:
        return False

def is_valid_card_number(card_number):
    """
    Validate credit/debit card number using Luhn algorithm.
    
    Args:
        card_number: The card number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not card_number:
        return False
        
    # Remove spaces and dashes
    card_number = re.sub(r'[\s\-]', '', str(card_number))
    
    # Check if all digits and proper length (13-19 digits)
    if not re.match(r'^[0-9]{13,19}$', card_number):
        return False
    
    # Luhn algorithm
    digits = [int(d) for d in card_number]
    checksum = 0
    odd_even = len(digits) % 2
    
    for i, digit in enumerate(digits):
        if ((i + odd_even) % 2) == 0:
            doubled = digit * 2
            checksum += doubled if doubled < 10 else doubled - 9
        else:
            checksum += digit
    
    return checksum % 10 == 0

def is_valid_cvv(cvv):
    """
    Validate CVV code.
    
    Args:
        cvv: The CVV to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not cvv:
        return False
        
    # CVV should be 3-4 digits
    pattern = r'^[0-9]{3,4}$'
    return bool(re.match(pattern, str(cvv)))

def is_valid_pin(pin):
    """
    Validate PIN code.
    
    Args:
        pin: The PIN to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not pin:
        return False
        
    # PIN should be 4-6 digits
    pattern = r'^[0-9]{4,6}$'
    return bool(re.match(pattern, str(pin)))

def is_valid_amount_range(amount, min_amount=0.01, max_amount=None):
    """
    Validate that the amount is within the specified range.
    
    Args:
        amount: The amount to validate
        min_amount: Minimum allowed amount (default: 0.01)
        max_amount: Maximum allowed amount (default: None, no upper limit)
        
    Returns:
        bool: True if valid, False otherwise
        
    Raises:
        ValueError: If the amount is not a valid number or outside the range
        TypeError: If the amount cannot be converted to float
    """
    try:
        amount = float(amount)
        
        if amount < min_amount:
            raise ValueError(f"Amount must be at least {min_amount}")
        
        if max_amount is not None and amount > max_amount:
            raise ValueError(f"Amount must not exceed {max_amount}")
        
        return True
    except ValueError as e:
        logger.warning(f"Invalid amount value: {e}")
        raise
    except TypeError as e:
        logger.warning(f"Invalid amount type: {e}")
        raise TypeError(f"Amount must be a number, got {type(amount).__name__}")

def validate_amount(amount):
    """
    Validate that the amount is a positive number.
    
    Args:
        amount: The amount to validate
        
    Returns:
        bool: True if valid, False otherwise
        
    Raises:
        ValueError: If the amount is not positive
        TypeError: If the amount cannot be converted to float
    """
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be greater than zero.")
        return True
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise
    except TypeError as e:
        logger.warning(f"Type error in validation: {e}")
        raise TypeError(f"Amount must be a number, got {type(amount).__name__}")

def is_valid_user_input(user_input, input_type):
    """
    Validates user input based on input type.
    
    Args:
        user_input: The user input to validate
        input_type: Type of input to validate ('email', 'phone', 'name', etc.)
        
    Returns:
        bool: True if input is valid, False otherwise
        
    Raises:
        ValueError: If the input_type is unrecognized or the validation fails with specific details
        TypeError: If the input is of incorrect type for the validation
    """
    try:
        if input_type == 'email':
            return is_valid_email(user_input)
        elif input_type == 'phone':
            return is_valid_phone(user_input)
        elif input_type == 'account_number':
            return is_valid_account_number(user_input)
        elif input_type == 'amount':
            return validate_amount(user_input)
        elif input_type == 'pin':
            return is_valid_pin(user_input)
        else:
            raise ValueError(f"Unrecognized input type: '{input_type}'")
    except ValueError as e:
        # Handle validation-specific errors
        logger.error(f"Validation error ({input_type}): {str(e)}")
        raise
    except TypeError as e:
        # Handle type errors
        logger.error(f"Type error in validation ({input_type}): {str(e)}")
        raise TypeError(f"Invalid type for {input_type} validation: {str(e)}")
    except Exception as e:
        # Handle any other unexpected errors
        logger.error(f"Unexpected error in validation ({input_type}): {str(e)}")
        raise ValueError(f"Validation failed for {input_type}: {str(e)}")
