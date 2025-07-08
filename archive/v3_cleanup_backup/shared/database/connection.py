"""
Database Connection Manager for Core Banking System V3.0

This module provides database connection management with support for:
- PostgreSQL (primary)
- MySQL (secondary)
- SQLite (development/testing)
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from .base import Base

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration class"""
    
    def __init__(self):
        self.db_type = os.getenv("CBS_DB_TYPE", "postgresql")
        self.host = os.getenv("CBS_DB_HOST", "localhost")
        self.port = int(os.getenv("CBS_DB_PORT", "5432"))
        self.database = os.getenv("CBS_DB_NAME", "core_banking")
        self.username = os.getenv("CBS_DB_USER", "cbs_user")
        self.password = os.getenv("CBS_DB_PASSWORD", "cbs_password")
        self.environment = os.getenv("CBS_ENVIRONMENT", "development")
        
    def get_database_url(self) -> str:
        """Generate database URL based on configuration"""
        if self.db_type == "postgresql":
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == "mysql":
            return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
        elif self.db_type == "sqlite":
            db_path = f"./data/{self.database}.db"
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            return f"sqlite:///{db_path}"
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

class DatabaseManager:
    """Database manager for handling connections and sessions"""
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
    def _create_engine(self) -> Engine:
        """Create database engine with appropriate configuration"""
        database_url = self.config.get_database_url()
        
        engine_kwargs = {
            "echo": self.config.environment == "development",
            "pool_pre_ping": True,
        }
        
        # SQLite specific configuration
        if self.config.db_type == "sqlite":
            engine_kwargs.update({
                "poolclass": StaticPool,
                "connect_args": {"check_same_thread": False},
            })
        
        logger.info(f"Creating database engine for {self.config.db_type}")
        return create_engine(database_url, **engine_kwargs)
    
    def create_tables(self):
        """Create all database tables"""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self):
        """Drop all database tables"""
        logger.info("Dropping database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.info("Database tables dropped successfully")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def get_session_factory(self):
        """Get session factory for dependency injection"""
        return self.SessionLocal

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None

def get_database_manager() -> DatabaseManager:
    """Get or create global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session.
    Use this in your FastAPI endpoints like:
    
    @app.get("/example")
    async def example(db: Session = Depends(get_db_session)):
        # Use db session here
        pass
    """
    db_manager = get_database_manager()
    with db_manager.get_session() as session:
        yield session

def init_database():
    """Initialize database - create tables if they don't exist"""
    db_manager = get_database_manager()
    db_manager.create_tables()
