"""
Common utility functions for the Core Banking System.

This module consolidates commonly used utility functions from across the system
to reduce code duplication and promote consistency.
"""

from typing import Dict, Any, List, Optional, Union
import datetime
import hashlib
import re
import logging

# Configure logger
logger = logging.getLogger(__name__)

# Common ID-related functions
def generate_reference_id(prefix: str, unique_data: str, timestamp: str = None) -> str:
    """
    Generate a reference ID with a prefix, timestamp, and hash.
    
    Args:
        prefix: The prefix to use for the reference ID
        unique_data: Data to use for hash generation
        timestamp: Optional timestamp (if None, current time is used)
        
    Returns:
        A reference ID in the format PREFIX-TIMESTAMP-HASH
    """
    if timestamp is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Create hash from the unique data
    hash_input = f"{unique_data}{timestamp}"
    hash_obj = hashlib.md5(hash_input.encode())
    hash_hex = hash_obj.hexdigest()[:8]  # Use first 8 chars of hash
    
    # Create and return the reference ID
    return f"{prefix}-{timestamp}-{hash_hex}"

# Common formatting functions
def format_ifsc_code(ifsc_code: str) -> str:
    """
    Format an IFSC code by removing spaces and converting to uppercase.
    
    Args:
        ifsc_code: The IFSC code to format
        
    Returns:
        The formatted IFSC code
    """
    if not ifsc_code:
        return ""
    
    return ifsc_code.strip().upper().replace(" ", "")

def sanitize_account_number(account_number: str) -> str:
    """
    Sanitize an account number by removing spaces and special characters.
    
    Args:
        account_number: The account number to sanitize
        
    Returns:
        The sanitized account number
    """
    if not account_number:
        return ""
    
    # Remove spaces, hyphens, and other special characters
    return re.sub(r'[^0-9]', '', account_number)

def mask_account_number(account_number: str) -> str:
    """
    Mask an account number for display purposes.
    
    Args:
        account_number: The account number to mask
        
    Returns:
        The masked account number
    """
    if not account_number:
        return ""
    
    # Sanitize the account number first
    account_number = sanitize_account_number(account_number)
    
    # If account number is less than 8 characters, mask all but the last 2
    if len(account_number) < 8:
        return "X" * (len(account_number) - 2) + account_number[-2:]
    
    # Otherwise, keep first 2 and last 4 digits visible
    return account_number[:2] + "X" * (len(account_number) - 6) + account_number[-4:]

def mask_mobile_number(mobile_number: str) -> str:
    """
    Mask a mobile number for display purposes.
    
    Args:
        mobile_number: The mobile number to mask
        
    Returns:
        The masked mobile number
    """
    if not mobile_number:
        return ""
    
    # Remove spaces, hyphens, and other special characters
    mobile_number = re.sub(r'[^0-9]', '', mobile_number)
    
    # Keep only the last 4 digits visible
    return "X" * (len(mobile_number) - 4) + mobile_number[-4:]

def standardize_mobile_number(mobile_number: str) -> str:
    """
    Standardize a mobile number by removing formatting and ensuring it has the correct prefix.
    
    Args:
        mobile_number: The mobile number to standardize
        
    Returns:
        The standardized mobile number
    """
    if not mobile_number:
        return ""
    
    # Remove spaces, hyphens, and other special characters
    mobile_number = re.sub(r'[^0-9]', '', mobile_number)
    
    # If the number starts with a country code, keep it as is
    if mobile_number.startswith("91") and len(mobile_number) >= 12:
        return mobile_number
    
    # If the number is 10 digits, add the country code for India
    if len(mobile_number) == 10:
        return f"91{mobile_number}"
    
    # For other cases, return as is
    return mobile_number
