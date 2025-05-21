"""
Centralized Validation Utilities for Core Banking System.

This module provides standardized validation utilities for all CBS modules.
It implements reusable validation functions for common data types and banking-specific data.

Tags: validation, data_verification
AI-Metadata:
    component_type: validator
    criticality: high
    purpose: data_validation
    impact_on_failure: data_integrity_errors
"""

import re
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from decimal import Decimal
import json
from colorama import init, Fore, Style
from pathlib import Path
import sys

# Initialize colorama for colored terminal output
init(autoreset=True)

# Use the centralized import manager
try:
    from utils.lib.packages import fix_path
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback to direct path manipulation if import manager is unavailable
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    parent_dir = str(Path(__file__).parent.parent)
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    print("Warning: Could not import centralized import manager, using direct sys.path modification")

# Configure logger
logger = logging.getLogger(__name__)

# Common validation patterns
ACCOUNT_NUMBER_PATTERN = r'^[0-9]{10,16}$'
CARD_NUMBER_PATTERN = r'^[0-9]{16}$'
PAYMENT_REFERENCE_PATTERN = r'^[A-Za-z0-9-]{6,30}$'
IFSC_CODE_PATTERN = r'^[A-Z]{4}0[A-Z0-9]{6}$'
UPI_ID_PATTERN = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$'
MOBILE_NUMBER_PATTERN = r'^[6-9][0-9]{9}$'  # Indian mobile number pattern
EMAIL_PATTERN = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
PAN_PATTERN = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'  # Indian PAN card pattern
AADHAAR_PATTERN = r'^[2-9][0-9]{11}$'  # Indian Aadhaar number pattern

def validate_account_number(account_number: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a bank account number.
    
    Args:
        account_number: The account number to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    AI-Metadata:
        validation_type: pattern
        business_context: account_identification
        criticality: high
    """
    if not account_number:
        return False, "Account number cannot be empty"
    
    # Remove spaces and hyphens
    account_number = account_number.replace(' ', '').replace('-', '')
    
    if not re.match(ACCOUNT_NUMBER_PATTERN, account_number):
        return False, "Invalid account number format"
    
    return True, None

def validate_amount(amount: Union[float, str, Decimal], 
                   min_limit: float = 0.01, 
                   max_limit: float = 10000000.0) -> Tuple[bool, Optional[str], float]:
    """
    Validate a monetary amount.
    
    Args:
        amount: The amount to validate
        min_limit: The minimum allowed amount
        max_limit: The maximum allowed amount
        
    Returns:
        Tuple of (is_valid, error_message, normalized_amount)
        
    AI-Metadata:
        validation_type: numeric
        business_context: financial_transaction
        criticality: high
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
        
        # Check if amount is within allowed range
        if normalized_amount < min_limit:
            return False, f"Amount must be at least {min_limit}", normalized_amount
        
        if normalized_amount > max_limit:
            return False, f"Amount exceeds maximum limit of {max_limit}", normalized_amount
        
        return True, None, normalized_amount
    
    except (ValueError, TypeError):
        return False, "Invalid amount format", 0.0

def validate_ifsc_code(ifsc_code: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an IFSC (Indian Financial System Code).
    
    Args:
        ifsc_code: The IFSC code to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    AI-Metadata:
        validation_type: pattern
        business_context: bank_branch_identification
        criticality: high
    """
    if not ifsc_code:
        return False, "IFSC code cannot be empty"
    
    # Convert to uppercase and remove spaces
    ifsc_code = ifsc_code.upper().replace(' ', '')
    
    if not re.match(IFSC_CODE_PATTERN, ifsc_code):
        return False, "Invalid IFSC code format"
    
    return True, None

def validate_card_number(card_number: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a credit/debit card number using Luhn algorithm.
    
    Args:
        card_number: The card number to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    AI-Metadata:
        validation_type: algorithm
        business_context: payment_card
        criticality: high
    """
    if not card_number:
        return False, "Card number cannot be empty"
    
    # Remove spaces and hyphens
    card_number = card_number.replace(' ', '').replace('-', '')
    
    if not re.match(CARD_NUMBER_PATTERN, card_number):
        return False, "Invalid card number format"
    
    # Apply Luhn algorithm (mod 10)
    digits = [int(d) for d in card_number]
    checksum = 0
    
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:  # Odd position (0-indexed from right)
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    
    if checksum % 10 != 0:
        return False, "Invalid card number (checksum failed)"
    
    return True, None

def validate_payment_reference(reference: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a payment reference number.
    
    Args:
        reference: The payment reference to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    AI-Metadata:
        validation_type: pattern
        business_context: transaction_identification
        criticality: medium
    """
    if not reference:
        return False, "Payment reference cannot be empty"
    
    if not re.match(PAYMENT_REFERENCE_PATTERN, reference):
        return False, "Invalid payment reference format"
    
    return True, None

def validate_date(date_str: str, 
                 format_str: str = "%Y-%m-%d", 
                 min_date: Optional[date] = None,
                 max_date: Optional[date] = None) -> Tuple[bool, Optional[str], Optional[date]]:
    """
    Validate a date string.
    
    Args:
        date_str: The date string to validate
        format_str: The expected date format
        min_date: The minimum allowed date (optional)
        max_date: The maximum allowed date (optional)
        
    Returns:
        Tuple of (is_valid, error_message, parsed_date)
        
    AI-Metadata:
        validation_type: date
        business_context: schedule_validation
        criticality: medium
    """
    if not date_str:
        return False, "Date cannot be empty", None
    
    try:
        parsed_date = datetime.strptime(date_str, format_str).date()
        
        if min_date and parsed_date < min_date:
            return False, f"Date must not be earlier than {min_date}", parsed_date
        
        if max_date and parsed_date > max_date:
            return False, f"Date must not be later than {max_date}", parsed_date
        
        return True, None, parsed_date
    
    except ValueError:
        return False, f"Invalid date format, expected {format_str}", None

def validate_mobile_number(mobile_number: str, country_code: str = "+91") -> Tuple[bool, Optional[str]]:
    """
    Validate a mobile number.
    
    Args:
        mobile_number: The mobile number to validate
        country_code: The country code to use (default: India +91)
        
    Returns:
        Tuple of (is_valid, error_message)
        
    AI-Metadata:
        validation_type: pattern
        business_context: customer_contact
        criticality: medium
    """
    if not mobile_number:
        return False, "Mobile number cannot be empty"
    
    # Remove spaces, hyphens, and country code
    mobile_number = mobile_number.replace(' ', '').replace('-', '')
    if mobile_number.startswith('+'):
        mobile_number = mobile_number[1:]  # Remove leading +
    if country_code.startswith('+'):
        country_code = country_code[1:]  # Remove leading +
    
    if mobile_number.startswith(country_code):
        mobile_number = mobile_number[len(country_code):]
    
    if not re.match(MOBILE_NUMBER_PATTERN, mobile_number):
        return False, "Invalid mobile number format"
    
    return True, None

def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an email address.
    
    Args:
        email: The email address to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    AI-Metadata:
        validation_type: pattern
        business_context: customer_contact
        criticality: medium
    """
    if not email:
        return False, "Email cannot be empty"
    
    if not re.match(EMAIL_PATTERN, email):
        return False, "Invalid email format"
    
    return True, None

def validate_pan(pan: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a PAN (Permanent Account Number - India).
    
    Args:
        pan: The PAN to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    AI-Metadata:
        validation_type: pattern
        business_context: customer_kyc
        criticality: high
    """
    if not pan:
        return False, "PAN cannot be empty"
    
    # Convert to uppercase and remove spaces
    pan = pan.upper().replace(' ', '')
    
    if not re.match(PAN_PATTERN, pan):
        return False, "Invalid PAN format"
    
    return True, None

def validate_aadhaar(aadhaar: str) -> Tuple[bool, Optional[str]]:
    """
    Validate an Aadhaar number (India).
    
    Args:
        aadhaar: The Aadhaar number to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    AI-Metadata:
        validation_type: pattern
        business_context: customer_kyc
        criticality: high
    """
    if not aadhaar:
        return False, "Aadhaar number cannot be empty"
    
    # Remove spaces and hyphens
    aadhaar = aadhaar.replace(' ', '').replace('-', '')
    
    if not re.match(AADHAAR_PATTERN, aadhaar):
        return False, "Invalid Aadhaar number format"
    
    return True, None

def validate_upi_id(upi_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a UPI ID.
    
    Args:
        upi_id: The UPI ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        
    AI-Metadata:
        validation_type: pattern
        business_context: payment_identification
        criticality: high
    """
    if not upi_id:
        return False, "UPI ID cannot be empty"
    
    if not re.match(UPI_ID_PATTERN, upi_id):
        return False, "Invalid UPI ID format"
    
    return True, None

def validate_input_length(input_str: str, 
                         min_length: int = 1, 
                         max_length: int = 255) -> Tuple[bool, Optional[str]]:
    """
    Validate the length of an input string.
    
    Args:
        input_str: The string to validate
        min_length: The minimum allowed length
        max_length: The maximum allowed length
        
    Returns:
        Tuple of (is_valid, error_message)
        
    AI-Metadata:
        validation_type: string
        business_context: general_input
        criticality: low
    """
    if input_str is None:
        return False, "Input cannot be None"
    
    if len(input_str) < min_length:
        return False, f"Input must be at least {min_length} characters"
    
    if len(input_str) > max_length:
        return False, f"Input cannot exceed {max_length} characters"
    
    return True, None

def validate_dictionary(data: Dict[str, Any], 
                       required_fields: List[str]) -> Tuple[bool, Optional[str]]:
    """
    Validate a dictionary has all required fields.
    
    Args:
        data: The dictionary to validate
        required_fields: List of required field names
        
    Returns:
        Tuple of (is_valid, error_message)
        
    AI-Metadata:
        validation_type: structure
        business_context: api_request
        criticality: medium
    """
    if not data:
        return False, "Data cannot be empty"
    
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, None

def validate_json_string(json_str: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate a JSON string.
    
    Args:
        json_str: The JSON string to validate
        
    Returns:
        Tuple of (is_valid, error_message, parsed_json)
        
    AI-Metadata:
        validation_type: format
        business_context: api_payload
        criticality: medium
    """
    if not json_str:
        return False, "JSON string cannot be empty", None
    
    try:
        parsed_json = json.loads(json_str)
        return True, None, parsed_json
    
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON format: {str(e)}", None

# Legacy compatibility functions
def is_valid_account_number(account_number):
    """Legacy compatibility function for validate_account_number"""
    result, _ = validate_account_number(str(account_number))
    return result

def is_valid_email(email):
    """Legacy compatibility function for validate_email"""
    result, _ = validate_email(email)
    return result

def is_valid_mobile(mobile):
    """Legacy compatibility function for validate_mobile_number"""
    result, _ = validate_mobile_number(mobile)
    return result

def is_valid_amount(amount):
    """Legacy compatibility function for validate_amount"""
    result, _, _ = validate_amount(amount)
    return result
