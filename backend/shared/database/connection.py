"""
Database Connection Manager for Core Banking System V3.0

This module handles database connections and session management.
"""

import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from ..models import Base

class DatabaseManager:
    """Database connection and session manager"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database connection"""
        # Database configuration from environment variables
        DB_USER = os.getenv("DB_USER", "postgres")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
        DB_HOST = os.getenv("DB_HOST", "localhost")
        DB_PORT = os.getenv("DB_PORT", "5432")
        DB_NAME = os.getenv("DB_NAME", "core_banking")
        
        # Create database URL
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        
        # Create engine with connection pooling
        self.engine = create_engine(
            DATABASE_URL,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=0,
            pool_pre_ping=True,
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Add event listeners for better connection handling
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set database pragmas for better performance"""
            if "sqlite" in str(self.engine.url):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables"""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()

# Global database manager instance
db_manager = DatabaseManager()

def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency function to get database session for FastAPI.
    
    Usage:
        @app.get("/")
        async def read_items(db: Session = Depends(get_db_session)):
            return db.query(Item).all()
    """
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()

def init_database():
    """Initialize database tables"""
    db_manager.create_tables()

def close_database():
    """Close database connections"""
    db_manager.close()

# Health check function
def check_database_health() -> bool:
    """Check if database is accessible"""
    try:
        session = db_manager.get_session()
        session.execute("SELECT 1")
        session.close()
        return True
    except Exception:
        return False
