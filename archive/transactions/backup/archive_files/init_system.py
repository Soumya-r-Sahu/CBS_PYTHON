#!/usr/bin/env python
"""
Core Banking System - Initialization Script

This script helps to initialize the Core Banking System with proper directory
structure, database configuration, and environment setup.
"""

import os
import sys
import logging
import shutil
from pathlib import Path
import argparse
from datetime import datetime

# Add parent directory to path to ensure modules can be imported

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, get_database_connection
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


# This needs to be created during initialization
APP_LIB_PATH = Path(__file__).parent / 'app' / 'lib'
APP_LIB_PATH.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("CBS-Init")

def init_directories():
    """Create necessary directory structure if missing"""
    logger.info("Initializing directory structure...")
    
    # List of directories to ensure exist
    directories = [
        "logs",
        "backups",
        "logs/transactions",
        "logs/accounts",
        "logs/api",
        "backups/daily",
        "backups/weekly",
    ]
    
    base_dir = Path(__file__).parent
    for directory in directories:
        dir_path = base_dir / directory
        if not dir_path.exists():
            logger.info(f"Creating directory: {directory}")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    return True

def check_configuration():
    """Check that configuration is properly set up"""
    logger.info("Checking configuration...")
    
    # Check if .env file exists, create from example if not
    base_dir = Path(__file__).parent
    env_file = base_dir / ".env"
    env_example = base_dir / ".env.example"
    
    if not env_file.exists() and env_example.exists():
        logger.info(".env file not found. Creating from .env.example")
        shutil.copy(env_example, env_file)
        logger.warning("Please update .env file with your specific configuration")
    elif not env_file.exists() and not env_example.exists():
        logger.warning("Neither .env nor .env.example files found. Creating basic .env")
        with open(env_file, "w") as f:
            f.write("""# Core Banking System Environment Configuration
CBS_ENVIRONMENT=development
CBS_DEBUG=true

# Database Configuration
CBS_DB_USER=root
CBS_DB_PASSWORD=password
CBS_DB_HOST=localhost
CBS_DB_PORT=3306
CBS_DB_NAME=core_banking

# Security
CBS_SECRET_KEY=change-this-to-a-secure-key
CBS_JWT_SECRET=change-this-to-a-secure-jwt-secret
""")
        logger.warning("A basic .env file has been created. Please update with secure values.")
    
    return True

def check_packages():
    """Check that required packages are installed"""
    logger.info("Checking required packages...")
    
    try:
        import sqlalchemy
        logger.info(f"SQLAlchemy version: {sqlalchemy.__version__}")
    except ImportError:
        logger.warning("SQLAlchemy not installed. Running pip install...")
        os.system("pip install sqlalchemy")
    
    try:
        import pydantic
        logger.info(f"Pydantic version: {pydantic.__version__}")
    except ImportError:
        logger.warning("Pydantic not installed. Running pip install...")
        os.system("pip install pydantic")
    
    # Check if requirements.txt exists and recommend installation
    base_dir = Path(__file__).parent
    req_file = base_dir / "requirements.txt"
    if req_file.exists():
        logger.info("requirements.txt found. To install all dependencies, run:")
        logger.info("pip install -r requirements.txt")
    
    return True

def init_database(force=False):
    """Initialize database schemas"""
    logger.info("Initializing database...")
    
    try:
        # First check if we can access the database configurations
        try:
            from core_banking.database import Base, engine
            logger.info("Using core_banking.database module")
        except ImportError:
            try:
                from database.python.db_manager import Base, engine
                logger.info("Using database.python.db_manager module")
            except ImportError:
                logger.error("Could not import database modules. Database initialization failed.")
                return False
        
        # Create database tables
        if force:
            logger.warning("Forcing recreation of all database tables!")
            Base.metadata.drop_all(bind=engine)
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

def main():
    """Main entry point for initialization"""
    parser = argparse.ArgumentParser(description="Initialize Core Banking System")
    parser.add_argument("--init-db", action="store_true", help="Initialize database tables")
    parser.add_argument("--force-db", action="store_true", help="Force recreate database tables (CAUTION: Deletes existing data)")
    parser.add_argument("--check-only", action="store_true", help="Only check configuration without making changes")
    args = parser.parse_args()
    
    logger.info("=" * 80)
    logger.info("Core Banking System - Initialization")
    logger.info("=" * 80)
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.check_only:
        logger.info("Running in check-only mode. No changes will be made.")
        check_configuration()
        check_packages()
        return
    
    # Initialize directories
    init_directories()
    
    # Check configuration
    check_configuration()
    
    # Check required packages
    check_packages()
    
    # Initialize database if requested
    if args.init_db or args.force_db:
        init_database(force=args.force_db)
    
    logger.info("=" * 80)
    logger.info("Initialization complete!")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()