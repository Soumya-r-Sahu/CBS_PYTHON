"""
ID Generator

Generates unique IDs for various entities in the Core Banking System.
"""

import random
import string
from enum import Enum
from datetime import datetime
import uuid

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path


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

def calculate_checksum(digits: str) -> str:
    """
    Calculate a Luhn algorithm checksum for account validation
    
    Args:
        digits: String of digits
    
    Returns:
        Two-digit checksum
    """
    # Luhn algorithm implementation
    def digits_of(n):
        return [int(d) for d in str(n)]
    
    digits = [int(d) for d in digits]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    
    return f"{(10 - (checksum % 10)) % 10:02d}"

def generate_account_number(branch_code="12345", account_type="01", sub_type="01") -> str:
    """
    Generate a unique account number with format BBBBB-AATT-CCCCCC-CC
    
    Args:
        branch_code: Five-digit branch code (default: 12345)
        account_type: Two-digit account type (default: 01=Savings)
        sub_type: Two-digit account sub-type/product code (default: 01)
        
    Returns:
        Account number string in the format BBBBB-AATT-CCCCCC-CC
    """
    # Ensure branch code is 5 digits
    branch_code = branch_code.zfill(5)[:5]
    
    # Ensure account type and sub-type are 2 digits
    account_type = account_type.zfill(2)[:2]
    sub_type = sub_type.zfill(2)[:2]
    
    # Generate 6-digit customer serial number
    customer_serial = ''.join(random.choices(string.digits, k=6))
    
    # Calculate checksum
    digits = f"{branch_code}{account_type}{sub_type}{customer_serial}"
    checksum = calculate_checksum(digits)
    
    # Combine
    account_number = f"{branch_code}-{account_type}{sub_type}-{customer_serial}-{checksum}"
    
    return account_number

def generate_customer_id(branch_code=1, user_type=1, sequence_num=None) -> str:
    """
    Generate a unique customer ID with format BBYYTSSSSS
    
    Args:
        branch_code: Two-digit branch code (default: 01)
        user_type: Single digit user type (default: 1)
        sequence_num: Optional sequence number (default: random 4-digit number)
        
    Returns:
        Customer ID string in the format BBYYTSSSSS where:
        - BB: Branch code (2 digits)
        - YY: Year (2 digits)
        - T: User type (1 digit)
        - SSSSS: Sequence number (4 digits)
    """
    # Current year (last 2 digits)
    year = datetime.now().year % 100  # e.g., 2025 -> 25
    
    # If sequence_num is not provided, generate a random 4-digit number
    if sequence_num is None:
        sequence_num = random.randint(1, 9999)
    
    # Combine and format
    customer_id = f"{branch_code:02d}{year:02d}{user_type}{sequence_num:04d}"
    
    return customer_id

def generate_transaction_id() -> str:
    """
    Generate a unique transaction ID with format TRX-YYYYMMDD-SSSSSS
    
    Returns:
        Transaction ID string in the format TRX-YYYYMMDD-SSSSSS
    """
    # Get current date in format YYYYMMDD
    date_part = datetime.now().strftime("%Y%m%d")
    
    # Generate 6-digit sequence number
    seq_part = ''.join(random.choices(string.digits, k=6))
    
    # Combine
    transaction_id = f"TRX-{date_part}-{seq_part}"
    
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

def generate_employee_id(zone_code="01", branch_code="01", designation_code="01") -> str:
    """
    Generate an employee ID with Bank of Baroda style format ZZBB-DD-EEEE
    
    Args:
        zone_code: Two-digit zone code (default: 01)
        branch_code: Two-digit branch or department code (default: 01)
        designation_code: Two-digit designation code (default: 01)
        
    Returns:
        Employee ID string in the format ZZBB-DD-EEEE
    """
    # Ensure codes are 2 digits
    zone_code = zone_code.zfill(2)[:2]
    branch_code = branch_code.zfill(2)[:2]
    designation_code = designation_code.zfill(2)[:2]
    
    # Generate 4-digit employee sequence number
    sequence = ''.join(random.choices(string.digits, k=4))
    
    # Combine
    employee_id = f"{zone_code}{branch_code}-{designation_code}-{sequence}"
    
    return employee_id
