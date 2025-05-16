"""
SQL Loan Repository

This module implements the loan repository interface using SQL database.
"""
import uuid
import json
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import date, datetime

from sqlalchemy import create_engine, Column, String, Date, Boolean, Integer, Numeric, Text, ForeignKey, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func

from ...domain.entities.loan import (
    Loan, LoanStatus, LoanType, RepaymentFrequency, 
    LoanTerms, PaymentScheduleItem
)
from ...application.interfaces.loan_repository_interface import LoanRepositoryInterface


# SQLAlchemy models
Base = declarative_base()

class LoanModel(Base):
    """SQLAlchemy model for loans table"""
    __tablename__ = 'loans'
    
    loan_id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), nullable=False)
    loan_type = Column(String(20), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    application_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    approval_date = Column(Date)
    disbursal_date = Column(Date)
    collateral_description = Column(Text)
    collateral_value = Column(Numeric(15, 2))
    purpose = Column(Text)
    
    # Loan terms
    interest_rate = Column(Numeric(6, 4), nullable=False)
    term_months = Column(Integer, nullable=False)
    repayment_frequency = Column(String(20), nullable=False)
    grace_period_days = Column(Integer, nullable=False)
    early_repayment_penalty = Column(Numeric(15, 2))
    late_payment_fee = Column(Numeric(15, 2))
    
    # Relationships
    payment_schedule = relationship("PaymentScheduleModel", back_populates="loan", cascade="all, delete-orphan")
    custom_fields = relationship("LoanCustomFieldModel", back_populates="loan", cascade="all, delete-orphan")


class PaymentScheduleModel(Base):
    """SQLAlchemy model for payment schedule table"""
    __tablename__ = 'loan_payment_schedule'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(String(50), ForeignKey('loans.loan_id'), nullable=False)
    due_date = Column(Date, nullable=False)
    payment_amount = Column(Numeric(15, 2), nullable=False)
    principal_amount = Column(Numeric(15, 2), nullable=False)
    interest_amount = Column(Numeric(15, 2), nullable=False)
    remaining_balance = Column(Numeric(15, 2), nullable=False)
    is_paid = Column(Boolean, default=False)
    payment_date = Column(Date)
    payment_amount_received = Column(Numeric(15, 2))
    late_fee_applied = Column(Numeric(15, 2))
    
    # Relationship
    loan = relationship("LoanModel", back_populates="payment_schedule")


class LoanCustomFieldModel(Base):
    """SQLAlchemy model for loan custom fields table"""
    __tablename__ = 'loan_custom_fields'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    loan_id = Column(String(50), ForeignKey('loans.loan_id'), nullable=False)
    field_name = Column(String(100), nullable=False)
    field_value = Column(Text)
    
    # Relationship
    loan = relationship("LoanModel", back_populates="custom_fields")


class SqlLoanRepository(LoanRepositoryInterface):
    """SQL implementation of the loan repository interface"""
    
    def __init__(self, connection_string: str):
        """
        Initialize the SQL loan repository.
        
        Args:
            connection_string: Database connection string
        """
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
    
    def create(self, loan: Loan) -> Loan:
        """
        Create a new loan record.
        
        Args:
            loan: The loan entity to store
            
        Returns:
            The stored loan entity with any system-generated values
        """
        session = self.Session()
        
        try:
            # Create loan model
            loan_model = LoanModel(
                loan_id=loan.loan_id or str(uuid.uuid4()),
                customer_id=loan.customer_id,
                loan_type=loan.loan_type.value,
                amount=loan.amount,
                application_date=loan.application_date,
                status=loan.status.value,
                approval_date=loan.approval_date,
                disbursal_date=loan.disbursal_date,
                collateral_description=loan.collateral_description,
                collateral_value=loan.collateral_value,
                purpose=loan.purpose,
                interest_rate=loan.terms.interest_rate,
                term_months=loan.terms.term_months,
                repayment_frequency=loan.terms.repayment_frequency.value,
                grace_period_days=loan.terms.grace_period_days,
                early_repayment_penalty=loan.terms.early_repayment_penalty,
                late_payment_fee=loan.terms.late_payment_fee
            )
            
            # Add payment schedule items
            for item in loan.payment_schedule:
                schedule_model = PaymentScheduleModel(
                    due_date=item.due_date,
                    payment_amount=item.payment_amount,
                    principal_amount=item.principal_amount,
                    interest_amount=item.interest_amount,
                    remaining_balance=item.remaining_balance,
                    is_paid=item.is_paid,
                    payment_date=item.payment_date,
                    payment_amount_received=item.payment_amount_received,
                    late_fee_applied=item.late_fee_applied
                )
                loan_model.payment_schedule.append(schedule_model)
            
            # Add custom fields
            for key, value in loan.custom_fields.items():
                field_model = LoanCustomFieldModel(
                    field_name=key,
                    field_value=str(value) if value is not None else None
                )
                loan_model.custom_fields.append(field_model)
            
            # Add to database
            session.add(loan_model)
            session.commit()
            
            # Update loan_id if it was generated
            if not loan.loan_id:
                loan.loan_id = loan_model.loan_id
            
            return loan
        
        except Exception as e:
            session.rollback()
            raise e
        
        finally:
            session.close()
    
    def get_by_id(self, loan_id: str) -> Optional[Loan]:
        """
        Get a loan by its ID.
        
        Args:
            loan_id: The loan ID
            
        Returns:
            The loan entity if found, None otherwise
        """
        session = self.Session()
        
        try:
            loan_model = session.query(LoanModel).filter(LoanModel.loan_id == loan_id).first()
            
            if not loan_model:
                return None
            
            return self._map_to_entity(loan_model)
        
        finally:
            session.close()
    
    def update(self, loan: Loan) -> Loan:
        """
        Update an existing loan record.
        
        Args:
            loan: The loan entity to update
            
        Returns:
            The updated loan entity
        """
        session = self.Session()
        
        try:
            # Get existing loan
            loan_model = session.query(LoanModel).filter(LoanModel.loan_id == loan.loan_id).first()
            
            if not loan_model:
                raise ValueError(f"Loan with ID {loan.loan_id} not found")
            
            # Update loan fields
            loan_model.customer_id = loan.customer_id
            loan_model.loan_type = loan.loan_type.value
            loan_model.amount = loan.amount
            loan_model.application_date = loan.application_date
            loan_model.status = loan.status.value
            loan_model.approval_date = loan.approval_date
            loan_model.disbursal_date = loan.disbursal_date
            loan_model.collateral_description = loan.collateral_description
            loan_model.collateral_value = loan.collateral_value
            loan_model.purpose = loan.purpose
            loan_model.interest_rate = loan.terms.interest_rate
            loan_model.term_months = loan.terms.term_months
            loan_model.repayment_frequency = loan.terms.repayment_frequency.value
            loan_model.grace_period_days = loan.terms.grace_period_days
            loan_model.early_repayment_penalty = loan.terms.early_repayment_penalty
            loan_model.late_payment_fee = loan.terms.late_payment_fee
            
            # Clear existing payment schedule and custom fields
            session.query(PaymentScheduleModel).filter(PaymentScheduleModel.loan_id == loan.loan_id).delete()
            session.query(LoanCustomFieldModel).filter(LoanCustomFieldModel.loan_id == loan.loan_id).delete()
            
            # Add payment schedule items
            for item in loan.payment_schedule:
                schedule_model = PaymentScheduleModel(
                    loan_id=loan.loan_id,
                    due_date=item.due_date,
                    payment_amount=item.payment_amount,
                    principal_amount=item.principal_amount,
                    interest_amount=item.interest_amount,
                    remaining_balance=item.remaining_balance,
                    is_paid=item.is_paid,
                    payment_date=item.payment_date,
                    payment_amount_received=item.payment_amount_received,
                    late_fee_applied=item.late_fee_applied
                )
                session.add(schedule_model)
            
            # Add custom fields
            for key, value in loan.custom_fields.items():
                field_model = LoanCustomFieldModel(
                    loan_id=loan.loan_id,
                    field_name=key,
                    field_value=str(value) if value is not None else None
                )
                session.add(field_model)
            
            session.commit()
            return loan
        
        except Exception as e:
            session.rollback()
            raise e
        
        finally:
            session.close()
    
    def get_by_customer_id(self, customer_id: str) -> List[Loan]:
        """
        Get all loans for a customer.
        
        Args:
            customer_id: The customer ID
            
        Returns:
            List of loan entities for the customer
        """
        session = self.Session()
        
        try:
            loan_models = session.query(LoanModel).filter(LoanModel.customer_id == customer_id).all()
            return [self._map_to_entity(loan_model) for loan_model in loan_models]
        
        finally:
            session.close()
    
    def get_by_status(self, status: LoanStatus) -> List[Loan]:
        """
        Get loans by status.
        
        Args:
            status: The loan status
            
        Returns:
            List of loan entities with the specified status
        """
        session = self.Session()
        
        try:
            loan_models = session.query(LoanModel).filter(LoanModel.status == status.value).all()
            return [self._map_to_entity(loan_model) for loan_model in loan_models]
        
        finally:
            session.close()
    
    def search(self, 
              customer_id: Optional[str] = None,
              loan_type: Optional[LoanType] = None,
              min_amount: Optional[Decimal] = None,
              max_amount: Optional[Decimal] = None,
              status: Optional[LoanStatus] = None,
              application_date_from: Optional[date] = None,
              application_date_to: Optional[date] = None) -> List[Loan]:
        """
        Search loans based on criteria.
        
        Args:
            customer_id: Optional customer ID filter
            loan_type: Optional loan type filter
            min_amount: Optional minimum amount filter
            max_amount: Optional maximum amount filter
            status: Optional status filter
            application_date_from: Optional application date from filter
            application_date_to: Optional application date to filter
            
        Returns:
            List of loan entities matching the criteria
        """
        session = self.Session()
        
        try:
            query = session.query(LoanModel)
            
            if customer_id:
                query = query.filter(LoanModel.customer_id == customer_id)
            
            if loan_type:
                query = query.filter(LoanModel.loan_type == loan_type.value)
            
            if min_amount:
                query = query.filter(LoanModel.amount >= min_amount)
            
            if max_amount:
                query = query.filter(LoanModel.amount <= max_amount)
            
            if status:
                query = query.filter(LoanModel.status == status.value)
            
            if application_date_from:
                query = query.filter(LoanModel.application_date >= application_date_from)
            
            if application_date_to:
                query = query.filter(LoanModel.application_date <= application_date_to)
            
            loan_models = query.all()
            return [self._map_to_entity(loan_model) for loan_model in loan_models]
        
        finally:
            session.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get loan statistics.
        
        Returns:
            Dictionary containing statistics about loans
        """
        session = self.Session()
        
        try:
            # Total loan count
            total_count = session.query(func.count(LoanModel.loan_id)).scalar()
            
            # Total amount disbursed
            total_active_amount = session.query(func.sum(LoanModel.amount)) \
                .filter(LoanModel.status == LoanStatus.ACTIVE.value) \
                .scalar() or Decimal('0')
            
            # Count by status
            status_counts = {}
            for status in LoanStatus:
                count = session.query(func.count(LoanModel.loan_id)) \
                    .filter(LoanModel.status == status.value) \
                    .scalar()
                status_counts[status.value] = count
            
            # Count by loan type
            type_counts = {}
            for loan_type in LoanType:
                count = session.query(func.count(LoanModel.loan_id)) \
                    .filter(LoanModel.loan_type == loan_type.value) \
                    .scalar()
                type_counts[loan_type.value] = count
            
            # Get overdue count
            today = date.today()
            overdue_count = session.query(func.count(LoanModel.loan_id)) \
                .join(PaymentScheduleModel) \
                .filter(
                    LoanModel.status == LoanStatus.ACTIVE.value,
                    PaymentScheduleModel.is_paid == False,
                    PaymentScheduleModel.due_date < today
                ) \
                .scalar()
            
            return {
                'total_count': total_count,
                'total_active_amount': total_active_amount,
                'status_counts': status_counts,
                'type_counts': type_counts,
                'overdue_count': overdue_count
            }
        
        finally:
            session.close()
    
    def get_overdue_loans(self) -> List[Loan]:
        """
        Get overdue loans.
        
        Returns:
            List of loan entities that are overdue
        """
        session = self.Session()
        
        try:
            today = date.today()
            
            # Find loans with overdue payments
            loan_ids = session.query(LoanModel.loan_id) \
                .join(PaymentScheduleModel) \
                .filter(
                    PaymentScheduleModel.is_paid == False,
                    PaymentScheduleModel.due_date < today
                ) \
                .distinct() \
                .all()
            
            # Get the full loan entities
            loan_entities = []
            for (loan_id,) in loan_ids:
                loan_model = session.query(LoanModel).filter(LoanModel.loan_id == loan_id).first()
                if loan_model:
                    loan_entities.append(self._map_to_entity(loan_model))
            
            return loan_entities
        
        finally:
            session.close()
    
    def _map_to_entity(self, loan_model: LoanModel) -> Loan:
        """
        Map a database model to a domain entity.
        
        Args:
            loan_model: The SQLAlchemy model
            
        Returns:
            The corresponding domain entity
        """
        # Map loan terms
        terms = LoanTerms(
            interest_rate=loan_model.interest_rate,
            term_months=loan_model.term_months,
            repayment_frequency=RepaymentFrequency(loan_model.repayment_frequency),
            grace_period_days=loan_model.grace_period_days,
            early_repayment_penalty=loan_model.early_repayment_penalty,
            late_payment_fee=loan_model.late_payment_fee
        )
        
        # Map payment schedule
        payment_schedule = []
        for item_model in loan_model.payment_schedule:
            item = PaymentScheduleItem(
                due_date=item_model.due_date,
                payment_amount=item_model.payment_amount,
                principal_amount=item_model.principal_amount,
                interest_amount=item_model.interest_amount,
                remaining_balance=item_model.remaining_balance,
                is_paid=item_model.is_paid,
                payment_date=item_model.payment_date,
                payment_amount_received=item_model.payment_amount_received,
                late_fee_applied=item_model.late_fee_applied
            )
            payment_schedule.append(item)
        
        # Map custom fields
        custom_fields = {}
        for field_model in loan_model.custom_fields:
            custom_fields[field_model.field_name] = field_model.field_value
        
        # Create loan entity
        loan = Loan(
            loan_id=loan_model.loan_id,
            customer_id=loan_model.customer_id,
            loan_type=LoanType(loan_model.loan_type),
            amount=loan_model.amount,
            terms=terms,
            application_date=loan_model.application_date,
            status=LoanStatus(loan_model.status),
            approval_date=loan_model.approval_date,
            disbursal_date=loan_model.disbursal_date,
            collateral_description=loan_model.collateral_description,
            collateral_value=loan_model.collateral_value,
            payment_schedule=payment_schedule,
            purpose=loan_model.purpose,
            custom_fields=custom_fields
        )
        
        return loan
