"""
ID Generator

Generates unique IDs for various entities in the Core Banking System.
"""

import random
import string
from enum import Enum
from datetime import datetime
import uuid

class AccountType(Enum):
    """
    Enum representing different types of bank accounts
    """
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    FIXED_DEPOSIT = "FIXED_DEPOSIT"
    RECURRING_DEPOSIT = "RECURRING_DEPOSIT"
    SALARY = "SALARY"
    NRI = "NRI"
    PENSION = "PENSION"

def generate_account_number(state_code: str = "14", branch_code: str = "MAH00001") -> str:
    """
    Generate a unique account number
    
    Format: {state_code}{branch_digit}{random_digits}
    
    Args:
        state_code: Two-digit state code (default: 14 for Maharashtra)
        branch_code: Branch code
        
    Returns:
        Unique account number string
    """
    # Extract digit from branch code
    branch_digit = ''.join(filter(str.isdigit, branch_code))[:1] or '1'
    
    # Current timestamp as string, format: yymmddHHMMSS
    timestamp = datetime.now().strftime('%y%m%d%H%M%S')
    
    # 5 random digits
    random_digits = ''.join(random.choices(string.digits, k=5))
    
    # Combine to form account number
    account_number = f"{state_code}{branch_digit}{timestamp[2:8]}{random_digits}"
    
    return account_number

def generate_customer_id() -> str:
    """
    Generate a unique customer ID
    
    Returns:
        Customer ID string
    """
    # Current timestamp as string, format: yymmdd
    timestamp = datetime.now().strftime('%y%m%d')
    
    # 6 random digits
    random_digits = ''.join(random.choices(string.digits, k=6))
    
    # Combine
    customer_id = f"C{timestamp}{random_digits}"
    
    return customer_id

def generate_transaction_id() -> str:
    """
    Generate a unique transaction ID
    
    Returns:
        Transaction ID string
    """
    # Generate a UUID
    transaction_uuid = uuid.uuid4()
    
    # Current timestamp as string, format: yymmddHHMMSS
    timestamp = datetime.now().strftime('%y%m%d%H%M%S')
    
    # Combine timestamp with part of UUID
    transaction_id = f"TXN{timestamp}{str(transaction_uuid)[:8]}"
    
    return transaction_id

def generate_ref_number(prefix: str = "REF") -> str:
    """
    Generate a reference number for various operations
    
    Args:
        prefix: Prefix string for the reference number
        
    Returns:
        Reference number string
    """
    # Current timestamp as string, format: yyMMddHHmmss
    timestamp = datetime.now().strftime('%y%m%d%H%M%S')
    
    # 4 random alphanumeric characters
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    
    # Combine
    ref_number = f"{prefix}{timestamp}{random_chars}"
    
    return ref_number
