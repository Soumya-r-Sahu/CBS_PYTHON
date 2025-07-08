"""
Account Service - Core Banking System V3.0

This microservice handles all account-related operations including:
- Account creation and management
- Account operations (deposits, withdrawals)
- Account balance and statement services
- Account status management

Architecture: Clean Architecture with Domain-Driven Design
Technology: FastAPI with async/await support
Database: PostgreSQL with SQLAlchemy ORM
Security: JWT authentication with role-based access control
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Account Service",
    description="Core Banking Account Management Service",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Security
security = HTTPBearer()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://banking.domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# Domain Models (Business Entities)
# ================================

class AccountType(str):
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    FIXED_DEPOSIT = "FIXED_DEPOSIT"
    RECURRING_DEPOSIT = "RECURRING_DEPOSIT"

class AccountStatus(str):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    FROZEN = "FROZEN"
    CLOSED = "CLOSED"

class TransactionType(str):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"

# ================================
# Request/Response Models
# ================================

class CreateAccountRequest(BaseModel):
    customer_id: str = Field(..., description="Customer UUID")
    account_type: AccountType = Field(..., description="Type of account")
    initial_deposit: Decimal = Field(0, ge=0, description="Initial deposit amount")
    currency: str = Field("USD", description="Account currency")
    branch_code: Optional[str] = Field(None, description="Branch code")

class AccountResponse(BaseModel):
    account_id: str
    account_number: str
    customer_id: str
    account_type: AccountType
    balance: Decimal
    available_balance: Decimal
    currency: str
    status: AccountStatus
    created_at: datetime
    updated_at: datetime
    branch_code: Optional[str]
    interest_rate: Optional[Decimal]

class DepositRequest(BaseModel):
    account_id: str
    amount: Decimal = Field(..., gt=0, description="Deposit amount")
    description: Optional[str] = Field(None, description="Transaction description")
    reference: Optional[str] = Field(None, description="External reference")

class WithdrawalRequest(BaseModel):
    account_id: str
    amount: Decimal = Field(..., gt=0, description="Withdrawal amount")
    description: Optional[str] = Field(None, description="Transaction description")
    reference: Optional[str] = Field(None, description="External reference")

class TransactionResponse(BaseModel):
    transaction_id: str
    account_id: str
    transaction_type: TransactionType
    amount: Decimal
    balance_after: Decimal
    description: Optional[str]
    reference: Optional[str]
    timestamp: datetime
    status: str

class BalanceResponse(BaseModel):
    account_id: str
    current_balance: Decimal
    available_balance: Decimal
    currency: str
    last_updated: datetime

# ================================
# Authentication Dependency
# ================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract and validate JWT token"""
    try:
        # In production, validate JWT token here
        # For now, mock authentication
        token = credentials.credentials
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Mock user data
        return {
            "user_id": "user_123",
            "username": "test_user",
            "roles": ["customer", "admin"]
        }
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# ================================
# Mock Database Layer
# ================================

class AccountDatabase:
    """Mock database for demonstration. In production, use SQLAlchemy with PostgreSQL"""
    
    def __init__(self):
        self.accounts = {}
        self.transactions = {}
    
    def create_account(self, account_data: dict) -> dict:
        """Create a new account"""
        account_id = str(uuid.uuid4())
        account_number = f"ACC{uuid.uuid4().int % 10000000000:010d}"
        
        account = {
            "account_id": account_id,
            "account_number": account_number,
            "customer_id": account_data["customer_id"],
            "account_type": account_data["account_type"],
            "balance": account_data["initial_deposit"],
            "available_balance": account_data["initial_deposit"],
            "currency": account_data["currency"],
            "status": AccountStatus.ACTIVE,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "branch_code": account_data.get("branch_code"),
            "interest_rate": self._get_interest_rate(account_data["account_type"])
        }
        
        self.accounts[account_id] = account
        return account
    
    def get_account(self, account_id: str) -> Optional[dict]:
        """Get account by ID"""
        return self.accounts.get(account_id)
    
    def update_account_balance(self, account_id: str, new_balance: Decimal) -> bool:
        """Update account balance"""
        if account_id in self.accounts:
            self.accounts[account_id]["balance"] = new_balance
            self.accounts[account_id]["available_balance"] = new_balance
            self.accounts[account_id]["updated_at"] = datetime.utcnow()
            return True
        return False
    
    def record_transaction(self, transaction_data: dict) -> dict:
        """Record a transaction"""
        transaction_id = str(uuid.uuid4())
        transaction = {
            "transaction_id": transaction_id,
            **transaction_data,
            "timestamp": datetime.utcnow(),
            "status": "COMPLETED"
        }
        
        self.transactions[transaction_id] = transaction
        return transaction
    
    def get_account_transactions(self, account_id: str, limit: int = 50) -> List[dict]:
        """Get transactions for an account"""
        return [
            tx for tx in self.transactions.values() 
            if tx["account_id"] == account_id
        ][:limit]
    
    def _get_interest_rate(self, account_type: str) -> Decimal:
        """Get interest rate based on account type"""
        rates = {
            AccountType.SAVINGS: Decimal("3.5"),
            AccountType.CURRENT: Decimal("0.0"),
            AccountType.FIXED_DEPOSIT: Decimal("6.5"),
            AccountType.RECURRING_DEPOSIT: Decimal("5.5")
        }
        return rates.get(account_type, Decimal("0.0"))

# Initialize mock database
db = AccountDatabase()

# ================================
# API Endpoints
# ================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "service": "account-service",
        "status": "healthy",
        "version": "3.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/accounts", response_model=AccountResponse)
async def create_account(
    request: CreateAccountRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new account"""
    try:
        logger.info(f"Creating account for customer {request.customer_id}")
        
        # Business validation
        if request.initial_deposit < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Initial deposit cannot be negative"
            )
        
        # Create account
        account_data = request.dict()
        account = db.create_account(account_data)
        
        # Record initial deposit transaction if amount > 0
        if request.initial_deposit > 0:
            transaction_data = {
                "account_id": account["account_id"],
                "transaction_type": TransactionType.DEPOSIT,
                "amount": request.initial_deposit,
                "balance_after": request.initial_deposit,
                "description": "Initial deposit",
                "reference": "ACCOUNT_OPENING"
            }
            db.record_transaction(transaction_data)
        
        logger.info(f"Account created successfully: {account['account_id']}")
        return AccountResponse(**account)
        
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account"
        )

@app.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get account details"""
    try:
        account = db.get_account(account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        return AccountResponse(**account)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve account"
        )

@app.get("/accounts/{account_id}/balance", response_model=BalanceResponse)
async def get_account_balance(
    account_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get account balance"""
    try:
        account = db.get_account(account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        return BalanceResponse(
            account_id=account["account_id"],
            current_balance=account["balance"],
            available_balance=account["available_balance"],
            currency=account["currency"],
            last_updated=account["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve balance"
        )

@app.post("/accounts/{account_id}/deposit", response_model=TransactionResponse)
async def deposit_funds(
    account_id: str,
    request: DepositRequest,
    current_user: dict = Depends(get_current_user)
):
    """Deposit funds to account"""
    try:
        # Validate account exists
        account = db.get_account(account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Check account status
        if account["status"] != AccountStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is not active"
            )
        
        # Calculate new balance
        new_balance = account["balance"] + request.amount
        
        # Update account balance
        db.update_account_balance(account_id, new_balance)
        
        # Record transaction
        transaction_data = {
            "account_id": account_id,
            "transaction_type": TransactionType.DEPOSIT,
            "amount": request.amount,
            "balance_after": new_balance,
            "description": request.description or "Deposit",
            "reference": request.reference
        }
        transaction = db.record_transaction(transaction_data)
        
        logger.info(f"Deposit completed: {request.amount} to {account_id}")
        return TransactionResponse(**transaction)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing deposit: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process deposit"
        )

@app.post("/accounts/{account_id}/withdraw", response_model=TransactionResponse)
async def withdraw_funds(
    account_id: str,
    request: WithdrawalRequest,
    current_user: dict = Depends(get_current_user)
):
    """Withdraw funds from account"""
    try:
        # Validate account exists
        account = db.get_account(account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Check account status
        if account["status"] != AccountStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is not active"
            )
        
        # Check sufficient balance
        if account["available_balance"] < request.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance"
            )
        
        # Calculate new balance
        new_balance = account["balance"] - request.amount
        
        # Update account balance
        db.update_account_balance(account_id, new_balance)
        
        # Record transaction
        transaction_data = {
            "account_id": account_id,
            "transaction_type": TransactionType.WITHDRAWAL,
            "amount": request.amount,
            "balance_after": new_balance,
            "description": request.description or "Withdrawal",
            "reference": request.reference
        }
        transaction = db.record_transaction(transaction_data)
        
        logger.info(f"Withdrawal completed: {request.amount} from {account_id}")
        return TransactionResponse(**transaction)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing withdrawal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process withdrawal"
        )

@app.get("/accounts/{account_id}/transactions", response_model=List[TransactionResponse])
async def get_account_transactions(
    account_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get account transaction history"""
    try:
        # Validate account exists
        account = db.get_account(account_id)
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        
        # Get transactions
        transactions = db.get_account_transactions(account_id, limit)
        
        return [TransactionResponse(**tx) for tx in transactions]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transactions"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
