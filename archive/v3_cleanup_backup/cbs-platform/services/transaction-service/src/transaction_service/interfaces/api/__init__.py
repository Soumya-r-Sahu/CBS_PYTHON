"""
Transaction Service REST API Controllers
FastAPI controllers for transaction processing and management
"""

from fastapi import FastAPI, HTTPException, Depends, Query, Path, Body, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
import logging

from platform.shared.auth import TokenData, get_current_user
from platform.shared.events import EventBus, DomainEvent
from ...domain.entities import Transaction, TransactionType, TransactionStatus, Money
from ...infrastructure.repositories import TransactionRepository, TransactionLimitRepository
from ...infrastructure.database import get_db_session

logger = logging.getLogger(__name__)

# Initialize security
security = HTTPBearer()

# Initialize event bus
event_bus = EventBus()

# Pydantic models for API requests/responses
from pydantic import BaseModel, Field
from typing import Union


class TransactionCreateRequest(BaseModel):
    """Request model for creating a transaction"""
    from_account_id: UUID = Field(..., description="Source account ID")
    to_account_id: Optional[UUID] = Field(None, description="Destination account ID")
    transaction_type: str = Field(..., description="Transaction type")
    amount: Decimal = Field(..., description="Transaction amount")
    currency: str = Field("USD", description="Currency code")
    description: Optional[str] = Field(None, description="Transaction description")
    reference_number: Optional[str] = Field(None, description="Reference number")
    category: Optional[str] = Field(None, description="Transaction category")
    channel: Optional[str] = Field("api", description="Transaction channel")
    location: Optional[str] = Field(None, description="Transaction location")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled execution time")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device information")


class TransactionUpdateRequest(BaseModel):
    """Request model for updating a transaction"""
    status: Optional[str] = Field(None, description="Transaction status")
    description: Optional[str] = Field(None, description="Transaction description")
    approval_notes: Optional[str] = Field(None, description="Approval notes")
    compliance_notes: Optional[str] = Field(None, description="Compliance notes")


class TransactionApprovalRequest(BaseModel):
    """Request model for transaction approval"""
    action: str = Field(..., description="Approval action: approve or reject")
    notes: Optional[str] = Field(None, description="Approval notes")


class BulkTransactionRequest(BaseModel):
    """Request model for bulk transaction processing"""
    transactions: List[TransactionCreateRequest] = Field(..., description="List of transactions")
    batch_name: Optional[str] = Field(None, description="Batch name")
    batch_type: str = Field("bulk_transfer", description="Batch type")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled execution time")


class TransactionResponse(BaseModel):
    """Response model for transaction data"""
    id: UUID
    transaction_id: str
    from_account_id: UUID
    to_account_id: Optional[UUID]
    transaction_type: str
    amount: Decimal
    currency: str
    status: str
    description: Optional[str]
    reference_number: Optional[str]
    category: Optional[str]
    transaction_fee: Decimal
    service_charge: Decimal
    tax_amount: Decimal
    exchange_rate: Optional[Decimal]
    processing_method: Optional[str]
    scheduled_at: Optional[datetime]
    processed_at: Optional[datetime]
    channel: Optional[str]
    location: Optional[str]
    approval_required: bool
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    approval_notes: Optional[str]
    risk_score: Optional[Decimal]
    aml_check_status: Optional[str]
    fraud_check_status: Optional[str]
    compliance_notes: Optional[str]
    reconciliation_status: str
    reconciled_at: Optional[datetime]
    reconciled_by: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]
    version: int

    @classmethod
    def from_domain_entity(cls, transaction: Transaction) -> "TransactionResponse":
        """Convert domain entity to response model"""
        return cls(
            id=transaction.id,
            transaction_id=transaction.transaction_id,
            from_account_id=transaction.from_account_id,
            to_account_id=transaction.to_account_id,
            transaction_type=transaction.transaction_type.value,
            amount=transaction.amount.amount,
            currency=transaction.amount.currency,
            status=transaction.status.value,
            description=transaction.description,
            reference_number=transaction.reference_number,
            category=transaction.category,
            transaction_fee=transaction.transaction_fee.amount if transaction.transaction_fee else Decimal('0.00'),
            service_charge=transaction.service_charge.amount if transaction.service_charge else Decimal('0.00'),
            tax_amount=transaction.tax_amount.amount if transaction.tax_amount else Decimal('0.00'),
            exchange_rate=transaction.exchange_rate,
            processing_method=transaction.processing_method,
            scheduled_at=transaction.scheduled_at,
            processed_at=transaction.processed_at,
            channel=transaction.channel,
            location=transaction.location,
            approval_required=transaction.approval_required,
            approved_by=transaction.approved_by,
            approved_at=transaction.approved_at,
            approval_notes=transaction.approval_notes,
            risk_score=transaction.risk_score,
            aml_check_status=transaction.aml_check_status,
            fraud_check_status=transaction.fraud_check_status,
            compliance_notes=transaction.compliance_notes,
            reconciliation_status=transaction.reconciliation_status,
            reconciled_at=transaction.reconciled_at,
            reconciled_by=transaction.reconciled_by,
            tags=transaction.tags or [],
            created_at=transaction.created_at,
            updated_at=transaction.updated_at,
            created_by=transaction.created_by,
            updated_by=transaction.updated_by,
            version=transaction.version
        )


class PaginatedTransactionResponse(BaseModel):
    """Paginated response for transactions"""
    transactions: List[TransactionResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


class TransactionSummaryResponse(BaseModel):
    """Response model for transaction summary"""
    account_id: Optional[str]
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    total_transactions: int
    total_amount: Decimal
    average_amount: Decimal
    min_amount: Decimal
    max_amount: Decimal
    total_fees: Decimal
    total_charges: Decimal
    total_tax: Decimal
    status_breakdown: Dict[str, Dict[str, Any]]


# API Controllers

def setup_transaction_routes(app: FastAPI):
    """Setup transaction service routes"""
    
    @app.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
    async def create_transaction(
        request: TransactionCreateRequest,
        current_user: TokenData = Depends(get_current_user)
    ):
        """Create a new transaction"""
        try:
            async with get_db_session() as session:
                transaction_repo = TransactionRepository(session)
                
                # Create domain entity
                transaction = Transaction(
                    from_account_id=request.from_account_id,
                    to_account_id=request.to_account_id,
                    transaction_type=TransactionType(request.transaction_type),
                    amount=Money(request.amount, request.currency),
                    status=TransactionStatus.PENDING,
                    description=request.description,
                    reference_number=request.reference_number,
                    category=request.category,
                    channel=request.channel,
                    location=request.location,
                    scheduled_at=request.scheduled_at,
                    device_info=request.device_info or {},
                    created_by=current_user.username
                )
                
                # Save transaction
                created_transaction = await transaction_repo.create(transaction)
                
                # Publish domain event
                event = DomainEvent(
                    event_type="transaction_created",
                    aggregate_id=str(created_transaction.id),
                    data={
                        "transaction_id": created_transaction.transaction_id,
                        "from_account_id": str(created_transaction.from_account_id),
                        "to_account_id": str(created_transaction.to_account_id) if created_transaction.to_account_id else None,
                        "transaction_type": created_transaction.transaction_type.value,
                        "amount": float(created_transaction.amount.amount),
                        "currency": created_transaction.amount.currency,
                        "channel": created_transaction.channel
                    },
                    user_id=current_user.user_id
                )
                await event_bus.publish(event)
                
                return TransactionResponse.from_domain_entity(created_transaction)
                
        except ValueError as e:
            logger.error(f"Validation error creating transaction: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.get("/transactions/{transaction_id}", response_model=TransactionResponse)
    async def get_transaction(
        transaction_id: UUID = Path(..., description="Transaction ID"),
        current_user: TokenData = Depends(get_current_user)
    ):
        """Get transaction by ID"""
        try:
            async with get_db_session() as session:
                transaction_repo = TransactionRepository(session)
                transaction = await transaction_repo.get_by_id(transaction_id)
                
                if not transaction:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Transaction not found"
                    )
                
                return TransactionResponse.from_domain_entity(transaction)
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting transaction {transaction_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.get("/transactions/reference/{reference_number}", response_model=TransactionResponse)
    async def get_transaction_by_reference(
        reference_number: str = Path(..., description="Reference number"),
        current_user: TokenData = Depends(get_current_user)
    ):
        """Get transaction by reference number"""
        try:
            async with get_db_session() as session:
                transaction_repo = TransactionRepository(session)
                
                # Search by reference number
                transactions, _ = await transaction_repo.search(
                    reference_number=reference_number,
                    limit=1
                )
                
                if not transactions:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Transaction not found"
                    )
                
                return TransactionResponse.from_domain_entity(transactions[0])
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting transaction by reference {reference_number}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.get("/accounts/{account_id}/transactions", response_model=PaginatedTransactionResponse)
    async def get_account_transactions(
        account_id: UUID = Path(..., description="Account ID"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Page size"),
        start_date: Optional[datetime] = Query(None, description="Start date"),
        end_date: Optional[datetime] = Query(None, description="End date"),
        transaction_type: Optional[str] = Query(None, description="Transaction type"),
        status: Optional[str] = Query(None, description="Transaction status"),
        current_user: TokenData = Depends(get_current_user)
    ):
        """Get transactions for an account"""
        try:
            async with get_db_session() as session:
                transaction_repo = TransactionRepository(session)
                
                offset = (page - 1) * page_size
                
                transactions, total_count = await transaction_repo.get_by_account_id(
                    account_id=account_id,
                    limit=page_size,
                    offset=offset,
                    start_date=start_date,
                    end_date=end_date,
                    transaction_type=TransactionType(transaction_type) if transaction_type else None,
                    status=TransactionStatus(status) if status else None
                )
                
                total_pages = (total_count + page_size - 1) // page_size
                
                return PaginatedTransactionResponse(
                    transactions=[TransactionResponse.from_domain_entity(transaction) for transaction in transactions],
                    total_count=total_count,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages
                )
                
        except ValueError as e:
            logger.error(f"Validation error getting account transactions: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error getting transactions for account {account_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.put("/transactions/{transaction_id}", response_model=TransactionResponse)
    async def update_transaction(
        transaction_id: UUID = Path(..., description="Transaction ID"),
        request: TransactionUpdateRequest = Body(...),
        current_user: TokenData = Depends(get_current_user)
    ):
        """Update a transaction"""
        try:
            async with get_db_session() as session:
                transaction_repo = TransactionRepository(session)
                transaction = await transaction_repo.get_by_id(transaction_id)
                
                if not transaction:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Transaction not found"
                    )
                
                # Update fields
                if request.status:
                    transaction.status = TransactionStatus(request.status)
                
                if request.description is not None:
                    transaction.description = request.description
                
                if request.approval_notes is not None:
                    transaction.approval_notes = request.approval_notes
                
                if request.compliance_notes is not None:
                    transaction.compliance_notes = request.compliance_notes
                
                transaction.updated_by = current_user.username
                
                # Save updates
                updated_transaction = await transaction_repo.update(transaction)
                
                # Publish domain event
                event = DomainEvent(
                    event_type="transaction_updated",
                    aggregate_id=str(updated_transaction.id),
                    data={
                        "transaction_id": updated_transaction.transaction_id,
                        "changes": request.dict(exclude_unset=True)
                    },
                    user_id=current_user.user_id
                )
                await event_bus.publish(event)
                
                return TransactionResponse.from_domain_entity(updated_transaction)
                
        except ValueError as e:
            logger.error(f"Validation error updating transaction: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating transaction {transaction_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.post("/transactions/{transaction_id}/approve", response_model=TransactionResponse)
    async def approve_transaction(
        transaction_id: UUID = Path(..., description="Transaction ID"),
        request: TransactionApprovalRequest = Body(...),
        current_user: TokenData = Depends(get_current_user)
    ):
        """Approve or reject a transaction"""
        try:
            async with get_db_session() as session:
                transaction_repo = TransactionRepository(session)
                transaction = await transaction_repo.get_by_id(transaction_id)
                
                if not transaction:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Transaction not found"
                    )
                
                if not transaction.approval_required:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Transaction does not require approval"
                    )
                
                # Update approval status
                if request.action.lower() == "approve":
                    transaction.status = TransactionStatus.APPROVED
                    transaction.approved_by = current_user.username
                    transaction.approved_at = datetime.utcnow()
                elif request.action.lower() == "reject":
                    transaction.status = TransactionStatus.REJECTED
                    transaction.approved_by = current_user.username
                    transaction.approved_at = datetime.utcnow()
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid approval action. Use 'approve' or 'reject'"
                    )
                
                transaction.approval_notes = request.notes
                transaction.updated_by = current_user.username
                
                # Save updates
                updated_transaction = await transaction_repo.update(transaction)
                
                # Publish domain event
                event = DomainEvent(
                    event_type="transaction_approval_processed",
                    aggregate_id=str(updated_transaction.id),
                    data={
                        "transaction_id": updated_transaction.transaction_id,
                        "action": request.action,
                        "approved_by": current_user.username,
                        "notes": request.notes
                    },
                    user_id=current_user.user_id
                )
                await event_bus.publish(event)
                
                return TransactionResponse.from_domain_entity(updated_transaction)
                
        except ValueError as e:
            logger.error(f"Validation error in transaction approval: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error approving transaction {transaction_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.get("/transactions/search", response_model=PaginatedTransactionResponse)
    async def search_transactions(
        from_account_id: Optional[UUID] = Query(None, description="From account ID"),
        to_account_id: Optional[UUID] = Query(None, description="To account ID"),
        transaction_type: Optional[str] = Query(None, description="Transaction type"),
        status: Optional[str] = Query(None, description="Transaction status"),
        min_amount: Optional[Decimal] = Query(None, description="Minimum amount"),
        max_amount: Optional[Decimal] = Query(None, description="Maximum amount"),
        start_date: Optional[datetime] = Query(None, description="Start date"),
        end_date: Optional[datetime] = Query(None, description="End date"),
        channel: Optional[str] = Query(None, description="Transaction channel"),
        category: Optional[str] = Query(None, description="Transaction category"),
        reference_number: Optional[str] = Query(None, description="Reference number"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Page size"),
        current_user: TokenData = Depends(get_current_user)
    ):
        """Search transactions with filters and pagination"""
        try:
            async with get_db_session() as session:
                transaction_repo = TransactionRepository(session)
                
                offset = (page - 1) * page_size
                
                transactions, total_count = await transaction_repo.search(
                    from_account_id=from_account_id,
                    to_account_id=to_account_id,
                    transaction_type=TransactionType(transaction_type) if transaction_type else None,
                    status=TransactionStatus(status) if status else None,
                    min_amount=min_amount,
                    max_amount=max_amount,
                    start_date=start_date,
                    end_date=end_date,
                    channel=channel,
                    category=category,
                    reference_number=reference_number,
                    limit=page_size,
                    offset=offset
                )
                
                total_pages = (total_count + page_size - 1) // page_size
                
                return PaginatedTransactionResponse(
                    transactions=[TransactionResponse.from_domain_entity(transaction) for transaction in transactions],
                    total_count=total_count,
                    page=page,
                    page_size=page_size,
                    total_pages=total_pages
                )
                
        except ValueError as e:
            logger.error(f"Validation error searching transactions: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error searching transactions: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.get("/transactions/summary", response_model=TransactionSummaryResponse)
    async def get_transaction_summary(
        account_id: Optional[UUID] = Query(None, description="Account ID"),
        start_date: Optional[datetime] = Query(None, description="Start date"),
        end_date: Optional[datetime] = Query(None, description="End date"),
        transaction_type: Optional[str] = Query(None, description="Transaction type"),
        current_user: TokenData = Depends(get_current_user)
    ):
        """Get transaction summary statistics"""
        try:
            async with get_db_session() as session:
                transaction_repo = TransactionRepository(session)
                
                summary = await transaction_repo.get_transaction_summary(
                    account_id=account_id,
                    start_date=start_date,
                    end_date=end_date,
                    transaction_type=TransactionType(transaction_type) if transaction_type else None
                )
                
                return TransactionSummaryResponse(**summary)
                
        except ValueError as e:
            logger.error(f"Validation error getting transaction summary: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error getting transaction summary: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    
    @app.get("/transactions/pending", response_model=List[TransactionResponse])
    async def get_pending_transactions(
        limit: int = Query(100, ge=1, le=1000, description="Maximum number of transactions"),
        scheduled_before: Optional[datetime] = Query(None, description="Scheduled before date"),
        current_user: TokenData = Depends(get_current_user)
    ):
        """Get pending transactions for processing"""
        try:
            async with get_db_session() as session:
                transaction_repo = TransactionRepository(session)
                
                transactions = await transaction_repo.get_pending_transactions(
                    limit=limit,
                    scheduled_before=scheduled_before
                )
                
                return [TransactionResponse.from_domain_entity(transaction) for transaction in transactions]
                
        except Exception as e:
            logger.error(f"Error getting pending transactions: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )


# Health check
def setup_health_routes(app: FastAPI):
    """Setup health check routes"""
    
    @app.get("/health")
    async def health_check():
        """Service health check"""
        try:
            from ...infrastructure.database import check_database_health
            db_health = check_database_health()
            
            return {
                "status": "healthy" if db_health["status"] == "healthy" else "unhealthy",
                "service": "transaction-service",
                "version": "2.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "database": db_health
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "transaction-service",
                "version": "2.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }


def create_transaction_service_app() -> FastAPI:
    """Create and configure the Transaction Service FastAPI application"""
    
    app = FastAPI(
        title="CBS Transaction Service",
        description="Core Banking System - Transaction Processing Service",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Setup routes
    setup_transaction_routes(app)
    setup_health_routes(app)
    
    return app


__all__ = [
    "create_transaction_service_app",
    "TransactionCreateRequest",
    "TransactionUpdateRequest",
    "TransactionApprovalRequest",
    "BulkTransactionRequest",
    "TransactionResponse",
    "PaginatedTransactionResponse",
    "TransactionSummaryResponse"
]
