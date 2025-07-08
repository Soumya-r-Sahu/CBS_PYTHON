"""
Core Banking Database Module
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import urllib.parse
import logging

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path


# Set up logging
logger = logging.getLogger(__name__)

# Import configuration
try:
    # Try relative import first
    from core_banking.utils.config import DATABASE_CONFIG
    logger.info("Using core_banking.utils.config")
except ImportError:
    try:
        from utils.config import DATABASE_CONFIG
        logger.info("Using utils.config")
    except ImportError:
        # Fallback configuration
        logger.warning("Could not import DATABASE_CONFIG, using fallback configuration")
        DATABASE_CONFIG = {
            'user': 'root',
            'password': 'password',
            'host': 'localhost',
            'port': 3306,
            'database': 'core_banking'
        }

# Create SQLAlchemy base class
Base = declarative_base()

# Create MySQL connection URL from config with URL encoded password
password = urllib.parse.quote_plus(DATABASE_CONFIG['password'])
DB_URL = f"mysql+mysqlconnector://{DATABASE_CONFIG['user']}:{password}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"

# Create engine with proper error handling
try:
    engine = create_engine(DB_URL)
    logger.info(f"Database engine created for {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}")
except Exception as e:
    logger.error(f"Error creating database engine: {str(e)}")
    engine = None

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Function to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
