"""
RTGS Payment Utilities - Core Banking System

This module provides utility functions for RTGS payments.
"""
import logging
from typing import Dict, Any, List
import hashlib
from datetime import datetime
import json

# Configure logger
logger = logging.getLogger(__name__)


def generate_rtgs_reference(account_number: str, amount: float, timestamp: str = None) -> str:
    """
    Generate a unique reference for an RTGS payment.
    
    Args:
        account_number: Account number
        amount: Transaction amount
        timestamp: Timestamp (defaults to current time)
        
    Returns:
        str: Unique payment reference
    """
    if timestamp is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        
    # Combine inputs and create a hash
    data = f"{account_number}:{amount}:{timestamp}"
    hash_value = hashlib.sha256(data.encode()).hexdigest()[:10]
    
    # Format: RTyymmddHHMMSS-HASH
    reference = f"RT{timestamp[-14:]}-{hash_value.upper()}"
    
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


def generate_purpose_code_description(purpose_code: str) -> str:
    """
    Get description for RTGS purpose code.
    
    Args:
        purpose_code: RBI purpose code
        
    Returns:
        str: Description of purpose code
    """
    purpose_codes = {
        "CORT": "Payment of Settlement of Court/Tribunal Judgements",
        "INTC": "Intra Company Payment",
        "TREA": "Treasury Payment",
        "CASH": "Cash Management Transfer",
        "DIVI": "Dividend Payment",
        "GOVT": "Government Payment",
        "HEDG": "Hedging Operation",
        "LOAN": "Loan Disbursement/Repayment",
        "PENS": "Pension Payment",
        "SALA": "Salary Payment",
        "SECU": "Securities Purchase/Sale",
        "SSBE": "Social Security Benefit",
        "SUPP": "Supplier Payment",
        "TAXS": "Tax Payment",
        "TRAD": "Trade Payment"
    }
    
    return purpose_codes.get(purpose_code, "Unknown Purpose Code")
