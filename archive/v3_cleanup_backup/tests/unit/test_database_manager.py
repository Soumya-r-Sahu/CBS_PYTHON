"""
Database Unit Tests

This module contains unit tests for database-related functionality.
Tests in this module are focused on database components and don't require 
actual database connections.
"""

import pytest
import os
import sys
import unittest
from unittest import mock

# Add parent directory to path

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, get_database_connection
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


from database.db_manager import DatabaseManager, Base


class TestDatabaseManager(unittest.TestCase):
    """Unit tests for DatabaseManager class."""
    
    @mock.patch('database.db_manager.create_engine')
    @mock.patch('database.db_manager.scoped_session')
    @mock.patch('database.db_manager.sessionmaker')
    @mock.patch('database.db_manager.load_config')
    def test_initialize(self, mock_load_config, mock_sessionmaker, 
                        mock_scoped_session, mock_create_engine):
        """Test database manager initialization with mocked dependencies."""
        # Setup mock
        mock_load_config.return_value = {
            'driver': 'mysql+mysqlconnector',
            'username': 'test_user',
            'password': 'test_pass',
            'host': 'localhost',
            'port': 3306,
            'name': 'test_db',
            'pool_size': 5,
            'max_overflow': 10,
            'timeout': 30
        }
        
        mock_engine = mock.MagicMock()
        mock_create_engine.return_value = mock_engine
        
        mock_session_factory = mock.MagicMock()
        mock_scoped_session.return_value = mock_session_factory
        
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Verify initialize was called
        mock_load_config.assert_called_once()
        mock_create_engine.assert_called_once()
        mock_sessionmaker.assert_called_once()
        mock_scoped_session.assert_called_once()
        
    @mock.patch('database.db_manager.create_engine')
    @mock.patch('database.db_manager.scoped_session')
    @mock.patch('database.db_manager.sessionmaker')
    @mock.patch('database.db_manager.load_config')
    def test_get_session(self, mock_load_config, mock_sessionmaker, 
                        mock_scoped_session, mock_create_engine):
        """Test get_session method."""
        # Setup mock
        mock_load_config.return_value = {
            'driver': 'mysql+mysqlconnector',
            'username': 'test_user',
            'password': 'test_pass',
            'host': 'localhost',
            'port': 3306,
            'name': 'test_db'
        }
        
        mock_session_factory = mock.MagicMock()
        mock_scoped_session.return_value = mock_session_factory
        
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Get session
        db_manager.get_session()
        
        # Verify session factory was called
        mock_session_factory.assert_called_once()
        
    @mock.patch('database.db_manager.create_engine')
    @mock.patch('database.db_manager.scoped_session')
    @mock.patch('database.db_manager.sessionmaker')
    @mock.patch('database.db_manager.load_config')
    def test_create_tables(self, mock_load_config, mock_sessionmaker, 
                          mock_scoped_session, mock_create_engine):
        """Test create_tables method."""
        # Setup mock
        mock_load_config.return_value = {
            'driver': 'mysql+mysqlconnector',
            'username': 'test_user',
            'password': 'test_pass',
            'host': 'localhost',
            'port': 3306,
            'name': 'test_db'
        }
        
        mock_engine = mock.MagicMock()
        mock_create_engine.return_value = mock_engine
        
        mock_base = mock.MagicMock()
        
        # Initialize database manager
        db_manager = DatabaseManager()
        
        # Create tables
        db_manager.create_tables(mock_base)
        
        # Verify metadata.create_all was called
        mock_base.metadata.create_all.assert_called_once_with(mock_engine)


if __name__ == "__main__":
    unittest.main()