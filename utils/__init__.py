# utils/__init__.py
"""
Utility modules for Core Banking System.

This package contains various utility functions and classes used throughout the system.
"""

# Import from utility modules
from utils.date import (
    format_date, parse_date, get_current_time, 
    get_current_date, convert_timezone, DATE_FORMATS
)

from utils.id import (
    generate_customer_id, generate_account_number, 
    generate_transaction_id, generate_reference_number,
    validate_customer_id, validate_account_number, 
    validate_iban, validate_ifsc_code, validate_swift_code
)

from utils.database import (
    get_database_type, set_database_type, get_connection_string,
    sanitize_sql_input, prevent_sql_injection, validate_sql_query
)

from utils.validation import (
    validate_email, validate_phone, validate_text_input,
    validate_numeric_input, validate_date_input, 
    validate_amount, validate_currency_code
)

from utils.security import (
    encrypt_data, decrypt_data, hash_password, verify_password,
    generate_token, verify_token, prevent_xss
)

from utils.payments import (
    generate_payment_reference, validate_payment_reference,
    format_payment_details, parse_payment_details
)

# Expose key utilities at the package level
__all__ = [
    # Date utilities
    'format_date', 'parse_date', 'get_current_time', 
    'get_current_date', 'convert_timezone', 'DATE_FORMATS',
    
    # ID utilities
    'generate_customer_id', 'generate_account_number', 
    'generate_transaction_id', 'generate_reference_number',
    'validate_customer_id', 'validate_account_number',
    'validate_iban', 'validate_ifsc_code', 'validate_swift_code',
    
    # Database utilities
    'get_database_type', 'set_database_type', 'get_connection_string',
    'sanitize_sql_input', 'prevent_sql_injection', 'validate_sql_query',
    
    # Validation utilities
    'validate_email', 'validate_phone', 'validate_text_input',
    'validate_numeric_input', 'validate_date_input',
    'validate_amount', 'validate_currency_code',
    
    # Security utilities
    'encrypt_data', 'decrypt_data', 'hash_password', 'verify_password',
    'generate_token', 'verify_token', 'prevent_xss',
    
    # Payment utilities
    'generate_payment_reference', 'validate_payment_reference',
    'format_payment_details', 'parse_payment_details'
]