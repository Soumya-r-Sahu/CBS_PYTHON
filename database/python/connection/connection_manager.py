# database/python/connection/connection_manager.py
"""
SQLAlchemy connection manager for Core Banking System.
Provides ORM-based database connections.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
import os
import yaml
import logging
import urllib.parse

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

# Try to import database type manager for dynamic database selection
try:
    from utils.config.database_type_manager import get_database_type, get_connection_string
    DYNAMIC_DB_TYPE = True
except ImportError:
    # Fallback if database type manager is not available
    DYNAMIC_DB_TYPE = False
    
# Set up logger
logger = logging.getLogger(__name__)

# Create SQLAlchemy base class
Base = declarative_base()

# Load database configuration
def load_config():
    """Load database configuration from YAML file and environment variables"""
    # Try multiple possible locations for the config file
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '../../app/config/settings.yaml'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'app/config/settings.yaml'),
        os.path.abspath(os.path.join(os.path.dirname(__file__), '../../app/config/settings.yaml'))
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
        from utils.config.config import DATABASE_CONFIG
        logger.info("Falling back to DATABASE_CONFIG from utils/config.py")
        return {
            'driver': 'mysql+mysqlconnector',
            'host': DATABASE_CONFIG['host'],
            'port': DATABASE_CONFIG['port'],
            'database': DATABASE_CONFIG['database'],
            'username': DATABASE_CONFIG['user'],
            'password': DATABASE_CONFIG['password'],
        }
    except ImportError:
        logger.critical("Could not load database configuration from any source!")
        return {
            'driver': 'mysql+mysqlconnector',
            'host': 'localhost',
            'port': 3306,
            'database': 'core_banking',
            'username': 'root',
            'password': '',
        }

# Create database URL
def create_db_url():
    """Create database URL based on configuration"""
    if DYNAMIC_DB_TYPE:
        db_type = get_database_type()
        connection_string = get_connection_string()
        if connection_string:
            return connection_string

    # Use configuration as fallback
    config = load_config()
    password = urllib.parse.quote_plus(config['password'])
    return f"{config['driver']}://{config['username']}:{password}@{config['host']}:{config['port']}/{config['database']}"

# Configure SQLAlchemy engine with proper settings
def configure_engine(url, **kwargs):
    """Configure SQLAlchemy engine with appropriate settings"""
    default_settings = {
        'pool_recycle': 3600,  # Recycle connections after 1 hour
        'pool_pre_ping': True,  # Verify connections before using them
        'pool_size': 10,        # Default connection pool size
        'max_overflow': 20,     # Allow up to 20 connections overflow
        'echo': False,          # Don't log all SQL
    }
    
    # Update with any provided settings
    settings = {**default_settings, **kwargs}
    
    # Create the SQLAlchemy engine
    return create_engine(url, **settings)

# Create engine
DB_URL = create_db_url()
engine = configure_engine(DB_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to get a database session
def get_db():
    """Get a database session with proper error handling"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
