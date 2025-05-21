"""
Validation Utilities for Payments Module

This module provides standardized validation utilities for the payments module.
It implements reusable validation functions for payment data across all payment interfaces.

Tags: payments, validation, data_verification
AI-Metadata:
    component_type: validator
    criticality: high
    purpose: payment_data_validation
    impact_on_failure: payment_processing_errors
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, date
import json

# Configure logger
logger = logging.getLogger(__name__)

# Import module-specific error handling
from payments.utils.error_handling import PaymentValidationError

# Common validation patterns
ACCOUNT_NUMBER_PATTERN = r'^[0-9]{10,16}$'
CARD_NUMBER_PATTERN = r'^[0-9]{16}$'
PAYMENT_REFERENCE_PATTERN = r'^[A-Za-z0-9-]{6,30}$'
IFSC_CODE_PATTERN = r'^[A-Z]{4}0[A-Z0-9]{6}$'
SWIFT_CODE_PATTERN = r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$'

# Valid payment types
VALID_PAYMENT_TYPES = [
    "CREDIT", "DEBIT", "TRANSFER", "NEFT", "RTGS", "IMPS", "UPI",
    "BILL_PAYMENT", "LOAN_PAYMENT", "RECURRING", "INTERNATIONAL"
]

# Valid currencies
VALID_CURRENCIES = [
    "INR", "USD", "EUR", "GBP", "JPY", "CAD", "AUD", "SGD", 
    "HKD", "CHF", "CNY", "AED", "SAR"
]

def validate_required_payment_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that all required payment fields are present and not empty

    Args:
        data: Payment data dictionary to validate
        required_fields: List of required field names

    Raises:
        PaymentValidationError: If any required fields are missing or empty
    
    AI-Metadata:
        purpose: Ensure all required fields are present
        criticality: high
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None or (isinstance(data[field], str) and not data[field].strip()):
            missing_fields.append(field)
    
    if missing_fields:
        raise PaymentValidationError(
            message=f"Missing required payment fields: {', '.join(missing_fields)}",
            field=missing_fields[0] if len(missing_fields) == 1 else None,
            details={"missing_fields": missing_fields}
        )

def validate_payment_amount(amount: Union[float, str, int], 
                           min_amount: float = 0.01, 
                           max_amount: Optional[float] = None) -> None:
    """
    Validate a payment amount

    Args:
        amount: The payment amount to validate
        min_amount: Minimum allowed amount (default: 0.01)
        max_amount: Maximum allowed amount (default: None = no maximum)

    Raises:
        PaymentValidationError: If the amount is invalid
    
    AI-Metadata:
        purpose: Validate payment amount
        criticality: high
    """
    if amount is None:
        raise PaymentValidationError("Payment amount is required", field="amount")
    
    try:
        if isinstance(amount, str):
            amount = float(amount)
    except ValueError:
        raise PaymentValidationError("Payment amount must be a valid number", field="amount")
    
    if amount < min_amount:
        raise PaymentValidationError(f"Payment amount must be at least {min_amount}", field="amount")
    
    if max_amount is not None and amount > max_amount:
        raise PaymentValidationError(f"Payment amount cannot exceed {max_amount}", field="amount")

def validate_account_number(account_number: str) -> None:
    """
    Validate an account number for payment processing

    Args:
        account_number: The account number to validate

    Raises:
        PaymentValidationError: If the account number is invalid
    
    AI-Metadata:
        purpose: Validate account number format
        criticality: high
    """
    if not account_number:
        raise PaymentValidationError("Account number is required", field="account_number")
    
    if not re.match(ACCOUNT_NUMBER_PATTERN, account_number):
        raise PaymentValidationError(
            "Invalid account number format. Must be 10-16 digits.",
            field="account_number"
        )

def validate_card_number(card_number: str) -> None:
    """
    Validate a payment card number

    Args:
        card_number: The card number to validate

    Raises:
        PaymentValidationError: If the card number is invalid
    
    AI-Metadata:
        purpose: Validate payment card number
        criticality: high
    """
    if not card_number:
        raise PaymentValidationError("Card number is required", field="card_number")
    
    # Remove spaces and dashes for validation
    card_number = card_number.replace(" ", "").replace("-", "")
    
    if not re.match(CARD_NUMBER_PATTERN, card_number):
        raise PaymentValidationError(
            "Invalid card number format. Must be 16 digits.",
            field="card_number"
        )
    
    # Luhn algorithm check (credit card checksum)
    if not luhn_check(card_number):
        raise PaymentValidationError(
            "Invalid card number checksum",
            field="card_number"
        )

def validate_payment_type(payment_type: str) -> None:
    """
    Validate a payment type

    Args:
        payment_type: The payment type to validate

    Raises:
        PaymentValidationError: If the payment type is invalid
    
    AI-Metadata:
        purpose: Validate payment type
        criticality: medium
    """
    if not payment_type:
        raise PaymentValidationError("Payment type is required", field="payment_type")
    
    if payment_type not in VALID_PAYMENT_TYPES:
        raise PaymentValidationError(
            f"Invalid payment type. Must be one of: {', '.join(VALID_PAYMENT_TYPES)}",
            field="payment_type"
        )

def validate_currency(currency: str) -> None:
    """
    Validate a payment currency

    Args:
        currency: The currency code to validate

    Raises:
        PaymentValidationError: If the currency is invalid
    
    AI-Metadata:
        purpose: Validate currency code
        criticality: high
    """
    if not currency:
        raise PaymentValidationError("Currency is required", field="currency")
    
    if currency not in VALID_CURRENCIES:
        raise PaymentValidationError(
            f"Invalid currency code. Must be one of: {', '.join(VALID_CURRENCIES)}",
            field="currency"
        )

def validate_payment_reference(reference: str) -> None:
    """
    Validate a payment reference number

    Args:
        reference: The payment reference to validate

    Raises:
        PaymentValidationError: If the reference is invalid
    
    AI-Metadata:
        purpose: Validate payment reference
        criticality: medium
    """
    if not reference:
        raise PaymentValidationError("Payment reference is required", field="reference")
    
    if not re.match(PAYMENT_REFERENCE_PATTERN, reference):
        raise PaymentValidationError(
            "Invalid payment reference format. Must be 6-30 alphanumeric characters or hyphens.",
            field="reference"
        )

def validate_payment_date(payment_date: str, format_str: str = "%Y-%m-%d") -> None:
    """
    Validate a payment date

    Args:
        payment_date: The payment date string to validate
        format_str: The expected date format string (default: YYYY-MM-DD)

    Raises:
        PaymentValidationError: If the payment date is invalid
    
    AI-Metadata:
        purpose: Validate payment date
        criticality: medium
    """
    if not payment_date:
        raise PaymentValidationError("Payment date is required", field="payment_date")
    
    try:
        dt = datetime.strptime(payment_date, format_str)
        
        # Check if date is in the past (for non-scheduled payments)
        today = datetime.now().date()
        if dt.date() < today:
            raise PaymentValidationError(
                "Payment date cannot be in the past",
                field="payment_date"
            )
    except ValueError:
        raise PaymentValidationError(
            f"Invalid payment date format. Expected format: {format_str}",
            field="payment_date"
        )

def luhn_check(card_number: str) -> bool:
    """
    Validate a card number using the Luhn algorithm (mod 10 checksum)
    
    Args:
        card_number: The card number to validate
        
    Returns:
        bool: True if the card number passes the Luhn check
    """
    digits = [int(d) for d in card_number]
    odd_digits = digits[-1::-2]  # From right to left, every other digit
    even_digits = digits[-2::-2]  # From right to left, every other digit starting with second-to-last
    
    # Double even digits and sum the digits if > 9
    doubled_even_digits = []
    for digit in even_digits:
        doubled = digit * 2
        if doubled > 9:
            doubled = doubled - 9  # Same as summing the digits
        doubled_even_digits.append(doubled)
    
    # Sum all digits
    total = sum(odd_digits) + sum(doubled_even_digits)
    
    # If the total mod 10 is 0, the number is valid
    return total % 10 == 0
