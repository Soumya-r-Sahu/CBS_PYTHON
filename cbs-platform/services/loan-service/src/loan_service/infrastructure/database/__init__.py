"""
Loan Service Infrastructure - Database Layer
Production-ready SQLAlchemy models for loan management
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


class LoanModel(Base):
    """Loan database model"""
    __tablename__ = 'loans'
    
    # Primary identification
    loan_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Customer and account details
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    primary_account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Loan details
    loan_type = Column(SQLEnum(
        'personal', 'home', 'auto', 'business', 'education', 
        'gold', 'agriculture', 'mortgage',
        name='loan_type_enum'
    ), nullable=False)
    
    loan_purpose = Column(String(200), nullable=False)
    loan_amount = Column(Numeric(18, 2), nullable=False)
    approved_amount = Column(Numeric(18, 2))
    disbursed_amount = Column(Numeric(18, 2), default=0)
    outstanding_amount = Column(Numeric(18, 2), default=0)
    
    # Terms
    interest_rate = Column(Numeric(5, 4), nullable=False)  # 99.9999% max
    tenure_months = Column(Integer, nullable=False)
    emi_amount = Column(Numeric(18, 2))
    
    # Status
    status = Column(SQLEnum(
        'draft', 'submitted', 'under_review', 'approved', 'rejected',
        'disbursed', 'active', 'completed', 'defaulted', 'cancelled',
        name='loan_status_enum'
    ), nullable=False, default='draft', index=True)
    
    # Risk assessment
    risk_category = Column(SQLEnum(
        'low', 'medium', 'high', 'very_high',
        name='risk_category_enum'
    ), default='medium')
    credit_score = Column(Integer)
    debt_to_income_ratio = Column(Numeric(5, 4))
    
    # Dates
    application_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    approval_date = Column(DateTime)
    disbursement_date = Column(DateTime)
    maturity_date = Column(DateTime)
    
    # Repayment details
    next_due_date = Column(DateTime, index=True)
    last_payment_date = Column(DateTime)
    total_payments_made = Column(Integer, default=0)
    total_amount_paid = Column(Numeric(18, 2), default=0)
    overdue_amount = Column(Numeric(18, 2), default=0)
    days_past_due = Column(Integer, default=0)
    
    # System fields
    created_by = Column(String(100), nullable=False)
    approved_by = Column(String(100))
    rejected_by = Column(String(100))
    rejection_reason = Column(Text)
    notes = Column(Text)
    metadata = Column(JSON, default=dict)
    version = Column(Integer, default=1, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    emi_schedules = relationship("EMIScheduleModel", back_populates="loan", cascade="all, delete-orphan")
    loan_documents = relationship("LoanDocumentModel", back_populates="loan", cascade="all, delete-orphan")
    collaterals = relationship("CollateralModel", back_populates="loan", cascade="all, delete-orphan")
    payment_history = relationship("LoanPaymentModel", back_populates="loan", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('loan_amount > 0', name='positive_loan_amount'),
        CheckConstraint('approved_amount >= 0', name='non_negative_approved_amount'),
        CheckConstraint('disbursed_amount >= 0', name='non_negative_disbursed_amount'),
        CheckConstraint('outstanding_amount >= 0', name='non_negative_outstanding_amount'),
        CheckConstraint('interest_rate > 0', name='positive_interest_rate'),
        CheckConstraint('tenure_months > 0', name='positive_tenure'),
        CheckConstraint('credit_score >= 300 AND credit_score <= 850', name='valid_credit_score'),
        CheckConstraint('debt_to_income_ratio >= 0 AND debt_to_income_ratio <= 1', name='valid_dti_ratio'),
        Index('idx_loan_status_type', 'status', 'loan_type'),
        Index('idx_loan_dates', 'application_date', 'next_due_date'),
        Index('idx_loan_customer', 'customer_id', 'status'),
    )


class EMIScheduleModel(Base):
    """EMI payment schedule for loans"""
    __tablename__ = 'emi_schedules'
    
    emi_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = Column(UUID(as_uuid=True), ForeignKey('loans.loan_id'), nullable=False)
    
    # EMI details
    installment_number = Column(Integer, nullable=False)
    emi_amount = Column(Numeric(18, 2), nullable=False)
    principal_amount = Column(Numeric(18, 2), nullable=False)
    interest_amount = Column(Numeric(18, 2), nullable=False)
    
    # Schedule
    due_date = Column(DateTime, nullable=False, index=True)
    
    # Payment status
    status = Column(SQLEnum(
        'pending', 'paid', 'overdue', 'partially_paid', 'waived',
        name='emi_status_enum'
    ), nullable=False, default='pending')
    
    paid_amount = Column(Numeric(18, 2), default=0)
    payment_date = Column(DateTime)
    penalty_amount = Column(Numeric(18, 2), default=0)
    waived_amount = Column(Numeric(18, 2), default=0)
    
    # Outstanding
    outstanding_principal = Column(Numeric(18, 2), nullable=False)
    outstanding_interest = Column(Numeric(18, 2), nullable=False)
    outstanding_penalty = Column(Numeric(18, 2), default=0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    loan = relationship("LoanModel", back_populates="emi_schedules")
    
    __table_args__ = (
        CheckConstraint('emi_amount > 0', name='positive_emi_amount'),
        CheckConstraint('principal_amount >= 0', name='non_negative_principal'),
        CheckConstraint('interest_amount >= 0', name='non_negative_interest'),
        CheckConstraint('installment_number > 0', name='positive_installment_number'),
        Index('idx_emi_due_date_status', 'due_date', 'status'),
        Index('idx_emi_loan_installment', 'loan_id', 'installment_number'),
    )


class LoanDocumentModel(Base):
    """Loan documents and attachments"""
    __tablename__ = 'loan_documents'
    
    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = Column(UUID(as_uuid=True), ForeignKey('loans.loan_id'), nullable=False)
    
    # Document details
    document_type = Column(SQLEnum(
        'application', 'income_proof', 'identity_proof', 'address_proof',
        'bank_statement', 'property_document', 'insurance', 'agreement',
        'guarantee', 'collateral_document', 'other',
        name='document_type_enum'
    ), nullable=False)
    
    document_name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))
    checksum = Column(String(64))  # SHA-256 hash
    
    # Status
    verification_status = Column(SQLEnum(
        'pending', 'verified', 'rejected', 'expired',
        name='verification_status_enum'
    ), default='pending')
    
    verified_by = Column(String(100))
    verified_at = Column(DateTime)
    verification_notes = Column(Text)
    
    # Metadata
    is_mandatory = Column(Boolean, default=False)
    expiry_date = Column(DateTime)
    upload_source = Column(String(50))  # web, mobile, branch, etc.
    
    # Audit
    uploaded_by = Column(String(100), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    loan = relationship("LoanModel", back_populates="loan_documents")
    
    __table_args__ = (
        Index('idx_document_loan_type', 'loan_id', 'document_type'),
        Index('idx_document_verification', 'verification_status', 'verified_at'),
    )


class CollateralModel(Base):
    """Loan collateral information"""
    __tablename__ = 'collaterals'
    
    collateral_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = Column(UUID(as_uuid=True), ForeignKey('loans.loan_id'), nullable=False)
    
    # Collateral details
    collateral_type = Column(SQLEnum(
        'property', 'vehicle', 'gold', 'securities', 'fixed_deposit',
        'insurance_policy', 'machinery', 'inventory', 'other',
        name='collateral_type_enum'
    ), nullable=False)
    
    description = Column(Text, nullable=False)
    estimated_value = Column(Numeric(18, 2), nullable=False)
    verified_value = Column(Numeric(18, 2))
    
    # Property specific (if applicable)
    property_address = Column(Text)
    property_type = Column(String(100))
    property_area = Column(Numeric(10, 2))
    property_registration_number = Column(String(100))
    
    # Vehicle specific (if applicable)
    vehicle_make = Column(String(100))
    vehicle_model = Column(String(100))
    vehicle_year = Column(Integer)
    vehicle_registration_number = Column(String(50))
    
    # Verification
    verification_status = Column(SQLEnum(
        'pending', 'verified', 'rejected', 'revaluation_required',
        name='collateral_verification_status_enum'
    ), default='pending')
    
    verified_by = Column(String(100))
    verified_at = Column(DateTime)
    verification_notes = Column(Text)
    valuation_date = Column(DateTime)
    next_valuation_date = Column(DateTime)
    
    # Legal
    ownership_status = Column(SQLEnum(
        'owned', 'jointly_owned', 'inherited', 'purchased',
        name='ownership_status_enum'
    ))
    
    legal_documents = Column(JSON)
    insurance_details = Column(JSON)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    loan = relationship("LoanModel", back_populates="collaterals")
    
    __table_args__ = (
        CheckConstraint('estimated_value > 0', name='positive_estimated_value'),
        CheckConstraint('verified_value >= 0', name='non_negative_verified_value'),
        Index('idx_collateral_loan_type', 'loan_id', 'collateral_type'),
        Index('idx_collateral_verification', 'verification_status', 'verified_at'),
    )


class LoanPaymentModel(Base):
    """Loan payment history"""
    __tablename__ = 'loan_payments'
    
    payment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = Column(UUID(as_uuid=True), ForeignKey('loans.loan_id'), nullable=False)
    emi_id = Column(UUID(as_uuid=True), ForeignKey('emi_schedules.emi_id'))
    
    # Payment details
    payment_amount = Column(Numeric(18, 2), nullable=False)
    principal_amount = Column(Numeric(18, 2), nullable=False)
    interest_amount = Column(Numeric(18, 2), nullable=False)
    penalty_amount = Column(Numeric(18, 2), default=0)
    processing_fee = Column(Numeric(18, 2), default=0)
    
    # Payment method
    payment_method = Column(SQLEnum(
        'cash', 'cheque', 'online_transfer', 'auto_debit', 'upi',
        'card', 'ach', 'wire_transfer',
        name='payment_method_enum'
    ), nullable=False)
    
    payment_reference = Column(String(100))
    transaction_id = Column(String(100))
    
    # Dates
    payment_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    value_date = Column(DateTime)
    
    # Status
    status = Column(SQLEnum(
        'pending', 'processed', 'bounced', 'reversed', 'failed',
        name='payment_status_enum'
    ), nullable=False, default='pending')
    
    # Outstanding after payment
    outstanding_principal = Column(Numeric(18, 2), nullable=False)
    outstanding_interest = Column(Numeric(18, 2), nullable=False)
    outstanding_penalty = Column(Numeric(18, 2), default=0)
    
    # System fields
    processed_by = Column(String(100))
    reversal_reason = Column(Text)
    notes = Column(Text)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    loan = relationship("LoanModel", back_populates="payment_history")
    
    __table_args__ = (
        CheckConstraint('payment_amount > 0', name='positive_payment_amount'),
        CheckConstraint('principal_amount >= 0', name='non_negative_principal_payment'),
        CheckConstraint('interest_amount >= 0', name='non_negative_interest_payment'),
        CheckConstraint('penalty_amount >= 0', name='non_negative_penalty_payment'),
        Index('idx_payment_loan_date', 'loan_id', 'payment_date'),
        Index('idx_payment_status', 'status', 'payment_date'),
    )


class LoanApplicationModel(Base):
    """Loan application workflow"""
    __tablename__ = 'loan_applications'
    
    application_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loan_id = Column(UUID(as_uuid=True), ForeignKey('loans.loan_id'), nullable=False)
    
    # Application stage
    current_stage = Column(SQLEnum(
        'application_submitted', 'document_verification', 'credit_check',
        'property_valuation', 'legal_verification', 'approval_committee',
        'final_approval', 'loan_agreement', 'disbursement',
        name='application_stage_enum'
    ), nullable=False)
    
    # Workflow
    workflow_data = Column(JSON)
    approval_hierarchy = Column(JSON)
    
    # Credit evaluation
    credit_evaluation = Column(JSON)
    risk_assessment = Column(JSON)
    underwriting_notes = Column(Text)
    
    # Decision
    final_decision = Column(SQLEnum(
        'pending', 'approved', 'rejected', 'cancelled',
        name='application_decision_enum'
    ))
    
    decision_date = Column(DateTime)
    decision_maker = Column(String(100))
    decision_notes = Column(Text)
    
    # Conditions
    approval_conditions = Column(JSON)
    conditions_satisfied = Column(Boolean, default=False)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_application_stage', 'current_stage', 'created_at'),
        Index('idx_application_decision', 'final_decision', 'decision_date'),
    )


# Database utilities
class LoanDatabaseManager:
    """Database session and connection management for loans"""
    
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
    
    def calculate_emi_schedule(
        self, 
        principal: Decimal, 
        rate: Decimal, 
        tenure_months: int
    ) -> List[Dict[str, Any]]:
        """Calculate EMI schedule"""
        import math
        
        monthly_rate = rate / (12 * 100)  # Convert annual % to monthly decimal
        
        # Calculate EMI using formula: P * r * (1+r)^n / ((1+r)^n - 1)
        emi = principal * monthly_rate * (1 + monthly_rate) ** tenure_months / ((1 + monthly_rate) ** tenure_months - 1)
        emi = round(emi, 2)
        
        schedule = []
        outstanding = principal
        
        for month in range(1, tenure_months + 1):
            interest = round(outstanding * monthly_rate, 2)
            principal_payment = round(emi - interest, 2)
            
            # Handle last installment rounding
            if month == tenure_months:
                principal_payment = outstanding
                emi = principal_payment + interest
            
            outstanding = round(outstanding - principal_payment, 2)
            
            schedule.append({
                'installment_number': month,
                'emi_amount': emi,
                'principal_amount': principal_payment,
                'interest_amount': interest,
                'outstanding_principal': outstanding,
                'outstanding_interest': 0
            })
        
        return schedule


# Export all models and utilities
__all__ = [
    'Base',
    'LoanModel',
    'EMIScheduleModel',
    'LoanDocumentModel',
    'CollateralModel', 
    'LoanPaymentModel',
    'LoanApplicationModel',
    'LoanDatabaseManager'
]
