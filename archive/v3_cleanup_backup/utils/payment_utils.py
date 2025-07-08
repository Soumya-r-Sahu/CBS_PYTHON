"""
Payment-specific utilities for the Core Banking System.

This module provides utility functions specifically for payment services like
NEFT, RTGS, IMPS, and UPI.
"""

from typing import Dict, Any
import datetime
from utils.id_generation import generate_neft_reference, generate_rtgs_reference, generate_imps_reference, generate_upi_reference

def generate_neft_reference(account_number: str, amount: float, 
                          timestamp: str = None) -> str:
    """
    Generate a NEFT reference number.
    
    Args:
        account_number: The account number involved
        amount: The transaction amount
        timestamp: Optional timestamp (if None, current time is used)
        
    Returns:
        NEFT reference number
    """
    # Delegating to centralized id_generation module
    from utils.id_generation import generate_neft_reference as gen_neft_ref
    return gen_neft_ref(account_number, amount, timestamp)

def generate_rtgs_reference(account_number: str, amount: float, 
                          timestamp: str = None) -> str:
    """
    Generate a RTGS reference number.
    
    Args:
        account_number: The account number involved
        amount: The transaction amount
        timestamp: Optional timestamp (if None, current time is used)
        
    Returns:
        RTGS reference number
    """
    # Delegating to centralized id_generation module
    from utils.id_generation import generate_rtgs_reference as gen_rtgs_ref
    return gen_rtgs_ref(account_number, amount, timestamp)
    return generate_reference_id("RTGS", unique_data, timestamp)

def generate_imps_reference(mobile_number: str, account_number: str, 
                          amount: float, timestamp: str = None) -> str:
    """
    Generate an IMPS reference number.
    
    Args:
        mobile_number: The mobile number involved
        account_number: The account number involved
        amount: The transaction amount
        timestamp: Optional timestamp (if None, current time is used)
        
    Returns:
        IMPS reference number
    """
    # Delegating to centralized id_generation module
    from utils.id_generation import generate_payment_reference
    unique_data = f"{mobile_number}_{account_number}_{amount}"
    return generate_payment_reference("IMPS", unique_data, amount, timestamp)

def generate_upi_reference(upi_id: str, amount: float, 
                         timestamp: str = None) -> str:
    """
    Generate a UPI reference number.
    
    Args:
        upi_id: The UPI ID involved
        amount: The transaction amount
        timestamp: Optional timestamp (if None, current time is used)
        
    Returns:
        UPI reference number
    """
    # Delegating to centralized id_generation module
    from utils.id_generation import generate_payment_reference
    return generate_payment_reference("UPI", upi_id, amount, timestamp)

def generate_purpose_code_description(purpose_code: str) -> str:
    """
    Get the description for an RTGS purpose code.
    
    Args:
        purpose_code: The purpose code
        
    Returns:
        Description of the purpose code
    """
    purpose_codes = {
        "CORT": "Corporate Payment",
        "HOLD": "Hold Payment",
        "INTC": "Intra Company Payment",
        "PHON": "Telephone Payment",
        "REPA": "Repayment",
        "SDVA": "Same Day Value Payment",
        "TREA": "Treasury Payment",
        "CASH": "Cash Management Transfer",
        # Add more purpose codes as needed
    }
    
    return purpose_codes.get(purpose_code, "General Payment")
