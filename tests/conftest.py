"""
Core Banking System Test Suite Configuration

This file contains pytest configuration, fixtures, and helpers
that are shared across all test files.
"""

import os
import sys
import pytest
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import project modules
try:
    from utils.config import DATABASE_CONFIG
    from database.connection import DatabaseConnection
except ImportError:
    print("Failed to import core modules. Check your project structure.")

# Configure logging for tests
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("cbs-tests")

# Test database configuration - use a separate test database
TEST_DATABASE_CONFIG = DATABASE_CONFIG.copy()
TEST_DATABASE_CONFIG["database"] = f"{DATABASE_CONFIG.get('database', 'core_banking_system')}_test"

@pytest.fixture(scope="session")
def db_connection():
    """Create a database connection for testing"""
    logger.info(f"Setting up test database: {TEST_DATABASE_CONFIG['database']}")
    
    # Use the standard connection but with test database
    conn = None
    try:
        # Create test database if it doesn't exist
        import mysql.connector
        temp_conn = mysql.connector.connect(
            host=TEST_DATABASE_CONFIG["host"],
            user=TEST_DATABASE_CONFIG["user"],
            password=TEST_DATABASE_CONFIG["password"],
            port=TEST_DATABASE_CONFIG["port"]
        )
        cursor = temp_conn.cursor()
        
        # Create test database
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {TEST_DATABASE_CONFIG['database']}")
        cursor.close()
        temp_conn.close()
        
        # Connect to test database
        db = DatabaseConnection(config=TEST_DATABASE_CONFIG)
        conn = db.get_connection()
        
        if not conn:
            logger.error("Failed to connect to test database")
            pytest.skip("Database connection failed")
        
        yield conn
        
    except Exception as e:
        logger.error(f"Error setting up test database: {e}")
        pytest.skip(f"Database setup failed: {e}")
    finally:
        if conn:
            conn.close()
            logger.info("Test database connection closed")

@pytest.fixture(scope="function")
def clean_test_db(db_connection):
    """Set up clean tables for each test"""
    logger.info("Setting up clean test tables")
    cursor = db_connection.cursor()
    
    # Schema setup SQL file path
    schema_file = Path(__file__).parent.parent / "database" / "setup_database.sql"
    
    try:
        # Read and execute schema setup
        with open(schema_file, 'r') as file:
            sql = file.read()
            # Split by delimiters and execute
            statements = sql.split(';')
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
        
        db_connection.commit()
        logger.info("Test tables created")
        
        yield db_connection
        
        # Clean up tables after test
        logger.info("Cleaning up test tables")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        # Disable foreign key checks for cleanup
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        for table in tables:
            table_name = table[0]
            if table_name.startswith('cbs_'):
                cursor.execute(f"TRUNCATE TABLE {table_name}")
        
        # Enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        db_connection.commit()
        
    except Exception as e:
        logger.error(f"Error setting up test tables: {e}")
        pytest.skip(f"Test table setup failed: {e}")
    finally:
        cursor.close()

@pytest.fixture(scope="function")
def sample_customer_data(clean_test_db):
    """Insert sample customer data for testing"""
    conn = clean_test_db
    cursor = conn.cursor()
    
    try:
        # Insert a sample customer
        customer = {
            "customer_id": "CUS1001TEST",
            "name": "Test Customer",
            "dob": "1990-01-01",
            "gender": "MALE",
            "customer_segment": "RETAIL",
            "occupation": "Engineer",
            "annual_income": 500000,
            "credit_score": 750,
            "risk_category": "LOW"
        }
        
        # Get the actual required fields
        cursor.execute("DESCRIBE cbs_customers")
        columns = cursor.fetchall()
        required_columns = [col[0] for col in columns if col[2] == 'NO']
        
        # Build SQL dynamically
        fields = []
        values = []
        placeholders = []
        
        for field in required_columns:
            if field in customer:
                fields.append(field)
                values.append(customer[field])
                placeholders.append("%s")
        
        sql = f"INSERT INTO cbs_customers ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
        cursor.execute(sql, values)
        conn.commit()
        
        yield customer
        
    except Exception as e:
        logger.error(f"Error inserting sample customer: {e}")
        pytest.skip(f"Sample data setup failed: {e}")
    finally:
        cursor.close()

@pytest.fixture(scope="function")
def sample_account_data(clean_test_db, sample_customer_data):
    """Insert sample account data for testing"""
    conn = clean_test_db
    cursor = conn.cursor()
    
    try:
        # Insert a sample account
        account = {
            "account_number": "ACC1001TEST",
            "customer_id": sample_customer_data["customer_id"],
            "account_type": "SAVINGS",
            "balance": 10000.00,
            "status": "ACTIVE",
            "branch_code": "BR001",
            "ifsc_code": "CBSTEST001"
        }
        
        # Get the actual required fields
        cursor.execute("DESCRIBE cbs_accounts")
        columns = cursor.fetchall()
        required_columns = [col[0] for col in columns if col[2] == 'NO']
        
        # Build SQL dynamically
        fields = []
        values = []
        placeholders = []
        
        for field in required_columns:
            if field in account:
                fields.append(field)
                values.append(account[field])
                placeholders.append("%s")
        
        sql = f"INSERT INTO cbs_accounts ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
        cursor.execute(sql, values)
        conn.commit()
        
        yield account
        
    except Exception as e:
        logger.error(f"Error inserting sample account: {e}")
        pytest.skip(f"Sample data setup failed: {e}")
    finally:
        cursor.close()

@pytest.fixture(scope="function")
def sample_transaction_data(clean_test_db, sample_account_data):
    """Insert sample transaction data for testing"""
    conn = clean_test_db
    cursor = conn.cursor()
    
    try:
        # Insert a sample transaction
        transaction = {
            "transaction_id": "TXN1001TEST",
            "account_number": sample_account_data["account_number"],
            "transaction_type": "DEPOSIT",
            "amount": 5000.00,
            "transaction_date": "2025-05-10 12:00:00",
            "channel": "BRANCH",
            "status": "SUCCESS"
        }
        
        # Get the actual required fields
        cursor.execute("DESCRIBE cbs_transactions")
        columns = cursor.fetchall()
        required_columns = [col[0] for col in columns if col[2] == 'NO']
        
        # Build SQL dynamically
        fields = []
        values = []
        placeholders = []
        
        for field in required_columns:
            if field in transaction:
                fields.append(field)
                values.append(transaction[field])
                placeholders.append("%s")
        
        sql = f"INSERT INTO cbs_transactions ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
        cursor.execute(sql, values)
        conn.commit()
        
        yield transaction
        
    except Exception as e:
        logger.error(f"Error inserting sample transaction: {e}")
        pytest.skip(f"Sample data setup failed: {e}")
    finally:
        cursor.close()

@pytest.fixture
def api_client():
    """
    Fixture to create a test client for API testing.
    
    This is used in API tests to make requests to the API endpoints.
    """
    import requests
    
    class APIClient:
        def __init__(self):
            self.base_url = "http://localhost:5000/api/v1"
            self.token = None
            self.headers = {}
            
        def login(self, customer_id="CUST123456", password="Password123!"):
            """Login to get authentication token"""
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={
                    "customer_id": customer_id,
                    "password": password,
                    "device_id": "TEST_DEVICE_001",
                    "device_info": {
                        "device_model": "Test Model",
                        "os_version": "Test OS 1.0",
                        "app_version": "1.0.0"
                    }
                }
            )
            
            if response.status_code == 200:
                self.token = response.json().get("data", {}).get("token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                return True
            return False
            
        def get(self, path, params=None):
            """Make GET request to API"""
            return requests.get(
                f"{self.base_url}/{path}",
                headers=self.headers,
                params=params
            )
            
        def post(self, path, data=None):
            """Make POST request to API"""
            return requests.post(
                f"{self.base_url}/{path}",
                headers=self.headers,
                json=data
            )
            
        def put(self, path, data=None):
            """Make PUT request to API"""
            return requests.put(
                f"{self.base_url}/{path}",
                headers=self.headers,
                json=data
            )
            
        def delete(self, path, params=None):
            """Make DELETE request to API"""
            return requests.delete(
                f"{self.base_url}/{path}",
                headers=self.headers,
                params=params
            )
    
    # Initialize client    
    client = APIClient()
    
    # Check if API server is running
    try:
        response = requests.get(f"{client.base_url}/health", timeout=2)
        if response.status_code != 200:
            pytest.skip("API server is not running or not responding")
    except:
        pytest.skip("API server is not running")
    
    return client
