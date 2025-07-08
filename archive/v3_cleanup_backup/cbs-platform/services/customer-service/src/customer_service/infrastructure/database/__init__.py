"""
Database Infrastructure for Customer Service
SQLAlchemy models and database session management
"""

from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Text, Integer, Decimal
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional
import os

# Database configuration
DATABASE_URL = os.getenv(
    "CUSTOMER_DATABASE_URL", 
    "postgresql://cbs_user:cbs_password@localhost:5432/cbs_customer_db"
)

Base = declarative_base()

# SQLAlchemy Models

class CustomerModel(Base):
    """Customer database model"""
    __tablename__ = "customers"
    
    customer_id = Column(String(36), primary_key=True)
    customer_number = Column(String(20), unique=True, nullable=False)
    customer_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    
    # Personal information
    first_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    last_name = Column(String(100), nullable=False)
    full_name = Column(String(300), nullable=False)
    date_of_birth = Column(DateTime)
    gender = Column(String(10))
    nationality = Column(String(50))
    marital_status = Column(String(20))
    
    # Contact information
    email = Column(String(255))
    phone = Column(String(20))
    alternate_phone = Column(String(20))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(100))
    
    # Identification
    id_type = Column(String(50))
    id_number = Column(String(100))
    id_issue_date = Column(DateTime)
    id_expiry_date = Column(DateTime)
    id_issuing_authority = Column(String(255))
    
    # Financial information
    occupation = Column(String(100))
    employer_name = Column(String(255))
    annual_income = Column(Decimal(15, 2))
    income_currency = Column(String(3), default="USD")
    source_of_funds = Column(String(255))
    
    # Risk and compliance
    risk_profile = Column(String(20), default="MEDIUM")
    aml_status = Column(String(20), default="CLEAR")
    kyc_status = Column(String(20), default="PENDING")
    kyc_completion_date = Column(DateTime)
    sanctions_screening_status = Column(String(20), default="CLEAR")
    pep_status = Column(Boolean, default=False)
    
    # Preferences
    preferred_language = Column(String(10), default="en")
    preferred_communication_channel = Column(String(20), default="EMAIL")
    marketing_consent = Column(Boolean, default=False)
    
    # System fields
    created_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)
    
    # Additional data as JSON
    metadata_json = Column(Text)


class DocumentModel(Base):
    """Customer document database model"""
    __tablename__ = "customer_documents"
    
    document_id = Column(String(36), primary_key=True)
    customer_id = Column(String(36), nullable=False)
    document_type = Column(String(50), nullable=False)
    document_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    mime_type = Column(String(100))
    checksum = Column(String(64))
    
    # Document status
    status = Column(String(20), default="UPLOADED")
    verification_status = Column(String(20), default="PENDING")
    verified_by = Column(String(100))
    verified_at = Column(DateTime)
    verification_notes = Column(Text)
    
    # Expiry information
    issue_date = Column(DateTime)
    expiry_date = Column(DateTime)
    issuing_authority = Column(String(255))
    
    # System fields
    uploaded_by = Column(String(100))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(Integer, default=1)


# Database Engine and Session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def get_db_session() -> Session:
    """Get database session"""
    return SessionLocal()


def close_db_session(session: Session):
    """Close database session"""
    session.close()


# Database utilities

def init_database():
    """Initialize database with tables"""
    try:
        create_tables()
        print("Customer service database initialized successfully")
    except Exception as e:
        print(f"Failed to initialize customer service database: {e}")
        raise


def health_check() -> bool:
    """Check database connectivity"""
    try:
        session = get_db_session()
        session.execute("SELECT 1")
        session.close()
        return True
    except Exception:
        return False
