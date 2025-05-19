"""
Core Banking System - Database connection utilities
"""

import os
import yaml
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path


# Try to import database type manager for dynamic database selection
try:
    from utils.database_type_manager import get_database_type, get_connection_string
    DYNAMIC_DB_TYPE = True
except ImportError:
    # Fallback if database type manager is not available
    DYNAMIC_DB_TYPE = False
    
# Set up logger
logger = logging.getLogger(__name__)

# Load database configuration
def load_config():
    """Load database configuration from YAML file and environment variables"""
    # Try multiple possible locations for the config file
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '../app/config/settings.yaml'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app/config/settings.yaml'),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../app/config/settings.yaml'))
    ]
    
    for config_path in possible_paths:
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as file:
                    config = yaml.safe_load(file)
                    
                # Replace environment variables
                db_config = config.get('database', {})
                db_config['username'] = os.environ.get('DB_USER', db_config.get('username'))
                db_config['password'] = os.environ.get('DB_PASSWORD', db_config.get('password'))
                
                logger.info(f"Loaded database configuration from: {config_path}")
                return db_config
            except Exception as e:
                logger.warning(f"Failed to load configuration from {config_path}: {e}")
    
    # If we get here, we couldn't find or load the config file
    logger.error("Could not find or load settings.yaml file")
    # Fall back to values from utils/config.py
    try:
        from utils.config import DATABASE_CONFIG
        logger.info("Falling back to DATABASE_CONFIG from utils/config.py")
        return {            'driver': 'mysql+mysqlconnector',
            'host': DATABASE_CONFIG.get('host', 'localhost'),
            'port': DATABASE_CONFIG.get('port', 3307),
            'name': DATABASE_CONFIG.get('database', 'CBS_PYTHON'),  # Updated to match config.py database name
            'username': DATABASE_CONFIG.get('user', 'root'),
            'password': DATABASE_CONFIG.get('password', 'Admin.root@123'),  # Updated to match config.py password
        }
    except Exception as e:
        logger.error(f"Failed to load fallback configuration: {e}")
        raise


class DatabaseManager:
    """Database connection manager for Core Banking System"""
    
    _instance = None
    _engine = None
    _session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
        
    def _initialize(self):
        """Initialize database connection"""
        try:
            # Load configuration
            db_config = load_config()
            
            # If dynamic database type is available, use it to generate the connection string
            if DYNAMIC_DB_TYPE:
                connection_string = get_connection_string()
                # Extract database type from the connection string
                db_type = 'mysql'  # Default
                if connection_string.startswith('sqlite'):
                    db_type = 'sqlite'
                elif connection_string.startswith('postgresql'):
                    db_type = 'postgresql'
                logger.info(f"Using database type from database_type_manager: {db_type}")
            else:
                # Create connection string manually
                connection_string = (
                    f"{db_config.get('driver', 'mysql+mysqlconnector')}://"
                    f"{db_config.get('username')}:{db_config.get('password')}"
                    f"@{db_config.get('host', 'localhost')}:{db_config.get('port', 3307)}"
                    f"/{db_config.get('name', 'CBS_PYTHON')}"
                )
            
            # Create engine
            self._engine = create_engine(
                connection_string,
                pool_size=db_config.get('pool_size', 5),
                max_overflow=db_config.get('max_overflow', 10),
                pool_timeout=db_config.get('timeout', 30),
                echo=False
            )
            
            # Create session factory
            self._session_factory = scoped_session(
                sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self._engine
                )
            )
            
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def get_engine(self):
        """Get SQLAlchemy engine"""
        return self._engine
    
    def get_session(self):
        """Get a new database session"""
        return self._session_factory()
    
    def close_session(self, session):
        """Close a database session"""
        if session:
            try:
                session.close()
            except Exception as e:
                logger.error(f"Error closing session: {e}")
    
    def create_tables(self, base):
        """Create all tables defined in SQLAlchemy models"""
        try:
            base.metadata.create_all(self._engine)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error creating tables: {e}")
            raise

# Base class for models
Base = declarative_base()

# Create singleton instance
db_manager = DatabaseManager()

# Function to get a database session
def get_db_session():
    """Get a database session"""
    return db_manager.get_session()
