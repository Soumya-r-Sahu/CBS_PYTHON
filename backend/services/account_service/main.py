"""
Account Service for Core Banking System V3.0

This service handles account management, balance operations, and account-related transactions.
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
import uuid
import random
import string

from ..shared.database import get_db_session
from ..shared.models import Account, Customer, Transaction, AccountType, AccountStatus, TransactionType, TransactionStatus
from ..auth_service.main import get_current_user, User

app = FastAPI(
    title="Account Service",
    description="Core Banking Account Management Service",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class AccountCreateRequest(BaseModel):
    customer_id: int
    account_type: AccountType
    initial_deposit: Optional[Decimal] = Field(Decimal('0.00'), ge=0)
    branch_code: str
    ifsc_code: str

class AccountResponse(BaseModel):
    id: int
    account_number: str
    account_type: str
    balance: Decimal
    available_balance: Decimal
    currency: str
    status: str
    customer_id: int
    customer_name: Optional[str] = None
    branch_code: str
    ifsc_code: str
    created_at: datetime

class AccountBalanceResponse(BaseModel):
    account_number: str
    balance: Decimal
    available_balance: Decimal
    currency: str
    last_transaction_date: Optional[datetime] = None

class DepositRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    description: str
    reference_number: Optional[str] = None

class WithdrawalRequest(BaseModel):
    amount: Decimal = Field(..., gt=0)
    description: str
    reference_number: Optional[str] = None

class TransferRequest(BaseModel):
    to_account_number: str
    amount: Decimal = Field(..., gt=0)
    description: str
    to_beneficiary_name: Optional[str] = None
    reference_number: Optional[str] = None

class TransactionResponse(BaseModel):
    transaction_id: str
    account_number: str
    transaction_type: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    description: str
    status: str
    created_at: datetime
    processed_at: Optional[datetime] = None

# Utility Functions
def generate_account_number() -> str:
    """Generate unique account number"""
    prefix = "AC"
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = ''.join(random.choices(string.digits, k=6))
    return f"{prefix}-{date_part}-{random_part}"

def generate_transaction_id() -> str:
    """Generate unique transaction ID"""
    prefix = "TXN"
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = ''.join(random.choices(string.digits + string.ascii_uppercase, k=8))
    return f"{prefix}-{date_part}-{random_part}"

# Account Endpoints
@app.post("/accounts", response_model=AccountResponse)
async def create_account(
    request: AccountCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Create new bank account"""
    # Check if user has permission to create accounts
    if not current_user.is_employee():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only bank employees can create accounts"
        )
    
    # Verify customer exists
    customer = db.query(Customer).filter(Customer.id == request.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Generate unique account number
    account_number = generate_account_number()
    while db.query(Account).filter(Account.account_number == account_number).first():
        account_number = generate_account_number()
    
    # Create account
    account = Account(
        account_number=account_number,
        account_type=request.account_type,
        customer_id=request.customer_id,
        balance=request.initial_deposit,
        available_balance=request.initial_deposit,
        branch_code=request.branch_code,
        ifsc_code=request.ifsc_code,
        status=AccountStatus.ACTIVE
    )
    
    db.add(account)
    db.commit()
    db.refresh(account)
    
    # Create initial deposit transaction if amount > 0
    if request.initial_deposit > 0:
        transaction = Transaction(
            transaction_id=generate_transaction_id(),
            account_id=account.id,
            transaction_type=TransactionType.DEPOSIT,
            amount=request.initial_deposit,
            balance_before=Decimal('0.00'),
            balance_after=request.initial_deposit,
            description="Initial deposit",
            status=TransactionStatus.COMPLETED,
            processed_at=datetime.utcnow(),
            processed_by=current_user.username
        )
        db.add(transaction)
        db.commit()
    
    return AccountResponse(
        id=account.id,
        account_number=account.account_number,
        account_type=account.account_type.value,
        balance=account.balance,
        available_balance=account.available_balance,
        currency=account.currency,
        status=account.status.value,
        customer_id=account.customer_id,
        customer_name=customer.get_full_name(),
        branch_code=account.branch_code,
        ifsc_code=account.ifsc_code,
        created_at=account.created_at
    )

@app.get("/accounts/{account_number}", response_model=AccountResponse)
async def get_account(
    account_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get account details"""
    account = db.query(Account).filter(Account.account_number == account_number).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Check access permissions
    if not current_user.is_employee():
        # Customers can only view their own accounts
        # This would require customer-user relationship which we haven't implemented yet
        pass
    
    customer = db.query(Customer).filter(Customer.id == account.customer_id).first()
    
    return AccountResponse(
        id=account.id,
        account_number=account.account_number,
        account_type=account.account_type.value,
        balance=account.balance,
        available_balance=account.available_balance,
        currency=account.currency,
        status=account.status.value,
        customer_id=account.customer_id,
        customer_name=customer.get_full_name() if customer else None,
        branch_code=account.branch_code,
        ifsc_code=account.ifsc_code,
        created_at=account.created_at
    )

@app.get("/accounts/{account_number}/balance", response_model=AccountBalanceResponse)
async def get_account_balance(
    account_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get account balance"""
    account = db.query(Account).filter(Account.account_number == account_number).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return AccountBalanceResponse(
        account_number=account.account_number,
        balance=account.balance,
        available_balance=account.available_balance,
        currency=account.currency,
        last_transaction_date=account.last_transaction_date
    )

@app.post("/accounts/{account_number}/deposit", response_model=TransactionResponse)
async def deposit_money(
    account_number: str,
    request: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Deposit money to account"""
    # Check permissions
    if not current_user.is_employee():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only bank employees can process deposits"
        )
    
    # Get account
    account = db.query(Account).filter(Account.account_number == account_number).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    if account.status != AccountStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not active"
        )
    
    # Record balance before transaction
    balance_before = account.balance
    
    # Update account balance
    account.balance += request.amount
    account.available_balance += request.amount
    account.last_transaction_date = datetime.utcnow()
    
    # Create transaction record
    transaction = Transaction(
        transaction_id=generate_transaction_id(),
        account_id=account.id,
        transaction_type=TransactionType.DEPOSIT,
        amount=request.amount,
        balance_before=balance_before,
        balance_after=account.balance,
        description=request.description,
        reference_number=request.reference_number,
        status=TransactionStatus.COMPLETED,
        processed_at=datetime.utcnow(),
        processed_by=current_user.username
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return TransactionResponse(
        transaction_id=transaction.transaction_id,
        account_number=account.account_number,
        transaction_type=transaction.transaction_type.value,
        amount=transaction.amount,
        balance_before=transaction.balance_before,
        balance_after=transaction.balance_after,
        description=transaction.description,
        status=transaction.status.value,
        created_at=transaction.created_at,
        processed_at=transaction.processed_at
    )

@app.post("/accounts/{account_number}/withdraw", response_model=TransactionResponse)
async def withdraw_money(
    account_number: str,
    request: WithdrawalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Withdraw money from account"""
    # Check permissions
    if not current_user.is_employee():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only bank employees can process withdrawals"
        )
    
    # Get account
    account = db.query(Account).filter(Account.account_number == account_number).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    if account.status != AccountStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not active"
        )
    
    # Check if withdrawal is possible
    if not account.can_withdraw(request.amount):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance or amount exceeds daily limit"
        )
    
    # Record balance before transaction
    balance_before = account.balance
    
    # Update account balance
    account.balance -= request.amount
    account.available_balance -= request.amount
    account.last_transaction_date = datetime.utcnow()
    
    # Create transaction record
    transaction = Transaction(
        transaction_id=generate_transaction_id(),
        account_id=account.id,
        transaction_type=TransactionType.WITHDRAWAL,
        amount=request.amount,
        balance_before=balance_before,
        balance_after=account.balance,
        description=request.description,
        reference_number=request.reference_number,
        status=TransactionStatus.COMPLETED,
        processed_at=datetime.utcnow(),
        processed_by=current_user.username
    )
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return TransactionResponse(
        transaction_id=transaction.transaction_id,
        account_number=account.account_number,
        transaction_type=transaction.transaction_type.value,
        amount=transaction.amount,
        balance_before=transaction.balance_before,
        balance_after=transaction.balance_after,
        description=transaction.description,
        status=transaction.status.value,
        created_at=transaction.created_at,
        processed_at=transaction.processed_at
    )

@app.get("/accounts/{account_number}/transactions", response_model=List[TransactionResponse])
async def get_account_transactions(
    account_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """Get account transaction history"""
    account = db.query(Account).filter(Account.account_number == account_number).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    transactions = db.query(Transaction).filter(
        Transaction.account_id == account.id
    ).order_by(desc(Transaction.created_at)).offset(offset).limit(limit).all()
    
    return [
        TransactionResponse(
            transaction_id=txn.transaction_id,
            account_number=account.account_number,
            transaction_type=txn.transaction_type.value,
            amount=txn.amount,
            balance_before=txn.balance_before,
            balance_after=txn.balance_after,
            description=txn.description,
            status=txn.status.value,
            created_at=txn.created_at,
            processed_at=txn.processed_at
        )
        for txn in transactions
    ]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "account-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
