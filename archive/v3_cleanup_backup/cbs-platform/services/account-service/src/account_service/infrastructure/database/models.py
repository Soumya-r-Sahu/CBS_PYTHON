"""
Account Service Infrastructure - Database Models and Repository Implementation

This module provides:
- SQLAlchemy models for account domain
- Repository pattern implementation
- Database configuration and migrations
- Connection pooling and optimization
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from sqlalchemy import Column, String, DateTime, Integer, Boolean, Numeric, Text, JSON, ForeignKey, Index, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import QueuePool
import structlog

from ..domain.entities.account import Account, AccountType, AccountStatus
from ..domain.repositories.account_repository import AccountRepository

logger = structlog.get_logger(__name__)

Base = declarative_base()


class AccountModel(Base):
    """SQLAlchemy model for Account entity"""
    __tablename__ = 'accounts'
    
    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_number = Column(String(20), unique=True, nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    account_type = Column(String(20), nullable=False, index=True)
    currency = Column(String(3), nullable=False)
    
    # Balance fields
    balance = Column(Numeric(precision=15, scale=2), nullable=False, default=0)
    available_balance = Column(Numeric(precision=15, scale=2), nullable=False, default=0)
    hold_amount = Column(Numeric(precision=15, scale=2), nullable=False, default=0)
    
    # Status and configuration
    status = Column(String(20), nullable=False, default=AccountStatus.ACTIVE.value, index=True)
    interest_rate = Column(Numeric(precision=5, scale=4), default=0)
    overdraft_limit = Column(Numeric(precision=15, scale=2), default=0)
    minimum_balance = Column(Numeric(precision=15, scale=2), default=0)
    
    # Limits and settings
    daily_transaction_limit = Column(Numeric(precision=15, scale=2))
    monthly_transaction_limit = Column(Numeric(precision=15, scale=2))
    withdrawal_limit = Column(Numeric(precision=15, scale=2))
    
    # Metadata
    branch_code = Column(String(10))
    product_code = Column(String(20))
    account_purpose = Column(String(100))
    metadata = Column(JSON)
    
    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100))
    updated_by = Column(String(100))
    version = Column(Integer, nullable=False, default=1)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_account_customer_type', 'customer_id', 'account_type'),
        Index('idx_account_status_type', 'status', 'account_type'),
        Index('idx_account_created_at', 'created_at'),
        Index('idx_account_balance', 'balance'),
    )
    
    def to_domain(self) -> Account:
        """Convert SQLAlchemy model to domain entity"""
        return Account(
            id=str(self.id),
            account_number=self.account_number,
            customer_id=str(self.customer_id),
            account_type=AccountType(self.account_type),
            currency=self.currency,
            balance=self.balance,
            available_balance=self.available_balance,
            hold_amount=self.hold_amount,
            status=AccountStatus(self.status),
            interest_rate=float(self.interest_rate) if self.interest_rate else 0.0,
            overdraft_limit=self.overdraft_limit,
            minimum_balance=self.minimum_balance,
            daily_transaction_limit=self.daily_transaction_limit,
            monthly_transaction_limit=self.monthly_transaction_limit,
            withdrawal_limit=self.withdrawal_limit,
            branch_code=self.branch_code,
            product_code=self.product_code,
            account_purpose=self.account_purpose,
            metadata=self.metadata or {},
            created_at=self.created_at,
            updated_at=self.updated_at,
            created_by=self.created_by,
            updated_by=self.updated_by,
            version=self.version
        )
    
    @classmethod
    def from_domain(cls, account: Account) -> 'AccountModel':
        """Create SQLAlchemy model from domain entity"""
        return cls(
            id=uuid.UUID(account.id) if account.id else uuid.uuid4(),
            account_number=account.account_number,
            customer_id=uuid.UUID(account.customer_id),
            account_type=account.account_type.value,
            currency=account.currency,
            balance=account.balance,
            available_balance=account.available_balance,
            hold_amount=account.hold_amount,
            status=account.status.value,
            interest_rate=Decimal(str(account.interest_rate)),
            overdraft_limit=account.overdraft_limit,
            minimum_balance=account.minimum_balance,
            daily_transaction_limit=account.daily_transaction_limit,
            monthly_transaction_limit=account.monthly_transaction_limit,
            withdrawal_limit=account.withdrawal_limit,
            branch_code=account.branch_code,
            product_code=account.product_code,
            account_purpose=account.account_purpose,
            metadata=account.metadata,
            created_at=account.created_at,
            updated_at=account.updated_at,
            created_by=account.created_by,
            updated_by=account.updated_by,
            version=account.version
        )


class AccountHoldModel(Base):
    """SQLAlchemy model for account holds"""
    __tablename__ = 'account_holds'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey('accounts.id'), nullable=False, index=True)
    amount = Column(Numeric(precision=15, scale=2), nullable=False)
    reason = Column(String(100), nullable=False)
    reference = Column(String(100))
    expires_at = Column(DateTime)
    status = Column(String(20), nullable=False, default='active')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_by = Column(String(100))
    
    # Relationship
    account = relationship("AccountModel", backref="holds")
    
    __table_args__ = (
        Index('idx_hold_account_status', 'account_id', 'status'),
        Index('idx_hold_expires_at', 'expires_at'),
    )


class AccountTransactionLimitModel(Base):
    """SQLAlchemy model for account transaction limits"""
    __tablename__ = 'account_transaction_limits'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = Column(UUID(as_uuid=True), ForeignKey('accounts.id'), nullable=False, index=True)
    limit_type = Column(String(50), nullable=False)  # daily, monthly, per_transaction
    transaction_type = Column(String(50), nullable=False)  # withdrawal, transfer, payment
    limit_amount = Column(Numeric(precision=15, scale=2), nullable=False)
    used_amount = Column(Numeric(precision=15, scale=2), nullable=False, default=0)
    reset_date = Column(DateTime)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    account = relationship("AccountModel", backref="transaction_limits")
    
    __table_args__ = (
        Index('idx_limit_account_type', 'account_id', 'limit_type', 'transaction_type'),
        Index('idx_limit_reset_date', 'reset_date'),
    )


class SQLAlchemyAccountRepository(AccountRepository):
    """SQLAlchemy implementation of AccountRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, account: Account) -> Account:
        """Create a new account"""
        try:
            # Generate account number if not provided
            if not account.account_number:
                account.account_number = await self._generate_account_number(account.account_type)
            
            model = AccountModel.from_domain(account)
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
            
            logger.info("Account created", account_id=str(model.id), account_number=model.account_number)
            return model.to_domain()
        
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to create account", error=str(e))
            raise
    
    async def get_by_id(self, account_id: str) -> Optional[Account]:
        """Get account by ID"""
        try:
            result = await self.session.get(AccountModel, uuid.UUID(account_id))
            return result.to_domain() if result else None
        except Exception as e:
            logger.error("Failed to get account by ID", account_id=account_id, error=str(e))
            raise
    
    async def get_by_account_number(self, account_number: str) -> Optional[Account]:
        """Get account by account number"""
        try:
            from sqlalchemy import select
            
            stmt = select(AccountModel).where(AccountModel.account_number == account_number)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            return model.to_domain() if model else None
        except Exception as e:
            logger.error("Failed to get account by number", account_number=account_number, error=str(e))
            raise
    
    async def get_by_customer_id(self, customer_id: str) -> List[Account]:
        """Get all accounts for a customer"""
        try:
            from sqlalchemy import select
            
            stmt = select(AccountModel).where(
                AccountModel.customer_id == uuid.UUID(customer_id)
            ).order_by(AccountModel.created_at)
            
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [model.to_domain() for model in models]
        except Exception as e:
            logger.error("Failed to get accounts by customer ID", customer_id=customer_id, error=str(e))
            raise
    
    async def update(self, account: Account) -> Account:
        """Update an existing account"""
        try:
            from sqlalchemy import select
            
            stmt = select(AccountModel).where(AccountModel.id == uuid.UUID(account.id))
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                raise ValueError(f"Account not found: {account.id}")
            
            # Update fields
            model.account_type = account.account_type.value
            model.currency = account.currency
            model.balance = account.balance
            model.available_balance = account.available_balance
            model.hold_amount = account.hold_amount
            model.status = account.status.value
            model.interest_rate = Decimal(str(account.interest_rate))
            model.overdraft_limit = account.overdraft_limit
            model.minimum_balance = account.minimum_balance
            model.daily_transaction_limit = account.daily_transaction_limit
            model.monthly_transaction_limit = account.monthly_transaction_limit
            model.withdrawal_limit = account.withdrawal_limit
            model.branch_code = account.branch_code
            model.product_code = account.product_code
            model.account_purpose = account.account_purpose
            model.metadata = account.metadata
            model.updated_at = datetime.utcnow()
            model.updated_by = account.updated_by
            model.version += 1
            
            await self.session.commit()
            await self.session.refresh(model)
            
            logger.info("Account updated", account_id=account.id)
            return model.to_domain()
        
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to update account", account_id=account.id, error=str(e))
            raise
    
    async def delete(self, account_id: str) -> bool:
        """Soft delete an account (set status to closed)"""
        try:
            from sqlalchemy import select
            
            stmt = select(AccountModel).where(AccountModel.id == uuid.UUID(account_id))
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return False
            
            model.status = AccountStatus.CLOSED.value
            model.updated_at = datetime.utcnow()
            
            await self.session.commit()
            
            logger.info("Account deleted (soft)", account_id=account_id)
            return True
        
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to delete account", account_id=account_id, error=str(e))
            raise
    
    async def get_by_criteria(
        self,
        customer_id: Optional[str] = None,
        account_type: Optional[AccountType] = None,
        status: Optional[AccountStatus] = None,
        branch_code: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Account]:
        """Get accounts by various criteria"""
        try:
            from sqlalchemy import select
            
            stmt = select(AccountModel)
            
            if customer_id:
                stmt = stmt.where(AccountModel.customer_id == uuid.UUID(customer_id))
            if account_type:
                stmt = stmt.where(AccountModel.account_type == account_type.value)
            if status:
                stmt = stmt.where(AccountModel.status == status.value)
            if branch_code:
                stmt = stmt.where(AccountModel.branch_code == branch_code)
            
            stmt = stmt.order_by(AccountModel.created_at.desc()).limit(limit).offset(offset)
            
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            return [model.to_domain() for model in models]
        
        except Exception as e:
            logger.error("Failed to get accounts by criteria", error=str(e))
            raise
    
    async def update_balance(
        self,
        account_id: str,
        new_balance: Decimal,
        new_available_balance: Optional[Decimal] = None
    ) -> bool:
        """Update account balance"""
        try:
            from sqlalchemy import select
            
            stmt = select(AccountModel).where(AccountModel.id == uuid.UUID(account_id))
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            if not model:
                return False
            
            model.balance = new_balance
            if new_available_balance is not None:
                model.available_balance = new_available_balance
            else:
                model.available_balance = new_balance - model.hold_amount
            
            model.updated_at = datetime.utcnow()
            model.version += 1
            
            await self.session.commit()
            
            logger.info(
                "Account balance updated",
                account_id=account_id,
                new_balance=str(new_balance),
                new_available_balance=str(model.available_balance)
            )
            return True
        
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to update account balance", account_id=account_id, error=str(e))
            raise
    
    async def add_hold(
        self,
        account_id: str,
        amount: Decimal,
        reason: str,
        reference: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> str:
        """Add a hold on account funds"""
        try:
            from sqlalchemy import select
            
            # Get account
            stmt = select(AccountModel).where(AccountModel.id == uuid.UUID(account_id))
            result = await self.session.execute(stmt)
            account_model = result.scalar_one_or_none()
            
            if not account_model:
                raise ValueError(f"Account not found: {account_id}")
            
            # Create hold
            hold = AccountHoldModel(
                account_id=uuid.UUID(account_id),
                amount=amount,
                reason=reason,
                reference=reference,
                expires_at=expires_at
            )
            
            self.session.add(hold)
            
            # Update account hold amount and available balance
            account_model.hold_amount += amount
            account_model.available_balance = account_model.balance - account_model.hold_amount
            account_model.updated_at = datetime.utcnow()
            account_model.version += 1
            
            await self.session.commit()
            
            logger.info(
                "Account hold added",
                account_id=account_id,
                hold_id=str(hold.id),
                amount=str(amount),
                reason=reason
            )
            return str(hold.id)
        
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to add account hold", account_id=account_id, error=str(e))
            raise
    
    async def release_hold(self, hold_id: str) -> bool:
        """Release an account hold"""
        try:
            from sqlalchemy import select
            
            # Get hold
            stmt = select(AccountHoldModel).where(AccountHoldModel.id == uuid.UUID(hold_id))
            result = await self.session.execute(stmt)
            hold = result.scalar_one_or_none()
            
            if not hold or hold.status != 'active':
                return False
            
            # Get account
            stmt = select(AccountModel).where(AccountModel.id == hold.account_id)
            result = await self.session.execute(stmt)
            account_model = result.scalar_one_or_none()
            
            if not account_model:
                return False
            
            # Release hold
            hold.status = 'released'
            
            # Update account hold amount and available balance
            account_model.hold_amount -= hold.amount
            account_model.available_balance = account_model.balance - account_model.hold_amount
            account_model.updated_at = datetime.utcnow()
            account_model.version += 1
            
            await self.session.commit()
            
            logger.info(
                "Account hold released",
                hold_id=hold_id,
                account_id=str(hold.account_id),
                amount=str(hold.amount)
            )
            return True
        
        except Exception as e:
            await self.session.rollback()
            logger.error("Failed to release account hold", hold_id=hold_id, error=str(e))
            raise
    
    async def get_account_summary(self, customer_id: str) -> Dict[str, Any]:
        """Get account summary for a customer"""
        try:
            from sqlalchemy import select, func as sql_func
            
            # Get total balance by account type
            stmt = select(
                AccountModel.account_type,
                sql_func.count(AccountModel.id).label('count'),
                sql_func.sum(AccountModel.balance).label('total_balance'),
                sql_func.sum(AccountModel.available_balance).label('total_available')
            ).where(
                AccountModel.customer_id == uuid.UUID(customer_id),
                AccountModel.status != AccountStatus.CLOSED.value
            ).group_by(AccountModel.account_type)
            
            result = await self.session.execute(stmt)
            summary_data = result.all()
            
            summary = {
                "customer_id": customer_id,
                "total_accounts": 0,
                "total_balance": Decimal('0'),
                "total_available_balance": Decimal('0'),
                "accounts_by_type": {}
            }
            
            for row in summary_data:
                summary["total_accounts"] += row.count
                summary["total_balance"] += row.total_balance or Decimal('0')
                summary["total_available_balance"] += row.total_available or Decimal('0')
                
                summary["accounts_by_type"][row.account_type] = {
                    "count": row.count,
                    "total_balance": row.total_balance or Decimal('0'),
                    "total_available": row.total_available or Decimal('0')
                }
            
            return summary
        
        except Exception as e:
            logger.error("Failed to get account summary", customer_id=customer_id, error=str(e))
            raise
    
    async def _generate_account_number(self, account_type: AccountType) -> str:
        """Generate unique account number"""
        import random
        
        # Account type prefix mapping
        prefixes = {
            AccountType.SAVINGS: "SAV",
            AccountType.CHECKING: "CHK", 
            AccountType.BUSINESS: "BUS",
            AccountType.LOAN: "LON",
            AccountType.CREDIT: "CRD"
        }
        
        prefix = prefixes.get(account_type, "ACC")
        
        # Generate unique number
        while True:
            number = f"{prefix}{random.randint(100000000, 999999999)}"
            
            # Check if already exists
            from sqlalchemy import select
            stmt = select(AccountModel).where(AccountModel.account_number == number)
            result = await self.session.execute(stmt)
            if not result.scalar_one_or_none():
                return number


class DatabaseConfig:
    """Database configuration for Account Service"""
    
    def __init__(
        self,
        database_url: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 30,
        pool_recycle: int = 3600
    ):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
    
    def create_engine(self):
        """Create SQLAlchemy async engine"""
        return create_async_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            echo=False  # Set to True for SQL debugging
        )
    
    def create_session_factory(self, engine):
        """Create session factory"""
        return sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )


# Database initialization
async def init_database(config: DatabaseConfig):
    """Initialize database tables"""
    engine = config.create_engine()
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    logger.info("Account service database initialized")


# Usage example
if __name__ == "__main__":
    import asyncio
    from decimal import Decimal
    
    async def main():
        # Database configuration
        config = DatabaseConfig("postgresql+asyncpg://user:password@localhost/account_db")
        
        # Initialize database
        await init_database(config)
        
        # Create engine and session
        engine = config.create_engine()
        session_factory = config.create_session_factory(engine)
        
        async with session_factory() as session:
            # Create repository
            repo = SQLAlchemyAccountRepository(session)
            
            # Create test account
            account = Account(
                customer_id="123e4567-e89b-12d3-a456-426614174000",
                account_type=AccountType.SAVINGS,
                currency="USD",
                balance=Decimal("1000.00"),
                available_balance=Decimal("1000.00")
            )
            
            # Save account
            saved_account = await repo.create(account)
            print(f"Created account: {saved_account.account_number}")
            
            # Get account by ID
            retrieved_account = await repo.get_by_id(saved_account.id)
            print(f"Retrieved account: {retrieved_account.account_number}")
            
            # Add hold
            hold_id = await repo.add_hold(
                saved_account.id,
                Decimal("100.00"),
                "Test hold",
                "TEST123"
            )
            print(f"Added hold: {hold_id}")
            
            # Get updated account
            updated_account = await repo.get_by_id(saved_account.id)
            print(f"Available balance after hold: {updated_account.available_balance}")
        
        await engine.dispose()
    
    asyncio.run(main())
