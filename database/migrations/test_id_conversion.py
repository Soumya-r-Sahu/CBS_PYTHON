"""
Test ID Conversion Functions

This script tests the ID conversion functions to make sure they correctly convert
between old and new formats.
"""

import re
import random
import string
from datetime import datetime

def calculate_checksum(digits):
    """Calculate a Luhn algorithm checksum for account validation"""
    def digits_of(n):
        return [int(d) for d in str(n)]
    
    digits = [int(d) for d in digits]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return f"{(10 - (checksum % 10)) % 10:02d}"

def generate_numeric_id(length=10):
    """Generate a random numeric ID of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def convert_customer_id(old_id):
    """
    Convert old customer ID format to new format YYDDD-BBBBB-SSSS
    Old format: CST-YYDDD-NNNNNN
    """
    if not old_id:
        return "Invalid ID"
    
    match = re.match(r'^CST-(\d{2})(\d{3})-(\d{6})$', old_id)
    if not match:
        return "Format doesn't match"
    
    year, day, seq = match.groups()
    branch_code = "12345"  # Default branch code
    
    # Take first 4 digits of the sequence
    new_seq = seq[:4]
    
    return f"{year}{day}-{branch_code}-{new_seq}"

def convert_account_number(old_number):
    """
    Convert old account number format to new format BBBBB-AATT-CCCCCC-CC
    Old format: BB-AAAAA-CCCCCCCC
    """
    if not old_number:
        return "Invalid number"
    
    match = re.match(r'^(\d{2})-(\d{5})-(\d{8})$', old_number)
    if not match:
        return "Format doesn't match"
    
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

def convert_transaction_id(old_id):
    """
    Convert old transaction ID format to new format TRX-YYYYMMDD-SSSSSS
    Old format: TXN-YYMMDD-HHMMSS-NNNNN
    """
    if not old_id:
        return "Invalid ID"
    
    match = re.match(r'^TXN-(\d{2})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})-(\d{5})$', old_id)
    if not match:
        return "Format doesn't match"
    
    year, month, day, _, _, _, seq = match.groups()
    
    # Convert 2-digit year to 4-digit year
    full_year = f"20{year}"
    
    # Use the sequence number, padded to 6 digits
    seq_part = seq.zfill(6)[:6]
    
    return f"TRX-{full_year}{month}{day}-{seq_part}"

def convert_employee_id(old_id):
    """
    Convert old employee ID format to new format ZZBB-DD-EEEE
    Old format: EMP-YYYYMM-NNNNN
    """
    if not old_id:
        return "Invalid ID"
    
    match = re.match(r'^EMP-(\d{4})(\d{2})-(\d{5})$', old_id)
    if not match:
        return "Format doesn't match"
    
    # Generate random zone code (01-99)
    zone_code = str(random.randint(1, 99)).zfill(2)
    
    # Generate random branch code (01-99)
    branch_code = str(random.randint(1, 99)).zfill(2)
    
    # Generate random designation code (01-99)
    designation_code = str(random.randint(1, 20)).zfill(2)
    
    # Use last 4 digits of the old sequence
    seq = match.group(3)[-4:].zfill(4)
    
    return f"{zone_code}{branch_code}-{designation_code}-{seq}"

def main():
    print("Testing ID conversion functions\n")
    
    # Test customer ID conversion
    print("Customer ID Conversion:")
    customer_ids = [
        "CST-22123-123456",
        "CST-21001-987654",
        "CST-23365-123123"
    ]
    for old_id in customer_ids:
        new_id = convert_customer_id(old_id)
        print(f"  {old_id} -> {new_id}")
    
    # Test account number conversion
    print("\nAccount Number Conversion:")
    account_numbers = [
        "12-34567-12345678",
        "99-12345-87654321",
        "01-56789-12345123"
    ]
    for old_number in account_numbers:
        new_number = convert_account_number(old_number)
        print(f"  {old_number} -> {new_number}")
    
    # Test transaction ID conversion
    print("\nTransaction ID Conversion:")
    transaction_ids = [
        "TXN-220513-123045-12345",
        "TXN-210101-235959-99999",
        "TXN-231225-101010-54321"
    ]
    for old_id in transaction_ids:
        new_id = convert_transaction_id(old_id)
        print(f"  {old_id} -> {new_id}")
    
    # Test employee ID conversion
    print("\nEmployee ID Conversion:")
    employee_ids = [
        "EMP-202205-12345",
        "EMP-201904-54321",
        "EMP-202312-99999"
    ]
    for old_id in employee_ids:
        new_id = convert_employee_id(old_id)
        print(f"  {old_id} -> {new_id}")

if __name__ == "__main__":
    main()
