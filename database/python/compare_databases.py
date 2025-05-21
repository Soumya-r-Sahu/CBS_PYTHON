"""
Database comparison script to test connection and operations 
with both cbs_python and core_banking_system databases
"""

import time
import os
from sqlalchemy import create_engine, text
import urllib.parse
import sys
from utils.config.config import DATABASE_CONFIG

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path


# Database configurations
databases = {
    "CBS_PYTHON": {
        "host": DATABASE_CONFIG['host'],
        "database": "CBS_PYTHON",
        "user": DATABASE_CONFIG['user'],
        "password": DATABASE_CONFIG['password'],
        "port": DATABASE_CONFIG['port']
    },
    "core_banking_system": {
        "host": DATABASE_CONFIG['host'], 
        "database": "core_banking_system",
        "user": DATABASE_CONFIG['user'],
        "password": DATABASE_CONFIG['password'], 
        "port": DATABASE_CONFIG['port']
    }
}

def test_database(db_name):
    """Test connection and operations with specified database"""
    print(f"\n🔍 Testing database: {db_name}")
    
    config = databases[db_name]
    encoded_password = urllib.parse.quote_plus(config['password'])
    
    # Create connection URL
    connection_url = f"mysql+mysqlconnector://{config['user']}:{encoded_password}@{config['host']}:{config['port']}/{config['database']}"
    
    try:
        # Create engine
        engine = create_engine(connection_url)
        
        # Test connection
        print("Attempting to connect...")
        start_time = time.time()
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).fetchone()
            if result and result[0] == 1:
                connect_time = time.time() - start_time
                print(f"✅ Connection successful! ({connect_time:.3f}s)")
            else:
                print("❌ Connection test returned unexpected result")
                return False
                
        # Get tables
        with engine.connect() as connection:
            start_time = time.time()
            tables = connection.execute(text("SHOW TABLES")).fetchall()
            tables_time = time.time() - start_time
            print(f"📊 Found {len(tables)} tables ({tables_time:.3f}s)")
            
            # Test a few key tables if they exist
            key_tables = ['cbs_customers', 'cbs_accounts', 'cbs_transactions', 'cbs_cards']
            for table in key_tables:
                table_exists = False
                for t in tables:
                    if t[0] == table:
                        table_exists = True
                        break
                
                if table_exists:
                    start_time = time.time()
                    count = connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                    query_time = time.time() - start_time
                    print(f"  - {table}: {count} records ({query_time:.3f}s)")
                else:
                    print(f"  - {table}: Not found")
        
        return True
                
    except Exception as e:
        print(f"❌ Error with {db_name}: {e}")
        return False

def main():
    """Test both databases and display results"""
    results = {}
    
    for db_name in databases:
        results[db_name] = test_database(db_name)
    
    print("\n📋 Summary:")
    for db_name, success in results.items():
        status = "✅ Working" if success else "❌ Failed"
        print(f"{db_name}: {status}")
    
    # Determine which database to recommend
    working_dbs = [db for db, success in results.items() if success]
    if "cbs_python" in working_dbs:
        print("\n🌟 Recommendation: Use 'cbs_python' database for your project")
        print("   - Update DATABASE_CONFIG['database'] = 'cbs_python' in utils/config.py")
    elif "core_banking_system" in working_dbs:
        print("\n🌟 Recommendation: Use 'core_banking_system' database for your project")
        print("   - Make sure DATABASE_CONFIG['database'] = 'core_banking_system' in utils/config.py")
    else:
        print("\n❌ Neither database is accessible. Please check your MySQL server.")

if __name__ == "__main__":
    main()
