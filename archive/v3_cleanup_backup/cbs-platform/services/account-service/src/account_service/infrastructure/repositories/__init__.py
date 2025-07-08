"""
Account Service Repository Implementations
SQLAlchemy-based repositories for account and transaction data access
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
import logging
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

# Import domain entities
from ...domain.entities import (
    Account, Transaction, AccountType, AccountStatus, TransactionType, 
    TransactionStatus, Money, AccountLimits, AccountHolder, AccountStatement
)

# Import database models
from ..database import (
    AccountModel, TransactionModel, AccountHolderModel, AccountStatementModel,
    get_db_session
)

# Setup logging
logger = logging.getLogger(__name__)


class AccountRepository:
    """
    SQLAlchemy-based repository for Account entities
    """
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session
    
    def _get_session(self) -> Session:
        """Get database session"""
        return self.session if self.session else get_db_session()
    
    def _to_domain_entity(self, model: AccountModel) -> Account:
        """Convert database model to domain entity"""
        try:
            # Create AccountLimits
            limits = AccountLimits(
                daily_withdrawal_limit=Money(model.daily_withdrawal_limit, model.currency),
                daily_transfer_limit=Money(model.daily_transfer_limit, model.currency),
                monthly_transaction_limit=Money(model.monthly_transaction_limit, model.currency),
                minimum_balance=Money(model.minimum_balance, model.currency),
                maximum_balance=Money(model.maximum_balance, model.currency) if model.maximum_balance else None
            )
            
            # Create Account entity
            return Account(
                id=model.id,
                account_number=model.account_number,
                customer_id=model.customer_id,
                account_type=AccountType(model.account_type),
                status=AccountStatus(model.status),
                balance=Money(model.balance, model.currency),
                limits=limits,
                interest_rate=model.interest_rate,
                maintenance_fee=Money(model.maintenance_fee, model.currency),
                overdraft_limit=Money(model.overdraft_limit, model.currency) if model.overdraft_limit else None,
                overdraft_fee=Money(model.overdraft_fee, model.currency),
                metadata=model.metadata or {},
                notes=model.notes,
                created_at=model.created_at,
                updated_at=model.updated_at,
                created_by=model.created_by,
                updated_by=model.updated_by,
                version=model.version
            )
        except Exception as e:
            logger.error(f"Error converting account model to entity: {e}")
            raise ValueError(f"Failed to convert account model: {e}")
    
    def _to_database_model(self, entity: Account, model: Optional[AccountModel] = None) -> AccountModel:
        """Convert domain entity to database model"""
        try:
            if model is None:
                model = AccountModel()
            
            # Basic fields
            model.id = entity.id
            model.account_number = entity.account_number
            model.customer_id = entity.customer_id
            model.account_type = entity.account_type.value
            model.status = entity.status.value
            model.balance = entity.balance.amount
            model.currency = entity.balance.currency
            
            # Limits
            model.daily_withdrawal_limit = entity.limits.daily_withdrawal_limit.amount
            model.daily_transfer_limit = entity.limits.daily_transfer_limit.amount
            model.monthly_transaction_limit = entity.limits.monthly_transaction_limit.amount
            model.minimum_balance = entity.limits.minimum_balance.amount
            model.maximum_balance = entity.limits.maximum_balance.amount if entity.limits.maximum_balance else None
            
            # Additional fields
            model.interest_rate = entity.interest_rate
            model.maintenance_fee = entity.maintenance_fee.amount if entity.maintenance_fee else Decimal('0.00')
            model.overdraft_limit = entity.overdraft_limit.amount if entity.overdraft_limit else None
            model.overdraft_fee = entity.overdraft_fee.amount if entity.overdraft_fee else Decimal('0.00')
            model.metadata = entity.metadata
            model.notes = entity.notes
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
            logger.error(f"Error converting account entity to model: {e}")
            raise ValueError(f"Failed to convert account entity: {e}")
    
    async def create(self, account: Account) -> Account:
        """Create a new account"""
        try:
            with self._get_session() as session:
                # Check for duplicate account number
                existing = session.query(AccountModel).filter(
                    AccountModel.account_number == account.account_number
                ).first()
                
                if existing:
                    raise ValueError(f"Account number {account.account_number} already exists")
                
                # Convert to database model
                db_model = self._to_database_model(account)
                
                # Add to session and flush to get ID
                session.add(db_model)
                session.flush()
                
                # Convert back to domain entity with updated ID
                created_account = self._to_domain_entity(db_model)
                
                logger.info(f"Created account: {created_account.account_number}")
                return created_account
                
        except IntegrityError as e:
            logger.error(f"Integrity error creating account: {e}")
            raise ValueError(f"Account creation failed: {e}")
        except Exception as e:
            logger.error(f"Error creating account: {e}")
            raise
    
    async def get_by_id(self, account_id: UUID) -> Optional[Account]:
        """Get account by ID"""
        try:
            with self._get_session() as session:
                model = session.query(AccountModel).filter(
                    AccountModel.id == account_id
                ).first()
                
                return self._to_domain_entity(model) if model else None
                
        except Exception as e:
            logger.error(f"Error getting account by ID {account_id}: {e}")
            raise
    
    async def get_by_account_number(self, account_number: str) -> Optional[Account]:
        """Get account by account number"""
        try:
            with self._get_session() as session:
                model = session.query(AccountModel).filter(
                    AccountModel.account_number == account_number
                ).first()
                
                return self._to_domain_entity(model) if model else None
                
        except Exception as e:
            logger.error(f"Error getting account by number {account_number}: {e}")
            raise
    
    async def get_by_customer_id(self, customer_id: UUID) -> List[Account]:
        """Get all accounts for a customer"""
        try:
            with self._get_session() as session:
                models = session.query(AccountModel).filter(
                    AccountModel.customer_id == customer_id
                ).order_by(desc(AccountModel.created_at)).all()
                
                return [self._to_domain_entity(model) for model in models]
                
        except Exception as e:
            logger.error(f"Error getting accounts for customer {customer_id}: {e}")
            raise
    
    async def update(self, account: Account) -> Account:
        """Update an existing account"""
        try:
            with self._get_session() as session:
                # Get existing model
                existing_model = session.query(AccountModel).filter(
                    AccountModel.id == account.id
                ).first()
                
                if not existing_model:
                    raise ValueError(f"Account {account.id} not found")
                
                # Update model
                updated_model = self._to_database_model(account, existing_model)
                
                # Merge changes
                session.merge(updated_model)
                session.flush()
                
                # Return updated entity
                updated_account = self._to_domain_entity(updated_model)
                
                logger.info(f"Updated account: {updated_account.account_number}")
                return updated_account
                
        except Exception as e:
            logger.error(f"Error updating account {account.id}: {e}")
            raise
    
    async def delete(self, account_id: UUID) -> bool:
        """Delete an account (soft delete by setting status to closed)"""
        try:
            with self._get_session() as session:
                model = session.query(AccountModel).filter(
                    AccountModel.id == account_id
                ).first()
                
                if not model:
                    return False
                
                # Soft delete by updating status
                model.status = AccountStatus.CLOSED.value
                model.updated_at = datetime.utcnow()
                
                session.merge(model)
                
                logger.info(f"Deleted (closed) account: {account_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting account {account_id}: {e}")
            raise
    
    async def search(
        self,
        customer_id: Optional[UUID] = None,
        account_type: Optional[AccountType] = None,
        status: Optional[AccountStatus] = None,
        min_balance: Optional[Decimal] = None,
        max_balance: Optional[Decimal] = None,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Account], int]:
        """Search accounts with filters and pagination"""
        try:
            with self._get_session() as session:
                query = session.query(AccountModel)
                
                # Apply filters
                if customer_id:
                    query = query.filter(AccountModel.customer_id == customer_id)
                
                if account_type:
                    query = query.filter(AccountModel.account_type == account_type.value)
                
                if status:
                    query = query.filter(AccountModel.status == status.value)
                
                if min_balance is not None:
                    query = query.filter(AccountModel.balance >= min_balance)
                
                if max_balance is not None:
                    query = query.filter(AccountModel.balance <= max_balance)
                
                if created_after:
                    query = query.filter(AccountModel.created_at >= created_after)
                
                if created_before:
                    query = query.filter(AccountModel.created_at <= created_before)
                
                # Get total count
                total_count = query.count()
                
                # Apply pagination and ordering
                models = query.order_by(desc(AccountModel.created_at))\
                             .offset(offset)\
                             .limit(limit)\
                             .all()
                
                accounts = [self._to_domain_entity(model) for model in models]
                
                return accounts, total_count
                
        except Exception as e:
            logger.error(f"Error searching accounts: {e}")
            raise
    
    async def update_balance(self, account_id: UUID, new_balance: Money) -> bool:
        """Update account balance"""
        try:
            with self._get_session() as session:
                result = session.query(AccountModel).filter(
                    AccountModel.id == account_id
                ).update({
                    'balance': new_balance.amount,
                    'currency': new_balance.currency,
                    'updated_at': datetime.utcnow()
                })
                
                return result > 0
                
        except Exception as e:
            logger.error(f"Error updating balance for account {account_id}: {e}")
            raise
    
    async def get_account_summary(self, customer_id: UUID) -> Dict[str, Any]:
        """Get account summary for a customer"""
        try:
            with self._get_session() as session:
                # Get account counts by type and status
                summary_query = session.query(
                    AccountModel.account_type,
                    AccountModel.status,
                    func.count(AccountModel.id).label('count'),
                    func.sum(AccountModel.balance).label('total_balance')
                ).filter(
                    AccountModel.customer_id == customer_id
                ).group_by(
                    AccountModel.account_type, AccountModel.status
                )
                
                results = summary_query.all()
                
                summary = {
                    'customer_id': str(customer_id),
                    'total_accounts': 0,
                    'total_balance': Decimal('0.00'),
                    'by_type': {},
                    'by_status': {}
                }
                
                for account_type, status, count, total_balance in results:
                    summary['total_accounts'] += count
                    summary['total_balance'] += total_balance or Decimal('0.00')
                    
                    # Group by type
                    if account_type not in summary['by_type']:
                        summary['by_type'][account_type] = {'count': 0, 'balance': Decimal('0.00')}
                    summary['by_type'][account_type]['count'] += count
                    summary['by_type'][account_type]['balance'] += total_balance or Decimal('0.00')
                    
                    # Group by status
                    if status not in summary['by_status']:
                        summary['by_status'][status] = {'count': 0, 'balance': Decimal('0.00')}
                    summary['by_status'][status]['count'] += count
                    summary['by_status'][status]['balance'] += total_balance or Decimal('0.00')
                
                return summary
                
        except Exception as e:
            logger.error(f"Error getting account summary for customer {customer_id}: {e}")
            raise


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
                account_id=model.account_id,
                transaction_type=TransactionType(model.transaction_type),
                amount=Money(model.amount, model.currency),
                status=TransactionStatus(model.status),
                description=model.description,
                reference_number=model.reference_number,
                related_account_id=model.related_account_id,
                balance_before=Money(model.balance_before, model.currency),
                balance_after=Money(model.balance_after, model.currency),
                processing_fee=Money(model.processing_fee, model.currency),
                exchange_rate=model.exchange_rate,
                metadata=model.metadata or {},
                channel=model.channel,
                location=model.location,
                initiated_at=model.initiated_at,
                completed_at=model.completed_at,
                created_by=model.created_by,
                authorized_by=model.authorized_by
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
            model.account_id = entity.account_id
            model.transaction_type = entity.transaction_type.value
            model.amount = entity.amount.amount
            model.currency = entity.amount.currency
            model.status = entity.status.value
            model.description = entity.description
            model.reference_number = entity.reference_number
            model.related_account_id = entity.related_account_id
            model.balance_before = entity.balance_before.amount
            model.balance_after = entity.balance_after.amount
            model.processing_fee = entity.processing_fee.amount if entity.processing_fee else Decimal('0.00')
            model.exchange_rate = entity.exchange_rate
            model.metadata = entity.metadata
            model.channel = entity.channel
            model.location = entity.location
            model.initiated_at = entity.initiated_at
            model.completed_at = entity.completed_at
            model.created_by = entity.created_by
            model.authorized_by = entity.authorized_by
            
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
                
                # Add to session and flush
                session.add(db_model)
                session.flush()
                
                # Convert back to domain entity
                created_transaction = self._to_domain_entity(db_model)
                
                logger.info(f"Created transaction: {created_transaction.transaction_id}")
                return created_transaction
                
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
        end_date: Optional[datetime] = None
    ) -> Tuple[List[Transaction], int]:
        """Get transactions for an account with pagination"""
        try:
            with self._get_session() as session:
                query = session.query(TransactionModel).filter(
                    TransactionModel.account_id == account_id
                )
                
                # Apply date filters
                if start_date:
                    query = query.filter(TransactionModel.initiated_at >= start_date)
                
                if end_date:
                    query = query.filter(TransactionModel.initiated_at <= end_date)
                
                # Get total count
                total_count = query.count()
                
                # Apply pagination and ordering
                models = query.order_by(desc(TransactionModel.initiated_at))\
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
    
    async def get_transaction_summary(
        self,
        account_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get transaction summary for an account"""
        try:
            with self._get_session() as session:
                query = session.query(TransactionModel).filter(
                    TransactionModel.account_id == account_id
                )
                
                # Apply date filters
                if start_date:
                    query = query.filter(TransactionModel.initiated_at >= start_date)
                
                if end_date:
                    query = query.filter(TransactionModel.initiated_at <= end_date)
                
                # Get summary statistics
                summary_query = query.with_entities(
                    func.count(TransactionModel.id).label('total_transactions'),
                    func.sum(
                        func.case(
                            [(TransactionModel.transaction_type == 'credit', TransactionModel.amount)],
                            else_=0
                        )
                    ).label('total_credits'),
                    func.sum(
                        func.case(
                            [(TransactionModel.transaction_type == 'debit', TransactionModel.amount)],
                            else_=0
                        )
                    ).label('total_debits'),
                    func.sum(TransactionModel.processing_fee).label('total_fees')
                )
                
                result = summary_query.first()
                
                return {
                    'account_id': str(account_id),
                    'total_transactions': result.total_transactions or 0,
                    'total_credits': result.total_credits or Decimal('0.00'),
                    'total_debits': result.total_debits or Decimal('0.00'),
                    'total_fees': result.total_fees or Decimal('0.00'),
                    'net_amount': (result.total_credits or Decimal('0.00')) - (result.total_debits or Decimal('0.00')),
                    'period_start': start_date,
                    'period_end': end_date
                }
                
        except Exception as e:
            logger.error(f"Error getting transaction summary for account {account_id}: {e}")
            raise


__all__ = [
    "AccountRepository",
    "TransactionRepository"
]
