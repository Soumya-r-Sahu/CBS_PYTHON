"""
Account Service REST API Controllers
FastAPI-based REST endpoints for account management
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Path, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
import logging
import asyncio
from contextlib import asynccontextmanager

# Import application DTOs and services
from ..application.dto import (
    CreateAccountRequest, UpdateAccountRequest, DepositRequest, WithdrawRequest,
    TransferRequest, AccountSearchRequest, TransactionSearchRequest,
    AccountDTO, TransactionDTO, AccountSummaryDTO, TransactionSummaryDTO,
    PaginatedResponse, CreateAccountResponse, TransactionResponse, ErrorResponse,
    account_to_dto, transaction_to_dto
)

# Import domain entities and services
from ..domain.entities import (
    Account, Transaction, AccountType, AccountStatus, TransactionType,
    TransactionStatus, Money, AccountLimits
)

# Import infrastructure
from ..infrastructure.repositories import AccountRepository, TransactionRepository
from ..infrastructure.database import get_db_session, check_database_health, create_tables

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Application state
app_state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    # Startup
    logger.info("Starting Account Service...")
    
    # Initialize database
    try:
        create_tables()
        health = check_database_health()
        if health["status"] == "healthy":
            logger.info("Database initialized successfully")
        else:
            logger.error(f"Database health check failed: {health}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # Store repositories in app state
    app_state["account_repo"] = AccountRepository()
    app_state["transaction_repo"] = TransactionRepository()
    
    logger.info("Account Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Account Service...")


# Create FastAPI application
app = FastAPI(
    title="CBS Account Service",
    description="Core Banking System - Account Management Service",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection
def get_account_repository() -> AccountRepository:
    """Get account repository"""
    return app_state.get("account_repo", AccountRepository())


def get_transaction_repository() -> TransactionRepository:
    """Get transaction repository"""
    return app_state.get("transaction_repo", TransactionRepository())


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify JWT token (simplified for demo)
    In production, implement proper JWT validation
    """
    # TODO: Implement proper JWT validation
    return {"user_id": "system", "role": "admin"}


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions"""
    logger.error(f"ValueError: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error_code="INVALID_INPUT",
            message=str(exc),
            timestamp=datetime.utcnow()
        ).__dict__
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details={"error": str(exc)},
            timestamp=datetime.utcnow()
        ).__dict__
    )


# Health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health = check_database_health()
    
    return {
        "status": "healthy" if health["status"] == "healthy" else "unhealthy",
        "service": "account-service",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database": health
    }


@app.get("/health/ready")
async def readiness_check():
    """Readiness check endpoint"""
    try:
        health = check_database_health()
        if health["status"] != "healthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready"
            )
        
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {e}"
        )


@app.get("/health/live")
async def liveness_check():
    """Liveness check endpoint"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


# Account management endpoints
@app.post("/api/v1/accounts", response_model=CreateAccountResponse)
async def create_account(
    request: CreateAccountRequest,
    user: dict = Depends(verify_token),
    account_repo: AccountRepository = Depends(get_account_repository)
):
    """Create a new account"""
    try:
        # Create Account entity
        account = Account.create(
            customer_id=UUID(request.customer_id),
            account_type=AccountType(request.account_type),
            currency=request.currency,
            initial_deposit=request.initial_deposit,
            created_by=user["user_id"]
        )
        
        # Set limits if provided
        if any([request.daily_withdrawal_limit, request.daily_transfer_limit, 
                request.monthly_transaction_limit, request.minimum_balance]):
            account.update_limits(
                daily_withdrawal_limit=Money(request.daily_withdrawal_limit or Decimal('5000'), request.currency),
                daily_transfer_limit=Money(request.daily_transfer_limit or Decimal('10000'), request.currency),
                monthly_transaction_limit=Money(request.monthly_transaction_limit or Decimal('100000'), request.currency),
                minimum_balance=Money(request.minimum_balance or Decimal('0'), request.currency),
                maximum_balance=Money(request.maximum_balance, request.currency) if request.maximum_balance else None
            )
        
        # Set additional properties
        if request.interest_rate:
            account.interest_rate = request.interest_rate
        if request.maintenance_fee:
            account.maintenance_fee = Money(request.maintenance_fee, request.currency)
        if request.overdraft_limit:
            account.overdraft_limit = Money(request.overdraft_limit, request.currency)
        if request.overdraft_fee:
            account.overdraft_fee = Money(request.overdraft_fee, request.currency)
        if request.metadata:
            account.metadata = request.metadata
        if request.notes:
            account.notes = request.notes
        
        # Save account
        created_account = await account_repo.create(account)
        
        # Handle initial deposit if provided
        if request.initial_deposit and request.initial_deposit > 0:
            # Create deposit transaction
            transaction_repo = get_transaction_repository()
            deposit_transaction = Transaction.create_deposit(
                account_id=created_account.id,
                amount=Money(request.initial_deposit, request.currency),
                description="Initial deposit",
                created_by=user["user_id"]
            )
            
            # Update account balance
            created_account.deposit(Money(request.initial_deposit, request.currency))
            await account_repo.update(created_account)
            await transaction_repo.create(deposit_transaction)
        
        return CreateAccountResponse(
            account=account_to_dto(created_account),
            message="Account created successfully",
            success=True
        )
        
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create account: {e}"
        )


@app.get("/api/v1/accounts/{account_id}", response_model=AccountDTO)
async def get_account(
    account_id: UUID = Path(..., description="Account ID"),
    user: dict = Depends(verify_token),
    account_repo: AccountRepository = Depends(get_account_repository)
):
    """Get account by ID"""
    try:
        account = await account_repo.get_by_id(account_id)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account {account_id} not found"
            )
        
        return account_to_dto(account)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account: {e}"
        )


@app.get("/api/v1/accounts/number/{account_number}", response_model=AccountDTO)
async def get_account_by_number(
    account_number: str = Path(..., description="Account number"),
    user: dict = Depends(verify_token),
    account_repo: AccountRepository = Depends(get_account_repository)
):
    """Get account by account number"""
    try:
        account = await account_repo.get_by_account_number(account_number)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account {account_number} not found"
            )
        
        return account_to_dto(account)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting account by number {account_number}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account: {e}"
        )


@app.get("/api/v1/customers/{customer_id}/accounts", response_model=List[AccountDTO])
async def get_customer_accounts(
    customer_id: UUID = Path(..., description="Customer ID"),
    user: dict = Depends(verify_token),
    account_repo: AccountRepository = Depends(get_account_repository)
):
    """Get all accounts for a customer"""
    try:
        accounts = await account_repo.get_by_customer_id(customer_id)
        return [account_to_dto(account) for account in accounts]
        
    except Exception as e:
        logger.error(f"Error getting customer accounts {customer_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer accounts: {e}"
        )


@app.put("/api/v1/accounts/{account_id}", response_model=AccountDTO)
async def update_account(
    account_id: UUID,
    request: UpdateAccountRequest,
    user: dict = Depends(verify_token),
    account_repo: AccountRepository = Depends(get_account_repository)
):
    """Update account details"""
    try:
        # Get existing account
        account = await account_repo.get_by_id(account_id)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account {account_id} not found"
            )
        
        # Update fields
        if any([request.daily_withdrawal_limit, request.daily_transfer_limit, 
                request.monthly_transaction_limit, request.minimum_balance]):
            account.update_limits(
                daily_withdrawal_limit=Money(request.daily_withdrawal_limit or account.limits.daily_withdrawal_limit.amount, account.balance.currency),
                daily_transfer_limit=Money(request.daily_transfer_limit or account.limits.daily_transfer_limit.amount, account.balance.currency),
                monthly_transaction_limit=Money(request.monthly_transaction_limit or account.limits.monthly_transaction_limit.amount, account.balance.currency),
                minimum_balance=Money(request.minimum_balance or account.limits.minimum_balance.amount, account.balance.currency),
                maximum_balance=Money(request.maximum_balance, account.balance.currency) if request.maximum_balance else account.limits.maximum_balance
            )
        
        if request.interest_rate is not None:
            account.interest_rate = request.interest_rate
        if request.maintenance_fee is not None:
            account.maintenance_fee = Money(request.maintenance_fee, account.balance.currency)
        if request.overdraft_limit is not None:
            account.overdraft_limit = Money(request.overdraft_limit, account.balance.currency)
        if request.overdraft_fee is not None:
            account.overdraft_fee = Money(request.overdraft_fee, account.balance.currency)
        if request.metadata is not None:
            account.metadata = request.metadata
        if request.notes is not None:
            account.notes = request.notes
        
        account.updated_by = user["user_id"]
        
        # Save updates
        updated_account = await account_repo.update(account)
        
        return account_to_dto(updated_account)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update account: {e}"
        )


@app.post("/api/v1/accounts/search", response_model=PaginatedResponse)
async def search_accounts(
    request: AccountSearchRequest,
    user: dict = Depends(verify_token),
    account_repo: AccountRepository = Depends(get_account_repository)
):
    """Search accounts with filters"""
    try:
        accounts, total_count = await account_repo.search(
            customer_id=UUID(request.customer_id) if request.customer_id else None,
            account_type=AccountType(request.account_type) if request.account_type else None,
            status=AccountStatus(request.status) if request.status else None,
            min_balance=request.min_balance,
            max_balance=request.max_balance,
            created_after=request.created_after,
            created_before=request.created_before,
            limit=request.limit,
            offset=request.offset
        )
        
        return PaginatedResponse(
            items=[account_to_dto(account) for account in accounts],
            total_count=total_count,
            limit=request.limit,
            offset=request.offset,
            has_more=(request.offset + request.limit) < total_count
        )
        
    except Exception as e:
        logger.error(f"Error searching accounts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search accounts: {e}"
        )


# Transaction endpoints
@app.post("/api/v1/accounts/{account_id}/deposit", response_model=TransactionResponse)
async def deposit_funds(
    account_id: UUID,
    request: DepositRequest,
    user: dict = Depends(verify_token),
    account_repo: AccountRepository = Depends(get_account_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository)
):
    """Deposit funds to an account"""
    try:
        # Get account
        account = await account_repo.get_by_id(account_id)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account {account_id} not found"
            )
        
        # Create deposit transaction
        transaction = Transaction.create_deposit(
            account_id=account_id,
            amount=Money(request.amount, request.currency),
            description=request.description,
            reference_number=request.reference_number,
            channel=request.channel,
            location=request.location,
            metadata=request.metadata,
            created_by=user["user_id"]
        )
        
        # Update account balance
        account.deposit(Money(request.amount, request.currency))
        
        # Save changes
        await transaction_repo.create(transaction)
        updated_account = await account_repo.update(account)
        
        return TransactionResponse(
            transaction=transaction_to_dto(transaction),
            account_balance={"amount": updated_account.balance.amount, "currency": updated_account.balance.currency},
            message="Deposit successful",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error depositing funds to account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to deposit funds: {e}"
        )


@app.post("/api/v1/accounts/{account_id}/withdraw", response_model=TransactionResponse)
async def withdraw_funds(
    account_id: UUID,
    request: WithdrawRequest,
    user: dict = Depends(verify_token),
    account_repo: AccountRepository = Depends(get_account_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository)
):
    """Withdraw funds from an account"""
    try:
        # Get account
        account = await account_repo.get_by_id(account_id)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account {account_id} not found"
            )
        
        # Check if withdrawal is allowed
        withdrawal_amount = Money(request.amount, request.currency)
        if not account.can_withdraw(withdrawal_amount):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient funds or withdrawal limit exceeded"
            )
        
        # Create withdrawal transaction
        transaction = Transaction.create_withdrawal(
            account_id=account_id,
            amount=withdrawal_amount,
            description=request.description,
            reference_number=request.reference_number,
            channel=request.channel,
            location=request.location,
            metadata=request.metadata,
            created_by=user["user_id"]
        )
        
        # Update account balance
        account.withdraw(withdrawal_amount)
        
        # Save changes
        await transaction_repo.create(transaction)
        updated_account = await account_repo.update(account)
        
        return TransactionResponse(
            transaction=transaction_to_dto(transaction),
            account_balance={"amount": updated_account.balance.amount, "currency": updated_account.balance.currency},
            message="Withdrawal successful",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error withdrawing funds from account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to withdraw funds: {e}"
        )


@app.get("/api/v1/accounts/{account_id}/transactions", response_model=PaginatedResponse)
async def get_account_transactions(
    account_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    user: dict = Depends(verify_token),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository)
):
    """Get transactions for an account"""
    try:
        transactions, total_count = await transaction_repo.get_by_account_id(
            account_id=account_id,
            limit=limit,
            offset=offset,
            start_date=start_date,
            end_date=end_date
        )
        
        return PaginatedResponse(
            items=[transaction_to_dto(transaction) for transaction in transactions],
            total_count=total_count,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total_count
        )
        
    except Exception as e:
        logger.error(f"Error getting transactions for account {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get transactions: {e}"
        )


@app.get("/api/v1/accounts/{account_id}/summary", response_model=AccountSummaryDTO)
async def get_account_summary(
    account_id: UUID,
    user: dict = Depends(verify_token),
    account_repo: AccountRepository = Depends(get_account_repository)
):
    """Get account summary"""
    try:
        account = await account_repo.get_by_id(account_id)
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Account {account_id} not found"
            )
        
        summary = await account_repo.get_account_summary(account.customer_id)
        
        return AccountSummaryDTO(**summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting account summary for {account_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account summary: {e}"
        )


# Application entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
