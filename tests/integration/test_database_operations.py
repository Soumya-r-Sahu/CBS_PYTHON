"""
Core Banking Database Integration Tests

This module contains integration tests for database operations.
These tests require an actual database connection.
"""

import pytest
import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import database modules
from database.python.connection import DatabaseConnection
from database.db_manager import get_db_session, DatabaseManager
from database.python.models import Customer, Account, Transaction

# Import verification utilities
from tests.integration.db_verification import verify_database_setup
from tests.integration.db_data_verification import verify_sample_data


class TestCustomerDatabaseOperations(unittest.TestCase):
    """Integration tests for customer database operations."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database session."""
        cls.db_session = get_db_session()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database session."""
        cls.db_session.close()
    
    def setUp(self):
        """Set up before each test."""
        # Create a test customer
        self.test_customer = Customer(
            customer_id="CUS_TEST",
            first_name="Integration",
            last_name="Test",
            email="integration.test@example.com",
            phone="1234567890",
            address="123 Integration St, Test City",
            date_of_birth="1990-01-01"
        )
        
        # Add to session but don't commit yet
        self.db_session.add(self.test_customer)
    
    def tearDown(self):
        """Clean up after each test."""
        # Roll back transaction
        self.db_session.rollback()
    
    def test_create_customer(self):
        """Test creating a customer in the database."""
        # Commit the transaction
        self.db_session.commit()
        
        # Query for the customer
        retrieved_customer = self.db_session.query(Customer).filter_by(
            customer_id="CUS_TEST"
        ).first()
        
        # Verify customer was created
        self.assertIsNotNone(retrieved_customer)
        self.assertEqual(retrieved_customer.customer_id, "CUS_TEST")
        self.assertEqual(retrieved_customer.first_name, "Integration")
        self.assertEqual(retrieved_customer.last_name, "Test")
        self.assertEqual(retrieved_customer.email, "integration.test@example.com")
    
    def test_update_customer(self):
        """Test updating a customer in the database."""
        # Commit the transaction to create the customer
        self.db_session.commit()
        
        # Query for the customer
        customer = self.db_session.query(Customer).filter_by(
            customer_id="CUS_TEST"
        ).first()
        
        # Update customer
        customer.email = "updated.email@example.com"
        customer.phone = "9876543210"
        self.db_session.commit()
        
        # Query for the updated customer
        updated_customer = self.db_session.query(Customer).filter_by(
            customer_id="CUS_TEST"
        ).first()
        
        # Verify customer was updated
        self.assertEqual(updated_customer.email, "updated.email@example.com")
        self.assertEqual(updated_customer.phone, "9876543210")
    
    def test_delete_customer(self):
        """Test deleting a customer from the database."""
        # Commit the transaction to create the customer
        self.db_session.commit()
        
        # Query for the customer
        customer = self.db_session.query(Customer).filter_by(
            customer_id="CUS_TEST"
        ).first()
        
        # Delete customer
        self.db_session.delete(customer)
        self.db_session.commit()
        
        # Query for the deleted customer
        deleted_customer = self.db_session.query(Customer).filter_by(
            customer_id="CUS_TEST"
        ).first()
        
        # Verify customer was deleted
        self.assertIsNone(deleted_customer)


class TestAccountDatabaseOperations(unittest.TestCase):
    """Integration tests for account database operations."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database session."""
        cls.db_session = get_db_session()
        
        # Create a test customer
        cls.test_customer = Customer(
            customer_id="CUS_ACC_TEST",
            first_name="Account",
            last_name="Test",
            email="account.test@example.com"
        )
        
        cls.db_session.add(cls.test_customer)
        cls.db_session.commit()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database session."""
        # Delete test customer
        customer = cls.db_session.query(Customer).filter_by(
            customer_id="CUS_ACC_TEST"
        ).first()
        
        if customer:
            cls.db_session.delete(customer)
            cls.db_session.commit()
        
        cls.db_session.close()
    
    def setUp(self):
        """Set up before each test."""
        # Create a test account
        self.test_account = Account(
            account_id="ACC_TEST",
            customer_id="CUS_ACC_TEST",
            account_type="SAVINGS",
            balance=1000.00,
            currency="USD",
            status="ACTIVE"
        )
        
        # Add to session but don't commit yet
        self.db_session.add(self.test_account)
    
    def tearDown(self):
        """Clean up after each test."""
        # Roll back transaction
        self.db_session.rollback()
    
    def test_create_account(self):
        """Test creating an account in the database."""
        # Commit the transaction
        self.db_session.commit()
        
        # Query for the account
        retrieved_account = self.db_session.query(Account).filter_by(
            account_id="ACC_TEST"
        ).first()
        
        # Verify account was created
        self.assertIsNotNone(retrieved_account)
        self.assertEqual(retrieved_account.account_id, "ACC_TEST")
        self.assertEqual(retrieved_account.customer_id, "CUS_ACC_TEST")
        self.assertEqual(retrieved_account.account_type, "SAVINGS")
        self.assertEqual(retrieved_account.balance, 1000.00)
    
    def test_update_account(self):
        """Test updating an account in the database."""
        # Commit the transaction to create the account
        self.db_session.commit()
        
        # Query for the account
        account = self.db_session.query(Account).filter_by(
            account_id="ACC_TEST"
        ).first()
        
        # Update account
        account.balance = 1500.00
        account.status = "INACTIVE"
        self.db_session.commit()
        
        # Query for the updated account
        updated_account = self.db_session.query(Account).filter_by(
            account_id="ACC_TEST"
        ).first()
        
        # Verify account was updated
        self.assertEqual(updated_account.balance, 1500.00)
        self.assertEqual(updated_account.status, "INACTIVE")


if __name__ == "__main__":
    unittest.main()
