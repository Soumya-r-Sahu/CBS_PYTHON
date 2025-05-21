"""
IMPS Payment Utilities - Core Banking System

This module provides utility functions for IMPS payments.
It now uses the consolidated utilities from the utils.common module.
"""
import logging
from typing import Dict, Any, List
import hashlib
from datetime import datetime
import re

# Import common utilities
from utils.lib.payment_utils import generate_imps_reference as common_generate_imps_reference
from utils.common import (
    format_ifsc_code as common_format_ifsc_code,
    sanitize_account_number as common_sanitize_account_number,
    mask_account_number as common_mask_account_number,
    standardize_mobile_number as common_standardize_mobile_number,
    mask_mobile_number as common_mask_mobile_number
)

# Configure logger
logger = logging.getLogger(__name__)


def generate_imps_reference(mobile_number: str = None, account_number: str = None, 
                          amount: float = None, timestamp: str = None) -> str:
    """
    Generate a unique reference for an IMPS payment.
    
    Args:
        mobile_number: Mobile number (optional)
        account_number: Account number (optional)
        amount: Transaction amount (optional)
        timestamp: Timestamp (defaults to current time)
        
    Returns:
        str: Unique payment reference
    """
    # Use the common implementation
    return common_generate_imps_reference(
        mobile_number or "", 
        account_number or "", 
        amount or 0.0, 
        timestamp
    )


def format_ifsc_code(ifsc_code: str) -> str:
    """
    Format IFSC code to standard format.
    
    Args:
        ifsc_code: IFSC code to format
        
    Returns:
        str: Formatted IFSC code
    """
    # Use the common implementation
    return common_format_ifsc_code(ifsc_code)


def standardize_mobile_number(mobile_number: str) -> str:
    """
    Standardize mobile number to 10-digit format without prefix.
    
    Args:
        mobile_number: Mobile number in any format
        
    Returns:
        str: Standardized 10-digit mobile number
    """
    # Use the common implementation
    return common_standardize_mobile_number(mobile_number)


def sanitize_account_number(account_number: str) -> str:
    """
    Sanitize account number by removing spaces and special characters.
    
    Args:
        account_number: Account number to sanitize
        
    Returns:
        str: Sanitized account number
    """
    # Use the common implementation
    return common_sanitize_account_number(account_number)


def mask_account_number(account_number: str) -> str:
    """
    Mask account number for display/logging.
    
    Args:
        account_number: Account number to mask
        
    Returns:
        str: Masked account number
    """
    # Use the common implementation
    return common_mask_account_number(account_number)


def mask_mobile_number(mobile_number: str) -> str:
    """
    Mask mobile number for display/logging.
    
    Args:
        mobile_number: Mobile number to mask
        
    Returns:
        str: Masked mobile number
    """
    # Use the common implementation
    return common_mask_mobile_number(mobile_number)


def generate_transaction_id() -> str:
    """
    Generate a unique transaction ID for IMPS.
    
    Returns:
        str: Unique transaction ID
    """
    # Format: IMPS-YYYYMMDD-XXXXXXXX
    date_part = datetime.utcnow().strftime("%Y%m%d")
    unique_part = hashlib.md5(f"{date_part}{datetime.utcnow().microsecond}".encode()).hexdigest()[:8].upper()
    
    return f"IMPS-{date_part}-{unique_part}"
