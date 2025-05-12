"""
End-to-End Database Tests

This module contains end-to-end tests for database functionality.
Tests the database in a complete workflow context, simulating real usage scenarios.
"""

import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.connection import DatabaseConnection
from database.db_manager import get_db_session

# Import workflow utilities
from tests.e2e.db_workflow_utils import (
    setup_complete_test_workflow, 
    cleanup_test_workflow,
    create_test_customer,
    create_test_account,
    create_test_transaction
)


@pytest.fixture
def db_connection():
    """Create a database connection for testing."""
    try:
        conn = DatabaseConnection().get_connection()
        yield conn
        conn.close()
    except Exception as e:
        pytest.fail(f"Failed to create database connection: {e}")


def test_complete_account_workflow(db_connection):
    """Test a complete account workflow from creation to transactions."""
    cursor = db_connection.cursor()
    
    try:
        # Generate test data
        customer_id = "TEST_CUSTOMER"
        account_number = f"TEST_ACC_{os.urandom(4).hex()}"
        
        # 1. Create customer
        cursor.execute(
            """
            INSERT INTO customers 
            (customer_id, name, email, phone, address, created_at, status)
            VALUES (%s, %s, %s, %s, %s, NOW(), %s)
            """,
            (customer_id, "Test Customer", "test@example.com", "1234567890", 
             "Test Address", "ACTIVE")
        )
        
        # Get the internal ID
        cursor.execute("SELECT LAST_INSERT_ID()")
        internal_customer_id = cursor.fetchone()[0]
        
        # 2. Create account
        cursor.execute(
            """
            INSERT INTO accounts
            (account_number, customer_id, account_type, balance, status, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            (account_number, internal_customer_id, "SAVINGS", 1000.00, "ACTIVE")
        )
        
        # Get the internal ID
        cursor.execute("SELECT LAST_INSERT_ID()")
        internal_account_id = cursor.fetchone()[0]
        
        # 3. Perform a transaction
        cursor.execute(
            """
            INSERT INTO transactions
            (transaction_id, account_id, amount, transaction_type, status, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            (f"TRX_{os.urandom(4).hex()}", internal_account_id, 100.00, "DEPOSIT", "SUCCESS")
        )
        
        # 4. Update account balance
        cursor.execute(
            """
            UPDATE accounts
            SET balance = balance + 100.00
            WHERE id = %s
            """,
            (internal_account_id,)
        )
        
        # 5. Verify updated balance
        cursor.execute(
            """
            SELECT balance
            FROM accounts
            WHERE id = %s
            """,
            (internal_account_id,)
        )
        
        balance = cursor.fetchone()[0]
        assert balance == 1100.00, f"Expected balance 1100.00, got {balance}"
        
        # Clean up test data
        cursor.execute("DELETE FROM transactions WHERE account_id = %s", (internal_account_id,))
        cursor.execute("DELETE FROM accounts WHERE id = %s", (internal_account_id,))
        cursor.execute("DELETE FROM customers WHERE id = %s", (internal_customer_id,))
        
        db_connection.commit()
        
    except Exception as e:
        db_connection.rollback()
        pytest.fail(f"Test failed: {e}")
    finally:
        cursor.close()


def test_database_schema_validation():
    """Test that validates the entire database schema."""
    conn = DatabaseConnection().get_connection()
    cursor = conn.cursor()
    
    try:
        # Check for core tables
        core_tables = [
            "customers",
            "accounts",
            "transactions",
            "cards",
            "upi_accounts",
            "upi_transactions",
            "notifications",
            "security_events"
        ]
        
        # Get list of tables in database
        cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        for table in core_tables:
            assert table in existing_tables, f"Missing core table: {table}"
        
        # Check schema of customers table
        cursor.execute("DESCRIBE customers")
        columns = {row[0]: row[1] for row in cursor.fetchall()}
        
        assert "id" in columns, "Missing 'id' column in customers table"
        assert "customer_id" in columns, "Missing 'customer_id' column in customers table"
        assert "name" in columns, "Missing 'name' column in customers table"
        assert "email" in columns, "Missing 'email' column in customers table"
        
        # Check schema of accounts table
        cursor.execute("DESCRIBE accounts")
        columns = {row[0]: row[1] for row in cursor.fetchall()}
        
        assert "id" in columns, "Missing 'id' column in accounts table"
        assert "account_number" in columns, "Missing 'account_number' column in accounts table"
        assert "customer_id" in columns, "Missing 'customer_id' column in accounts table"
        assert "balance" in columns, "Missing 'balance' column in accounts table"
        
        # Check schema of transactions table
        cursor.execute("DESCRIBE transactions")
        columns = {row[0]: row[1] for row in cursor.fetchall()}
        
        assert "id" in columns, "Missing 'id' column in transactions table"
        assert "transaction_id" in columns, "Missing 'transaction_id' column in transactions table"
        assert "account_id" in columns, "Missing 'account_id' column in transactions table"
        assert "amount" in columns, "Missing 'amount' column in transactions table"
        
    except Exception as e:
        pytest.fail(f"Schema validation failed: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    pytest.main()
