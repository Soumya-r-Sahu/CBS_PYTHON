"""
Database Migration Script for ID Format Conversion

This script updates existing database records to use the new universal ID formats:
1. Customer IDs: YYDDD-BBBBB-SSSS
2. Account Numbers: BBBBB-AATT-CCCCCC-CC
3. Transaction IDs: TRX-YYYYMMDD-SSSSSS
4. Employee IDs: ZZBB-DD-EEEE

Run this script after updating the id_generator.py and id_validator.py modules.
"""

import os
import sys
import re
import datetime
import random
import string
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import argparse

# Use centralized import system
try:
    from utils.lib.packages import fix_path
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    print("Warning: Import manager not available. Continuing with standard imports.")

# Define the calculate_checksum function
def calculate_checksum(digits):
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

# Define generator functions
def generate_customer_id(branch_code="12345"):
    """Generate a customer ID with universal numeric format YYDDD-BBBBB-SSSS"""
    today = datetime.datetime.now()
    year_part = today.strftime("%y")
    day_part = today.strftime("%j")
    branch_code = branch_code.zfill(5)[:5]
    sequence = ''.join(random.choices(string.digits, k=4))
    return f"{year_part}{day_part}-{branch_code}-{sequence}"

def generate_account_number(branch_code="12345", account_type="01", sub_type="11"):
    """Generate a unique account number with universal format BBBBB-AATT-CCCCCC-CC"""
    branch_code = branch_code.zfill(5)[:5]
    account_type = account_type.zfill(2)[:2]
    sub_type = sub_type.zfill(2)[:2]
    customer_serial = ''.join(random.choices(string.digits, k=6))
    checksum = calculate_checksum(f"{branch_code}{account_type}{sub_type}{customer_serial}")
    return f"{branch_code}-{account_type}{sub_type}-{customer_serial}-{checksum}"

def generate_transaction_id():
    """Generate a unique transaction ID with format TRX-YYYYMMDD-SSSSSS"""
    date_part = datetime.datetime.now().strftime("%Y%m%d")
    seq_part = ''.join(random.choices(string.digits, k=6))
    return f"TRX-{date_part}-{seq_part}"

def generate_employee_id(zone_code="01", branch_code="23", designation_code="10"):
    """Generate an employee ID with Bank of Baroda style format ZZBB-DD-EEEE"""
    zone_code = zone_code.zfill(2)[:2]
    branch_code = branch_code.zfill(2)[:2]
    designation_code = designation_code.zfill(2)[:2]
    sequence = ''.join(random.choices(string.digits, k=4))
    return f"{zone_code}{branch_code}-{designation_code}-{sequence}"

def get_connection_string():
    """Get database connection string from environment variables"""
    try:
        # Try to get from environment variables first
        host = os.environ.get('CBS_DB_HOST', 'localhost')
        port = os.environ.get('CBS_DB_PORT', '3306')
        user = os.environ.get('CBS_DB_USER', 'root')
        password = os.environ.get('CBS_DB_PASSWORD', '')
        database = os.environ.get('CBS_DB_NAME', 'cbs')
          # Try to load from config if available
        try:
            # Try new config location first
            from utils.config.database import DATABASE_CONFIG as db_config
        except ImportError:
            try:
                # Fall back to old config location
                # Import with fallback for backward compatibility
                try:
                    from utils.config.config_loader import config
                except ImportError:
                    # Fallback to old import path
                    from app.config.config_loader import config
                db_config = config.get('database', {})
            except ImportError:
                db_config = {}
            host = db_config.get('host', host)
            port = db_config.get('port', port)
            user = db_config.get('user', user)
            password = db_config.get('password', password)
            database = db_config.get('database', database)
        except ImportError:
            # If config module not available, use environment variables
            pass
            
        return f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"
    except Exception as e:
        print(f"Error getting connection string: {e}")
        return None

def create_id_mapping_tables(engine):
    """Create temporary tables to store ID mappings"""
    with engine.begin() as conn:
        # Customer ID mapping table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS cbs_id_migration_customer (
            old_id VARCHAR(20) NOT NULL PRIMARY KEY,
            new_id VARCHAR(20) NOT NULL,
            migrated BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))
        
        # Account number mapping table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS cbs_id_migration_account (
            old_number VARCHAR(20) NOT NULL PRIMARY KEY,
            new_number VARCHAR(20) NOT NULL,
            migrated BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))
        
        # Transaction ID mapping table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS cbs_id_migration_transaction (
            old_id VARCHAR(25) NOT NULL PRIMARY KEY,
            new_id VARCHAR(25) NOT NULL,
            migrated BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))
        
        # Employee ID mapping table
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS cbs_id_migration_employee (
            old_id VARCHAR(20) NOT NULL PRIMARY KEY,
            new_id VARCHAR(20) NOT NULL,
            migrated BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """))
        
        print("Created ID mapping tables")

def convert_customer_id(old_id):
    """
    Convert old customer ID format to new format YYDDD-BBBBB-SSSS
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

def convert_account_number(old_number):
    """
    Convert old account number format to new format BBBBB-AATT-CCCCCC-CC
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

def convert_transaction_id(old_id):
    """
    Convert old transaction ID format to new format TRX-YYYYMMDD-SSSSSS
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

def convert_employee_id(old_id):
    """
    Convert old employee ID format to new format ZZBB-DD-EEEE
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

def update_customer_ids(engine, dry_run=True):
    """Update customer IDs in the database"""
    with engine.begin() as conn:
        # Get all customer IDs
        result = conn.execute(text("SELECT id, customer_id FROM cbs_customers"))
        customers = result.fetchall()
        
        print(f"Found {len(customers)} customers to update")
        
        # Create mapping of old ID to new ID
        for customer in customers:
            old_id = customer[1]
            new_id = convert_customer_id(old_id)
            
            # Insert into mapping table
            conn.execute(text(
                "INSERT INTO cbs_id_migration_customer (old_id, new_id) VALUES (:old, :new)"
            ), {"old": old_id, "new": new_id})
            
            if not dry_run:
                # Update the customer ID
                conn.execute(text(
                    "UPDATE cbs_customers SET customer_id = :new_id WHERE customer_id = :old_id"
                ), {"new_id": new_id, "old_id": old_id})
                
                # Update the mapping table
                conn.execute(text(
                    "UPDATE cbs_id_migration_customer SET migrated = TRUE WHERE old_id = :old_id"
                ), {"old_id": old_id})
        
        print(f"{'Would update' if dry_run else 'Updated'} {len(customers)} customer IDs")

def update_account_numbers(engine, dry_run=True):
    """Update account numbers in the database"""
    with engine.begin() as conn:
        # Get all account numbers
        result = conn.execute(text("SELECT id, account_number FROM cbs_accounts"))
        accounts = result.fetchall()
        
        print(f"Found {len(accounts)} accounts to update")
        
        # Create mapping of old number to new number
        for account in accounts:
            old_number = account[1]
            new_number = convert_account_number(old_number)
            
            # Insert into mapping table
            conn.execute(text(
                "INSERT INTO cbs_id_migration_account (old_number, new_number) VALUES (:old, :new)"
            ), {"old": old_number, "new": new_number})
            
            if not dry_run:
                # Update the account number
                conn.execute(text(
                    "UPDATE cbs_accounts SET account_number = :new_number WHERE account_number = :old_number"
                ), {"new_number": new_number, "old_number": old_number})
                
                # Update the mapping table
                conn.execute(text(
                    "UPDATE cbs_id_migration_account SET migrated = TRUE WHERE old_number = :old_number"
                ), {"old_number": old_number})
        
        print(f"{'Would update' if dry_run else 'Updated'} {len(accounts)} account numbers")

def update_transaction_ids(engine, dry_run=True):
    """Update transaction IDs in the database"""
    with engine.begin() as conn:
        # Get all transaction IDs
        result = conn.execute(text("SELECT id, transaction_id FROM cbs_transactions"))
        transactions = result.fetchall()
        
        print(f"Found {len(transactions)} transactions to update")
        
        # Create mapping of old ID to new ID
        for transaction in transactions:
            old_id = transaction[1]
            new_id = convert_transaction_id(old_id)
            
            # Insert into mapping table
            conn.execute(text(
                "INSERT INTO cbs_id_migration_transaction (old_id, new_id) VALUES (:old, :new)"
            ), {"old": old_id, "new": new_id})
            
            if not dry_run:
                # Update the transaction ID
                conn.execute(text(
                    "UPDATE cbs_transactions SET transaction_id = :new_id WHERE transaction_id = :old_id"
                ), {"new_id": new_id, "old_id": old_id})
                
                # Update the mapping table
                conn.execute(text(
                    "UPDATE cbs_id_migration_transaction SET migrated = TRUE WHERE old_id = :old_id"
                ), {"old_id": old_id})
        
        print(f"{'Would update' if dry_run else 'Updated'} {len(transactions)} transaction IDs")

def update_employee_ids(engine, dry_run=True):
    """Update employee IDs in the database"""
    with engine.begin() as conn:
        # Get all employee IDs
        result = conn.execute(text("SELECT id, employee_id FROM cbs_employee_directory"))
        employees = result.fetchall()
        
        print(f"Found {len(employees)} employees to update")
        
        # Create mapping of old ID to new ID
        for employee in employees:
            old_id = employee[1]
            new_id = convert_employee_id(old_id)
            
            # Insert into mapping table
            conn.execute(text(
                "INSERT INTO cbs_id_migration_employee (old_id, new_id) VALUES (:old, :new)"
            ), {"old": old_id, "new": new_id})
            
            if not dry_run:
                # Update the employee ID
                conn.execute(text(
                    "UPDATE cbs_employee_directory SET employee_id = :new_id WHERE employee_id = :old_id"
                ), {"new_id": new_id, "old_id": old_id})
                
                # Update the mapping table
                conn.execute(text(
                    "UPDATE cbs_id_migration_employee SET migrated = TRUE WHERE old_id = :old_id"
                ), {"old_id": old_id})
        
        print(f"{'Would update' if dry_run else 'Updated'} {len(employees)} employee IDs")

def main():
    parser = argparse.ArgumentParser(description="Migrate database IDs to new formats")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    parser.add_argument("--customers", action="store_true", help="Update customer IDs")
    parser.add_argument("--accounts", action="store_true", help="Update account numbers")
    parser.add_argument("--transactions", action="store_true", help="Update transaction IDs")
    parser.add_argument("--employees", action="store_true", help="Update employee IDs")
    parser.add_argument("--all", action="store_true", help="Update all ID types")
    parser.add_argument("--test", action="store_true", help="Run with test database (SQLite)")
    
    args = parser.parse_args()
    
    # If no specific ID type is selected, update all
    if not (args.customers or args.accounts or args.transactions or args.employees):
        args.all = True
    
    # Use SQLite for testing if requested
    conn_string = None
    if args.test:
        conn_string = "sqlite:///:memory:"
        print("Using in-memory SQLite database for testing")
    else:
        conn_string = get_connection_string()
        
    if not conn_string:
        print("Error: Could not get database connection string")
        sys.exit(1)
    
    try:
        engine = create_engine(conn_string)
        print("Connected to database")
        
        # Create mapping tables
        create_id_mapping_tables(engine)
        
        # Update IDs based on arguments
        if args.all or args.customers:
            update_customer_ids(engine, args.dry_run)
        
        if args.all or args.accounts:
            update_account_numbers(engine, args.dry_run)
        
        if args.all or args.transactions:
            update_transaction_ids(engine, args.dry_run)
        
        if args.all or args.employees:
            update_employee_ids(engine, args.dry_run)
        
        print("Migration completed successfully")
        
        if args.dry_run:
            print("\nThis was a dry run. No changes were made to the database.")
            print("Run without --dry-run to apply the changes.")
    
    except Exception as e:
        print(f"Error during migration: {e}")
        sys.exit(1)

def test_id_conversions():
    """Test the ID conversion functions"""
    print("\nTesting ID conversion functions:")
    
    # Test customer ID conversion
    old_customer_id = "CST-22123-123456"
    new_customer_id = convert_customer_id(old_customer_id)
    print(f"Customer ID: {old_customer_id} -> {new_customer_id}")
    
    # Test account number conversion
    old_account_number = "12-34567-12345678"
    new_account_number = convert_account_number(old_account_number)
    print(f"Account Number: {old_account_number} -> {new_account_number}")
    
    # Test transaction ID conversion
    old_transaction_id = "TXN-220513-123045-12345"
    new_transaction_id = convert_transaction_id(old_transaction_id)
    print(f"Transaction ID: {old_transaction_id} -> {new_transaction_id}")
    
    # Test employee ID conversion
    old_employee_id = "EMP-202205-12345"
    new_employee_id = convert_employee_id(old_employee_id)
    print(f"Employee ID: {old_employee_id} -> {new_employee_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate database IDs to new formats")
    parser.add_argument("--test-only", action="store_true", help="Only run conversion tests without database operations")
    args, remaining_args = parser.parse_known_args()
    
    if args.test_only:
        test_id_conversions()
    else:
        sys.argv = [sys.argv[0]] + remaining_args
        main()
