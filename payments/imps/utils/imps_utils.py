"""
IMPS Payment Utilities - Core Banking System

This module provides utility functions for IMPS payments.
"""
import logging
from typing import Dict, Any, List
import hashlib
from datetime import datetime
import re

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
    if timestamp is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    
    # Combine available inputs
    data = f"{mobile_number or ''}:{account_number or ''}:{amount or ''}:{timestamp}"
    hash_value = hashlib.sha256(data.encode()).hexdigest()[:8]
    
    # Format: IM-yymmddHHMMSS-HASH
    reference = f"IM-{timestamp[-12:]}-{hash_value.upper()}"
    
    return reference


def format_ifsc_code(ifsc_code: str) -> str:
    """
    Format IFSC code to standard format.
    
    Args:
        ifsc_code: IFSC code to format
        
    Returns:
        str: Formatted IFSC code
    """
    # Remove spaces and convert to uppercase
    formatted = ifsc_code.replace(" ", "").upper()
    
    return formatted


def standardize_mobile_number(mobile_number: str) -> str:
    """
    Standardize mobile number to 10-digit format without prefix.
    
    Args:
        mobile_number: Mobile number in any format
        
    Returns:
        str: Standardized 10-digit mobile number
    """
    # Remove spaces, hyphens, etc.
    cleaned = re.sub(r'[\s\-\(\)]+', '', mobile_number)
    
    # Remove country code if present
    if cleaned.startswith('+91'):
        cleaned = cleaned[3:]
    elif cleaned.startswith('91') and len(cleaned) > 10:
        cleaned = cleaned[2:]
    elif cleaned.startswith('0'):
        cleaned = cleaned[1:]
    
    return cleaned


def sanitize_account_number(account_number: str) -> str:
    """
    Sanitize account number by removing spaces and special characters.
    
    Args:
        account_number: Account number to sanitize
        
    Returns:
        str: Sanitized account number
    """
    # Remove spaces and special characters
    sanitized = ''.join(c for c in account_number if c.isalnum())
    
    return sanitized


def mask_account_number(account_number: str) -> str:
    """
    Mask account number for display/logging.
    
    Args:
        account_number: Account number to mask
        
    Returns:
        str: Masked account number
    """
    # Keep first 2 and last 4 digits visible
    if len(account_number) > 6:
        masked = account_number[:2] + '*' * (len(account_number) - 6) + account_number[-4:]
    else:
        # If account number is too short, just show last 4
        masked = '*' * (len(account_number) - 4) + account_number[-4:]
    
    return masked


def mask_mobile_number(mobile_number: str) -> str:
    """
    Mask mobile number for display/logging.
    
    Args:
        mobile_number: Mobile number to mask
        
    Returns:
        str: Masked mobile number
    """
    # Standardize first
    mobile = standardize_mobile_number(mobile_number)
    
    # Keep first 2 and last 2 digits visible
    if len(mobile) >= 6:
        masked = mobile[:2] + '*' * (len(mobile) - 4) + mobile[-2:]
    else:
        # If very short, mask the middle
        masked = mobile[0] + '*' * (len(mobile) - 2) + mobile[-1:]
    
    return masked


def generate_transaction_id() -> str:
    """
    Generate a unique transaction ID for IMPS.
    
    Returns:
        str: Unique transaction ID
    """
    # Format: IMPS-YYYYMMDD-XXXXXXXX
    date_part = datetime.utcnow().strftime("%Y%m%d")
    time_part = datetime.utcnow().strftime("%H%M%S")
    unique_part = hashlib.md5(f"{date_part}{time_part}{datetime.utcnow().microsecond}".encode()).hexdigest()[:8].upper()
    
    return f"IMPS-{date_part}-{unique_part}"
