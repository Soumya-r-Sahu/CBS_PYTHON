# database/python/utilities/migration_helpers.py
"""
Database migration helpers for Core Banking System.

These utilities provide functionality to help with database schema migrations,
version tracking, and safely applying changes to the database.
"""

import os
import logging
import datetime
import sqlalchemy as sa
from sqlalchemy import text
from typing import List, Dict, Any, Optional, Tuple

# Import from database module
from database.python.connection.connection_manager import engine, Base

# Set up logger
logger = logging.getLogger(__name__)

def get_migration_version() -> int:
    """
    Get the current migration version from the database.
    
    Returns:
        The current migration version as an integer.
    """
    try:
        # Check if the migration_version table exists
        metadata = sa.MetaData()
        metadata.reflect(bind=engine)
        
        if 'migration_version' not in metadata.tables:
            # Create the migration_version table if it doesn't exist
            with engine.begin() as conn:
                conn.execute(text("""
                    CREATE TABLE migration_version (
                        id INT PRIMARY KEY,
                        version INT NOT NULL,
                        applied_at TIMESTAMP NOT NULL
                    )
                """))
                conn.execute(text("""
                    INSERT INTO migration_version (id, version, applied_at)
                    VALUES (1, 0, CURRENT_TIMESTAMP)
                """))
            return 0
            
        # Get the current version
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version FROM migration_version WHERE id=1"))
            version = result.scalar()
            return version if version is not None else 0
            
    except Exception as e:
        logger.error(f"Error getting migration version: {str(e)}")
        return 0

def update_migration_version(version: int) -> None:
    """
    Update the migration version in the database.
    
    Args:
        version: The new migration version.
    """
    try:
        with engine.begin() as conn:
            conn.execute(text("""
                UPDATE migration_version 
                SET version = :version, applied_at = CURRENT_TIMESTAMP
                WHERE id = 1
            """), {"version": version})
            
        logger.info(f"Migration version updated to {version}")
        
    except Exception as e:
        logger.error(f"Error updating migration version: {str(e)}")
        raise

def get_migration_files(migrations_dir: str) -> List[Tuple[int, str]]:
    """
    Get a list of migration files sorted by version.
    
    Args:
        migrations_dir: Directory containing migration files.
        
    Returns:
        A list of tuples (version, filepath) sorted by version.
    """
    if not os.path.exists(migrations_dir):
        logger.warning(f"Migrations directory does not exist: {migrations_dir}")
        return []
        
    migration_files = []
    
    for filename in os.listdir(migrations_dir):
        if not filename.endswith('.sql'):
            continue
            
        try:
            # Expected format: V001__some_description.sql
            if not filename.startswith('V'):
                continue
                
            version_part = filename.split('__', 1)[0][1:]
            version = int(version_part)
            
            migration_files.append(
                (version, os.path.join(migrations_dir, filename))
            )
            
        except (ValueError, IndexError):
            logger.warning(f"Ignoring invalid migration filename: {filename}")
            
    # Sort by version
    return sorted(migration_files, key=lambda x: x[0])

def migrate_schema(migrations_dir: str, target_version: Optional[int] = None) -> Dict[str, Any]:
    """
    Apply database migrations.
    
    Args:
        migrations_dir: Directory containing migration files.
        target_version: Target migration version. If None, applies all migrations.
        
    Returns:
        A dictionary with migration results.
    """
    # Get current migration version
    current_version = get_migration_version()
    logger.info(f"Current migration version: {current_version}")
    
    # Get available migrations
    migrations = get_migration_files(migrations_dir)
    
    if not migrations:
        logger.info("No migration files found")
        return {
            "success": True,
            "already_current": True,
            "current_version": current_version,
            "target_version": current_version,
            "migrations_applied": 0
        }
    
    # Determine target version if not specified
    if target_version is None:
        target_version = max(m[0] for m in migrations)
    
    logger.info(f"Target migration version: {target_version}")
    
    # If already at or beyond target version, skip
    if current_version >= target_version:
        logger.info(f"Database already at or beyond target version ({current_version} >= {target_version})")
        return {
            "success": True,
            "already_current": True,
            "current_version": current_version,
            "target_version": target_version,
            "migrations_applied": 0
        }
    
    # Filter migrations to apply
    migrations_to_apply = [m for m in migrations if current_version < m[0] <= target_version]
    
    if not migrations_to_apply:
        logger.info("No migrations to apply")
        return {
            "success": True,
            "already_current": True,
            "current_version": current_version,
            "target_version": target_version,
            "migrations_applied": 0
        }
    
    # Apply migrations
    applied_migrations = []
    
    try:
        for version, filepath in migrations_to_apply:
            logger.info(f"Applying migration V{version}: {os.path.basename(filepath)}")
            
            # Read migration file
            with open(filepath, 'r') as f:
                sql = f.read()
                
            # Apply migration
            with engine.begin() as conn:
                statements = sql.split(';')
                for statement in statements:
                    if statement.strip():
                        conn.execute(text(statement))
            
            # Update version after each successful migration
            update_migration_version(version)
            applied_migrations.append(filepath)
            
        logger.info(f"Migration successful. Current version: {target_version}")
        
        return {
            "success": True,
            "already_current": False,
            "current_version": target_version,
            "initial_version": current_version,
            "target_version": target_version,
            "migrations_applied": len(applied_migrations),
            "applied_files": applied_migrations
        }
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "current_version": get_migration_version(),
            "initial_version": current_version,
            "target_version": target_version,
            "migrations_applied": len(applied_migrations),
            "applied_files": applied_migrations
        }
