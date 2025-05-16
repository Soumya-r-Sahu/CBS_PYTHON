import os
import sys
import logging
import time
from pathlib import Path
import mysql.connector
from mysql.connector import Error, pooling
from contextlib import contextmanager
from colorama import init, Fore, Style

# Define environment functions that may be overridden later
env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
def get_environment_name(): return env_str
def is_production(): return env_str == "production"
def is_test(): return env_str == "test"
def is_development(): return env_str == "development"
def is_debug_enabled(): return os.environ.get("DEBUG", "0").lower() in ("1", "true", "yes")

# Use centralized import manager if available
try:
    from utils.lib.packages import fix_path
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    print("Warning: Import manager not available. Using fallback import mechanism.")


# Import from config
try:
    from utils.config import DATABASE_CONFIG
except ImportError:
    # Define fallback config
    DATABASE_CONFIG = {
        'host': 'localhost',
        'database': 'core_banking',
        'user': 'dbuser',
        'password': 'password'
    }

# Environment functions with fallback implementation
env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
def get_environment_name(): return env_str
def is_production(): return env_str == "production"
def is_test(): return env_str == "test"

# Try to import environment module from new structure if available
try:
    from utils.config.environment import get_environment_name, is_production, is_test
except ImportError:
    # Already have fallback implementation defined above
    pass

# Initialize colorama
init(autoreset=True)

# Set up logger
logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self):
        # Set pool settings based on environment
        pool_name = f"db_pool_{get_environment_name()}"
        
        # Adjust pool size based on environment
        if is_production():
            pool_size = int(os.environ.get('CBS_DB_POOL_SIZE', 10))
            pool_reset_session = True
        elif is_test():
            pool_size = 3
            pool_reset_session = True
        else:  # development
            pool_size = 5
            pool_reset_session = False
            
        self.env = get_environment_name()
        self.pool = mysql.connector.pooling.MySQLConnectionPool(
            pool_name=pool_name,
            pool_size=pool_size,
            pool_reset_session=pool_reset_session,
            **DATABASE_CONFIG
        )

    def get_connection(self):
        """Get a connection from the pool"""
        try:
            connection = self.pool.get_connection()
            
            # In test environment, we might want to log connection usage
            if is_test():
                print(f"{Fore.YELLOW}🔍 [TEST] Database connection established from pool{Style.RESET_ALL}")
                
            return connection
        except Error as e:
            env_tag = f"[{self.env.upper()}]"
            error_msg = f"{env_tag} Error getting connection from pool: {e}"
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            logger.error(error_msg)
            return None

    def close_connection(self, connection):
        """Close a specific connection and return it to the pool"""
        if connection and hasattr(connection, 'is_connected') and connection.is_connected():
            try:
                connection.close()
                # In test environment, we might want to log connection returns
                if is_test():
                    print(f"{Fore.YELLOW}🔍 [TEST] Database connection returned to pool{Style.RESET_ALL}")
            except Error as e:
                env_tag = f"[{self.env.upper()}]"
                error_msg = f"{env_tag} Error closing connection: {e}"
                print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
                logger.error(error_msg)
    
    @contextmanager
    def transaction(self, max_retries=3, retry_delay=0.5):
        """
        Context manager for handling database transactions with proper rollback on error.
        
        Usage:
            db = DatabaseConnection()
            with db.transaction() as (conn, cursor):
                cursor.execute("INSERT INTO accounts (id, name) VALUES (%s, %s)", (1, "Test"))
                # Automatically commits if successful or rolls back if an exception occurs
        
        Args:
            max_retries: Number of times to retry on network errors
            retry_delay: Delay between retries in seconds
        
        Returns:
            tuple: (connection, cursor)
        """
        connection = None
        cursor = None
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                connection = self.get_connection()
                if not connection:
                    raise Error("Failed to get database connection from pool")
                
                cursor = connection.cursor(dictionary=True)
                
                # Reset autocommit and start transaction
                connection.autocommit = False
                
                # Yield connection and cursor for use in the with block
                yield (connection, cursor)
                
                # If we get here without exception, commit the transaction
                connection.commit()
                logger.debug("Transaction committed successfully")
                
                # Successfully completed - break out of retry loop
                break
                
            except (mysql.connector.errors.OperationalError, 
                    mysql.connector.errors.InterfaceError,
                    mysql.connector.errors.PoolError) as net_err:
                # Handle network and connection errors with retry logic
                retry_count += 1
                
                # Log the error
                env_tag = f"[{self.env.upper()}]"
                error_msg = f"{env_tag} Network error in transaction (attempt {retry_count}/{max_retries}): {net_err}"
                logger.warning(error_msg)
                
                # Always try to rollback what might have happened before the error
                if connection:
                    try:
                        connection.rollback()
                        logger.debug("Transaction rolled back due to network error")
                    except Exception as rollback_err:
                        logger.error(f"Error during rollback after network error: {rollback_err}")
                
                # Close the connection that had an error
                if cursor:
                    try:
                        cursor.close()
                    except:
                        pass
                self.close_connection(connection)
                
                # If we've reached max retries, re-raise the last error
                if retry_count > max_retries:
                    logger.error(f"Max retries ({max_retries}) reached. Transaction failed permanently.")
                    raise
                
                # Wait before retrying
                logger.info(f"Retrying transaction in {retry_delay} seconds...")
                time.sleep(retry_delay)
                
                # Increase delay for next retry (exponential backoff)
                retry_delay *= 2
                
            except Exception as e:
                # For all other errors, rollback immediately and re-raise
                env_tag = f"[{self.env.upper()}]"
                error_msg = f"{env_tag} Error in transaction: {e}"
                logger.error(error_msg)
                
                if connection:
                    try:
                        connection.rollback()
                        logger.debug("Transaction rolled back due to error")
                    except Exception as rollback_err:
                        logger.error(f"Error during rollback: {rollback_err}")
                
                # Re-raise the original exception
                raise
                
            finally:
                # Always clean up resources
                if cursor and not cursor.closed:
                    try:
                        cursor.close()
                    except:
                        pass
                self.close_connection(connection)

    def execute_query(self, query, params=None):
        """
        Execute a query with proper error handling and automatic rollback.
        
        Args:
            query (str): SQL query to execute
            params (tuple, dict, optional): Parameters for the query
            
        Returns:
            list: Query results (for SELECT) or affected rows (for other queries)
        """
        with self.transaction() as (conn, cursor):
            cursor.execute(query, params or ())
            
            # For SELECT queries, return the results
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            
            # For other queries, return the rowcount
            return cursor.rowcount

    def execute_many(self, query, params_list):
        """
        Execute a batch query with proper error handling and automatic rollback.
        
        Args:
            query (str): SQL query to execute
            params_list (list): List of parameter tuples/dicts
            
        Returns:
            int: Number of affected rows
        """
        with self.transaction() as (conn, cursor):
            cursor.executemany(query, params_list)
            return cursor.rowcount
            
# Example usage:
if __name__ == "__main__":
    db = DatabaseConnection()
    
    # Example using the transaction context manager
    try:
        with db.transaction() as (conn, cursor):
            # Multiple operations in a single transaction
            cursor.execute("SELECT 1")
            print("Query successful")
    except Exception as e:
        print(f"Transaction failed: {e}")
    
    # Example using the helper methods
    try:
        results = db.execute_query("SELECT 1 as test")
        print(f"Results: {results}")
    except Exception as e:
        print(f"Query failed: {e}")