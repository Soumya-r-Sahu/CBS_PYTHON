"""
Payment Service Infrastructure - Database Layer
Production-ready SQLAlchemy models for payment processing
"""

from sqlalchemy import (
    Column, String, Numeric, DateTime, Text, Integer, Boolean, 
    Enum as SQLEnum, ForeignKey, Index, CheckConstraint, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
from decimal import Decimal

Base = declarative_base()


class PaymentModel(Base):
    """Payment database model"""
    __tablename__ = 'payments'
    
    # Primary identification
    payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Payment details
    payment_type = Column(SQLEnum(
        'upi', 'neft', 'rtgs', 'imps', 'internal_transfer', 
        'bill_payment', 'merchant_payment',
        name='payment_type_enum'
    ), nullable=False)
    
    status = Column(SQLEnum(
        'initiated', 'pending', 'processing', 'completed', 
        'failed', 'cancelled', 'refunded',
        name='payment_status_enum'
    ), nullable=False, default='initiated', index=True)
    
    channel = Column(SQLEnum(
        'mobile', 'internet_banking', 'atm', 'branch', 'api',
        name='payment_channel_enum'
    ), nullable=False, default='api')
    
    # Amount details
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='USD')
    
    # Party details - Sender
    sender_account_number = Column(String(50), nullable=False, index=True)
    sender_account_name = Column(String(200), nullable=False)
    sender_bank_code = Column(String(20), nullable=False)
    sender_bank_name = Column(String(200), nullable=False)
    sender_branch_code = Column(String(20))
    sender_ifsc_code = Column(String(20))
    
    # Party details - Receiver
    receiver_account_number = Column(String(50), nullable=False, index=True)
    receiver_account_name = Column(String(200), nullable=False)
    receiver_bank_code = Column(String(20), nullable=False)
    receiver_bank_name = Column(String(200), nullable=False)
    receiver_branch_code = Column(String(20))
    receiver_ifsc_code = Column(String(20))
    
    # UPI specific details
    upi_vpa = Column(String(100))
    upi_merchant_id = Column(String(50))
    upi_qr_code = Column(Text)
    upi_purpose = Column(String(100))
    
    # Bill payment details
    bill_biller_id = Column(String(50))
    bill_biller_name = Column(String(200))
    bill_number = Column(String(100))
    bill_due_date = Column(DateTime)
    bill_amount = Column(Numeric(18, 2))
    
    # Fraud detection
    fraud_risk_level = Column(SQLEnum(
        'low', 'medium', 'high', 'critical',
        name='fraud_risk_level_enum'
    ))
    fraud_risk_score = Column(Integer)
    fraud_flags = Column(JSON)
    fraud_checked_at = Column(DateTime)
    
    # Timestamps
    initiated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    processed_at = Column(DateTime, index=True)
    completed_at = Column(DateTime, index=True)
    
    # System fields
    initiated_by = Column(String(100))
    processed_by = Column(String(100))
    failure_reason = Column(Text)
    description = Column(Text)
    metadata = Column(JSON, default=dict)
    version = Column(Integer, default=1, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    payment_limits = relationship("PaymentLimitModel", back_populates="payment")
    emi_schedules = relationship("EMIScheduleModel", back_populates="payment")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('amount > 0', name='positive_amount'),
        CheckConstraint('fraud_risk_score >= 0 AND fraud_risk_score <= 100', name='valid_risk_score'),
        Index('idx_payment_status_type', 'status', 'payment_type'),
        Index('idx_payment_dates', 'initiated_at', 'completed_at'),
        Index('idx_payment_parties', 'sender_account_number', 'receiver_account_number'),
    )


class PaymentLimitModel(Base):
    """Payment limits and restrictions"""
    __tablename__ = 'payment_limits'
    
    limit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey('payments.payment_id'), nullable=False)
    
    # Limit details
    limit_type = Column(SQLEnum(
        'daily_amount', 'monthly_amount', 'transaction_count', 
        'single_transaction', 'velocity_check',
        name='limit_type_enum'
    ), nullable=False)
    
    limit_value = Column(Numeric(18, 2), nullable=False)
    current_usage = Column(Numeric(18, 2), default=0)
    limit_period_start = Column(DateTime, nullable=False)
    limit_period_end = Column(DateTime, nullable=False)
    
    # Status
    is_breached = Column(Boolean, default=False, nullable=False)
    breach_timestamp = Column(DateTime)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    payment = relationship("PaymentModel", back_populates="payment_limits")
    
    __table_args__ = (
        Index('idx_limit_type_period', 'limit_type', 'limit_period_start', 'limit_period_end'),
    )


class EMIScheduleModel(Base):
    """EMI payment schedules for installment payments"""
    __tablename__ = 'emi_schedules'
    
    emi_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey('payments.payment_id'), nullable=False)
    
    # EMI details
    installment_number = Column(Integer, nullable=False)
    total_installments = Column(Integer, nullable=False)
    emi_amount = Column(Numeric(18, 2), nullable=False)
    principal_amount = Column(Numeric(18, 2), nullable=False)
    interest_amount = Column(Numeric(18, 2), nullable=False)
    
    # Schedule
    due_date = Column(DateTime, nullable=False, index=True)
    payment_date = Column(DateTime)
    
    # Status
    status = Column(SQLEnum(
        'pending', 'paid', 'overdue', 'waived', 'partially_paid',
        name='emi_status_enum'
    ), nullable=False, default='pending')
    
    paid_amount = Column(Numeric(18, 2), default=0)
    penalty_amount = Column(Numeric(18, 2), default=0)
    waived_amount = Column(Numeric(18, 2), default=0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    payment = relationship("PaymentModel", back_populates="emi_schedules")
    
    __table_args__ = (
        CheckConstraint('emi_amount > 0', name='positive_emi_amount'),
        CheckConstraint('installment_number > 0', name='positive_installment_number'),
        CheckConstraint('total_installments > 0', name='positive_total_installments'),
        CheckConstraint('installment_number <= total_installments', name='valid_installment_number'),
        Index('idx_emi_due_date_status', 'due_date', 'status'),
    )


class FraudDetectionModel(Base):
    """Advanced fraud detection results and patterns"""
    __tablename__ = 'fraud_detection'
    
    fraud_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey('payments.payment_id'), nullable=False)
    
    # Risk assessment
    risk_level = Column(SQLEnum(
        'low', 'medium', 'high', 'critical',
        name='fraud_risk_level_enum'
    ), nullable=False)
    risk_score = Column(Integer, nullable=False)
    
    # Detection details
    detection_rules = Column(JSON)  # Rules that triggered
    anomaly_indicators = Column(JSON)  # Specific anomalies detected
    behavioral_patterns = Column(JSON)  # User behavior analysis
    device_fingerprint = Column(JSON)  # Device characteristics
    geolocation_data = Column(JSON)  # Location information
    
    # ML model results
    ml_model_version = Column(String(50))
    ml_confidence_score = Column(Numeric(5, 4))  # 0.0000 to 1.0000
    ml_features = Column(JSON)  # Features used for prediction
    
    # Resolution
    is_false_positive = Column(Boolean)
    reviewed_by = Column(String(100))
    review_notes = Column(Text)
    review_timestamp = Column(DateTime)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        CheckConstraint('risk_score >= 0 AND risk_score <= 100', name='valid_risk_score'),
        CheckConstraint('ml_confidence_score >= 0 AND ml_confidence_score <= 1', name='valid_confidence_score'),
        Index('idx_fraud_risk_level_score', 'risk_level', 'risk_score'),
        Index('idx_fraud_timestamp', 'created_at'),
    )


class PaymentBatchModel(Base):
    """Batch processing for bulk payments (NEFT, RTGS)"""
    __tablename__ = 'payment_batches'
    
    batch_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    batch_reference = Column(String(50), unique=True, nullable=False, index=True)
    
    # Batch details
    batch_type = Column(SQLEnum(
        'neft', 'rtgs', 'bulk_transfer', 'salary_batch',
        name='batch_type_enum'
    ), nullable=False)
    
    batch_status = Column(SQLEnum(
        'created', 'validated', 'submitted', 'processing', 
        'completed', 'failed', 'partially_processed',
        name='batch_status_enum'
    ), nullable=False, default='created')
    
    # Batch statistics
    total_payments = Column(Integer, nullable=False, default=0)
    total_amount = Column(Numeric(18, 2), nullable=False, default=0)
    successful_payments = Column(Integer, default=0)
    failed_payments = Column(Integer, default=0)
    
    # Processing
    submitted_at = Column(DateTime)
    processed_at = Column(DateTime)
    completion_timestamp = Column(DateTime)
    
    # System fields
    created_by = Column(String(100), nullable=False)
    processed_by = Column(String(100))
    failure_reason = Column(Text)
    metadata = Column(JSON, default=dict)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        CheckConstraint('total_payments >= 0', name='non_negative_total_payments'),
        CheckConstraint('total_amount >= 0', name='non_negative_total_amount'),
        CheckConstraint('successful_payments >= 0', name='non_negative_successful_payments'),
        CheckConstraint('failed_payments >= 0', name='non_negative_failed_payments'),
        Index('idx_batch_status_type', 'batch_status', 'batch_type'),
        Index('idx_batch_timestamps', 'submitted_at', 'processed_at'),
    )


class PaymentGatewayModel(Base):
    """Payment gateway configurations and responses"""
    __tablename__ = 'payment_gateways'
    
    gateway_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey('payments.payment_id'), nullable=False)
    
    # Gateway details
    gateway_name = Column(String(100), nullable=False)
    gateway_type = Column(SQLEnum(
        'upi', 'neft', 'rtgs', 'imps', 'card', 'wallet',
        name='gateway_type_enum'
    ), nullable=False)
    
    # Transaction details
    gateway_transaction_id = Column(String(100), unique=True, index=True)
    gateway_reference = Column(String(100))
    gateway_status = Column(String(50))
    
    # Request/Response
    request_payload = Column(JSON)
    response_payload = Column(JSON)
    error_details = Column(JSON)
    
    # Timing
    request_timestamp = Column(DateTime, default=datetime.utcnow)
    response_timestamp = Column(DateTime)
    processing_time_ms = Column(Integer)
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False)
    reconciled_at = Column(DateTime)
    reconciliation_reference = Column(String(100))
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_gateway_transaction_id', 'gateway_transaction_id'),
        Index('idx_gateway_name_type', 'gateway_name', 'gateway_type'),
        Index('idx_gateway_reconciliation', 'is_reconciled', 'reconciled_at'),
    )


# Database utilities
class DatabaseManager:
    """Database session and connection management"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.session
    
    def close_session(self):
        """Close database session"""
        if self.session:
            self.session.close()
    
    def commit(self):
        """Commit transaction"""
        self.session.commit()
    
    def rollback(self):
        """Rollback transaction"""
        self.session.rollback()
    
    def flush(self):
        """Flush session"""
        self.session.flush()


# Export all models and utilities
__all__ = [
    'Base',
    'PaymentModel',
    'PaymentLimitModel', 
    'EMIScheduleModel',
    'FraudDetectionModel',
    'PaymentBatchModel',
    'PaymentGatewayModel',
    'DatabaseManager'
]
