"""
Payment Service Infrastructure - Repository Implementations
Production-ready repository implementations for payment management
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import SQLAlchemyError

from ...domain.entities import (
    Payment, PaymentAmount, PaymentParty, UPIDetails, 
    BillPaymentDetails, FraudCheck, PaymentType, PaymentStatus
)
from ..database import (
    PaymentModel, PaymentLimitModel, EMIScheduleModel,
    FraudDetectionModel, PaymentBatchModel, PaymentGatewayModel
)


class PaymentRepositoryInterface(ABC):
    """Payment repository interface"""
    
    @abstractmethod
    def save(self, payment: Payment) -> Payment:
        """Save payment"""
        pass
    
    @abstractmethod
    def find_by_id(self, payment_id: str) -> Optional[Payment]:
        """Find payment by ID"""
        pass
    
    @abstractmethod
    def find_by_reference(self, reference_number: str) -> Optional[Payment]:
        """Find payment by reference number"""
        pass
    
    @abstractmethod
    def find_by_account(self, account_number: str, limit: int = 100) -> List[Payment]:
        """Find payments by account number"""
        pass
    
    @abstractmethod
    def find_by_status(self, status: PaymentStatus, limit: int = 100) -> List[Payment]:
        """Find payments by status"""
        pass
    
    @abstractmethod
    def find_pending_payments(self, older_than_minutes: int = 30) -> List[Payment]:
        """Find payments pending for specified time"""
        pass
    
    @abstractmethod
    def get_payment_summary(self, account_number: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get payment summary for account"""
        pass


class SQLPaymentRepository(PaymentRepositoryInterface):
    """SQL implementation of payment repository"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def save(self, payment: Payment) -> Payment:
        """Save payment to database"""
        try:
            # Check if payment exists
            payment_model = self.session.query(PaymentModel).filter_by(
                payment_id=payment.payment_id
            ).first()
            
            if payment_model:
                # Update existing payment
                self._update_payment_model(payment_model, payment)
            else:
                # Create new payment
                payment_model = self._create_payment_model(payment)
                self.session.add(payment_model)
            
            self.session.commit()
            return payment
            
        except SQLAlchemyError as e:
            self.session.rollback()
            raise Exception(f"Database error saving payment: {str(e)}")
    
    def find_by_id(self, payment_id: str) -> Optional[Payment]:
        """Find payment by ID"""
        try:
            payment_model = self.session.query(PaymentModel).filter_by(
                payment_id=payment_id
            ).first()
            
            return self._to_domain_entity(payment_model) if payment_model else None
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error finding payment: {str(e)}")
    
    def find_by_reference(self, reference_number: str) -> Optional[Payment]:
        """Find payment by reference number"""
        try:
            payment_model = self.session.query(PaymentModel).filter_by(
                reference_number=reference_number
            ).first()
            
            return self._to_domain_entity(payment_model) if payment_model else None
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error finding payment: {str(e)}")
    
    def find_by_account(self, account_number: str, limit: int = 100) -> List[Payment]:
        """Find payments by account number"""
        try:
            payment_models = self.session.query(PaymentModel).filter(
                or_(
                    PaymentModel.sender_account_number == account_number,
                    PaymentModel.receiver_account_number == account_number
                )
            ).order_by(desc(PaymentModel.initiated_at)).limit(limit).all()
            
            return [self._to_domain_entity(model) for model in payment_models]
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error finding payments: {str(e)}")
    
    def find_by_status(self, status: PaymentStatus, limit: int = 100) -> List[Payment]:
        """Find payments by status"""
        try:
            payment_models = self.session.query(PaymentModel).filter_by(
                status=status.value
            ).order_by(desc(PaymentModel.initiated_at)).limit(limit).all()
            
            return [self._to_domain_entity(model) for model in payment_models]
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error finding payments: {str(e)}")
    
    def find_pending_payments(self, older_than_minutes: int = 30) -> List[Payment]:
        """Find payments pending for specified time"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=older_than_minutes)
            
            payment_models = self.session.query(PaymentModel).filter(
                and_(
                    PaymentModel.status.in_(['pending', 'processing']),
                    PaymentModel.initiated_at < cutoff_time
                )
            ).all()
            
            return [self._to_domain_entity(model) for model in payment_models]
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error finding pending payments: {str(e)}")
    
    def get_payment_summary(self, account_number: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get payment summary for account"""
        try:
            # Query for summary statistics
            result = self.session.query(
                PaymentModel.status,
                PaymentModel.payment_type,
                func.count(PaymentModel.payment_id).label('count'),
                func.sum(PaymentModel.amount).label('total_amount'),
                func.avg(PaymentModel.amount).label('avg_amount')
            ).filter(
                and_(
                    or_(
                        PaymentModel.sender_account_number == account_number,
                        PaymentModel.receiver_account_number == account_number
                    ),
                    PaymentModel.initiated_at >= start_date,
                    PaymentModel.initiated_at <= end_date
                )
            ).group_by(
                PaymentModel.status, PaymentModel.payment_type
            ).all()
            
            # Organize results
            summary = {
                'account_number': account_number,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'total_transactions': sum(r.count for r in result),
                'total_amount': sum(r.total_amount or 0 for r in result),
                'by_status': {},
                'by_type': {}
            }
            
            for row in result:
                # By status
                if row.status not in summary['by_status']:
                    summary['by_status'][row.status] = {'count': 0, 'amount': 0}
                summary['by_status'][row.status]['count'] += row.count
                summary['by_status'][row.status]['amount'] += float(row.total_amount or 0)
                
                # By type
                if row.payment_type not in summary['by_type']:
                    summary['by_type'][row.payment_type] = {'count': 0, 'amount': 0}
                summary['by_type'][row.payment_type]['count'] += row.count
                summary['by_type'][row.payment_type]['amount'] += float(row.total_amount or 0)
            
            return summary
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error getting payment summary: {str(e)}")
    
    def find_high_value_payments(self, amount_threshold: Decimal, limit: int = 50) -> List[Payment]:
        """Find high value payments requiring approval"""
        try:
            payment_models = self.session.query(PaymentModel).filter(
                and_(
                    PaymentModel.amount >= amount_threshold,
                    PaymentModel.status.in_(['initiated', 'pending'])
                )
            ).order_by(desc(PaymentModel.amount)).limit(limit).all()
            
            return [self._to_domain_entity(model) for model in payment_models]
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error finding high value payments: {str(e)}")
    
    def find_suspicious_payments(self, risk_threshold: int = 70) -> List[Payment]:
        """Find payments with high fraud risk"""
        try:
            payment_models = self.session.query(PaymentModel).filter(
                and_(
                    PaymentModel.fraud_risk_score >= risk_threshold,
                    PaymentModel.status.in_(['initiated', 'pending'])
                )
            ).order_by(desc(PaymentModel.fraud_risk_score)).all()
            
            return [self._to_domain_entity(model) for model in payment_models]
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error finding suspicious payments: {str(e)}")
    
    def get_daily_payment_volume(self, account_number: str, date: datetime) -> Dict[str, Any]:
        """Get daily payment volume for account"""
        try:
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            result = self.session.query(
                func.count(PaymentModel.payment_id).label('count'),
                func.sum(PaymentModel.amount).label('total_amount')
            ).filter(
                and_(
                    PaymentModel.sender_account_number == account_number,
                    PaymentModel.initiated_at >= start_of_day,
                    PaymentModel.initiated_at < end_of_day,
                    PaymentModel.status != 'cancelled'
                )
            ).first()
            
            return {
                'date': date.date().isoformat(),
                'transaction_count': result.count or 0,
                'total_amount': float(result.total_amount or 0)
            }
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error getting daily volume: {str(e)}")
    
    def _create_payment_model(self, payment: Payment) -> PaymentModel:
        """Create payment model from domain entity"""
        model = PaymentModel(
            payment_id=payment.payment_id,
            reference_number=payment.reference_number,
            payment_type=payment.payment_type.value,
            status=payment.status.value,
            channel=payment.channel.value,
            
            # Amount
            amount=payment.amount.amount,
            currency=payment.amount.currency,
            
            # Sender
            sender_account_number=payment.sender.account_number,
            sender_account_name=payment.sender.account_name,
            sender_bank_code=payment.sender.bank_code,
            sender_bank_name=payment.sender.bank_name,
            sender_branch_code=payment.sender.branch_code,
            sender_ifsc_code=payment.sender.ifsc_code,
            
            # Receiver
            receiver_account_number=payment.receiver.account_number,
            receiver_account_name=payment.receiver.account_name,
            receiver_bank_code=payment.receiver.bank_code,
            receiver_bank_name=payment.receiver.bank_name,
            receiver_branch_code=payment.receiver.branch_code,
            receiver_ifsc_code=payment.receiver.ifsc_code,
            
            # Timestamps
            initiated_at=payment.initiated_at,
            processed_at=payment.processed_at,
            completed_at=payment.completed_at,
            
            # System fields
            initiated_by=payment.initiated_by,
            processed_by=payment.processed_by,
            failure_reason=payment.failure_reason,
            description=payment.description,
            metadata=payment.metadata,
            version=payment.version
        )
        
        # UPI details
        if payment.upi_details:
            model.upi_vpa = payment.upi_details.vpa
            model.upi_merchant_id = payment.upi_details.merchant_id
            model.upi_qr_code = payment.upi_details.qr_code
            model.upi_purpose = payment.upi_details.purpose
        
        # Bill details
        if payment.bill_details:
            model.bill_biller_id = payment.bill_details.biller_id
            model.bill_biller_name = payment.bill_details.biller_name
            model.bill_number = payment.bill_details.bill_number
            model.bill_due_date = payment.bill_details.due_date
            model.bill_amount = payment.bill_details.bill_amount.amount if payment.bill_details.bill_amount else None
        
        # Fraud check
        if payment.fraud_check:
            model.fraud_risk_level = payment.fraud_check.risk_level.value
            model.fraud_risk_score = payment.fraud_check.risk_score
            model.fraud_flags = payment.fraud_check.flags
            model.fraud_checked_at = payment.fraud_check.checked_at
        
        return model
    
    def _update_payment_model(self, model: PaymentModel, payment: Payment):
        """Update payment model from domain entity"""
        model.status = payment.status.value
        model.processed_at = payment.processed_at
        model.completed_at = payment.completed_at
        model.processed_by = payment.processed_by
        model.failure_reason = payment.failure_reason
        model.metadata = payment.metadata
        model.version = payment.version
        
        # Update fraud check if present
        if payment.fraud_check:
            model.fraud_risk_level = payment.fraud_check.risk_level.value
            model.fraud_risk_score = payment.fraud_check.risk_score
            model.fraud_flags = payment.fraud_check.flags
            model.fraud_checked_at = payment.fraud_check.checked_at
    
    def _to_domain_entity(self, model: PaymentModel) -> Payment:
        """Convert payment model to domain entity"""
        # Create payment amount
        amount = PaymentAmount(
            amount=model.amount,
            currency=model.currency
        )
        
        # Create sender and receiver
        sender = PaymentParty(
            account_number=model.sender_account_number,
            account_name=model.sender_account_name,
            bank_code=model.sender_bank_code,
            bank_name=model.sender_bank_name,
            branch_code=model.sender_branch_code,
            ifsc_code=model.sender_ifsc_code
        )
        
        receiver = PaymentParty(
            account_number=model.receiver_account_number,
            account_name=model.receiver_account_name,
            bank_code=model.receiver_bank_code,
            bank_name=model.receiver_bank_name,
            branch_code=model.receiver_branch_code,
            ifsc_code=model.receiver_ifsc_code
        )
        
        # Create UPI details if present
        upi_details = None
        if model.upi_vpa:
            upi_details = UPIDetails(
                vpa=model.upi_vpa,
                merchant_id=model.upi_merchant_id,
                qr_code=model.upi_qr_code,
                purpose=model.upi_purpose or "PAYMENT"
            )
        
        # Create bill details if present
        bill_details = None
        if model.bill_biller_id:
            bill_amount = PaymentAmount(model.bill_amount, model.currency) if model.bill_amount else None
            bill_details = BillPaymentDetails(
                biller_id=model.bill_biller_id,
                biller_name=model.bill_biller_name,
                bill_number=model.bill_number,
                due_date=model.bill_due_date,
                bill_amount=bill_amount
            )
        
        # Create fraud check if present
        fraud_check = None
        if model.fraud_risk_level:
            from ...domain.entities import FraudRiskLevel
            fraud_check = FraudCheck(
                risk_level=FraudRiskLevel(model.fraud_risk_level),
                risk_score=model.fraud_risk_score,
                flags=model.fraud_flags or [],
                checked_at=model.fraud_checked_at or datetime.utcnow()
            )
        
        # Create payment entity
        payment = Payment(
            payment_id=str(model.payment_id),
            payment_type=PaymentType(model.payment_type),
            amount=amount,
            sender=sender,
            receiver=receiver,
            status=PaymentStatus(model.status),
            channel=model.channel,
            reference_number=model.reference_number,
            description=model.description or "",
            upi_details=upi_details,
            bill_details=bill_details,
            fraud_check=fraud_check,
            initiated_at=model.initiated_at,
            processed_at=model.processed_at,
            completed_at=model.completed_at,
            initiated_by=model.initiated_by,
            processed_by=model.processed_by,
            failure_reason=model.failure_reason,
            metadata=model.metadata or {},
            version=model.version
        )
        
        return payment


class PaymentLimitRepository:
    """Repository for payment limits and restrictions"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def check_daily_limit(self, account_number: str, amount: Decimal) -> Dict[str, Any]:
        """Check if payment exceeds daily limit"""
        try:
            today = datetime.utcnow().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            end_of_day = start_of_day + timedelta(days=1)
            
            # Get today's total
            total_today = self.session.query(
                func.sum(PaymentModel.amount)
            ).filter(
                and_(
                    PaymentModel.sender_account_number == account_number,
                    PaymentModel.initiated_at >= start_of_day,
                    PaymentModel.initiated_at < end_of_day,
                    PaymentModel.status.in_(['completed', 'processing', 'pending'])
                )
            ).scalar() or Decimal('0')
            
            daily_limit = Decimal('100000')  # $100,000 daily limit
            remaining = daily_limit - total_today
            
            return {
                'within_limit': (total_today + amount) <= daily_limit,
                'current_usage': float(total_today),
                'daily_limit': float(daily_limit),
                'remaining_limit': float(remaining),
                'requested_amount': float(amount)
            }
            
        except SQLAlchemyError as e:
            raise Exception(f"Database error checking daily limit: {str(e)}")


# Export all repository implementations
__all__ = [
    'PaymentRepositoryInterface',
    'SQLPaymentRepository',
    'PaymentLimitRepository'
]
