"""
Core Banking Database Models Unit Tests

This module contains unit tests for database models.
"""

import pytest
import unittest
from unittest import mock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import models
from database.python.common.database_operations import Customer, Account, Transaction, Loan


class TestCustomerModel(unittest.TestCase):
    """Unit tests for Customer model."""
    
    def test_customer_creation(self):
        """Test creating a Customer instance."""
        customer = Customer(
            customer_id="CUS123456",
            first_name="Test",
            last_name="Customer",
            email="test.customer@example.com",
            phone="1234567890",
            address="123 Test St, Test City",
            date_of_birth="1990-01-01"
        )
        
        self.assertEqual(customer.customer_id, "CUS123456")
        self.assertEqual(customer.first_name, "Test")
        self.assertEqual(customer.last_name, "Customer")
        self.assertEqual(customer.email, "test.customer@example.com")
        self.assertEqual(customer.phone, "1234567890")
        self.assertEqual(customer.address, "123 Test St, Test City")
        self.assertEqual(customer.date_of_birth, "1990-01-01")
    
    def test_customer_to_dict(self):
        """Test converting a Customer instance to dictionary."""
        customer = Customer(
            customer_id="CUS123456",
            first_name="Test",
            last_name="Customer",
            email="test.customer@example.com"
        )
        
        customer_dict = customer.to_dict()
        
        self.assertIsInstance(customer_dict, dict)
        self.assertEqual(customer_dict["customer_id"], "CUS123456")
        self.assertEqual(customer_dict["first_name"], "Test")
        self.assertEqual(customer_dict["last_name"], "Customer")
        self.assertEqual(customer_dict["email"], "test.customer@example.com")
    
    def test_customer_repr(self):
        """Test string representation of Customer."""
        customer = Customer(
            customer_id="CUS123456",
            first_name="Test",
            last_name="Customer"
        )
        
        self.assertIn("CUS123456", repr(customer))
        self.assertIn("Test", repr(customer))
        self.assertIn("Customer", repr(customer))


class TestAccountModel(unittest.TestCase):
    """Unit tests for Account model."""
    
    def test_account_creation(self):
        """Test creating an Account instance."""
        account = Account(
            account_id="ACC123456",
            customer_id="CUS123456",
            account_type="SAVINGS",
            balance=1000.00,
            currency="USD",
            status="ACTIVE"
        )
        
        self.assertEqual(account.account_id, "ACC123456")
        self.assertEqual(account.customer_id, "CUS123456")
        self.assertEqual(account.account_type, "SAVINGS")
        self.assertEqual(account.balance, 1000.00)
        self.assertEqual(account.currency, "USD")
        self.assertEqual(account.status, "ACTIVE")
    
    def test_account_to_dict(self):
        """Test converting an Account instance to dictionary."""
        account = Account(
            account_id="ACC123456",
            customer_id="CUS123456",
            account_type="SAVINGS",
            balance=1000.00
        )
        
        account_dict = account.to_dict()
        
        self.assertIsInstance(account_dict, dict)
        self.assertEqual(account_dict["account_id"], "ACC123456")
        self.assertEqual(account_dict["customer_id"], "CUS123456")
        self.assertEqual(account_dict["account_type"], "SAVINGS")
        self.assertEqual(account_dict["balance"], 1000.00)
    
    def test_account_repr(self):
        """Test string representation of Account."""
        account = Account(
            account_id="ACC123456",
            account_type="SAVINGS",
            balance=1000.00
        )
        
        self.assertIn("ACC123456", repr(account))
        self.assertIn("SAVINGS", repr(account))
        self.assertIn("1000.0", repr(account))


class TestTransactionModel(unittest.TestCase):
    """Unit tests for Transaction model."""
    
    def test_transaction_creation(self):
        """Test creating a Transaction instance."""
        transaction = Transaction(
            transaction_id="TRX123456",
            account_id="ACC123456",
            transaction_type="DEPOSIT",
            amount=500.00,
            currency="USD",
            description="Test deposit",
            status="COMPLETED"
        )
        
        self.assertEqual(transaction.transaction_id, "TRX123456")
        self.assertEqual(transaction.account_id, "ACC123456")
        self.assertEqual(transaction.transaction_type, "DEPOSIT")
        self.assertEqual(transaction.amount, 500.00)
        self.assertEqual(transaction.currency, "USD")
        self.assertEqual(transaction.description, "Test deposit")
        self.assertEqual(transaction.status, "COMPLETED")
    
    def test_transaction_to_dict(self):
        """Test converting a Transaction instance to dictionary."""
        transaction = Transaction(
            transaction_id="TRX123456",
            account_id="ACC123456",
            transaction_type="DEPOSIT",
            amount=500.00
        )
        
        transaction_dict = transaction.to_dict()
        
        self.assertIsInstance(transaction_dict, dict)
        self.assertEqual(transaction_dict["transaction_id"], "TRX123456")
        self.assertEqual(transaction_dict["account_id"], "ACC123456")
        self.assertEqual(transaction_dict["transaction_type"], "DEPOSIT")
        self.assertEqual(transaction_dict["amount"], 500.00)
    
    def test_transaction_repr(self):
        """Test string representation of Transaction."""
        transaction = Transaction(
            transaction_id="TRX123456",
            transaction_type="DEPOSIT",
            amount=500.00
        )
        
        self.assertIn("TRX123456", repr(transaction))
        self.assertIn("DEPOSIT", repr(transaction))
        self.assertIn("500.0", repr(transaction))


if __name__ == "__main__":
    unittest.main()
