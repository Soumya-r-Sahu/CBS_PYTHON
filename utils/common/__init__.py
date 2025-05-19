"""
Common utilities for the Core Banking System.

This module exports all utility functions from submodules to provide a single
import point for common utilities.
"""

# Import from submodules
from .id_formatters import (
    generate_reference_id,
    format_ifsc_code,
    sanitize_account_number,
    mask_account_number,
    mask_mobile_number,
    standardize_mobile_number
)

from .validators import (
    validate_amount,
    validate_upi_id,
    validate_mobile_number,
    validate_account_number,
    validate_ifsc_code
)

from .encryption import (
    generate_key,
    encrypt_data,
    decrypt_data,
    encrypt_sensitive_data
)

# Export all functions
__all__ = [
    # ID formatters
    'generate_reference_id',
    'format_ifsc_code',
    'sanitize_account_number',
    'mask_account_number',
    'mask_mobile_number',
    'standardize_mobile_number',
    
    # Validators
    'validate_amount',
    'validate_upi_id',
    'validate_mobile_number',
    'validate_account_number',
    'validate_ifsc_code',
    
    # Encryption
    'generate_key',
    'encrypt_data',
    'decrypt_data',
    'encrypt_sensitive_data'
]
