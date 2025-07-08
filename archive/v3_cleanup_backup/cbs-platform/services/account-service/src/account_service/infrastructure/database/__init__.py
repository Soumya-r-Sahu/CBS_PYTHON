"""
Database Configuration and Models for Account Service
SQLAlchemy models and database session management
"""

from sqlalchemy import (
    Column, String, Integer, Numeric, DateTime, Text, Boolean, 
    Enum, ForeignKey, Index, create_engine, event
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
import os
from contextlib import contextmanager
from typing import Generator, Optional

# Create base class
Base = declarative_base()

# Database configuration
DATABASE_URL = os.getenv(
    "ACCOUNT_DATABASE_URL", 
    "postgresql://cbs_user:cbs_password@localhost/cbs_account_db"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true"
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Get database session with proper cleanup
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_db() -> Session:
    """
    Dependency for getting database session
    """
    return SessionLocal()


# Account Model
class AccountModel(Base):
    """Account database model"""
    __tablename__ = "accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_number = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    account_type = Column(String(20), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="active", index=True)
    
    # Balance and currency
    balance = Column(Numeric(15, 2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Account limits (stored as JSON)
    daily_withdrawal_limit = Column(Numeric(15, 2), nullable=False, default=5000.00)
    daily_transfer_limit = Column(Numeric(15, 2), nullable=False, default=10000.00)
    monthly_transaction_limit = Column(Numeric(15, 2), nullable=False, default=100000.00)
    minimum_balance = Column(Numeric(15, 2), nullable=False, default=0.00)
    maximum_balance = Column(Numeric(15, 2), nullable=True)
    
    # Interest and fees
    interest_rate = Column(Numeric(5, 4), nullable=True, default=0.0000)
    maintenance_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    overdraft_limit = Column(Numeric(15, 2), nullable=True)
    overdraft_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    
    # Metadata
    metadata = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    
    # Relationships
    transactions = relationship("TransactionModel", back_populates="account", lazy="dynamic")
    
    # Indexes
    __table_args__ = (
        Index('idx_account_customer_type', 'customer_id', 'account_type'),
        Index('idx_account_status_type', 'status', 'account_type'),
        Index('idx_account_created', 'created_at'),
    )


# Transaction Model
class TransactionModel(Base):
    """Transaction database model"""
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String(50), unique=True, nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(String(20), nullable=False, default="pending", index=True)
    
    # Transaction context
    description = Column(Text, nullable=True)
    reference_number = Column(String(100), nullable=True, index=True)
    related_account_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Balances
    balance_before = Column(Numeric(15, 2), nullable=False)
    balance_after = Column(Numeric(15, 2), nullable=False)
    
    # Processing details
    processing_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    exchange_rate = Column(Numeric(10, 6), nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True)
    channel = Column(String(50), nullable=True)  # web, mobile, atm, branch
    location = Column(String(255), nullable=True)
    
    # Audit fields
    initiated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(String(100), nullable=True)
    authorized_by = Column(String(100), nullable=True)
    
    # Relationships
    account = relationship("AccountModel", back_populates="transactions")
    
    # Indexes
    __table_args__ = (
        Index('idx_transaction_account_type', 'account_id', 'transaction_type'),
        Index('idx_transaction_status_date', 'status', 'initiated_at'),
        Index('idx_transaction_reference', 'reference_number'),
        Index('idx_transaction_date_range', 'initiated_at'),
    )


# Account Holder Model (for additional account holder information)
class AccountHolderModel(Base):
    """Account holder database model"""
    __tablename__ = "account_holders"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Holder details
    holder_type = Column(String(20), nullable=False, default="primary")  # primary, joint, beneficiary
    relationship = Column(String(50), nullable=True)  # spouse, child, parent, etc.
    authority_level = Column(String(20), nullable=False, default="full")  # full, read_only, limited
    
    # Permissions
    can_withdraw = Column(Boolean, nullable=False, default=True)
    can_transfer = Column(Boolean, nullable=False, default=True)
    can_view_statements = Column(Boolean, nullable=False, default=True)
    withdrawal_limit = Column(Numeric(15, 2), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_holder_account_customer', 'account_id', 'customer_id'),
        Index('idx_holder_type', 'holder_type'),
    )


# Account Statement Model
class AccountStatementModel(Base):
    """Account statement database model"""
    __tablename__ = "account_statements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id"), nullable=False, index=True)
    
    # Statement period
    statement_date = Column(DateTime, nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Balances
    opening_balance = Column(Numeric(15, 2), nullable=False)
    closing_balance = Column(Numeric(15, 2), nullable=False)
    
    # Summary
    total_credits = Column(Numeric(15, 2), nullable=False, default=0.00)
    total_debits = Column(Numeric(15, 2), nullable=False, default=0.00)
    transaction_count = Column(Integer, nullable=False, default=0)
    
    # Statement generation
    generated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    generated_by = Column(String(100), nullable=True)
    file_path = Column(String(500), nullable=True)  # Path to generated PDF/document
    
    # Indexes
    __table_args__ = (
        Index('idx_statement_account_date', 'account_id', 'statement_date'),
        Index('idx_statement_period', 'period_start', 'period_end'),
    )


# Database event listeners for audit trails
@event.listens_for(AccountModel, 'before_update')
def account_update_version(mapper, connection, target):
    """Update version on account changes"""
    target.version += 1
    target.updated_at = datetime.utcnow()


@event.listens_for(TransactionModel, 'before_insert')
def set_transaction_id(mapper, connection, target):
    """Generate unique transaction ID if not provided"""
    if not target.transaction_id:
        # Generate unique transaction ID with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        target.transaction_id = f"TXN{timestamp}{str(uuid.uuid4())[:8].upper()}"


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables"""
    Base.metadata.drop_all(bind=engine)


# Health check function
def check_database_health() -> dict:
    """
    Check database connectivity and basic operations
    """
    try:
        with get_db_session() as session:
            # Simple query to check connectivity
            result = session.execute("SELECT 1").scalar()
            
            # Check if tables exist
            tables_exist = engine.dialect.has_table(engine, 'accounts')
            
            return {
                "status": "healthy",
                "database_connected": True,
                "tables_exist": tables_exist,
                "query_test": result == 1
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database_connected": False,
            "error": str(e)
        }


__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db_session",
    "get_db",
    "AccountModel",
    "TransactionModel", 
    "AccountHolderModel",
    "AccountStatementModel",
    "create_tables",
    "drop_tables",
    "check_database_health"
]
