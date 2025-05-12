"""
Database Connection Unit Tests

This module contains unit tests for database connection functionality.
These tests use mocks to avoid actual database connections.
"""

import unittest
from unittest import mock
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.connection import DatabaseConnection
from utils.config import DATABASE_CONFIG

class TestDatabaseConnection:
    """Unit tests for the DatabaseConnection class using mocks."""
    
    def test_connection_initialization(self):
        """Test that DatabaseConnection can be initialized."""
        db = DatabaseConnection()
        assert db is not None
        assert hasattr(db, 'get_connection')
    
    @mock.patch('mysql.connector.connect')
    def test_database_connection_mock(self, mock_connect):
        """Test database connection with mocked connector."""
        # Setup mock
        mock_conn = mock.MagicMock()
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn
        
        # Test the connection
        db = DatabaseConnection()
        conn = db.get_connection()
        
        assert conn is not None
        assert conn.is_connected() == True
        
        # Verify mock was called with expected args
        mock_connect.assert_called_once()
        
        db.close_connection()
    
    @mock.patch('mysql.connector.connect')
    def test_connection_with_config(self, mock_connect):
        """Test connecting with specific configuration."""
        # Setup mock
        mock_conn = mock.MagicMock()
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn
        
        # Test with config
        test_config = DATABASE_CONFIG.copy()
        db = DatabaseConnection(config=test_config)
        conn = db.get_connection()
        
        assert conn is not None
        assert conn.is_connected() == True
        
        # Verify mock was called with our config
        mock_connect.assert_called_once_with(**test_config)
        
        db.close_connection()
    
    def test_connection_retry(self):
        """Test the connection retry logic."""
        # Create invalid config to force retry
        invalid_config = DATABASE_CONFIG.copy()
        invalid_config['port'] = 9999  # Invalid port
        
        with pytest.raises(Exception):
            # Should retry and eventually fail with max retries
            db = DatabaseConnection(config=invalid_config, max_retries=2, retry_delay=1)
            conn = db.get_connection()
    
    def test_cursor_creation(self, db_connection):
        """Test that we can create a cursor."""
        cursor = db_connection.cursor()
        assert cursor is not None
        cursor.close()

    def test_execute_query(self, db_connection):
        """Test executing a simple query."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT VERSION()")
        result = cursor.fetchone()
        
        assert result is not None
        assert len(result) > 0
        
        cursor.close()
    
    def test_database_existence(self, db_connection):
        """Test that our database exists."""
        cursor = db_connection.cursor()
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()[0]
        
        # Should be our test database
        assert db_name is not None
        assert "_test" in db_name
        
        cursor.close()
