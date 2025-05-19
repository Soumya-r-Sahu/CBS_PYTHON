"""
Database Workflow Utilities

This module provides utilities for verifying complete database workflows
for the Core Banking System end-to-end tests.
"""

import os
import sys
import random
import uuid
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.lib.packages import import_module
DatabaseConnection = import_module("database.python.connection").DatabaseConnection


def create_test_customer(cursor, customer_data=None):
    """Create a test customer record for workflow testing"""
    if not customer_data:
        customer_data = {
            'customer_id': f"TEST_CUST_{uuid.uuid4().hex[:8]}",
            'name': "Test Customer",
            'email': f"test{random.randint(1000, 9999)}@example.com",
            'phone': f"{random.randint(1000000000, 9999999999)}",
            'address': "123 Test Street, Test City",
            'status': 'ACTIVE'
        }
    
    cursor.execute(
        """
        INSERT INTO customers 
        (customer_id, name, email, phone, address, created_at, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            customer_data['customer_id'],
            customer_data['name'],
            customer_data['email'],
            customer_data['phone'],
            customer_data['address'],
            datetime.now(),
            customer_data['status']
        )
    )
    
    cursor.execute("SELECT LAST_INSERT_ID()")
    customer_id = cursor.fetchone()[0]
    
    return customer_id, customer_data


def create_test_account(cursor, customer_id, account_data=None):
    """Create a test account for workflow testing"""
    if not account_data:
        account_data = {
            'account_number': f"TEST_ACC_{uuid.uuid4().hex[:8]}",
            'account_type': 'SAVINGS',
            'balance': 1000.00,
            'currency': 'INR',
            'status': 'ACTIVE'
        }
    
    cursor.execute(
        """
        INSERT INTO accounts
        (customer_id, account_number, account_type, balance, currency, created_at, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            customer_id,
            account_data['account_number'],
            account_data['account_type'],
            account_data['balance'],
            account_data['currency'],
            datetime.now(),
            account_data['status']
        )
    )
    
    cursor.execute("SELECT LAST_INSERT_ID()")
    account_id = cursor.fetchone()[0]
    
    return account_id, account_data


def create_test_transaction(cursor, account_id, transaction_data=None):
    """Create a test transaction for workflow testing"""
    if not transaction_data:
        transaction_data = {
            'transaction_type': 'DEPOSIT',
            'amount': 500.00,
            'description': 'Test transaction',
            'status': 'COMPLETED'
        }
    
    cursor.execute(
        """
        INSERT INTO transactions
        (account_id, transaction_type, amount, description, created_at, status)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            account_id,
            transaction_data['transaction_type'],
            transaction_data['amount'],
            transaction_data['description'],
            datetime.now(),
            transaction_data['status']
        )
    )
    
    cursor.execute("SELECT LAST_INSERT_ID()")
    transaction_id = cursor.fetchone()[0]
    
    return transaction_id, transaction_data


def setup_complete_test_workflow():
    """Set up a complete test workflow with customer, account, and transaction"""
    conn = DatabaseConnection().get_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        conn.start_transaction()
        
        # Create test customer
        customer_id, customer = create_test_customer(cursor)
        
        # Create test account
        account_id, account = create_test_account(cursor, customer_id)
        
        # Create test transaction
        transaction_id, transaction = create_test_transaction(cursor, account_id)
        
        # Commit transaction
        conn.commit()
        
        result = {
            'customer_id': customer_id,
            'customer': customer,
            'account_id': account_id,
            'account': account,
            'transaction_id': transaction_id,
            'transaction': transaction
        }
        
        return True, result
    
    except Exception as e:
        # Rollback on error
        conn.rollback()
        print(f"Error setting up test workflow: {e}")
        return False, str(e)
    
    finally:
        # Close cursor and connection
        cursor.close()
        conn.close()


def cleanup_test_workflow(customer_id=None, account_id=None, transaction_id=None):
    """Clean up test data created for workflow testing"""
    conn = DatabaseConnection().get_connection()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        conn.start_transaction()
        
        # Delete in reverse order to respect foreign key constraints
        if transaction_id:
            cursor.execute("DELETE FROM transactions WHERE id = %s", (transaction_id,))
        
        if account_id:
            cursor.execute("DELETE FROM accounts WHERE id = %s", (account_id,))
        
        if customer_id:
            cursor.execute("DELETE FROM customers WHERE id = %s", (customer_id,))
        
        # Commit transaction
        conn.commit()
        
        return True
    
    except Exception as e:
        # Rollback on error
        conn.rollback()
        print(f"Error cleaning up test workflow: {e}")
        return False
    
    finally:
        # Close cursor and connection
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # Test the workflow setup
    success, result = setup_complete_test_workflow()
    
    if success:
        print("Test workflow setup successful")
        print(f"Customer ID: {result['customer_id']}")
        print(f"Account ID: {result['account_id']}")
        print(f"Transaction ID: {result['transaction_id']}")
        
        # Clean up the test data
        cleanup_success = cleanup_test_workflow(
            result['customer_id'], 
            result['account_id'], 
            result['transaction_id']
        )
        
        if cleanup_success:
            print("Test workflow cleanup successful")
        else:
            print("Test workflow cleanup failed")
    else:
        print(f"Test workflow setup failed: {result}")
