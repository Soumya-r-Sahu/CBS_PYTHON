"""
Customer Model Tests

This module contains tests for customer-related functionality.
"""

import pytest
from datetime import datetime, date
import mysql.connector

class TestCustomerModel:
    """Tests for the Customer model."""
    
    def test_customer_creation(self, clean_test_db, sample_customer_data):
        """Test that a customer can be created."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Check that our test customer exists
        cursor.execute(
            "SELECT * FROM cbs_customers WHERE customer_id = %s",
            (sample_customer_data["customer_id"],)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == sample_customer_data["customer_id"]
        assert result[1] == sample_customer_data["name"]
        
        cursor.close()
    
    def test_customer_update(self, clean_test_db, sample_customer_data):
        """Test that a customer can be updated."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Update the customer
        cursor.execute(
            "UPDATE cbs_customers SET occupation = %s WHERE customer_id = %s",
            ("Developer", sample_customer_data["customer_id"])
        )
        conn.commit()
        
        # Check that the update was successful
        cursor.execute(
            "SELECT occupation FROM cbs_customers WHERE customer_id = %s",
            (sample_customer_data["customer_id"],)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == "Developer"
        
        cursor.close()
    
    def test_customer_deletion(self, clean_test_db, sample_customer_data):
        """Test that a customer can be deleted."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Delete the customer
        cursor.execute(
            "DELETE FROM cbs_customers WHERE customer_id = %s",
            (sample_customer_data["customer_id"],)
        )
        conn.commit()
        
        # Check that the customer no longer exists
        cursor.execute(
            "SELECT COUNT(*) FROM cbs_customers WHERE customer_id = %s",
            (sample_customer_data["customer_id"],)
        )
        count = cursor.fetchone()[0]
        
        assert count == 0
        
        cursor.close()
    
    def test_get_customer_by_id(self, clean_test_db, sample_customer_data):
        """Test retrieving a customer by ID."""
        conn = clean_test_db
        cursor = conn.cursor(dictionary=True)
        
        # Retrieve the customer
        cursor.execute(
            "SELECT * FROM cbs_customers WHERE customer_id = %s",
            (sample_customer_data["customer_id"],)
        )
        customer = cursor.fetchone()
        
        assert customer is not None
        assert customer["customer_id"] == sample_customer_data["customer_id"]
        assert customer["name"] == sample_customer_data["name"]
        
        cursor.close()
    
    def test_get_all_customers(self, clean_test_db, sample_customer_data):
        """Test retrieving all customers."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Insert another customer
        cursor.execute(
            """
            INSERT INTO cbs_customers 
            (customer_id, name, dob, gender, customer_segment) 
            VALUES (%s, %s, %s, %s, %s)
            """,
            ("CUS1002TEST", "Another Customer", "1992-02-02", "FEMALE", "CORPORATE")
        )
        conn.commit()
        
        # Retrieve all customers
        cursor.execute("SELECT COUNT(*) FROM cbs_customers")
        count = cursor.fetchone()[0]
        
        assert count == 2
        
        cursor.close()
    
    def test_customer_validation(self, clean_test_db):
        """Test customer data validation."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Try to insert invalid data (wrong gender enum value)
        with pytest.raises(Exception):
            cursor.execute(
                """
                INSERT INTO cbs_customers 
                (customer_id, name, dob, gender, customer_segment) 
                VALUES (%s, %s, %s, %s, %s)
                """,
                ("CUS1003TEST", "Invalid Customer", "1993-03-03", "INVALID_GENDER", "RETAIL")
            )
            conn.commit()
        
        # Make sure the invalid customer wasn't inserted
        cursor.execute("SELECT COUNT(*) FROM cbs_customers WHERE customer_id = 'CUS1003TEST'")
        count = cursor.fetchone()[0]
        
        assert count == 0
        
        cursor.close()
