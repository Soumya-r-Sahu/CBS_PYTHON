"""
Validation Utilities for Digital Channels Module

This module provides standardized validation utilities for the digital channels module.
It implements reusable validation functions for common validations across all digital channel interfaces.

Usage:
    from digital_channels.utils.validators import validate_account_number, validate_customer_id

    # Validate account number
    is_valid, error = validate_account_number(account_number)
    if not is_valid:
        raise ValidationError(error)
"""

import re
import logging
from typing import Tuple, Union, Dict, Any, List, Optional
from datetime import datetime, date

# Configure logger
logger = logging.getLogger(__name__)

# Import module-specific error handling
from digital_channels.utils.error_handling import ValidationError

# Common validation patterns
ACCOUNT_NUMBER_PATTERN = r'^[0-9]{10,16}$'
CUSTOMER_ID_PATTERN = r'^[A-Za-z0-9]{8,12}$'
CARD_NUMBER_PATTERN = r'^[0-9]{16}$'
UUID_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PHONE_PATTERN = r'^[+]?[0-9]{10,15}$'

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that all required fields are present and not empty

    Args:
        data: Data dictionary to validate
        required_fields: List of required field names

    Raises:
        ValidationError: If any required fields are missing or empty
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(
            message=f"Missing required fields: {', '.join(missing_fields)}",
            field=missing_fields[0] if len(missing_fields) == 1 else None,
            details={"missing_fields": missing_fields}
        )

def validate_account_number(account_number: str) -> None:
    """
    Validate an account number

    Args:
        account_number: The account number to validate

    Raises:
        ValidationError: If the account number is invalid
    """
    if not account_number:
        raise ValidationError("Account number is required", field="account_number")
    
    if not re.match(ACCOUNT_NUMBER_PATTERN, account_number):
        raise ValidationError(
            "Invalid account number format. Must be 10-16 digits.",
            field="account_number"
        )

def validate_customer_id(customer_id: str) -> None:
    """
    Validate a customer ID

    Args:
        customer_id: The customer ID to validate

    Raises:
        ValidationError: If the customer ID is invalid
    """
    if not customer_id:
        raise ValidationError("Customer ID is required", field="customer_id")
    
    if not re.match(CUSTOMER_ID_PATTERN, customer_id):
        raise ValidationError(
            "Invalid customer ID format. Must be 8-12 alphanumeric characters.",
            field="customer_id"
        )

def validate_card_number(card_number: str) -> None:
    """
    Validate a card number

    Args:
        card_number: The card number to validate

    Raises:
        ValidationError: If the card number is invalid
    """
    if not card_number:
        raise ValidationError("Card number is required", field="card_number")
    
    # Remove spaces and dashes for validation
    card_number = card_number.replace(" ", "").replace("-", "")
    
    if not re.match(CARD_NUMBER_PATTERN, card_number):
        raise ValidationError(
            "Invalid card number format. Must be 16 digits.",
            field="card_number"
        )
        
    # Optional: Add Luhn algorithm check for more thorough validation
    # if not validate_luhn_checksum(card_number):
    #     raise ValidationError("Invalid card number checksum", field="card_number")

def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> None:
    """
    Validate a date string format

    Args:
        date_str: The date string to validate
        format_str: The expected date format string (default: YYYY-MM-DD)

    Raises:
        ValidationError: If the date string is invalid
    """
    if not date_str:
        raise ValidationError("Date is required", field="date")
    
    try:
        datetime.strptime(date_str, format_str)
    except ValueError:
        raise ValidationError(
            f"Invalid date format. Expected format: {format_str}",
            field="date"
        )

def validate_email(email: str) -> None:
    """
    Validate an email address

    Args:
        email: The email address to validate

    Raises:
        ValidationError: If the email address is invalid
    """
    if not email:
        raise ValidationError("Email is required", field="email")
    
    if not re.match(EMAIL_PATTERN, email):
        raise ValidationError(
            "Invalid email address format",
            field="email"
        )

def validate_phone(phone: str) -> None:
    """
    Validate a phone number

    Args:
        phone: The phone number to validate

    Raises:
        ValidationError: If the phone number is invalid
    """
    if not phone:
        raise ValidationError("Phone number is required", field="phone")
    
    # Remove spaces, dashes, and parentheses for validation
    phone = re.sub(r'[\s\-()]', '', phone)
    
    if not re.match(PHONE_PATTERN, phone):
        raise ValidationError(
            "Invalid phone number format. Must be 10-15 digits with optional + prefix.",
            field="phone"
        )

def validate_amount(amount: Union[float, str, int], min_value: float = 0.01, max_value: Optional[float] = None) -> None:
    """
    Validate a monetary amount

    Args:
        amount: The amount to validate
        min_value: Minimum allowed value (default: 0.01)
        max_value: Maximum allowed value (default: None = no maximum)

    Raises:
        ValidationError: If the amount is invalid
    """
    if amount is None:
        raise ValidationError("Amount is required", field="amount")
    
    try:
        if isinstance(amount, str):
            amount = float(amount)
    except ValueError:
        raise ValidationError("Amount must be a valid number", field="amount")
    
    if amount < min_value:
        raise ValidationError(f"Amount must be at least {min_value}", field="amount")
    
    if max_value is not None and amount > max_value:
        raise ValidationError(f"Amount cannot exceed {max_value}", field="amount")
