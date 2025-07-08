"""
Transaction Service for Core Banking System V3.0

This service handles all transaction processing operations including:
- Transaction creation and validation
- Transaction history and reporting
- Transaction status management
- Transaction reversal and reconciliation
- Fraud detection and risk assessment
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from ..models.transaction import Transaction, TransactionType, TransactionStatus
from ..models.account import Account
from ..models.customer import Customer
from ..database.connection import get_db_session

class TransactionService:
    """Transaction processing service."""
    
    def __init__(self):
        """Initialize the transaction service."""
        pass
    
    def get_transaction(self, transaction_id: str, db: Session) -> Optional[Transaction]:
        """Get a transaction by transaction ID."""
        return db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    
    def get_transaction_by_id(self, id: int, db: Session) -> Optional[Transaction]:
        """Get a transaction by internal ID."""
        return db.query(Transaction).filter(Transaction.id == id).first()
    
    def get_account_transactions(self, account_number: str, start_date: datetime = None,
                               end_date: datetime = None, limit: int = 50, offset: int = 0,
                               transaction_type: TransactionType = None, db: Session = None) -> List[Transaction]:
        """Get transactions for an account with filtering options."""
        # Get account
        account = db.query(Account).filter(Account.account_number == account_number).first()
        if not account:
            raise ValueError("Account not found")
        
        # Build query
        query = db.query(Transaction).filter(Transaction.account_id == account.id)
        
        # Apply date filters
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        # Apply transaction type filter
        if transaction_type:
            query = query.filter(Transaction.transaction_type == transaction_type)
        
        # Order by date (most recent first) and apply pagination
        return query.order_by(desc(Transaction.transaction_date)).offset(offset).limit(limit).all()
    
    def get_customer_transactions(self, customer_id: str, start_date: datetime = None,
                                end_date: datetime = None, limit: int = 50, offset: int = 0,
                                db: Session = None) -> List[Transaction]:
        """Get all transactions for a customer across all accounts."""
        # Get customer
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            raise ValueError("Customer not found")
        
        # Get customer's accounts
        account_ids = db.query(Account.id).filter(Account.customer_id == customer.id).subquery()
        
        # Build query
        query = db.query(Transaction).filter(Transaction.account_id.in_(account_ids))
        
        # Apply date filters
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        # Order by date (most recent first) and apply pagination
        return query.order_by(desc(Transaction.transaction_date)).offset(offset).limit(limit).all()
    
    def search_transactions(self, search_criteria: Dict[str, Any], db: Session) -> List[Transaction]:
        """Search transactions based on various criteria."""
        query = db.query(Transaction)
        
        # Filter by transaction ID
        if search_criteria.get('transaction_id'):
            query = query.filter(Transaction.transaction_id.ilike(f"%{search_criteria['transaction_id']}%"))
        
        # Filter by reference number
        if search_criteria.get('reference_number'):
            query = query.filter(Transaction.reference_number.ilike(f"%{search_criteria['reference_number']}%"))
        
        # Filter by account number
        if search_criteria.get('account_number'):
            account = db.query(Account).filter(Account.account_number == search_criteria['account_number']).first()
            if account:
                query = query.filter(Transaction.account_id == account.id)
        
        # Filter by transaction type
        if search_criteria.get('transaction_type'):
            query = query.filter(Transaction.transaction_type == search_criteria['transaction_type'])
        
        # Filter by status
        if search_criteria.get('status'):
            query = query.filter(Transaction.status == search_criteria['status'])
        
        # Filter by amount range
        if search_criteria.get('min_amount'):
            query = query.filter(Transaction.amount >= search_criteria['min_amount'])
        if search_criteria.get('max_amount'):
            query = query.filter(Transaction.amount <= search_criteria['max_amount'])
        
        # Filter by date range
        if search_criteria.get('start_date'):
            query = query.filter(Transaction.transaction_date >= search_criteria['start_date'])
        if search_criteria.get('end_date'):
            query = query.filter(Transaction.transaction_date <= search_criteria['end_date'])
        
        # Apply pagination
        limit = search_criteria.get('limit', 50)
        offset = search_criteria.get('offset', 0)
        
        return query.order_by(desc(Transaction.transaction_date)).offset(offset).limit(limit).all()
    
    def get_pending_transactions(self, limit: int = 50, db: Session = None) -> List[Transaction]:
        """Get all pending transactions."""
        return db.query(Transaction).filter(
            Transaction.status == TransactionStatus.PENDING
        ).order_by(Transaction.transaction_date).limit(limit).all()
    
    def get_failed_transactions(self, start_date: datetime = None, limit: int = 50, db: Session = None) -> List[Transaction]:
        """Get failed transactions."""
        query = db.query(Transaction).filter(Transaction.status == TransactionStatus.FAILED)
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        
        return query.order_by(desc(Transaction.transaction_date)).limit(limit).all()
    
    def update_transaction_status(self, transaction_id: str, status: TransactionStatus,
                                failure_reason: str = None, db: Session = None) -> Transaction:
        """Update transaction status."""
        transaction = self.get_transaction(transaction_id, db)
        if not transaction:
            raise ValueError("Transaction not found")
        
        old_status = transaction.status
        transaction.status = status
        
        # Add failure reason if provided
        if failure_reason and status == TransactionStatus.FAILED:
            transaction.description += f" (Failed: {failure_reason})"
        
        db.commit()
        db.refresh(transaction)
        
        return transaction
    
    def reverse_transaction(self, transaction_id: str, reason: str, initiated_by: str, db: Session = None) -> Transaction:
        """Reverse a completed transaction."""
        original_transaction = self.get_transaction(transaction_id, db)
        if not original_transaction:
            raise ValueError("Transaction not found")
        
        if original_transaction.status != TransactionStatus.COMPLETED:
            raise ValueError("Can only reverse completed transactions")
        
        # Get the account
        account = db.query(Account).filter(Account.id == original_transaction.account_id).first()
        if not account:
            raise ValueError("Account not found")
        
        # Create reversal transaction
        reversal_transaction_id = self._generate_transaction_id(db)
        
        # Determine reversal type and amount adjustment
        if original_transaction.transaction_type == TransactionType.DEPOSIT:
            reversal_type = TransactionType.WITHDRAWAL
            account.balance -= original_transaction.amount
        elif original_transaction.transaction_type == TransactionType.WITHDRAWAL:
            reversal_type = TransactionType.DEPOSIT
            account.balance += original_transaction.amount
        elif original_transaction.transaction_type == TransactionType.TRANSFER:
            reversal_type = TransactionType.REVERSAL
            account.balance += original_transaction.amount
            
            # If it was a transfer, also reverse the credit in the destination account
            if original_transaction.to_account_number:
                dest_account = db.query(Account).filter(
                    Account.account_number == original_transaction.to_account_number
                ).first()
                if dest_account:
                    dest_account.balance -= original_transaction.amount
        else:
            reversal_type = TransactionType.REVERSAL
        
        # Create reversal transaction
        reversal_transaction = Transaction(
            transaction_id=reversal_transaction_id,
            account_id=original_transaction.account_id,
            transaction_type=reversal_type,
            amount=original_transaction.amount,
            description=f"Reversal of {original_transaction.transaction_id}: {reason}",
            reference_number=original_transaction.transaction_id,
            status=TransactionStatus.COMPLETED,
            initiated_by=initiated_by
        )
        
        # Update original transaction status
        original_transaction.status = TransactionStatus.REVERSED
        
        # Update account last transaction date
        account.last_transaction_date = datetime.utcnow()
        
        db.add(reversal_transaction)
        db.commit()
        db.refresh(reversal_transaction)
        
        return reversal_transaction
    
    def get_transaction_summary(self, start_date: datetime = None, end_date: datetime = None, db: Session = None) -> Dict[str, Any]:
        """Get transaction summary statistics."""
        # Set default date range (today if not specified)
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Base query
        query = db.query(Transaction).filter(
            and_(
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            )
        )
        
        # Total transactions
        total_transactions = query.count()
        
        # Transactions by type
        type_stats = db.query(
            Transaction.transaction_type,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total_amount')
        ).filter(
            and_(
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            )
        ).group_by(Transaction.transaction_type).all()
        
        # Transactions by status
        status_stats = db.query(
            Transaction.status,
            func.count(Transaction.id).label('count')
        ).filter(
            and_(
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            )
        ).group_by(Transaction.status).all()
        
        # Calculate totals
        total_amount = db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
                Transaction.status == TransactionStatus.COMPLETED
            )
        ).scalar() or Decimal('0.00')
        
        # Failed transaction rate
        failed_count = db.query(Transaction).filter(
            and_(
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
                Transaction.status == TransactionStatus.FAILED
            )
        ).count()
        
        failure_rate = (failed_count / total_transactions * 100) if total_transactions > 0 else 0
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "totals": {
                "total_transactions": total_transactions,
                "total_amount": float(total_amount),
                "failure_rate": round(failure_rate, 2)
            },
            "by_type": [
                {
                    "type": type_stat.transaction_type.value,
                    "count": type_stat.count,
                    "total_amount": float(type_stat.total_amount or 0)
                }
                for type_stat in type_stats
            ],
            "by_status": [
                {
                    "status": status_stat.status.value,
                    "count": status_stat.count
                }
                for status_stat in status_stats
            ]
        }
    
    def get_high_value_transactions(self, threshold: Decimal = Decimal('100000.00'),
                                  start_date: datetime = None, end_date: datetime = None,
                                  db: Session = None) -> List[Transaction]:
        """Get high-value transactions for monitoring."""
        query = db.query(Transaction).filter(Transaction.amount >= threshold)
        
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)
        
        return query.order_by(desc(Transaction.amount)).limit(100).all()
    
    def detect_suspicious_patterns(self, customer_id: str = None, db: Session = None) -> List[Dict[str, Any]]:
        """Detect suspicious transaction patterns."""
        suspicious_transactions = []
        
        # Pattern 1: Multiple large withdrawals in a short time
        if customer_id:
            customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
            if customer:
                account_ids = db.query(Account.id).filter(Account.customer_id == customer.id).subquery()
                
                # Check for multiple large withdrawals in last 24 hours
                yesterday = datetime.utcnow() - timedelta(days=1)
                large_withdrawals = db.query(Transaction).filter(
                    and_(
                        Transaction.account_id.in_(account_ids),
                        Transaction.transaction_type == TransactionType.WITHDRAWAL,
                        Transaction.amount >= Decimal('25000.00'),
                        Transaction.transaction_date >= yesterday,
                        Transaction.status == TransactionStatus.COMPLETED
                    )
                ).all()
                
                if len(large_withdrawals) >= 3:
                    suspicious_transactions.append({
                        "type": "multiple_large_withdrawals",
                        "description": f"Customer {customer_id} made {len(large_withdrawals)} large withdrawals in 24 hours",
                        "transactions": [t.transaction_id for t in large_withdrawals],
                        "risk_level": "HIGH"
                    })
        
        # Pattern 2: Round number transactions (potential structuring)
        round_number_transactions = db.query(Transaction).filter(
            and_(
                Transaction.amount.in_([Decimal('10000.00'), Decimal('25000.00'), Decimal('50000.00')]),
                Transaction.transaction_date >= datetime.utcnow() - timedelta(days=7),
                Transaction.status == TransactionStatus.COMPLETED
            )
        ).limit(10).all()
        
        if round_number_transactions:
            suspicious_transactions.append({
                "type": "round_number_transactions",
                "description": f"Found {len(round_number_transactions)} round number transactions in last 7 days",
                "transactions": [t.transaction_id for t in round_number_transactions],
                "risk_level": "MEDIUM"
            })
        
        return suspicious_transactions
    
    def _generate_transaction_id(self, db: Session) -> str:
        """Generate a unique transaction ID."""
        today = datetime.now()
        prefix = f"TXN{today.strftime('%Y%m%d')}"
        
        # Find the last transaction ID for today
        last_transaction = db.query(Transaction).filter(
            Transaction.transaction_id.startswith(prefix)
        ).order_by(Transaction.transaction_id.desc()).first()
        
        if last_transaction:
            # Extract the sequence number and increment
            last_seq = int(last_transaction.transaction_id[-8:])
            new_seq = last_seq + 1
        else:
            new_seq = 1
        
        return f"{prefix}{new_seq:08d}"
