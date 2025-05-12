"""
Database connection test module
Tests connectivity and basic operations with the database
"""
import unittest
import sys
import os
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import db_manager, get_db_session

class TestDatabaseConnection(unittest.TestCase):
    """Test basic database connectivity and operations"""
    
    def setUp(self):
        """Setup test case - get a database session"""
        self.session = get_db_session()
    
    def tearDown(self):
        """Cleanup after test - close the session"""
        if hasattr(self, 'session'):
            db_manager.close_session(self.session)
    
    def test_connection(self):
        """Test basic connection to the database"""
        result = self.session.execute(text("SELECT 1")).scalar()
        self.assertEqual(1, result, "Database connection failed")
        
    def test_database_name(self):
        """Test if we're connected to the expected database"""
        db_name = self.session.execute(text("SELECT DATABASE()")).scalar()
        from utils.config import DATABASE_CONFIG
        self.assertEqual(DATABASE_CONFIG['database'], db_name, 
                         f"Connected to wrong database. Expected: {DATABASE_CONFIG['database']}, Got: {db_name}")
        
    def test_tables_exist(self):
        """Test if essential tables exist"""
        essential_tables = [
            'cbs_customers', 
            'cbs_accounts', 
            'cbs_transactions', 
            'cbs_cards'
        ]
        
        for table in essential_tables:
            query = text(f"SELECT COUNT(*) FROM information_schema.tables "
                         f"WHERE table_schema = DATABASE() AND table_name = '{table}'")
            result = self.session.execute(query).scalar()
            self.assertEqual(1, result, f"Table {table} not found in database")
            
    def test_customer_structure(self):
        """Test if customer table has expected structure"""
        expected_fields = [
            'customer_id', 'name', 'email', 'phone', 'status', 
            'registration_date', 'kyc_status'
        ]
        
        for field in expected_fields:
            query = text(f"SELECT COUNT(*) FROM information_schema.columns "
                        f"WHERE table_schema = DATABASE() AND table_name = 'cbs_customers' "
                        f"AND column_name = '{field}'")
            result = self.session.execute(query).scalar()
            self.assertEqual(1, result, f"Field {field} not found in cbs_customers table")
            
    def test_customer_data_access(self):
        """Test if we can access customer data"""
        result = self.session.execute(text("SELECT COUNT(*) FROM cbs_customers")).scalar()
        self.assertIsNotNone(result, "Failed to count customers")
        print(f"Customer count: {result}")
        
if __name__ == '__main__':
    unittest.main()
