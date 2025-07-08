"""
Core Banking System Test Fixtures

This module contains pytest fixtures used across different test categories.
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Database fixtures
@pytest.fixture(scope="session")
def db_connection():
    """Create a database connection for testing."""
    from database.python.connection import DatabaseConnection
    
    # Create connection
    db = DatabaseConnection()
    connection = db.get_connection()
    
    yield connection
    
    # Cleanup after tests
    connection.close()

@pytest.fixture(scope="session")
def db_session():
    """Create a database session for testing."""
    from database.db_manager import get_db_session
    
    # Create session
    session = get_db_session()
    
    yield session
    
    # Cleanup after tests
    session.close()

# Mock database fixtures
@pytest.fixture
def mock_db_connection(monkeypatch):
    """Mock database connection for unit tests."""
    import unittest.mock as mock
    
    mock_connection = mock.MagicMock()
    mock_cursor = mock.MagicMock()
    
    # Configure mocks
    mock_connection.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (1,)
    mock_cursor.fetchall.return_value = [(1, 'test'), (2, 'test2')]
    
    # Apply monkeypatch
    monkeypatch.setattr(
        'database.python.connection.DatabaseConnection.get_connection',
        lambda self: mock_connection
    )
    
    return mock_connection, mock_cursor

# Customer fixtures
@pytest.fixture
def sample_customer_data():
    """Return sample customer data for tests."""
    return {
        'customer_id': 'CUS123456',
        'first_name': 'Test',
        'last_name': 'Customer',
        'email': 'test.customer@example.com',
        'phone': '1234567890',
        'address': '123 Test St, Test City',
        'date_of_birth': '1990-01-01'
    }

# Account fixtures
@pytest.fixture
def sample_account_data():
    """Return sample account data for tests."""
    return {
        'account_id': 'ACC123456',
        'customer_id': 'CUS123456',
        'account_type': 'SAVINGS',
        'balance': 1000.00,
        'currency': 'USD',
        'status': 'ACTIVE',
        'created_at': '2023-01-01',
        'updated_at': '2023-01-01'
    }

# Transaction fixtures
@pytest.fixture
def sample_transaction_data():
    """Return sample transaction data for tests."""
    return {
        'transaction_id': 'TRX123456',
        'account_id': 'ACC123456',
        'transaction_type': 'DEPOSIT',
        'amount': 500.00,
        'currency': 'USD',
        'description': 'Test deposit',
        'status': 'COMPLETED',
        'created_at': '2023-01-01'
    }

# API client fixture
@pytest.fixture
def api_client():
    """Create a test client for API tests."""
    import requests
    from unittest.mock import patch
    
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            
        def json(self):
            return self.json_data
    
    # Create patch for requests
    with patch('requests.get') as mock_get, patch('requests.post') as mock_post:
        # Configure default responses
        mock_get.return_value = MockResponse({'status': 'success'}, 200)
        mock_post.return_value = MockResponse({'status': 'success'}, 201)
        
        yield requests
