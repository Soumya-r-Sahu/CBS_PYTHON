"""
Database Configuration and Models for Transaction Service
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
    "TRANSACTION_DATABASE_URL", 
    "postgresql://cbs_user:cbs_password@localhost/cbs_transaction_db"
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


# Transaction Model
class TransactionModel(Base):
    """Transaction database model"""
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Account information
    from_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    to_account_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(String(20), nullable=False, default="pending", index=True)
    
    # Transaction context
    description = Column(Text, nullable=True)
    reference_number = Column(String(100), nullable=True, index=True)
    category = Column(String(50), nullable=True, index=True)
    
    # Fees and charges
    transaction_fee = Column(Numeric(10, 2), nullable=False, default=0.00)
    service_charge = Column(Numeric(10, 2), nullable=False, default=0.00)
    tax_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    exchange_rate = Column(Numeric(10, 6), nullable=True)
    
    # Processing details
    processing_method = Column(String(50), nullable=True)  # immediate, batch, scheduled
    scheduled_at = Column(DateTime, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Channel and location
    channel = Column(String(50), nullable=True)  # web, mobile, atm, branch, api
    location = Column(String(255), nullable=True)
    device_info = Column(JSONB, nullable=True)
    
    # Business rules
    approval_required = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_notes = Column(Text, nullable=True)
    
    # Risk and compliance
    risk_score = Column(Numeric(5, 2), nullable=True)
    aml_check_status = Column(String(20), nullable=True)
    fraud_check_status = Column(String(20), nullable=True)
    compliance_notes = Column(Text, nullable=True)
    
    # Reconciliation
    reconciliation_status = Column(String(20), nullable=False, default="pending")
    reconciled_at = Column(DateTime, nullable=True)
    reconciled_by = Column(String(100), nullable=True)
    
    # Metadata
    metadata = Column(JSONB, nullable=True)
    tags = Column(JSONB, nullable=True)  # For categorization and filtering
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    version = Column(Integer, nullable=False, default=1)
    
    # Relationships
    legs = relationship("TransactionLegModel", back_populates="transaction", lazy="dynamic")
    
    # Indexes
    __table_args__ = (
        Index('idx_transaction_from_account', 'from_account_id'),
        Index('idx_transaction_to_account', 'to_account_id'),
        Index('idx_transaction_type_status', 'transaction_type', 'status'),
        Index('idx_transaction_date_range', 'created_at'),
        Index('idx_transaction_processed', 'processed_at'),
        Index('idx_transaction_reference', 'reference_number'),
        Index('idx_transaction_channel', 'channel'),
        Index('idx_transaction_category', 'category'),
    )


# Transaction Leg Model (for double-entry bookkeeping)
class TransactionLegModel(Base):
    """Transaction leg database model for double-entry accounting"""
    __tablename__ = "transaction_legs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), nullable=False, index=True)
    
    # Account and amounts
    account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    debit_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    credit_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Balance tracking
    balance_before = Column(Numeric(15, 2), nullable=False)
    balance_after = Column(Numeric(15, 2), nullable=False)
    
    # Leg details
    leg_type = Column(String(20), nullable=False)  # debit, credit
    description = Column(Text, nullable=True)
    
    # GL account mapping
    gl_account_code = Column(String(20), nullable=True)
    cost_center = Column(String(20), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    transaction = relationship("TransactionModel", back_populates="legs")
    
    # Indexes
    __table_args__ = (
        Index('idx_leg_transaction_account', 'transaction_id', 'account_id'),
        Index('idx_leg_account_date', 'account_id', 'created_at'),
        Index('idx_leg_gl_account', 'gl_account_code'),
    )


# Transaction Batch Model (for batch processing)
class TransactionBatchModel(Base):
    """Transaction batch database model"""
    __tablename__ = "transaction_batches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Batch details
    batch_type = Column(String(20), nullable=False)  # salary, bulk_transfer, scheduled
    batch_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Processing status
    status = Column(String(20), nullable=False, default="created")  # created, processing, completed, failed
    total_transactions = Column(Integer, nullable=False, default=0)
    successful_transactions = Column(Integer, nullable=False, default=0)
    failed_transactions = Column(Integer, nullable=False, default=0)
    
    # Amounts
    total_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Scheduling
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_batch_status', 'status'),
        Index('idx_batch_scheduled', 'scheduled_at'),
        Index('idx_batch_type', 'batch_type'),
    )


# Transaction Rule Model (for business rules)
class TransactionRuleModel(Base):
    """Transaction rule database model"""
    __tablename__ = "transaction_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_name = Column(String(100), nullable=False)
    rule_type = Column(String(20), nullable=False)  # limit, fee, approval, validation
    
    # Rule conditions
    conditions = Column(JSONB, nullable=False)  # JSON conditions for rule matching
    actions = Column(JSONB, nullable=False)     # JSON actions to execute
    
    # Applicability
    account_types = Column(JSONB, nullable=True)      # Which account types this applies to
    transaction_types = Column(JSONB, nullable=True)  # Which transaction types this applies to
    channels = Column(JSONB, nullable=True)           # Which channels this applies to
    
    # Rule status
    is_active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=100)
    
    # Effective dates
    effective_from = Column(DateTime, nullable=False, default=datetime.utcnow)
    effective_to = Column(DateTime, nullable=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_rule_type_active', 'rule_type', 'is_active'),
        Index('idx_rule_effective', 'effective_from', 'effective_to'),
        Index('idx_rule_priority', 'priority'),
    )


# Transaction Limit Model
class TransactionLimitModel(Base):
    """Transaction limit database model"""
    __tablename__ = "transaction_limits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Limit scope
    account_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Null for global limits
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    account_type = Column(String(20), nullable=True)
    
    # Limit details
    limit_type = Column(String(20), nullable=False)  # daily, monthly, per_transaction, velocity
    transaction_type = Column(String(20), nullable=True)  # Which transaction type
    channel = Column(String(50), nullable=True)  # Which channel
    
    # Amounts
    limit_amount = Column(Numeric(15, 2), nullable=False)
    used_amount = Column(Numeric(15, 2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default="USD")
    
    # Count limits
    count_limit = Column(Integer, nullable=True)
    used_count = Column(Integer, nullable=False, default=0)
    
    # Time period
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    
    # Reset schedule
    reset_frequency = Column(String(20), nullable=True)  # daily, weekly, monthly
    last_reset_at = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_limit_account', 'account_id'),
        Index('idx_limit_customer', 'customer_id'),
        Index('idx_limit_type_channel', 'limit_type', 'channel'),
        Index('idx_limit_period', 'period_start', 'period_end'),
    )


# Database event listeners
@event.listens_for(TransactionModel, 'before_update')
def transaction_update_version(mapper, connection, target):
    """Update version on transaction changes"""
    target.version += 1
    target.updated_at = datetime.utcnow()


@event.listens_for(TransactionModel, 'before_insert')
def set_transaction_id(mapper, connection, target):
    """Generate unique transaction ID if not provided"""
    if not target.transaction_id:
        # Generate unique transaction ID with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        target.transaction_id = f"TXN{timestamp}{str(uuid.uuid4())[:8].upper()}"


@event.listens_for(TransactionBatchModel, 'before_insert')
def set_batch_id(mapper, connection, target):
    """Generate unique batch ID if not provided"""
    if not target.batch_id:
        # Generate unique batch ID with timestamp
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        target.batch_id = f"BATCH{timestamp}{str(uuid.uuid4())[:6].upper()}"


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
            tables_exist = engine.dialect.has_table(engine, 'transactions')
            
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
    "TransactionModel",
    "TransactionLegModel",
    "TransactionBatchModel",
    "TransactionRuleModel",
    "TransactionLimitModel",
    "create_tables",
    "drop_tables",
    "check_database_health"
]
