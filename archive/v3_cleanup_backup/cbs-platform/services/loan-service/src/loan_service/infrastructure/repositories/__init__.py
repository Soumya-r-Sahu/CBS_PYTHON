"""
Loan Service Infrastructure - Repository Implementations
Production-ready repository implementations for loan management
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import SQLAlchemyError

from ...domain.entities import (
    Loan, LoanAmount, LoanTerm, LoanStatus, LoanType,
    EMISchedule, LoanDocument, Collateral
)
from ..database import (
    LoanModel, EMIScheduleModel, LoanDocumentModel,
    CollateralModel, LoanPaymentModel, LoanApplicationModel
)


class LoanRepositoryInterface(ABC):
    """Loan repository interface"""
    
    @abstractmethod
    def save(self, loan: Loan) -> Loan:
        """Save loan"""
        pass
    
    @abstractmethod
    def find_by_id(self, loan_id: str) -> Optional[Loan]:
        """Find loan by ID"""
        pass
    
    @abstractmethod
    def find_by_number(self, loan_number: str) -> Optional[Loan]:
        """Find loan by loan number"""
        pass
    
    @abstractmethod
    def find_by_customer(self, customer_id: str, limit: int = 100) -> List[Loan]:
        """Find loans by customer ID"""
        pass
    
    @abstractmethod
    def find_by_status(self, status: LoanStatus, limit: int = 100) -> List[Loan]:
        """Find loans by status"""
        pass
    
    @abstractmethod
    def find_overdue_loans(self, days_overdue: int = 1) -> List[Loan]:
        """Find overdue loans"""
        pass
    
    @abstractmethod
    def get_loan_summary(self, customer_id: str) -> Dict[str, Any]:
        """Get loan summary for customer"""
        pass


class SQLLoanRepository(LoanRepositoryInterface):
    """SQL implementation of loan repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, loan: Loan) -> Loan:
        """Save loan to database"""
        try:
            # Check if loan exists
            loan_model = self.session.query(LoanModel).filter_by(
                loan_id=loan.loan_id
            ).first()
            
            if loan_model:
                # Update existing loan
                self._update_loan_model(loan_model, loan)
            else:
                # Create new loan
                loan_model = self._create_loan_model(loan)
                self.session.add(loan_model)
            
            self.session.commit()
            return loan
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Database error saving loan: {str(e)}")
    
    def find_by_id(self, loan_id: str) -> Optional[Loan]:
        """Find loan by ID"""
        try:
            loan_model = self.session.query(LoanModel).filter_by(
                loan_id=loan_id
            ).first()
            
            return self._to_domain_entity(loan_model) if loan_model else None
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error finding loan: {str(e)}")
    
    def find_by_number(self, loan_number: str) -> Optional[Loan]:
        """Find loan by loan number"""
        try:
            loan_model = self.session.query(LoanModel).filter_by(
                loan_number=loan_number
            ).first()
            
            return self._to_domain_entity(loan_model) if loan_model else None
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error finding loan: {str(e)}")
    
    def find_by_customer(self, customer_id: str, limit: int = 100) -> List[Loan]:
        """Find loans by customer ID"""
        try:
            loan_models = self.session.query(LoanModel).filter_by(
                customer_id=customer_id
            ).order_by(desc(LoanModel.application_date)).limit(limit).all()
            
            return [self._to_domain_entity(model) for model in loan_models]
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error finding loans: {str(e)}")
    
    def find_by_status(self, status: LoanStatus, limit: int = 100) -> List[Loan]:
        """Find loans by status"""
        try:
            loan_models = self.session.query(LoanModel).filter_by(
                status=status.value
            ).order_by(desc(LoanModel.application_date)).limit(limit).all()
            
            return [self._to_domain_entity(model) for model in loan_models]
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error finding loans: {str(e)}")
    
    def find_overdue_loans(self, days_overdue: int = 1) -> List[Loan]:
        """Find overdue loans"""
        try:
            cutoff_date = datetime.utcnow().date() - timedelta(days=days_overdue)
            
            loan_models = self.session.query(LoanModel).filter(
                and_(
                    LoanModel.status == 'active',
                    LoanModel.next_due_date < cutoff_date,
                    LoanModel.outstanding_amount > 0
                )
            ).order_by(desc(LoanModel.days_past_due)).all()
            
            return [self._to_domain_entity(model) for model in loan_models]
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error finding overdue loans: {str(e)}")
    
    def get_loan_summary(self, customer_id: str) -> Dict[str, Any]:
        """Get loan summary for customer"""
        try:
            # Query for summary statistics
            result = self.session.query(
                LoanModel.status,
                LoanModel.loan_type,
                func.count(LoanModel.loan_id).label('count'),
                func.sum(LoanModel.loan_amount).label('total_loan_amount'),
                func.sum(LoanModel.outstanding_amount).label('total_outstanding'),
                func.avg(LoanModel.interest_rate).label('avg_interest_rate')
            ).filter(
                LoanModel.customer_id == customer_id
            ).group_by(
                LoanModel.status, LoanModel.loan_type
            ).all()
            
            # Organize results
            summary = {
                'customer_id': customer_id,
                'total_loans': sum(r.count for r in result),
                'total_loan_amount': sum(r.total_loan_amount or 0 for r in result),
                'total_outstanding': sum(r.total_outstanding or 0 for r in result),
                'by_status': {},
                'by_type': {}
            }
            
            for row in result:
                # By status
                if row.status not in summary['by_status']:
                    summary['by_status'][row.status] = {
                        'count': 0, 'loan_amount': 0, 'outstanding': 0
                    }
                summary['by_status'][row.status]['count'] += row.count
                summary['by_status'][row.status]['loan_amount'] += float(row.total_loan_amount or 0)
                summary['by_status'][row.status]['outstanding'] += float(row.total_outstanding or 0)
                
                # By type
                if row.loan_type not in summary['by_type']:
                    summary['by_type'][row.loan_type] = {
                        'count': 0, 'loan_amount': 0, 'outstanding': 0
                    }
                summary['by_type'][row.loan_type]['count'] += row.count
                summary['by_type'][row.loan_type]['loan_amount'] += float(row.total_loan_amount or 0)
                summary['by_type'][row.loan_type]['outstanding'] += float(row.total_outstanding or 0)
            
            return summary
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error getting loan summary: {str(e)}")
    
    def find_loans_due_for_payment(self, due_date: datetime) -> List[Loan]:
        """Find loans due for payment on specific date"""
        try:
            loan_models = self.session.query(LoanModel).filter(
                and_(
                    LoanModel.status == 'active',
                    LoanModel.next_due_date <= due_date.date(),
                    LoanModel.outstanding_amount > 0
                )
            ).all()
            
            return [self._to_domain_entity(model) for model in loan_models]
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error finding due loans: {str(e)}")
    
    def get_portfolio_statistics(self) -> Dict[str, Any]:
        """Get overall loan portfolio statistics"""
        try:
            # Active loans statistics
            active_stats = self.session.query(
                func.count(LoanModel.loan_id).label('count'),
                func.sum(LoanModel.loan_amount).label('total_loan_amount'),
                func.sum(LoanModel.outstanding_amount).label('total_outstanding'),
                func.avg(LoanModel.interest_rate).label('avg_rate')
            ).filter(LoanModel.status == 'active').first()
            
            # Overdue statistics
            overdue_stats = self.session.query(
                func.count(LoanModel.loan_id).label('count'),
                func.sum(LoanModel.overdue_amount).label('total_overdue')
            ).filter(
                and_(
                    LoanModel.status == 'active',
                    LoanModel.days_past_due > 0
                )
            ).first()
            
            # NPA (Non-Performing Assets) - loans overdue by 90+ days
            npa_stats = self.session.query(
                func.count(LoanModel.loan_id).label('count'),
                func.sum(LoanModel.outstanding_amount).label('total_npa')
            ).filter(
                and_(
                    LoanModel.status == 'active',
                    LoanModel.days_past_due >= 90
                )
            ).first()
            
            return {
                'active_loans': {
                    'count': active_stats.count or 0,
                    'total_amount': float(active_stats.total_loan_amount or 0),
                    'outstanding_amount': float(active_stats.total_outstanding or 0),
                    'average_rate': float(active_stats.avg_rate or 0)
                },
                'overdue_loans': {
                    'count': overdue_stats.count or 0,
                    'total_overdue': float(overdue_stats.total_overdue or 0)
                },
                'npa_loans': {
                    'count': npa_stats.count or 0,
                    'total_npa': float(npa_stats.total_npa or 0)
                }
            }
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error getting portfolio statistics: {str(e)}")
    
    def _create_loan_model(self, loan: Loan) -> LoanModel:
        """Create loan model from domain entity"""
        model = LoanModel(
            loan_id=loan.loan_id,
            loan_number=loan.loan_number,
            customer_id=loan.customer_id,
            primary_account_id=loan.primary_account_id,
            loan_type=loan.loan_type.value,
            loan_purpose=loan.loan_purpose,
            loan_amount=loan.amount.principal,
            approved_amount=loan.approved_amount,
            disbursed_amount=loan.disbursed_amount,
            outstanding_amount=loan.outstanding_amount,
            interest_rate=loan.terms.interest_rate,
            tenure_months=loan.terms.tenure_months,
            emi_amount=loan.terms.emi_amount,
            status=loan.status.value,
            risk_category=loan.risk_category.value if loan.risk_category else None,
            credit_score=loan.credit_score,
            debt_to_income_ratio=loan.debt_to_income_ratio,
            application_date=loan.application_date,
            approval_date=loan.approval_date,
            disbursement_date=loan.disbursement_date,
            maturity_date=loan.maturity_date,
            next_due_date=loan.next_due_date,
            last_payment_date=loan.last_payment_date,
            total_payments_made=loan.total_payments_made,
            total_amount_paid=loan.total_amount_paid,
            overdue_amount=loan.overdue_amount,
            days_past_due=loan.days_past_due,
            created_by=loan.created_by,
            approved_by=loan.approved_by,
            rejected_by=loan.rejected_by,
            rejection_reason=loan.rejection_reason,
            notes=loan.notes,
            metadata=loan.metadata,
            version=loan.version
        )
        
        return model
    
    def _update_loan_model(self, model: LoanModel, loan: Loan):
        """Update loan model from domain entity"""
        model.status = loan.status.value
        model.approved_amount = loan.approved_amount
        model.disbursed_amount = loan.disbursed_amount
        model.outstanding_amount = loan.outstanding_amount
        model.approval_date = loan.approval_date
        model.disbursement_date = loan.disbursement_date
        model.maturity_date = loan.maturity_date
        model.next_due_date = loan.next_due_date
        model.last_payment_date = loan.last_payment_date
        model.total_payments_made = loan.total_payments_made
        model.total_amount_paid = loan.total_amount_paid
        model.overdue_amount = loan.overdue_amount
        model.days_past_due = loan.days_past_due
        model.approved_by = loan.approved_by
        model.rejected_by = loan.rejected_by
        model.rejection_reason = loan.rejection_reason
        model.notes = loan.notes
        model.metadata = loan.metadata
        model.version = loan.version
    
    def _to_domain_entity(self, model: LoanModel) -> Loan:
        """Convert loan model to domain entity"""
        # Import domain entities
        from ...domain.entities import (
            LoanAmount, LoanTerm, LoanStatus, LoanType, RiskCategory
        )
        
        # Create loan amount
        amount = LoanAmount(
            principal=model.loan_amount,
            currency="USD"  # Default currency
        )
        
        # Create loan terms
        terms = LoanTerm(
            interest_rate=model.interest_rate,
            tenure_months=model.tenure_months,
            emi_amount=model.emi_amount or Decimal('0')
        )
        
        # Create loan entity
        loan = Loan(
            loan_id=str(model.loan_id),
            loan_number=model.loan_number,
            customer_id=str(model.customer_id),
            primary_account_id=str(model.primary_account_id),
            loan_type=LoanType(model.loan_type),
            loan_purpose=model.loan_purpose,
            amount=amount,
            terms=terms,
            status=LoanStatus(model.status),
            approved_amount=model.approved_amount,
            disbursed_amount=model.disbursed_amount,
            outstanding_amount=model.outstanding_amount,
            credit_score=model.credit_score,
            debt_to_income_ratio=model.debt_to_income_ratio,
            application_date=model.application_date,
            approval_date=model.approval_date,
            disbursement_date=model.disbursement_date,
            maturity_date=model.maturity_date,
            next_due_date=model.next_due_date,
            last_payment_date=model.last_payment_date,
            total_payments_made=model.total_payments_made,
            total_amount_paid=model.total_amount_paid,
            overdue_amount=model.overdue_amount,
            days_past_due=model.days_past_due,
            created_by=model.created_by,
            approved_by=model.approved_by,
            rejected_by=model.rejected_by,
            rejection_reason=model.rejection_reason,
            notes=model.notes,
            metadata=model.metadata or {},
            version=model.version
        )
        
        # Set risk category if available
        if model.risk_category:
            loan.risk_category = RiskCategory(model.risk_category)
        
        return loan


class EMIScheduleRepository:
    """Repository for EMI schedules"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save_schedule(self, loan_id: str, schedule: List[EMISchedule]) -> bool:
        """Save EMI schedule for a loan"""
        try:
            # Delete existing schedule
            self.session.query(EMIScheduleModel).filter_by(loan_id=loan_id).delete()
            
            # Create new schedule
            for emi in schedule:
                emi_model = EMIScheduleModel(
                    loan_id=loan_id,
                    installment_number=emi.installment_number,
                    emi_amount=emi.emi_amount,
                    principal_amount=emi.principal_amount,
                    interest_amount=emi.interest_amount,
                    due_date=emi.due_date,
                    outstanding_principal=emi.outstanding_principal,
                    outstanding_interest=emi.outstanding_interest
                )
                self.session.add(emi_model)
            
            self.session.commit()
            return True
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Database error saving EMI schedule: {str(e)}")
    
    def get_schedule(self, loan_id: str) -> List[EMISchedule]:
        """Get EMI schedule for a loan"""
        try:
            emi_models = self.session.query(EMIScheduleModel).filter_by(
                loan_id=loan_id
            ).order_by(EMIScheduleModel.installment_number).all()
            
            schedule = []
            for model in emi_models:
                emi = EMISchedule(
                    installment_number=model.installment_number,
                    emi_amount=model.emi_amount,
                    principal_amount=model.principal_amount,
                    interest_amount=model.interest_amount,
                    due_date=model.due_date,
                    outstanding_principal=model.outstanding_principal,
                    outstanding_interest=model.outstanding_interest,
                    status=model.status,
                    paid_amount=model.paid_amount,
                    payment_date=model.payment_date
                )
                schedule.append(emi)
            
            return schedule
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error getting EMI schedule: {str(e)}")
    
    def get_pending_emis(self, loan_id: str) -> List[EMISchedule]:
        """Get pending EMIs for a loan"""
        try:
            emi_models = self.session.query(EMIScheduleModel).filter(
                and_(
                    EMIScheduleModel.loan_id == loan_id,
                    EMIScheduleModel.status == 'pending'
                )
            ).order_by(EMIScheduleModel.installment_number).all()
            
            return [self._emi_model_to_entity(model) for model in emi_models]
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error getting pending EMIs: {str(e)}")
    
    def mark_emi_paid(self, loan_id: str, installment_number: int, paid_amount: Decimal, payment_date: datetime) -> bool:
        """Mark EMI as paid"""
        try:
            emi_model = self.session.query(EMIScheduleModel).filter(
                and_(
                    EMIScheduleModel.loan_id == loan_id,
                    EMIScheduleModel.installment_number == installment_number
                )
            ).first()
            
            if emi_model:
                emi_model.status = 'paid'
                emi_model.paid_amount = paid_amount
                emi_model.payment_date = payment_date
                self.session.commit()
                return True
            
            return False
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Database error marking EMI as paid: {str(e)}")
    
    def _emi_model_to_entity(self, model: EMIScheduleModel) -> EMISchedule:
        """Convert EMI model to domain entity"""
        return EMISchedule(
            installment_number=model.installment_number,
            emi_amount=model.emi_amount,
            principal_amount=model.principal_amount,
            interest_amount=model.interest_amount,
            due_date=model.due_date,
            outstanding_principal=model.outstanding_principal,
            outstanding_interest=model.outstanding_interest,
            status=model.status,
            paid_amount=model.paid_amount,
            payment_date=model.payment_date
        )


class LoanDocumentRepository:
    """Repository for loan documents"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save_document(self, loan_id: str, document: LoanDocument) -> LoanDocument:
        """Save loan document"""
        try:
            document_model = LoanDocumentModel(
                document_id=document.document_id,
                loan_id=loan_id,
                document_type=document.document_type.value,
                document_name=document.document_name,
                file_path=document.file_path,
                file_size=document.file_size,
                file_type=document.file_type,
                checksum=document.checksum,
                verification_status=document.verification_status.value,
                is_mandatory=document.is_mandatory,
                uploaded_by=document.uploaded_by
            )
            
            self.session.add(document_model)
            self.session.commit()
            return document
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Database error saving document: {str(e)}")
    
    def get_documents(self, loan_id: str) -> List[LoanDocument]:
        """Get all documents for a loan"""
        try:
            document_models = self.session.query(LoanDocumentModel).filter_by(
                loan_id=loan_id
            ).all()
            
            return [self._document_model_to_entity(model) for model in document_models]
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error getting documents: {str(e)}")
    
    def _document_model_to_entity(self, model: LoanDocumentModel) -> LoanDocument:
        """Convert document model to domain entity"""
        from ...domain.entities import DocumentType, VerificationStatus
        
        return LoanDocument(
            document_id=str(model.document_id),
            document_type=DocumentType(model.document_type),
            document_name=model.document_name,
            file_path=model.file_path,
            file_size=model.file_size,
            file_type=model.file_type,
            checksum=model.checksum,
            verification_status=VerificationStatus(model.verification_status),
            is_mandatory=model.is_mandatory,
            uploaded_by=model.uploaded_by,
            uploaded_at=model.uploaded_at
        )


# Export all repository implementations
__all__ = [
    'LoanRepositoryInterface',
    'SQLLoanRepository',
    'EMIScheduleRepository',
    'LoanDocumentRepository'
]
