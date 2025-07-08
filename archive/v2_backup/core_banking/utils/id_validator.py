"""
ID Validator

This module provides validation functions for the new ID formats in the Core Banking System.
It enforces validation rules for customer IDs, account numbers, transaction IDs, and employee IDs.
"""

import re
from datetime import datetime

def validate_customer_id(customer_id: str) -> bool:
    """
    Validates a customer ID in the format YYDDD-BBBBB-SSSS
    
    Args:
        customer_id: Customer ID string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not customer_id:
        return False
    
    # Check format with regex
    pattern = r'^(\d{2})(\d{3})-(\d{5})-(\d{4})$'
    match = re.match(pattern, customer_id)
    
    if not match:
        return False
    
    # Extract components
    year, day, branch, sequence = match.groups()
    
    # Validate year (allow up to next year for pre-generated IDs)
    current_year = int(datetime.now().strftime('%y'))
    if not (0 <= int(year) <= current_year + 1):
        return False
    
    # Validate day of year (1-366)
    day_num = int(day)
    if not (1 <= day_num <= 366):
        return False
    
    # Further validation could include checking if branch code exists
    
    return True

def validate_account_number(account_number: str) -> bool:
    """
    Validates an account number in the format BBBBB-AATT-CCCCCC-CC
    
    Args:
        account_number: Account number string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not account_number:
        return False
    
    # Check format with regex
    pattern = r'^(\d{5})-(\d{2})(\d{2})-(\d{6})-(\d{2})$'
    match = re.match(pattern, account_number)
    
    if not match:
        return False
    
    # Extract components
    branch, acc_type, sub_type, customer_serial, checksum = match.groups()
    
    # Validate account type (01-99)
    acc_type_num = int(acc_type)
    if not (1 <= acc_type_num <= 99):
        return False
    
    # Validate sub-type (01-99)
    sub_type_num = int(sub_type)
    if not (1 <= sub_type_num <= 99):
        return False
    
    # Validate checksum using Luhn algorithm
    digits = f"{branch}{acc_type}{sub_type}{customer_serial}"
    calculated_checksum = calculate_checksum(digits)
    
    if calculated_checksum != checksum:
        return False
    
    return True

def validate_transaction_id(transaction_id: str) -> bool:
    """
    Validates a transaction ID in the format TRX-YYYYMMDD-SSSSSS
    
    Args:
        transaction_id: Transaction ID string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not transaction_id:
        return False
    
    # Check format with regex
    pattern = r'^TRX-(\d{4})(\d{2})(\d{2})-(\d{6})$'
    match = re.match(pattern, transaction_id)
    
    if not match:
        return False
    
    # Extract components
    year, month, day, sequence = match.groups()
    
    # Validate date components
    try:
        date = datetime(int(year), int(month), int(day))
        
        # Don't allow future dates more than 1 day ahead (for pre-generated IDs)
        current_date = datetime.now()
        if (date - current_date).days > 1:
            return False
    except ValueError:
        # Invalid date
        return False
    
    return True

def validate_employee_id(employee_id: str) -> bool:
    """
    Validates an employee ID in the format ZZBB-DD-EEEE
    
    Args:
        employee_id: Employee ID string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not employee_id:
        return False
    
    # Check format with regex
    pattern = r'^(\d{2})(\d{2})-(\d{2})-(\d{4})$'
    match = re.match(pattern, employee_id)
    
    if not match:
        return False
    
    # Extract components
    zone, branch, designation, sequence = match.groups()
    
    # Validate zone code (01-99)
    zone_num = int(zone)
    if not (1 <= zone_num <= 99):
        return False
    
    # Validate branch code (01-99)
    branch_num = int(branch)
    if not (1 <= branch_num <= 99):
        return False
    
    # Validate designation code (01-99)
    designation_num = int(designation)
    if not (1 <= designation_num <= 99):
        return False
    
    return True

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
