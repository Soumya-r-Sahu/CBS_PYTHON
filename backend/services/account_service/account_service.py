"""
Account Service for Core Banking System V3.0

This service handles all account management operations including:
- Account creation and management
- Account balance operations
- Account status management
- Account limits and settings
- Account statements and history
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..models.account import Account, AccountType
from ..models.customer import Customer
from ..models.transaction import Transaction, TransactionType, TransactionStatus
from ..database.connection import get_db_session

class AccountService:
    """Account management service."""
    
    def __init__(self):
        """Initialize the account service."""
        pass
    
    def create_account(self, customer_id: str, account_type: AccountType, 
                      initial_deposit: Decimal = Decimal('0.00'), 
                      branch_code: str = "001", db: Session = None) -> Account:
        """Create a new account for a customer."""
        # Get customer
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            raise ValueError("Customer not found")
        
        # Check if customer already has this type of account
        existing_account = db.query(Account).filter(
            and_(
                Account.customer_id == customer.id,
                Account.account_type == account_type,
                Account.status == "ACTIVE"
            )
        ).first()
        
        if existing_account and account_type in [AccountType.SAVINGS, AccountType.CURRENT]:
            raise ValueError(f"Customer already has an active {account_type.value} account")
        
        # Generate account number
        account_number = self._generate_account_number(account_type, branch_code, db)
        
        # Generate IFSC code (basic format)
        ifsc_code = f"CBS0{branch_code}"
        
        # Set default limits based on account type
        daily_withdrawal_limit, daily_transfer_limit = self._get_default_limits(account_type)
        
        # Create account
        account = Account(
            account_number=account_number,
            account_type=account_type,
            balance=initial_deposit,
            branch_code=branch_code,
            ifsc_code=ifsc_code,
            daily_withdrawal_limit=daily_withdrawal_limit,
            daily_transfer_limit=daily_transfer_limit,
            customer_id=customer.id,
            opened_date=datetime.utcnow(),
            last_transaction_date=datetime.utcnow() if initial_deposit > 0 else None
        )
        
        db.add(account)
        db.commit()
        db.refresh(account)
        
        # Create initial deposit transaction if amount > 0
        if initial_deposit > 0:
            self._create_transaction(
                account=account,
                transaction_type=TransactionType.DEPOSIT,
                amount=initial_deposit,
                description="Initial deposit",
                db=db
            )
        
        return account
    
    def get_account(self, account_number: str, db: Session) -> Optional[Account]:
        """Get an account by account number."""
        return db.query(Account).filter(Account.account_number == account_number).first()
    
    def get_account_by_id(self, account_id: int, db: Session) -> Optional[Account]:
        """Get an account by internal ID."""
        return db.query(Account).filter(Account.id == account_id).first()
    
    def get_customer_accounts(self, customer_id: str, db: Session) -> List[Account]:
        """Get all accounts for a customer."""
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            return []
        
        return db.query(Account).filter(
            and_(
                Account.customer_id == customer.id,
                Account.is_active == True
            )
        ).all()
    
    def get_account_balance(self, account_number: str, db: Session) -> Dict[str, Any]:
        """Get account balance and details."""
        account = self.get_account(account_number, db)
        if not account:
            raise ValueError("Account not found")
        
        return {
            "account_number": account.account_number,
            "account_type": account.account_type.value,
            "balance": float(account.balance),
            "currency": account.currency,
            "status": account.status,
            "last_transaction_date": account.last_transaction_date.isoformat() if account.last_transaction_date else None,
            "daily_withdrawal_limit": float(account.daily_withdrawal_limit),
            "daily_transfer_limit": float(account.daily_transfer_limit)
        }
    
    def deposit(self, account_number: str, amount: Decimal, description: str = None, db: Session = None) -> Transaction:
        """Deposit money to an account."""
        account = self.get_account(account_number, db)
        if not account:
            raise ValueError("Account not found")
        
        if account.status != "ACTIVE":
            raise ValueError("Account is not active")
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Update account balance
        account.balance += amount
        account.last_transaction_date = datetime.utcnow()
        
        # Create transaction record
        transaction = self._create_transaction(
            account=account,
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            description=description or "Deposit",
            db=db
        )
        
        db.commit()
        return transaction
    
    def withdraw(self, account_number: str, amount: Decimal, description: str = None, db: Session = None) -> Transaction:
        """Withdraw money from an account."""
        account = self.get_account(account_number, db)
        if not account:
            raise ValueError("Account not found")
        
        if account.status != "ACTIVE":
            raise ValueError("Account is not active")
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if account.balance < amount:
            raise ValueError("Insufficient balance")
        
        # Check daily withdrawal limit
        if not self._check_daily_withdrawal_limit(account, amount, db):
            raise ValueError("Daily withdrawal limit exceeded")
        
        # Update account balance
        account.balance -= amount
        account.last_transaction_date = datetime.utcnow()
        
        # Create transaction record
        transaction = self._create_transaction(
            account=account,
            transaction_type=TransactionType.WITHDRAWAL,
            amount=amount,
            description=description or "Withdrawal",
            db=db
        )
        
        db.commit()
        return transaction
    
    def transfer(self, from_account_number: str, to_account_number: str, 
                amount: Decimal, description: str = None, db: Session = None) -> Dict[str, Transaction]:
        """Transfer money between accounts."""
        from_account = self.get_account(from_account_number, db)
        to_account = self.get_account(to_account_number, db)
        
        if not from_account:
            raise ValueError("Source account not found")
        if not to_account:
            raise ValueError("Destination account not found")
        
        if from_account.status != "ACTIVE":
            raise ValueError("Source account is not active")
        if to_account.status != "ACTIVE":
            raise ValueError("Destination account is not active")
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if from_account.balance < amount:
            raise ValueError("Insufficient balance")
        
        # Check daily transfer limit
        if not self._check_daily_transfer_limit(from_account, amount, db):
            raise ValueError("Daily transfer limit exceeded")
        
        # Update balances
        from_account.balance -= amount
        to_account.balance += amount
        
        transaction_time = datetime.utcnow()
        from_account.last_transaction_date = transaction_time
        to_account.last_transaction_date = transaction_time
        
        # Create transaction records
        debit_transaction = self._create_transaction(
            account=from_account,
            transaction_type=TransactionType.TRANSFER,
            amount=amount,
            description=f"Transfer to {to_account_number}: {description}" if description else f"Transfer to {to_account_number}",
            to_account_number=to_account_number,
            db=db
        )
        
        credit_transaction = self._create_transaction(
            account=to_account,
            transaction_type=TransactionType.DEPOSIT,
            amount=amount,
            description=f"Transfer from {from_account_number}: {description}" if description else f"Transfer from {from_account_number}",
            reference_number=debit_transaction.transaction_id,
            db=db
        )
        
        db.commit()
        
        return {
            "debit_transaction": debit_transaction,
            "credit_transaction": credit_transaction
        }
    
    def get_account_statement(self, account_number: str, start_date: datetime = None, 
                            end_date: datetime = None, limit: int = 50, db: Session = None) -> Dict[str, Any]:
        """Get account statement with transactions."""
        account = self.get_account(account_number, db)
        if not account:
            raise ValueError("Account not found")
        
        # Set default date range (last 30 days if not specified)
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Get transactions
        query = db.query(Transaction).filter(
            and_(
                Transaction.account_id == account.id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            )
        ).order_by(desc(Transaction.transaction_date))
        
        transactions = query.limit(limit).all()
        
        # Calculate summary
        total_credits = sum(t.amount for t in transactions if t.transaction_type in [TransactionType.DEPOSIT])
        total_debits = sum(t.amount for t in transactions if t.transaction_type in [TransactionType.WITHDRAWAL, TransactionType.TRANSFER])
        
        return {
            "account": {
                "account_number": account.account_number,
                "account_type": account.account_type.value,
                "current_balance": float(account.balance),
                "currency": account.currency
            },
            "statement_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "summary": {
                "total_credits": float(total_credits),
                "total_debits": float(total_debits),
                "transaction_count": len(transactions)
            },
            "transactions": [
                {
                    "transaction_id": t.transaction_id,
                    "date": t.transaction_date.isoformat(),
                    "type": t.transaction_type.value,
                    "amount": float(t.amount),
                    "description": t.description,
                    "reference_number": t.reference_number,
                    "status": t.status.value,
                    "to_account": t.to_account_number
                }
                for t in transactions
            ]
        }
    
    def update_account_limits(self, account_number: str, daily_withdrawal_limit: Decimal = None,
                            daily_transfer_limit: Decimal = None, db: Session = None) -> Account:
        """Update account limits."""
        account = self.get_account(account_number, db)
        if not account:
            raise ValueError("Account not found")
        
        if daily_withdrawal_limit is not None:
            account.daily_withdrawal_limit = daily_withdrawal_limit
        
        if daily_transfer_limit is not None:
            account.daily_transfer_limit = daily_transfer_limit
        
        db.commit()
        db.refresh(account)
        
        return account
    
    def close_account(self, account_number: str, db: Session) -> bool:
        """Close an account."""
        account = self.get_account(account_number, db)
        if not account:
            raise ValueError("Account not found")
        
        if account.balance > 0:
            raise ValueError("Cannot close account with positive balance")
        
        account.status = "CLOSED"
        account.is_active = False
        db.commit()
        
        return True
    
    def _generate_account_number(self, account_type: AccountType, branch_code: str, db: Session) -> str:
        """Generate a unique account number."""
        today = datetime.now()
        
        # Account type prefixes
        type_prefixes = {
            AccountType.SAVINGS: "SAV",
            AccountType.CURRENT: "CUR",
            AccountType.FIXED_DEPOSIT: "FD",
            AccountType.LOAN: "LON",
            AccountType.CREDIT: "CC"
        }
        
        prefix = f"{type_prefixes[account_type]}{branch_code}{today.strftime('%y%m')}"
        
        # Find the last account number for this prefix
        last_account = db.query(Account).filter(
            Account.account_number.startswith(prefix)
        ).order_by(Account.account_number.desc()).first()
        
        if last_account:
            # Extract the sequence number and increment
            last_seq = int(last_account.account_number[-6:])
            new_seq = last_seq + 1
        else:
            new_seq = 1
        
        return f"{prefix}{new_seq:06d}"
    
    def _get_default_limits(self, account_type: AccountType) -> tuple:
        """Get default limits for account type."""
        limits = {
            AccountType.SAVINGS: (Decimal('50000.00'), Decimal('100000.00')),
            AccountType.CURRENT: (Decimal('100000.00'), Decimal('500000.00')),
            AccountType.FIXED_DEPOSIT: (Decimal('0.00'), Decimal('0.00')),
            AccountType.LOAN: (Decimal('0.00'), Decimal('0.00')),
            AccountType.CREDIT: (Decimal('25000.00'), Decimal('50000.00'))
        }
        return limits.get(account_type, (Decimal('25000.00'), Decimal('50000.00')))
    
    def _check_daily_withdrawal_limit(self, account: Account, amount: Decimal, db: Session) -> bool:
        """Check if withdrawal is within daily limit."""
        today = datetime.utcnow().date()
        
        # Get today's withdrawals
        today_withdrawals = db.query(Transaction).filter(
            and_(
                Transaction.account_id == account.id,
                Transaction.transaction_type == TransactionType.WITHDRAWAL,
                Transaction.transaction_date >= today,
                Transaction.status == TransactionStatus.COMPLETED
            )
        ).all()
        
        total_withdrawn_today = sum(t.amount for t in today_withdrawals)
        return (total_withdrawn_today + amount) <= account.daily_withdrawal_limit
    
    def _check_daily_transfer_limit(self, account: Account, amount: Decimal, db: Session) -> bool:
        """Check if transfer is within daily limit."""
        today = datetime.utcnow().date()
        
        # Get today's transfers
        today_transfers = db.query(Transaction).filter(
            and_(
                Transaction.account_id == account.id,
                Transaction.transaction_type == TransactionType.TRANSFER,
                Transaction.transaction_date >= today,
                Transaction.status == TransactionStatus.COMPLETED
            )
        ).all()
        
        total_transferred_today = sum(t.amount for t in today_transfers)
        return (total_transferred_today + amount) <= account.daily_transfer_limit
    
    def _create_transaction(self, account: Account, transaction_type: TransactionType,
                          amount: Decimal, description: str, to_account_number: str = None,
                          reference_number: str = None, db: Session = None) -> Transaction:
        """Create a transaction record."""
        transaction_id = self._generate_transaction_id(db)
        
        transaction = Transaction(
            transaction_id=transaction_id,
            account_id=account.id,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            to_account_number=to_account_number,
            reference_number=reference_number,
            status=TransactionStatus.COMPLETED
        )
        
        db.add(transaction)
        return transaction
    
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
