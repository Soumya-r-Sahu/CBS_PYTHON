"""
NEFT Payment Utilities - Core Banking System

This module provides utility functions for NEFT payments.
It now uses the consolidated utilities from the utils.common module.
"""
import logging
from typing import Dict, Any, List
import json

# Import common utilities
from utils.lib.payment_utils import generate_neft_reference as common_generate_neft_reference
from utils.common import (
    format_ifsc_code as common_format_ifsc_code,
    sanitize_account_number as common_sanitize_account_number,
    mask_account_number as common_mask_account_number
)

# Configure logger
logger = logging.getLogger(__name__)


def generate_neft_reference(account_number: str, amount: float, timestamp: str = None) -> str:
    """
    Generate a unique reference for a NEFT payment.
    
    Args:
        account_number: Account number
        amount: Transaction amount
        timestamp: Timestamp (defaults to current time)
        
    Returns:
        str: Unique payment reference
    """
    # Use the common implementation
    return common_generate_neft_reference(account_number, amount, timestamp)


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
