"""
SQLAlchemy Transaction Repository

Repository implementation for transactions using SQLAlchemy ORM.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import func, and_, or_, between
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from core_banking.database import SessionLocal
from core_banking.database.models import Transaction as TransactionModel

from ...application.interfaces.transaction_repository_interface import TransactionRepositoryInterface
from ...domain.entities.transaction import Transaction, TransactionStatus, TransactionType

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path


class SQLAlchemyTransactionRepository(TransactionRepositoryInterface):
    """SQLAlchemy implementation of TransactionRepositoryInterface"""
    
    def __init__(self, session_factory=None):
        """
        Initialize repository with session factory
        
        Args:
            session_factory: Function that creates DB sessions (defaults to SessionLocal)
        """
        self._session_factory = session_factory or SessionLocal
    
    def save(self, transaction: Transaction) -> Transaction:
        """
        Save a transaction to the database
        
        Args:
            transaction: Transaction to save
            
        Returns:
            Saved transaction
        """
        try:
            with self._session_factory() as session:
                # Convert domain entity to database model
                db_transaction = self._to_db_model(transaction)
                
                # Add to session
                session.add(db_transaction)
                session.commit()
                
                # Convert back to domain entity with generated values
                return self._to_domain_entity(db_transaction)
        except SQLAlchemyError as e:
            # Log the error
            import logging
            logging.error(f"Error saving transaction: {str(e)}")
            raise
    
    def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """
        Get transaction by ID
        
        Args:
            transaction_id: Transaction ID to retrieve
            
        Returns:
            Transaction if found, None otherwise
        """
        try:
            with self._session_factory() as session:
                db_transaction = session.query(TransactionModel).filter(
                    TransactionModel.id == str(transaction_id)
                ).first()
                
                if db_transaction:
                    return self._to_domain_entity(db_transaction)
                
                return None
        except SQLAlchemyError as e:
            # Log the error
            import logging
            logging.error(f"Error retrieving transaction: {str(e)}")
            raise
    
    def get_by_account_id(self, account_id: UUID, limit: int = 10, offset: int = 0) -> List[Transaction]:
        """
        Get transactions for an account
        
        Args:
            account_id: Account ID to retrieve transactions for
            limit: Maximum number of transactions to return
            offset: Offset for pagination
            
        Returns:
            List of transactions for the account
        """
        try:
            with self._session_factory() as session:
                db_transactions = session.query(TransactionModel).filter(
                    TransactionModel.account_id == str(account_id)
                ).order_by(
                    TransactionModel.timestamp.desc()
                ).offset(offset).limit(limit).all()
                
                return [self._to_domain_entity(t) for t in db_transactions]
        except SQLAlchemyError as e:
            # Log the error
            import logging
            logging.error(f"Error retrieving transactions for account: {str(e)}")
            raise
    
    def update_status(self, transaction_id: UUID, status: TransactionStatus) -> Optional[Transaction]:
        """
        Update transaction status
        
        Args:
            transaction_id: Transaction ID to update
            status: New status
            
        Returns:
            Updated transaction if found, None otherwise
        """
        try:
            with self._session_factory() as session:
                db_transaction = session.query(TransactionModel).filter(
                    TransactionModel.id == str(transaction_id)
                ).first()
                
                if not db_transaction:
                    return None
                
                # Update status
                db_transaction.status = status.value
                
                # Update completed_at if status is COMPLETED
                if status == TransactionStatus.COMPLETED:
                    db_transaction.completed_at = datetime.now()
                
                session.commit()
                
                return self._to_domain_entity(db_transaction)
        except SQLAlchemyError as e:
            # Log the error
            import logging
            logging.error(f"Error updating transaction status: {str(e)}")
            raise
    
    def get_account_daily_total(self, account_id: UUID, transaction_type: TransactionType, date: datetime) -> Decimal:
        """
        Get total transaction amount for an account on a specific date and type
        
        Args:
            account_id: Account ID to check
            transaction_type: Type of transactions to total
            date: Date to check
            
        Returns:
            Total transaction amount
        """
        try:
            start_date = datetime(date.year, date.month, date.day, 0, 0, 0)
            end_date = datetime(date.year, date.month, date.day, 23, 59, 59)
            
            with self._session_factory() as session:
                result = session.query(func.sum(TransactionModel.amount)).filter(
                    TransactionModel.account_id == str(account_id),
                    TransactionModel.transaction_type == transaction_type.value,
                    TransactionModel.status == TransactionStatus.COMPLETED.value,
                    TransactionModel.timestamp.between(start_date, end_date)
                ).scalar()
                
                return Decimal(str(result)) if result is not None else Decimal('0')
        except SQLAlchemyError as e:
            # Log the error
            import logging
            logging.error(f"Error calculating daily total: {str(e)}")
            raise
    
    def search(self, criteria: Dict[str, Any], limit: int = 10, offset: int = 0) -> List[Transaction]:
        """
        Search transactions by criteria
        
        Args:
            criteria: Search criteria
            limit: Maximum number of transactions to return
            offset: Offset for pagination
            
        Returns:
            List of matching transactions
        """
        try:
            with self._session_factory() as session:
                query = session.query(TransactionModel)
                
                # Apply filters based on criteria
                if "account_id" in criteria:
                    query = query.filter(TransactionModel.account_id == str(criteria["account_id"]))
                
                if "transaction_type" in criteria:
                    query = query.filter(TransactionModel.transaction_type == criteria["transaction_type"])
                
                if "status" in criteria:
                    query = query.filter(TransactionModel.status == criteria["status"])
                
                if "min_amount" in criteria:
                    query = query.filter(TransactionModel.amount >= criteria["min_amount"])
                
                if "max_amount" in criteria:
                    query = query.filter(TransactionModel.amount <= criteria["max_amount"])
                
                if "start_date" in criteria and "end_date" in criteria:
                    query = query.filter(TransactionModel.timestamp.between(
                        criteria["start_date"], 
                        criteria["end_date"]
                    ))
                
                if "to_account_id" in criteria:
                    query = query.filter(TransactionModel.to_account_id == str(criteria["to_account_id"]))
                
                # Get sorted results
                db_transactions = query.order_by(
                    TransactionModel.timestamp.desc()
                ).offset(offset).limit(limit).all()
                
                return [self._to_domain_entity(t) for t in db_transactions]
        except SQLAlchemyError as e:
            # Log the error
            import logging
            logging.error(f"Error searching transactions: {str(e)}")
            raise
    
    def _to_db_model(self, transaction: Transaction) -> TransactionModel:
        """
        Convert domain entity to database model
        
        Args:
            transaction: Domain entity
            
        Returns:
            Database model
        """
        metadata_dict = transaction.metadata.to_dict() if transaction.metadata else {}
        
        return TransactionModel(
            id=str(transaction.transaction_id),
            account_id=str(transaction.account_id) if transaction.account_id else None,
            amount=float(transaction.amount),
            transaction_type=transaction.transaction_type.value if transaction.transaction_type else None,
            status=transaction.status.value,
            description=transaction.description,
            timestamp=transaction.timestamp,
            metadata=metadata_dict,
            reference_transaction_id=str(transaction.reference_transaction_id) if transaction.reference_transaction_id else None,
            to_account_id=str(transaction.to_account_id) if transaction.to_account_id else None,
            completed_at=transaction.completed_at,
            failure_reason=transaction.failure_reason
        )
    
    def _to_domain_entity(self, db_transaction: TransactionModel) -> Transaction:
        """
        Convert database model to domain entity
        
        Args:
            db_transaction: Database model
            
        Returns:
            Domain entity
        """
        from ...domain.entities.transaction import TransactionMetadata
        
        # Create metadata object if available
        metadata = None
        if db_transaction.metadata:
            metadata = TransactionMetadata.from_dict(db_transaction.metadata)
        
        # Create transaction object
        transaction = Transaction(
            transaction_id=UUID(db_transaction.id) if db_transaction.id else None,
            account_id=UUID(db_transaction.account_id) if db_transaction.account_id else None,
            amount=Decimal(str(db_transaction.amount)),
            transaction_type=TransactionType(db_transaction.transaction_type) if db_transaction.transaction_type else None,
            status=TransactionStatus(db_transaction.status) if db_transaction.status else TransactionStatus.PENDING,
            description=db_transaction.description,
            timestamp=db_transaction.timestamp,
            metadata=metadata,
            reference_transaction_id=UUID(db_transaction.reference_transaction_id) if db_transaction.reference_transaction_id else None,
            to_account_id=UUID(db_transaction.to_account_id) if db_transaction.to_account_id else None
        )
        
        # Set additional properties that aren't in the constructor
        if db_transaction.completed_at:
            transaction._completed_at = db_transaction.completed_at
        
        if db_transaction.failure_reason:
            transaction._failure_reason = db_transaction.failure_reason
        
        return transaction
