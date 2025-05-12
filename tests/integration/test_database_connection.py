"""
Database Connection Integration Tests

This module contains integration tests for database connections and operations.
These tests require an actual database connection to run.
"""

import pytest
import os
import sys
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database.connection import DatabaseConnection
from database.db_manager import get_db_session, DatabaseManager, Base

# Import database verification utilities
from tests.integration.db_verification import verify_database_setup
from tests.integration.db_data_verification import verify_sample_data, verify_specific_record


class TestDatabaseConnection(unittest.TestCase):
    """Integration tests for database connection functionality."""
    
    def test_connection_initialization(self):
        """Test initializing a database connection."""
        try:
            db = DatabaseConnection()
            self.assertIsNotNone(db)
        except Exception as e:
            self.fail(f"DatabaseConnection initialization raised exception: {e}")
    
    def test_get_connection(self):
        """Test getting an actual database connection."""
        try:
            db = DatabaseConnection()
            conn = db.get_connection()
            
            self.assertIsNotNone(conn)
            if hasattr(conn, 'is_connected'):
                self.assertTrue(conn.is_connected())
            
            # Close connection
            conn.close()
        except Exception as e:
            self.fail(f"Failed to connect to database: {e}")
    
    def test_connection_with_query(self):
        """Test executing a query with the connection."""
        try:
            db = DatabaseConnection()
            conn = db.get_connection()
            
            # Create cursor
            cursor = conn.cursor()
            
            # Execute a simple query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            self.assertEqual(result[0], 1)
            
            # Close cursor and connection
            cursor.close()
            conn.close()
        except Exception as e:
            self.fail(f"Failed to execute query: {e}")


class TestDatabaseSession(unittest.TestCase):
    """Integration tests for SQLAlchemy sessions."""
    
    def test_session_creation(self):
        """Test creating an SQLAlchemy session."""
        try:
            session = get_db_session()
            self.assertIsNotNone(session)
            session.close()
        except Exception as e:
            self.fail(f"Failed to create session: {e}")
    
    def test_session_with_query(self):
        """Test executing a query with an SQLAlchemy session."""
        try:
            session = get_db_session()
            
            # Execute a simple query
            result = session.execute("SELECT 1")
            val = result.scalar()
            
            self.assertEqual(val, 1)
            
            # Close session
            session.close()
        except Exception as e:
            self.fail(f"Failed to execute query with session: {e}")


def validate_database_tables():
    """Validate that required database tables exist."""
    try:
        conn = DatabaseConnection().get_connection()
        cursor = conn.cursor()
        
        # Check for key tables
        tables_to_check = [
            "customers",
            "accounts",
            "transactions",
            "upi_accounts",
            "upi_transactions",
            "cards"
        ]
        
        missing_tables = []
        
        # Get list of tables in database
        cursor.execute("SHOW TABLES")
        existing_tables = [table[0] for table in cursor.fetchall()]
        
        for table in tables_to_check:
            if table not in existing_tables:
                missing_tables.append(table)
        
        cursor.close()
        conn.close()
        
        return missing_tables
    except Exception as e:
        print(f"Error validating tables: {e}")
        return tables_to_check  # Assume all tables are missing if there's an error


@pytest.mark.integration
def test_database_tables():
    """Test that required database tables exist."""
    missing_tables = validate_database_tables()
    
    if missing_tables:
        pytest.fail(f"Missing tables: {', '.join(missing_tables)}")


@pytest.mark.integration
def test_database_setup():
    """Test that the database is properly set up."""
    success, missing_tables, procedures = verify_database_setup()
    
    if not success:
        if missing_tables:
            pytest.fail(f"Missing tables: {', '.join(missing_tables)}")
        elif not procedures:
            pytest.fail("No stored procedures found")
        else:
            pytest.fail("Database setup verification failed")


@pytest.mark.integration
def test_sample_data():
    """Test that sample data is loaded in the database."""
    success, results = verify_sample_data()
    
    if not success:
        empty_tables = [table for table, count in results.items() if count == 0]
        pytest.fail(f"Missing data in tables: {', '.join(empty_tables)}")
    
    # Verify we have at least one customer and account
    assert results.get('customers', 0) > 0, "No customers found in database"
    assert results.get('accounts', 0) > 0, "No accounts found in database"


if __name__ == "__main__":
    unittest.main()
