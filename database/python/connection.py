import logging
import time
import os
from pathlib import Path
import mysql.connector
from mysql.connector import Error, pooling
from contextlib import contextmanager
from colorama import init, Fore, Style

# Use centralized import system
from utils.lib.packages import fix_path
from utils.config.environment import get_environment_name, is_production, is_test, is_development, is_debug_enabled

fix_path()  # Ensures the project root is in sys.path

# Import database type manager
from utils.config.database_type_manager import get_database_type, get_connection_string
DYNAMIC_DB_TYPE = True

# Import database configuration
from utils.config.config import DATABASE_CONFIG

# Initialize colorama
init(autoreset=True)

# Set up logger
logger = logging.getLogger(__name__)

class DatabaseConnection:
    def __init__(self, config=None):
        # Use provided config or default
        self.config = config or DATABASE_CONFIG
        
        # Determine database type
        self.db_type = 'mysql'  # Default type
        if DYNAMIC_DB_TYPE:
            self.db_type = get_database_type()
            
        # Set environment name
        self.env = get_environment_name()
        
        if self.db_type == 'mysql':
            self._initialize_mysql()
        elif self.db_type == 'sqlite':
            self._initialize_sqlite()
        elif self.db_type == 'postgresql':
            self._initialize_postgresql()
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")
    
    def _initialize_mysql(self):
        """Initialize MySQL connection pool"""
        # Set pool settings based on environment
        pool_name = f"mysql_pool_{self.env}"
        
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
        
        try:
            self.pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name=pool_name,
                pool_size=pool_size,
                pool_reset_session=pool_reset_session,
                **self.config
            )
            logger.info(f"MySQL connection pool initialized for {self.env}")
        except Exception as e:
            logger.error(f"Failed to initialize MySQL connection pool: {e}")
            self.pool = None
    
    def _initialize_sqlite(self):
        """Initialize SQLite connection"""
        import sqlite3
        
        # Create data directory if it doesn't exist
        data_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = data_dir / f"cbs_python_{self.env}.db"
        logger.info(f"SQLite connection initialized with path: {self.db_path}")
    
    def _initialize_postgresql(self):
        """Initialize PostgreSQL connection pool"""
        import psycopg2
        from psycopg2 import pool as pg_pool
            
        # Configure pool settings
        if is_production():
            min_conn = 2
            max_conn = 10
        elif is_test():
            min_conn = 1
            max_conn = 3
        else:  # development
            min_conn = 1
            max_conn = 5
        
        try:
            # Extract PostgreSQL config
            pg_config = {
                'host': os.environ.get('CBS_PG_HOST', self.config.get('pg_host', 'localhost')),
                'port': os.environ.get('CBS_PG_PORT', self.config.get('pg_port', 5432)),
                'user': os.environ.get('CBS_PG_USER', self.config.get('pg_user', 'postgres')),
                'password': os.environ.get('CBS_PG_PASSWORD', self.config.get('pg_password', 'postgres')),
                'database': os.environ.get('CBS_PG_DB', self.config.get('pg_database', 'CBS_PYTHON'))
            }
            
            self.pool = pg_pool.ThreadedConnectionPool(
                minconn=min_conn,
                maxconn=max_conn,
                host=pg_config['host'],
                port=pg_config['port'],
                user=pg_config['user'],
                password=pg_config['password'],
                database=pg_config['database']
            )
            logger.info(f"PostgreSQL connection pool initialized for {self.env}")
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL connection pool: {e}")
            self.pool = None