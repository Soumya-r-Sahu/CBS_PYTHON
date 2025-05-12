"""
Direct MySQL database connection test script to troubleshoot connection issues.
"""
import os
import sys

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

# Import required modules
import mysql.connector
from utils.config import DATABASE_CONFIG
from sqlalchemy import create_engine, text
import urllib.parse

def test_mysql_direct():
    """Test direct MySQL connection using mysql-connector"""
    print("\n1. Testing direct MySQL connection using mysql-connector")
    print("-" * 50)
    print(f"Database config: {DATABASE_CONFIG}")
    
    try:
        # Create a direct connection
        print(f"Connecting to MySQL at {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}...")
        conn = mysql.connector.connect(
            host=DATABASE_CONFIG['host'],
            port=DATABASE_CONFIG['port'],
            user=DATABASE_CONFIG['user'],
            password=DATABASE_CONFIG['password'],
            database=DATABASE_CONFIG['database']
        )
        
        # Test the connection
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"Connected! MySQL version: {version[0]}")
        
        # Get table list
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"Found {len(tables)} tables")
        
        # Close connection
        cursor.close()
        conn.close()
        print("Connection closed successfully")
        return True
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


def test_sqlalchemy_direct():
    """Test direct SQLAlchemy connection"""
    print("\n2. Testing direct SQLAlchemy connection")
    print("-" * 50)
    
    try:
        # Encode password for URL
        password = urllib.parse.quote_plus(DATABASE_CONFIG['password'])
        
        # Create connection URL
        url = f"mysql+mysqlconnector://{DATABASE_CONFIG['user']}:{password}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
        print(f"Connection URL: {url.replace(password, '***')}")
        
        # Create engine and connect
        print("Creating SQLAlchemy engine...")
        engine = create_engine(url)
        
        # Test connection
        with engine.connect() as connection:
            print("Executing test query...")
            result = connection.execute(text("SELECT 1")).fetchone()
            if result and result[0] == 1:
                print("✓ Connection successful!")
            
            # Get database name
            db_name = connection.execute(text("SELECT DATABASE()")).scalar()
            print(f"Connected to database: {db_name}")
            
            # Get tables
            tables = connection.execute(text("SHOW TABLES")).fetchall()
            print(f"Found {len(tables)} tables")
            
            # Check for customer data
            customer_count = connection.execute(text("SELECT COUNT(*) FROM cbs_customers")).scalar()
            print(f"Customer count: {customer_count}")
            
        print("Connection closed successfully")
        return True
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("DIRECT DATABASE CONNECTION TEST")
    print("=" * 70)
    print(f"Testing connection to {DATABASE_CONFIG['database']} database")
    
    mysql_success = test_mysql_direct()
    sqlalchemy_success = test_sqlalchemy_direct()
    
    print("\nSUMMARY:")
    print("-" * 50)
    print(f"MySQL Connector: {'SUCCESS' if mysql_success else 'FAILED'}")
    print(f"SQLAlchemy: {'SUCCESS' if sqlalchemy_success else 'FAILED'}")
    
    sys.exit(0 if mysql_success and sqlalchemy_success else 1)
