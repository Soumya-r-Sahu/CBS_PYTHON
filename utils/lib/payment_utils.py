"""
Payment Utilities Module

This module provides standardized utility functions for payment processing,
currency conversion, and payment format validation used in the Core Banking System.

The module implements common payment-related functionality that is used across
different modules in the system, ensuring consistency in payment processing.
"""

import re
import decimal
from decimal import Decimal
from typing import Dict, List, Union, Optional, Tuple
import datetime
import json

# Set decimal precision for monetary calculations
decimal.getcontext().prec = 10

# Currency code mapping (ISO 4217)
CURRENCY_CODES = {
    'INR': {'name': 'Indian Rupee', 'symbol': '₹', 'decimals': 2},
    'USD': {'name': 'US Dollar', 'symbol': '$', 'decimals': 2},
    'EUR': {'name': 'Euro', 'symbol': '€', 'decimals': 2},
    'GBP': {'name': 'British Pound', 'symbol': '£', 'decimals': 2},
    'JPY': {'name': 'Japanese Yen', 'symbol': '¥', 'decimals': 0},
    # Add more currencies as needed
}

def format_amount(amount: Union[Decimal, float, str], currency: str = 'INR') -> str:
    """
    Format an amount with the appropriate currency symbol and decimal places.
    
    Args:
        amount: The amount to format
        currency: ISO currency code (default: INR)
    
    Returns:
        Formatted amount string with currency symbol
    
    Examples:
        >>> format_amount(1234.56, 'USD')
        '$1,234.56'
        >>> format_amount(1234.56, 'INR')
        '₹1,234.56'
    """
    # Convert to Decimal for precision
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    
    # Get currency info or default to INR
    currency_info = CURRENCY_CODES.get(currency.upper(), CURRENCY_CODES['INR'])
    symbol = currency_info['symbol']
    decimals = currency_info['decimals']
    
    # Format with thousands separator and decimal places
    formatted_amount = '{:,.{prec}f}'.format(amount, prec=decimals)
    
    # Add currency symbol
    return f"{symbol}{formatted_amount}"

def parse_amount(amount_str: str) -> Tuple[Decimal, Optional[str]]:
    """
    Parse an amount string with potential currency symbol into a numeric value.
    
    Args:
        amount_str: String representation of amount (e.g., "$1,234.56")
    
    Returns:
        Tuple of (Decimal amount, currency code or None)
    
    Examples:
        >>> parse_amount("$1,234.56")
        (Decimal('1234.56'), 'USD')
        >>> parse_amount("1234.56")
        (Decimal('1234.56'), None)
    """
    # Remove all whitespace
    amount_str = amount_str.strip()
    
    # Extract currency symbol if present
    currency_code = None
    for code, info in CURRENCY_CODES.items():
        if amount_str.startswith(info['symbol']):
            currency_code = code
            amount_str = amount_str[len(info['symbol']):]
            break
    
    # Remove commas and convert to Decimal
    amount_str = amount_str.replace(',', '')
    try:
        amount = Decimal(amount_str)
        return amount, currency_code
    except (decimal.InvalidOperation, ValueError):
        raise ValueError(f"Invalid amount format: {amount_str}")

def calculate_transaction_fee(amount: Decimal, transaction_type: str, 
                             currency: str = 'INR') -> Decimal:
    """
    Calculate transaction fee based on amount, type and currency.
    
    Args:
        amount: Transaction amount
        transaction_type: Type of transaction (e.g., 'RTGS', 'NEFT', 'IMPS')
        currency: ISO currency code (default: INR)
    
    Returns:
        Transaction fee as Decimal
    """
    # Default fee structure (customize as needed)
    fee_structure = {
        'RTGS': {
            'INR': {'percentage': Decimal('0.0005'), 'min_fee': Decimal('25'), 'max_fee': Decimal('50')},
            'USD': {'percentage': Decimal('0.001'), 'min_fee': Decimal('5'), 'max_fee': Decimal('20')},
            'EUR': {'percentage': Decimal('0.001'), 'min_fee': Decimal('5'), 'max_fee': Decimal('20')},
        },
        'NEFT': {
            'INR': {'percentage': Decimal('0.0005'), 'min_fee': Decimal('2.5'), 'max_fee': Decimal('25')},
            'USD': {'percentage': Decimal('0.001'), 'min_fee': Decimal('1'), 'max_fee': Decimal('10')},
            'EUR': {'percentage': Decimal('0.001'), 'min_fee': Decimal('1'), 'max_fee': Decimal('10')},
        },
        'IMPS': {
            'INR': {'percentage': Decimal('0.001'), 'min_fee': Decimal('5'), 'max_fee': Decimal('15')},
            'USD': {'percentage': Decimal('0.002'), 'min_fee': Decimal('1'), 'max_fee': Decimal('5')},
            'EUR': {'percentage': Decimal('0.002'), 'min_fee': Decimal('1'), 'max_fee': Decimal('5')},
        },
        # Add more transaction types as needed
    }
    
    # Get fee structure for transaction type and currency
    try:
        fee_info = fee_structure[transaction_type.upper()][currency.upper()]
    except KeyError:
        # Default to NEFT/INR if not found
        fee_info = fee_structure['NEFT']['INR']
    
    # Calculate percentage-based fee
    percentage_fee = amount * fee_info['percentage']
    
    # Apply min/max constraints
    if percentage_fee < fee_info['min_fee']:
        return fee_info['min_fee']
    elif percentage_fee > fee_info['max_fee']:
        return fee_info['max_fee']
    else:
        return percentage_fee.quantize(Decimal('0.01'), rounding=decimal.ROUND_HALF_UP)

def validate_ifsc_code(ifsc_code: str) -> bool:
    """
    Validate an IFSC (Indian Financial System Code).
    
    Args:
        ifsc_code: IFSC code to validate
    
    Returns:
        Boolean indicating if the IFSC code is valid
    """
    if not ifsc_code:
        return False
    
    # IFSC format: 4 characters (bank code) + 0 + 6 characters (branch code)
    pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
    return bool(re.match(pattern, ifsc_code))

def validate_account_number(account_number: str) -> bool:
    """
    Validate a bank account number.
    
    Args:
        account_number: Account number to validate
    
    Returns:
        Boolean indicating if the account number is valid
    """
    if not account_number:
        return False
    
    # Remove spaces and hyphens
    account_number = account_number.replace(' ', '').replace('-', '')
    
    # Basic validation: must be numeric and between 9-18 digits
    if not account_number.isdigit():
        return False
    
    if not (9 <= len(account_number) <= 18):
        return False
    
    return True

def format_reference_number(prefix: str, date: datetime.date, 
                            sequence: int, length: int = 10) -> str:
    """
    Generate a formatted reference number for payments.
    
    Args:
        prefix: Reference number prefix (e.g., 'PMT', 'REF')
        date: Transaction date
        sequence: Sequence number
        length: Desired length of sequence part (default: 10)
    
    Returns:
        Formatted reference number
    """
    date_str = date.strftime('%Y%m%d')
    seq_str = str(sequence).zfill(length)
    return f"{prefix}-{date_str}-{seq_str}"

def get_exchange_rate(from_currency: str, to_currency: str) -> Decimal:
    """
    Get the current exchange rate between two currencies.
    
    This is a placeholder implementation. In a real system, this would
    fetch rates from an external service or database.
    
    Args:
        from_currency: Source currency code
        to_currency: Target currency code
    
    Returns:
        Exchange rate as Decimal
    """
    # Sample static rates (in a real system, these would be dynamically updated)
    exchange_rates = {
        'INR_USD': Decimal('0.012'),
        'USD_INR': Decimal('83.21'),
        'EUR_INR': Decimal('89.54'),
        'INR_EUR': Decimal('0.011'),
        'USD_EUR': Decimal('0.92'),
        'EUR_USD': Decimal('1.08'),
        # Add more pairs as needed
    }
    
    # Handle same currency
    if from_currency == to_currency:
        return Decimal('1.0')
    
    # Try to get direct rate
    pair_key = f"{from_currency}_{to_currency}"
    if pair_key in exchange_rates:
        return exchange_rates[pair_key]
    
    # Try reverse rate
    reverse_key = f"{to_currency}_{from_currency}"
    if reverse_key in exchange_rates:
        return Decimal('1.0') / exchange_rates[reverse_key]
    
    # If no direct conversion, try via USD
    if from_currency != 'USD' and to_currency != 'USD':
        # Convert from_currency to USD, then USD to to_currency
        from_to_usd = get_exchange_rate(from_currency, 'USD')
        usd_to_target = get_exchange_rate('USD', to_currency)
        return from_to_usd * usd_to_target
    
    # Default fallback
    return Decimal('1.0')

def convert_currency(amount: Decimal, from_currency: str, 
                    to_currency: str) -> Decimal:
    """
    Convert an amount from one currency to another.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
    
    Returns:
        Converted amount as Decimal
    """
    # No conversion needed for same currency
    if from_currency == to_currency:
        return amount
    
    # Get exchange rate and apply conversion
    rate = get_exchange_rate(from_currency, to_currency)
    converted = amount * rate
    
    # Get target currency decimals for rounding
    decimals = CURRENCY_CODES.get(to_currency, CURRENCY_CODES['INR'])['decimals']
    
    # Round to appropriate decimal places
    return converted.quantize(Decimal(10) ** -decimals, rounding=decimal.ROUND_HALF_UP)
