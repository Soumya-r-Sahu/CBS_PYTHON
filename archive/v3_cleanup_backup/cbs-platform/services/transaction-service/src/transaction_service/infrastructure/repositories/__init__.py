"""
Transaction Service Repository Implementations
SQLAlchemy-based repositories for transaction data access
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import UUID
import logging
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Import domain entities
from ...domain.entities import (
    Transaction, TransactionType, TransactionStatus, Money, TransactionLeg,
    TransactionBatch, TransactionRule, TransactionLimit
)

# Import database models
from ..database import (
    TransactionModel, TransactionLegModel, TransactionBatchModel,
    TransactionRuleModel, TransactionLimitModel, get_db_session
)

# Setup logging
logger = logging.getLogger(__name__)


class TransactionRepository:
    """
    SQLAlchemy-based repository for Transaction entities
    """
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session
    
    def _get_session(self) -> Session:
        """Get database session"""
        return self.session if self.session else get_db_session()
    
    def _to_domain_entity(self, model: TransactionModel) -> Transaction:
        """Convert database model to domain entity"""
        try:
            return Transaction(
                id=model.id,
                transaction_id=model.transaction_id,
                from_account_id=model.from_account_id,
                to_account_id=model.to_account_id,
                transaction_type=TransactionType(model.transaction_type),
                amount=Money(model.amount, model.currency),
                status=TransactionStatus(model.status),
                description=model.description,
                reference_number=model.reference_number,
                category=model.category,
                transaction_fee=Money(model.transaction_fee, model.currency),
                service_charge=Money(model.service_charge, model.currency),
                tax_amount=Money(model.tax_amount, model.currency),
                exchange_rate=model.exchange_rate,
                processing_method=model.processing_method,
                scheduled_at=model.scheduled_at,
                processed_at=model.processed_at,
                channel=model.channel,
                location=model.location,
                device_info=model.device_info or {},
                approval_required=model.approval_required,
                approved_by=model.approved_by,
                approved_at=model.approved_at,
                approval_notes=model.approval_notes,
                risk_score=model.risk_score,
                aml_check_status=model.aml_check_status,
                fraud_check_status=model.fraud_check_status,
                compliance_notes=model.compliance_notes,
                reconciliation_status=model.reconciliation_status,
                reconciled_at=model.reconciled_at,
                reconciled_by=model.reconciled_by,
                metadata=model.metadata or {},
                tags=model.tags or [],
                created_at=model.created_at,
                updated_at=model.updated_at,
                created_by=model.created_by,
                updated_by=model.updated_by,
                version=model.version
            )
        except Exception as e:
            logger.error(f"Error converting transaction model to entity: {e}")
            raise ValueError(f"Failed to convert transaction model: {e}")
    
    def _to_database_model(self, entity: Transaction, model: Optional[TransactionModel] = None) -> TransactionModel:
        """Convert domain entity to database model"""
        try:
            if model is None:
                model = TransactionModel()
            
            model.id = entity.id
            model.transaction_id = entity.transaction_id
            model.from_account_id = entity.from_account_id
            model.to_account_id = entity.to_account_id
            model.transaction_type = entity.transaction_type.value
            model.amount = entity.amount.amount
            model.currency = entity.amount.currency
            model.status = entity.status.value
            model.description = entity.description
            model.reference_number = entity.reference_number
            model.category = entity.category
            model.transaction_fee = entity.transaction_fee.amount if entity.transaction_fee else Decimal('0.00')
            model.service_charge = entity.service_charge.amount if entity.service_charge else Decimal('0.00')
            model.tax_amount = entity.tax_amount.amount if entity.tax_amount else Decimal('0.00')
            model.exchange_rate = entity.exchange_rate
            model.processing_method = entity.processing_method
            model.scheduled_at = entity.scheduled_at
            model.processed_at = entity.processed_at
            model.channel = entity.channel
            model.location = entity.location
            model.device_info = entity.device_info
            model.approval_required = entity.approval_required
            model.approved_by = entity.approved_by
            model.approved_at = entity.approved_at
            model.approval_notes = entity.approval_notes
            model.risk_score = entity.risk_score
            model.aml_check_status = entity.aml_check_status
            model.fraud_check_status = entity.fraud_check_status
            model.compliance_notes = entity.compliance_notes
            model.reconciliation_status = entity.reconciliation_status
            model.reconciled_at = entity.reconciled_at
            model.reconciled_by = entity.reconciled_by
            model.metadata = entity.metadata
            model.tags = entity.tags
            model.created_by = entity.created_by
            model.updated_by = entity.updated_by
            
            if hasattr(entity, 'created_at') and entity.created_at:
                model.created_at = entity.created_at
            if hasattr(entity, 'updated_at') and entity.updated_at:
                model.updated_at = entity.updated_at
            if hasattr(entity, 'version') and entity.version:
                model.version = entity.version
            
            return model
            
        except Exception as e:
            logger.error(f"Error converting transaction entity to model: {e}")
            raise ValueError(f"Failed to convert transaction entity: {e}")
    
    async def create(self, transaction: Transaction) -> Transaction:
        """Create a new transaction"""
        try:
            with self._get_session() as session:
                # Convert to database model
                db_model = self._to_database_model(transaction)
                
                # Add to session and flush to get ID
                session.add(db_model)
                session.flush()
                
                # Convert back to domain entity with updated ID
                created_transaction = self._to_domain_entity(db_model)
                
                logger.info(f"Created transaction: {created_transaction.transaction_id}")
                return created_transaction
                
        except IntegrityError as e:
            logger.error(f"Integrity error creating transaction: {e}")
            raise ValueError(f"Transaction creation failed: {e}")
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            raise
    
    async def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """Get transaction by ID"""
        try:
            with self._get_session() as session:
                model = session.query(TransactionModel).filter(
                    TransactionModel.id == transaction_id
                ).first()
                
                return self._to_domain_entity(model) if model else None
                
        except Exception as e:
            logger.error(f"Error getting transaction by ID {transaction_id}: {e}")
            raise
    
    async def get_by_transaction_id(self, transaction_id: str) -> Optional[Transaction]:
        """Get transaction by transaction ID"""
        try:
            with self._get_session() as session:
                model = session.query(TransactionModel).filter(
                    TransactionModel.transaction_id == transaction_id
                ).first()
                
                return self._to_domain_entity(model) if model else None
                
        except Exception as e:
            logger.error(f"Error getting transaction by transaction ID {transaction_id}: {e}")
            raise
    
    async def get_by_account_id(
        self,
        account_id: UUID,
        limit: int = 100,
        offset: int = 0,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None
    ) -> Tuple[List[Transaction], int]:
        """Get transactions for an account with filters and pagination"""
        try:
            with self._get_session() as session:
                query = session.query(TransactionModel).filter(
                    or_(
                        TransactionModel.from_account_id == account_id,
                        TransactionModel.to_account_id == account_id
                    )
                )
                
                # Apply filters
                if start_date:
                    query = query.filter(TransactionModel.created_at >= start_date)
                
                if end_date:
                    query = query.filter(TransactionModel.created_at <= end_date)
                
                if transaction_type:
                    query = query.filter(TransactionModel.transaction_type == transaction_type.value)
                
                if status:
                    query = query.filter(TransactionModel.status == status.value)
                
                # Get total count
                total_count = query.count()
                
                # Apply pagination and ordering
                models = query.order_by(desc(TransactionModel.created_at))\
                             .offset(offset)\
                             .limit(limit)\
                             .all()
                
                transactions = [self._to_domain_entity(model) for model in models]
                
                return transactions, total_count
                
        except Exception as e:
            logger.error(f"Error getting transactions for account {account_id}: {e}")
            raise
    
    async def update(self, transaction: Transaction) -> Transaction:
        """Update an existing transaction"""
        try:
            with self._get_session() as session:
                # Get existing model
                existing_model = session.query(TransactionModel).filter(
                    TransactionModel.id == transaction.id
                ).first()
                
                if not existing_model:
                    raise ValueError(f"Transaction {transaction.id} not found")
                
                # Update model
                updated_model = self._to_database_model(transaction, existing_model)
                
                # Merge changes
                session.merge(updated_model)
                session.flush()
                
                # Return updated entity
                updated_transaction = self._to_domain_entity(updated_model)
                
                logger.info(f"Updated transaction: {updated_transaction.transaction_id}")
                return updated_transaction
                
        except Exception as e:
            logger.error(f"Error updating transaction {transaction.id}: {e}")
            raise
    
    async def search(
        self,
        from_account_id: Optional[UUID] = None,
        to_account_id: Optional[UUID] = None,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        channel: Optional[str] = None,
        category: Optional[str] = None,
        reference_number: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Transaction], int]:
        """Search transactions with filters and pagination"""
        try:
            with self._get_session() as session:
                query = session.query(TransactionModel)
                
                # Apply filters
                if from_account_id:
                    query = query.filter(TransactionModel.from_account_id == from_account_id)
                
                if to_account_id:
                    query = query.filter(TransactionModel.to_account_id == to_account_id)
                
                if transaction_type:
                    query = query.filter(TransactionModel.transaction_type == transaction_type.value)
                
                if status:
                    query = query.filter(TransactionModel.status == status.value)
                
                if min_amount is not None:
                    query = query.filter(TransactionModel.amount >= min_amount)
                
                if max_amount is not None:
                    query = query.filter(TransactionModel.amount <= max_amount)
                
                if start_date:
                    query = query.filter(TransactionModel.created_at >= start_date)
                
                if end_date:
                    query = query.filter(TransactionModel.created_at <= end_date)
                
                if channel:
                    query = query.filter(TransactionModel.channel == channel)
                
                if category:
                    query = query.filter(TransactionModel.category == category)
                
                if reference_number:
                    query = query.filter(TransactionModel.reference_number.ilike(f"%{reference_number}%"))
                
                # Get total count
                total_count = query.count()
                
                # Apply pagination and ordering
                models = query.order_by(desc(TransactionModel.created_at))\
                             .offset(offset)\
                             .limit(limit)\
                             .all()
                
                transactions = [self._to_domain_entity(model) for model in models]
                
                return transactions, total_count
                
        except Exception as e:
            logger.error(f"Error searching transactions: {e}")
            raise
    
    async def get_transaction_summary(
        self,
        account_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[TransactionType] = None
    ) -> Dict[str, Any]:
        """Get transaction summary statistics"""
        try:
            with self._get_session() as session:
                query = session.query(TransactionModel)
                
                # Apply filters
                if account_id:
                    query = query.filter(
                        or_(
                            TransactionModel.from_account_id == account_id,
                            TransactionModel.to_account_id == account_id
                        )
                    )
                
                if start_date:
                    query = query.filter(TransactionModel.created_at >= start_date)
                
                if end_date:
                    query = query.filter(TransactionModel.created_at <= end_date)
                
                if transaction_type:
                    query = query.filter(TransactionModel.transaction_type == transaction_type.value)
                
                # Get summary statistics
                summary_query = query.with_entities(
                    func.count(TransactionModel.id).label('total_transactions'),
                    func.sum(TransactionModel.amount).label('total_amount'),
                    func.avg(TransactionModel.amount).label('average_amount'),
                    func.min(TransactionModel.amount).label('min_amount'),
                    func.max(TransactionModel.amount).label('max_amount'),
                    func.sum(TransactionModel.transaction_fee).label('total_fees'),
                    func.sum(TransactionModel.service_charge).label('total_charges'),
                    func.sum(TransactionModel.tax_amount).label('total_tax')
                )
                
                result = summary_query.first()
                
                # Get status breakdown
                status_query = query.with_entities(
                    TransactionModel.status,
                    func.count(TransactionModel.id).label('count'),
                    func.sum(TransactionModel.amount).label('amount')
                ).group_by(TransactionModel.status)
                
                status_breakdown = {}
                for status, count, amount in status_query.all():
                    status_breakdown[status] = {
                        'count': count,
                        'amount': amount or Decimal('0.00')
                    }
                
                return {
                    'account_id': str(account_id) if account_id else None,
                    'period_start': start_date,
                    'period_end': end_date,
                    'total_transactions': result.total_transactions or 0,
                    'total_amount': result.total_amount or Decimal('0.00'),
                    'average_amount': result.average_amount or Decimal('0.00'),
                    'min_amount': result.min_amount or Decimal('0.00'),
                    'max_amount': result.max_amount or Decimal('0.00'),
                    'total_fees': result.total_fees or Decimal('0.00'),
                    'total_charges': result.total_charges or Decimal('0.00'),
                    'total_tax': result.total_tax or Decimal('0.00'),
                    'status_breakdown': status_breakdown
                }
                
        except Exception as e:
            logger.error(f"Error getting transaction summary: {e}")
            raise
    
    async def get_pending_transactions(
        self,
        limit: int = 100,
        scheduled_before: Optional[datetime] = None
    ) -> List[Transaction]:
        """Get pending transactions for processing"""
        try:
            with self._get_session() as session:
                query = session.query(TransactionModel).filter(
                    TransactionModel.status == TransactionStatus.PENDING.value
                )
                
                if scheduled_before:
                    query = query.filter(
                        or_(
                            TransactionModel.scheduled_at.is_(None),
                            TransactionModel.scheduled_at <= scheduled_before
                        )
                    )
                
                models = query.order_by(asc(TransactionModel.created_at))\
                             .limit(limit)\
                             .all()
                
                return [self._to_domain_entity(model) for model in models]
                
        except Exception as e:
            logger.error(f"Error getting pending transactions: {e}")
            raise
    
    async def bulk_update_status(
        self,
        transaction_ids: List[UUID],
        new_status: TransactionStatus,
        updated_by: str
    ) -> int:
        """Bulk update transaction status"""
        try:
            with self._get_session() as session:
                result = session.query(TransactionModel).filter(
                    TransactionModel.id.in_(transaction_ids)
                ).update({
                    'status': new_status.value,
                    'updated_by': updated_by,
                    'updated_at': datetime.utcnow()
                }, synchronize_session=False)
                
                logger.info(f"Bulk updated {result} transactions to status {new_status.value}")
                return result
                
        except Exception as e:
            logger.error(f"Error bulk updating transaction status: {e}")
            raise


class TransactionLimitRepository:
    """
    SQLAlchemy-based repository for Transaction Limit entities
    """
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session
    
    def _get_session(self) -> Session:
        """Get database session"""
        return self.session if self.session else get_db_session()
    
    async def get_applicable_limits(
        self,
        account_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        account_type: Optional[str] = None,
        transaction_type: Optional[str] = None,
        channel: Optional[str] = None
    ) -> List[TransactionLimitModel]:
        """Get applicable transaction limits"""
        try:
            with self._get_session() as session:
                query = session.query(TransactionLimitModel).filter(
                    TransactionLimitModel.is_active == True
                )
                
                # Apply scope filters
                scope_filters = []
                
                if account_id:
                    scope_filters.append(TransactionLimitModel.account_id == account_id)
                
                if customer_id:
                    scope_filters.append(TransactionLimitModel.customer_id == customer_id)
                
                if account_type:
                    scope_filters.append(TransactionLimitModel.account_type == account_type)
                
                # Add global limits (no specific scope)
                scope_filters.append(
                    and_(
                        TransactionLimitModel.account_id.is_(None),
                        TransactionLimitModel.customer_id.is_(None),
                        TransactionLimitModel.account_type.is_(None)
                    )
                )
                
                query = query.filter(or_(*scope_filters))
                
                # Apply transaction type filter
                if transaction_type:
                    query = query.filter(
                        or_(
                            TransactionLimitModel.transaction_type == transaction_type,
                            TransactionLimitModel.transaction_type.is_(None)
                        )
                    )
                
                # Apply channel filter
                if channel:
                    query = query.filter(
                        or_(
                            TransactionLimitModel.channel == channel,
                            TransactionLimitModel.channel.is_(None)
                        )
                    )
                
                return query.all()
                
        except Exception as e:
            logger.error(f"Error getting applicable limits: {e}")
            raise
    
    async def update_limit_usage(
        self,
        limit_id: UUID,
        amount_used: Decimal,
        count_used: int = 1
    ) -> bool:
        """Update limit usage"""
        try:
            with self._get_session() as session:
                result = session.query(TransactionLimitModel).filter(
                    TransactionLimitModel.id == limit_id
                ).update({
                    'used_amount': TransactionLimitModel.used_amount + amount_used,
                    'used_count': TransactionLimitModel.used_count + count_used,
                    'updated_at': datetime.utcnow()
                })
                
                return result > 0
                
        except Exception as e:
            logger.error(f"Error updating limit usage: {e}")
            raise
    
    async def reset_periodic_limits(self, reset_frequency: str) -> int:
        """Reset periodic limits based on frequency"""
        try:
            with self._get_session() as session:
                now = datetime.utcnow()
                
                # Determine reset criteria based on frequency
                if reset_frequency == 'daily':
                    reset_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
                elif reset_frequency == 'weekly':
                    days_since_monday = now.weekday()
                    reset_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
                elif reset_frequency == 'monthly':
                    reset_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                else:
                    return 0
                
                # Update limits that need reset
                result = session.query(TransactionLimitModel).filter(
                    and_(
                        TransactionLimitModel.reset_frequency == reset_frequency,
                        TransactionLimitModel.is_active == True,
                        or_(
                            TransactionLimitModel.last_reset_at.is_(None),
                            TransactionLimitModel.last_reset_at < reset_date
                        )
                    )
                ).update({
                    'used_amount': 0,
                    'used_count': 0,
                    'last_reset_at': now,
                    'updated_at': now
                })
                
                logger.info(f"Reset {result} {reset_frequency} limits")
                return result
                
        except Exception as e:
            logger.error(f"Error resetting periodic limits: {e}")
            raise


__all__ = [
    "TransactionRepository",
    "TransactionLimitRepository"
]
