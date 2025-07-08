"""
Account Model Tests

This module contains tests for account-related functionality.
"""

import pytest
from datetime import datetime, date
import mysql.connector

class TestAccountModel:
    """Tests for the Account model."""
    
    def test_account_creation(self, clean_test_db, sample_account_data):
        """Test that an account can be created."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Check that our test account exists
        cursor.execute(
            "SELECT * FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == sample_account_data["account_number"]
        
        cursor.close()
    
    def test_account_update_balance(self, clean_test_db, sample_account_data):
        """Test that an account balance can be updated."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Update the account balance
        new_balance = 15000.00
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (new_balance, sample_account_data["account_number"])
        )
        conn.commit()
        
        # Check that the update was successful
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert float(result[0]) == new_balance
        
        cursor.close()
    
    def test_account_status_change(self, clean_test_db, sample_account_data):
        """Test that an account status can be changed."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Change the account status
        new_status = "INACTIVE"
        cursor.execute(
            "UPDATE cbs_accounts SET status = %s WHERE account_number = %s",
            (new_status, sample_account_data["account_number"])
        )
        conn.commit()
        
        # Check that the update was successful
        cursor.execute(
            "SELECT status FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == new_status
        
        cursor.close()
    
    def test_get_account_by_customer(self, clean_test_db, sample_account_data, sample_customer_data):
        """Test retrieving accounts by customer ID."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Retrieve account by customer ID
        cursor.execute(
            "SELECT * FROM cbs_accounts WHERE customer_id = %s",
            (sample_customer_data["customer_id"],)
        )
        results = cursor.fetchall()
        
        assert len(results) == 1
        assert results[0][0] == sample_account_data["account_number"]
        assert results[0][1] == sample_customer_data["customer_id"]
        
        cursor.close()
    
    def test_multiple_accounts_per_customer(self, clean_test_db, sample_account_data, sample_customer_data):
        """Test that a customer can have multiple accounts."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Insert second account for the same customer
        cursor.execute(
            """
            INSERT INTO cbs_accounts 
            (account_number, customer_id, account_type, balance, status, branch_code, ifsc_code) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                "ACC1002TEST", 
                sample_customer_data["customer_id"],
                "CURRENT",
                20000.00,
                "ACTIVE",
                "BR001",
                "CBSTEST001"
            )
        )
        conn.commit()
        
        # Check that both accounts exist for the customer
        cursor.execute(
            "SELECT COUNT(*) FROM cbs_accounts WHERE customer_id = %s",
            (sample_customer_data["customer_id"],)
        )
        count = cursor.fetchone()[0]
        
        assert count == 2
        
        cursor.close()
    
    def test_invalid_account_type(self, clean_test_db, sample_customer_data):
        """Test validation of account type."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Try to insert invalid account type
        with pytest.raises(Exception):
            cursor.execute(
                """
                INSERT INTO cbs_accounts 
                (account_number, customer_id, account_type, balance, status, branch_code, ifsc_code) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    "ACC1003TEST", 
                    sample_customer_data["customer_id"],
                    "INVALID_TYPE",
                    5000.00,
                    "ACTIVE",
                    "BR001",
                    "CBSTEST001"
                )
            )
            conn.commit()
        
        cursor.close()
