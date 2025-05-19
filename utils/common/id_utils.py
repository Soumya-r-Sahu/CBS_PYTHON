"""
ID Utilities Module for Core Banking System

This module provides comprehensive utilities for working with IDs, including generation, validation,
and conversion functions that are used across the core banking system.

ID Formats:
-----------
1. Customer ID: YYDDD-BBBBB-SSSS
   - YY: Last 2 digits of creation year
   - DDD: Day of year (001-366)
   - BBBBB: Branch code (5 digits)
   - SSSS: Customer sequence number (4 digits)

2. Account Number: BBBBB-AATT-CCCCCC-CC
   - BBBBB: Branch code (5 digits)
   - AA: Account type (01=Savings, 02=Current, etc.)
   - TT: Account sub-type/product code (2 digits)
   - CCCCCC: Customer serial number (6 digits)
   - CC: Checksum (2 digits using Luhn algorithm)

3. Transaction ID: TRX-YYYYMMDD-SSSSSS
   - TRX: Fixed prefix
   - YYYYMMDD: Date (year, month, day)
   - SSSSSS: Sequence number (6 digits)

4. Employee ID: ZZBB-DD-EEEE
   - ZZ: Zone code (2 digits)
   - BB: Branch or Department code (2 digits)
   - DD: Designation code (2 digits)
   - EEEE: Employee sequence number (4 digits)

Functions:
----------
- Generators: Create new IDs in the standard formats
- Validators: Verify existing IDs against the expected formats
- Converters: Transform legacy ID formats to new formats
- Utilities: Handle checksums and other ID-related operations

Examples:
---------
>>> from utils.common.id_utils import generate_customer_id, validate_customer_id
>>> customer_id = generate_customer_id(branch_code="12345")
>>> print(customer_id)  # Example: 23142-12345-8765
>>> validate_customer_id(customer_id)  # Returns: True
"""

import re
import random
import string
import datetime
import logging
from typing import Union, Optional, Tuple, Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

def calculate_checksum(digits: str) -> str:
    """
    Calculate a Luhn algorithm checksum for account validation.
    
    The Luhn algorithm (also known as the "modulus 10" algorithm) is used to
    validate various identification numbers like credit card numbers.
    
    Args:
        digits: String of digits to calculate checksum for
    
    Returns:
        Two-digit checksum string (00-99)
        
    Raises:
        ValueError: If the input contains non-digit characters
    """
    if not isinstance(digits, str):
        digits = str(digits)
        
    if not digits.isdigit():
        raise ValueError("Checksum calculation requires a string of digits")
        
    # Luhn algorithm implementation
    def digits_of(n: int) -> list:
        """Convert a number to a list of its digits"""
        return [int(d) for d in str(n)]
    
    try:
        digits_list = [int(d) for d in digits]
        odd_digits = digits_list[-1::-2]
        even_digits = digits_list[-2::-2]
        checksum = sum(odd_digits)
        
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
            
        return f"{(10 - (checksum % 10)) % 10:02d}"
    except Exception as e:
        logger.error(f"Error calculating checksum: {str(e)}")
        return "00"  # Return default checksum on error

def validate_customer_id(customer_id: str) -> bool:
    """
    Validate a customer ID against the universal format YYDDD-BBBBB-SSSS.
    
    Args:
        customer_id: Customer ID to validate
        
    Returns:
        Boolean indicating if the ID is valid
        
    Examples:
        >>> validate_customer_id("23142-12345-8765")
        True
        >>> validate_customer_id("invalid-id")
        False
    """
    if not customer_id or not isinstance(customer_id, str):
        return False
    
    # Check against the standard format
    pattern = r'^(\d{2})(\d{3})-(\d{5})-(\d{4})$'
    match = re.match(pattern, customer_id)
    
    if not match:
        return False
    
    year, day, branch, seq = match.groups()
    
    # Validate year (00-99)
    if not (0 <= int(year) <= 99):
        return False
    
    # Validate day of year (001-366)
    if not (1 <= int(day) <= 366):
        return False
    
    # Validate branch code (5 digits)
    if len(branch) != 5:
        return False
    
    # Validate sequence (4 digits)
    if len(seq) != 4:
        return False
    
    return True

def validate_account_number(account_number: str) -> bool:
    """
    Validate an account number against the universal format BBBBB-AATT-CCCCCC-CC.
    
    Args:
        account_number: Account number to validate
        
    Returns:
        Boolean indicating if the account number is valid
    """
    if not account_number or not isinstance(account_number, str):
        return False
    
    # Check against the new format
    pattern = r'^(\d{5})-(\d{2})(\d{2})-(\d{6})-(\d{2})$'
    match = re.match(pattern, account_number)
    
    if not match:
        return False
    
    branch, account_type, sub_type, customer_part, checksum = match.groups()
    
    # Calculate checksum and compare
    base = f"{branch}{account_type}{sub_type}{customer_part}"
    calc_checksum = calculate_checksum(base)
    
    if calc_checksum != checksum:
        return False
    
    return True

def validate_transaction_id(transaction_id: str) -> bool:
    """
    Validate a transaction ID against the format TRX-YYYYMMDD-SSSSSS.
    
    Args:
        transaction_id: Transaction ID to validate
        
    Returns:
        Boolean indicating if the ID is valid
    """
    if not transaction_id or not isinstance(transaction_id, str):
        return False
    
    # Check against the new format
    pattern = r'^TRX-(\d{4})(\d{2})(\d{2})-(\d{6})$'
    match = re.match(pattern, transaction_id)
    
    if not match:
        return False
    
    year, month, day, seq = match.groups()
    
    # Validate date
    try:
        datetime.datetime(int(year), int(month), int(day))
    except ValueError:
        return False
    
    # Validate sequence
    if len(seq) != 6:
        return False
    
    return True

def validate_employee_id(employee_id: str) -> bool:
    """
    Validate an employee ID against the Bank of Baroda format ZZBB-DD-EEEE.
    
    Args:
        employee_id: Employee ID to validate
        
    Returns:
        Boolean indicating if the ID is valid
    """
    if not employee_id or not isinstance(employee_id, str):
        return False
    
    # Check against the new format
    pattern = r'^(\d{2})(\d{2})-(\d{2})-(\d{4})$'
    match = re.match(pattern, employee_id)
    
    if not match:
        return False
    
    zone, branch, designation, sequence = match.groups()
    
    # Validate zone code (01-99)
    if not (1 <= int(zone) <= 99):
        return False
    
    # Validate branch code (01-99)
    if not (1 <= int(branch) <= 99):
        return False
    
    # Validate designation code (01-99)
    if not (1 <= int(designation) <= 99):
        return False
    
    # Validate sequence (4 digits)
    if len(sequence) != 4:
        return False
    
    return True

def generate_numeric_id(length: int = 10) -> str:
    """Generate a random numeric ID of specified length."""
    return ''.join(random.choices(string.digits, k=length))

def generate_customer_id(branch_code: str = "12345") -> str:
    """
    Generate a unique customer ID with universal numeric format YYDDD-BBBBB-SSSS.
    
    Format:
    - YY: Last 2 digits of creation year
    - DDD: Day of year (001-366)
    - BBBBB: Branch code (5 digits)
    - SSSS: Customer sequence number (4 digits)
    """
    today = datetime.datetime.now()
    year_part = today.strftime("%y")  # Last 2 digits of year
    day_part = today.strftime("%j")   # Day of year (001-366)
    
    # Ensure branch_code is 5 digits
    branch_code = branch_code.zfill(5)[:5]
    
    # Generate 4-digit sequence
    sequence = generate_numeric_id(4)
    
    # Format with dashes for readability
    return f"{year_part}{day_part}-{branch_code}-{sequence}"

def generate_account_number(branch_code: str = "12345", account_type: str = "01", sub_type: str = "11") -> str:
    """
    Generate a unique account number with universal format BBBBB-AATT-CCCCCC-CC.
    
    Format:
    - BBBBB: Branch code (5 digits)
    - AA: Account type (01=Savings, 02=Current, etc.)
    - TT: Account sub-type/product code (2 digits)
    - CCCCCC: Customer serial number (6 digits)
    - CC: Checksum (2 digits)
    """
    # Ensure branch_code is 5 digits
    branch_code = branch_code.zfill(5)[:5]
    
    # Ensure account_type is 2 digits
    account_type = account_type.zfill(2)[:2]
    
    # Ensure sub_type is 2 digits
    sub_type = sub_type.zfill(2)[:2]
    
    # Generate 6-digit customer serial
    customer_serial = generate_numeric_id(6)
    
    # Calculate checksum
    checksum = calculate_checksum(f"{branch_code}{account_type}{sub_type}{customer_serial}")
    
    # Format with dashes for readability
    return f"{branch_code}-{account_type}{sub_type}-{customer_serial}-{checksum}"

def generate_transaction_id() -> str:
    """
    Generate a unique transaction ID with format TRX-YYYYMMDD-SSSSSS.
    
    Format:
    - TRX: Fixed prefix
    - YYYYMMDD: Date (year, month, day)
    - SSSSSS: Sequence number (6 digits)
    """
    # Get current date
    now = datetime.datetime.now()
    date_part = now.strftime("%Y%m%d")  # Full year, month, day
    
    # Generate 6-digit sequence number
    seq_part = generate_numeric_id(6)
    
    return f"TRX-{date_part}-{seq_part}"

def generate_employee_id(zone_code: str = "01", branch_code: str = "23", designation_code: str = "10") -> str:
    """
    Generate an employee ID with Bank of Baroda style format ZZBB-DD-EEEE.
    
    Format:
    - ZZ: Zone code (2 digits, e.g., North = 01)
    - BB: Branch or Department code (2 digits)
    - DD: Designation code (2 digits, e.g., Officer = 10)
    - EEEE: Employee sequence number (4 digits)
    """
    # Ensure zone_code is 2 digits
    zone_code = zone_code.zfill(2)[:2]
    
    # Ensure branch_code is 2 digits
    branch_code = branch_code.zfill(2)[:2]
    
    # Ensure designation_code is 2 digits
    designation_code = designation_code.zfill(2)[:2]
    
    # Generate 4-digit employee sequence number
    sequence = generate_numeric_id(4)
    
    # Format with dashes for readability
    return f"{zone_code}{branch_code}-{designation_code}-{sequence}"

def convert_customer_id(old_id: Optional[str]) -> str:
    """
    Convert old customer ID format to new format YYDDD-BBBBB-SSSS.
    Old format: CST-YYDDD-NNNNNN
    """
    if not old_id:
        return generate_customer_id()
    
    match = re.match(r'^CST-(\d{2})(\d{3})-(\d{6})$', old_id)
    if not match:
        # If format doesn't match, generate a new ID
        return generate_customer_id()
    
    year, day, seq = match.groups()
    branch_code = "12345"  # Default branch code
    
    # Take first 4 digits of the sequence
    new_seq = seq[:4]
    
    return f"{year}{day}-{branch_code}-{new_seq}"

def convert_account_number(old_number: Optional[str]) -> str:
    """
    Convert old account number format to new format BBBBB-AATT-CCCCCC-CC.
    Old format: BB-AAAAA-CCCCCCCC
    """
    if not old_number:
        return generate_account_number()
    
    match = re.match(r'^(\d{2})-(\d{5})-(\d{8})$', old_number)
    if not match:
        # If format doesn't match, generate a new account number
        return generate_account_number()
    
    bank_code, branch_code, customer_seq = match.groups()
    
    # Use first 5 chars of branch code or pad with zeros
    branch_part = branch_code.zfill(5)[:5]
    
    # Default account type (01=Savings)
    account_type = "01"
    
    # Default sub-type (11=Regular Savings)
    sub_type = "11"
    
    # Use first 6 chars of customer sequence
    customer_part = customer_seq[:6]
    
    # Calculate checksum
    base = f"{branch_part}{account_type}{sub_type}{customer_part}"
    checksum = calculate_checksum(base)
    
    return f"{branch_part}-{account_type}{sub_type}-{customer_part}-{checksum}"

def convert_transaction_id(old_id: Optional[str]) -> str:
    """
    Convert old transaction ID format to new format TRX-YYYYMMDD-SSSSSS.
    Old format: TXN-YYMMDD-HHMMSS-NNNNN
    """
    if not old_id:
        return generate_transaction_id()
    
    match = re.match(r'^TXN-(\d{2})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})-(\d{5})$', old_id)
    if not match:
        # If format doesn't match, generate a new ID
        return generate_transaction_id()
    
    year, month, day, _, _, _, seq = match.groups()
    
    # Convert 2-digit year to 4-digit year
    full_year = f"20{year}"
    
    # Use the sequence number, padded to 6 digits
    seq_part = seq.zfill(6)[:6]
    
    return f"TRX-{full_year}{month}{day}-{seq_part}"

def convert_employee_id(old_id: Optional[str]) -> str:
    """
    Convert old employee ID format to new format ZZBB-DD-EEEE.
    Old format: EMP-YYYYMM-NNNNN
    """
    if not old_id:
        return generate_employee_id()
    
    match = re.match(r'^EMP-(\d{4})(\d{2})-(\d{5})$', old_id)
    if not match:
        # If format doesn't match, generate a new ID
        return generate_employee_id()
    
    # Generate random zone code (01-99)
    zone_code = str(random.randint(1, 99)).zfill(2)
    
    # Generate random branch code (01-99)
    branch_code = str(random.randint(1, 99)).zfill(2)
    
    # Generate random designation code (01-99)
    designation_code = str(random.randint(1, 20)).zfill(2)
    
    # Use last 4 digits of the old sequence
    seq = match.group(3)[-4:].zfill(4)
    
    return f"{zone_code}{branch_code}-{designation_code}-{seq}"
