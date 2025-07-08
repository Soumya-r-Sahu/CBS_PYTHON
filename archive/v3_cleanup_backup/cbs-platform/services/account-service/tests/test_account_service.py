"""
Comprehensive Test Suite for Account Service
Tests for domain entities, repositories, and API endpoints
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

# Import modules to test
from account_service.domain.entities import (
    Account, Transaction, AccountType, AccountStatus, TransactionType,
    TransactionStatus, Money, AccountLimits
)
from account_service.infrastructure.database import Base, AccountModel, TransactionModel
from account_service.infrastructure.repositories import AccountRepository, TransactionRepository
from account_service.interfaces.api import app
from account_service.application.dto import (
    CreateAccountRequest, DepositRequest, WithdrawRequest,
    account_to_dto, transaction_to_dto
)


# Test configuration
TEST_DATABASE_URL = "sqlite:///./test_account_service.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def setup_test_database():
    """Setup test database"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_session(setup_test_database):
    """Create test database session"""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_account_data():
    """Sample account data for testing"""
    return {
        "customer_id": str(uuid4()),
        "account_type": AccountType.SAVINGS,
        "currency": "USD",
        "initial_balance": Decimal("1000.00")
    }


@pytest.fixture
def sample_money():
    """Sample Money object"""
    return Money(Decimal("100.00"), "USD")


class TestMoneyValueObject:
    """Test Money value object"""
    
    def test_money_creation(self):
        """Test Money object creation"""
        money = Money(Decimal("100.50"), "USD")
        assert money.amount == Decimal("100.50")
        assert money.currency == "USD"
    
    def test_money_validation(self):
        """Test Money validation"""
        with pytest.raises(ValueError):
            Money(Decimal("-10.00"), "USD")  # Negative amount
        
        with pytest.raises(ValueError):
            Money(Decimal("100.00"), "")  # Empty currency
    
    def test_money_arithmetic(self):
        """Test Money arithmetic operations"""
        money1 = Money(Decimal("100.00"), "USD")
        money2 = Money(Decimal("50.00"), "USD")
        
        # Addition
        result = money1.add(money2)
        assert result.amount == Decimal("150.00")
        assert result.currency == "USD"
        
        # Subtraction
        result = money1.subtract(money2)
        assert result.amount == Decimal("50.00")
        assert result.currency == "USD"
    
    def test_money_comparison(self):
        """Test Money comparison operations"""
        money1 = Money(Decimal("100.00"), "USD")
        money2 = Money(Decimal("50.00"), "USD")
        
        assert money1.is_greater_than(money2)
        assert money1.is_greater_than_or_equal(money2)
        assert not money2.is_greater_than(money1)
    
    def test_money_different_currencies(self):
        """Test Money operations with different currencies"""
        money_usd = Money(Decimal("100.00"), "USD")
        money_eur = Money(Decimal("50.00"), "EUR")
        
        with pytest.raises(ValueError):
            money_usd.add(money_eur)
        
        with pytest.raises(ValueError):
            money_usd.subtract(money_eur)
        
        with pytest.raises(ValueError):
            money_usd.is_greater_than(money_eur)


class TestAccountEntity:
    """Test Account domain entity"""
    
    def test_account_creation(self, sample_account_data):
        """Test Account entity creation"""
        account = Account.create(
            customer_id=UUID(sample_account_data["customer_id"]),
            account_type=sample_account_data["account_type"],
            currency=sample_account_data["currency"],
            initial_deposit=sample_account_data["initial_balance"]
        )
        
        assert account.customer_id == UUID(sample_account_data["customer_id"])
        assert account.account_type == sample_account_data["account_type"]
        assert account.balance.currency == sample_account_data["currency"]
        assert account.status == AccountStatus.ACTIVE
        assert len(account.account_number) > 0
    
    def test_account_deposit(self, sample_account_data, sample_money):
        """Test account deposit functionality"""
        account = Account.create(
            customer_id=UUID(sample_account_data["customer_id"]),
            account_type=sample_account_data["account_type"],
            currency=sample_account_data["currency"]
        )
        
        initial_balance = account.balance.amount
        account.deposit(sample_money)
        
        assert account.balance.amount == initial_balance + sample_money.amount
    
    def test_account_withdrawal(self, sample_account_data, sample_money):
        """Test account withdrawal functionality"""
        account = Account.create(
            customer_id=UUID(sample_account_data["customer_id"]),
            account_type=sample_account_data["account_type"],
            currency=sample_account_data["currency"],
            initial_deposit=Decimal("1000.00")
        )
        
        initial_balance = account.balance.amount
        result = account.withdraw(sample_money)
        
        assert result is True
        assert account.balance.amount == initial_balance - sample_money.amount
    
    def test_account_insufficient_funds(self, sample_account_data):
        """Test withdrawal with insufficient funds"""
        account = Account.create(
            customer_id=UUID(sample_account_data["customer_id"]),
            account_type=sample_account_data["account_type"],
            currency=sample_account_data["currency"],
            initial_deposit=Decimal("50.00")
        )
        
        large_amount = Money(Decimal("100.00"), "USD")
        result = account.withdraw(large_amount)
        
        assert result is False
    
    def test_account_limits_update(self, sample_account_data):
        """Test updating account limits"""
        account = Account.create(
            customer_id=UUID(sample_account_data["customer_id"]),
            account_type=sample_account_data["account_type"],
            currency=sample_account_data["currency"]
        )
        
        new_limits = AccountLimits(
            daily_withdrawal_limit=Money(Decimal("2000.00"), "USD"),
            daily_transfer_limit=Money(Decimal("5000.00"), "USD"),
            monthly_transaction_limit=Money(Decimal("50000.00"), "USD"),
            minimum_balance=Money(Decimal("100.00"), "USD")
        )
        
        account.update_limits(
            daily_withdrawal_limit=new_limits.daily_withdrawal_limit,
            daily_transfer_limit=new_limits.daily_transfer_limit,
            monthly_transaction_limit=new_limits.monthly_transaction_limit,
            minimum_balance=new_limits.minimum_balance
        )
        
        assert account.limits.daily_withdrawal_limit.amount == Decimal("2000.00")
        assert account.limits.minimum_balance.amount == Decimal("100.00")


class TestTransactionEntity:
    """Test Transaction domain entity"""
    
    def test_transaction_creation(self, sample_account_data, sample_money):
        """Test Transaction entity creation"""
        account_id = uuid4()
        
        transaction = Transaction.create_deposit(
            account_id=account_id,
            amount=sample_money,
            description="Test deposit",
            created_by="test_user"
        )
        
        assert transaction.account_id == account_id
        assert transaction.transaction_type == TransactionType.CREDIT
        assert transaction.amount.amount == sample_money.amount
        assert transaction.status == TransactionStatus.PENDING
        assert transaction.description == "Test deposit"
    
    def test_transaction_completion(self, sample_money):
        """Test transaction completion"""
        account_id = uuid4()
        
        transaction = Transaction.create_deposit(
            account_id=account_id,
            amount=sample_money,
            description="Test deposit"
        )
        
        balance_before = Money(Decimal("500.00"), "USD")
        balance_after = Money(Decimal("600.00"), "USD")
        
        transaction.complete(balance_before, balance_after)
        
        assert transaction.status == TransactionStatus.COMPLETED
        assert transaction.balance_before.amount == Decimal("500.00")
        assert transaction.balance_after.amount == Decimal("600.00")
        assert transaction.completed_at is not None
    
    def test_transaction_failure(self, sample_money):
        """Test transaction failure"""
        account_id = uuid4()
        
        transaction = Transaction.create_withdrawal(
            account_id=account_id,
            amount=sample_money,
            description="Test withdrawal"
        )
        
        transaction.fail("Insufficient funds")
        
        assert transaction.status == TransactionStatus.FAILED
        assert "Insufficient funds" in str(transaction.metadata)


class TestAccountRepository:
    """Test Account repository"""
    
    @pytest.mark.asyncio
    async def test_create_account(self, test_session, sample_account_data):
        """Test creating an account"""
        repo = AccountRepository(test_session)
        
        account = Account.create(
            customer_id=UUID(sample_account_data["customer_id"]),
            account_type=sample_account_data["account_type"],
            currency=sample_account_data["currency"]
        )
        
        created_account = await repo.create(account)
        
        assert created_account.id is not None
        assert created_account.customer_id == UUID(sample_account_data["customer_id"])
        assert created_account.account_type == sample_account_data["account_type"]
    
    @pytest.mark.asyncio
    async def test_get_account_by_id(self, test_session, sample_account_data):
        """Test getting account by ID"""
        repo = AccountRepository(test_session)
        
        # Create account
        account = Account.create(
            customer_id=UUID(sample_account_data["customer_id"]),
            account_type=sample_account_data["account_type"],
            currency=sample_account_data["currency"]
        )
        
        created_account = await repo.create(account)
        
        # Retrieve account
        retrieved_account = await repo.get_by_id(created_account.id)
        
        assert retrieved_account is not None
        assert retrieved_account.id == created_account.id
        assert retrieved_account.customer_id == created_account.customer_id
    
    @pytest.mark.asyncio
    async def test_get_customer_accounts(self, test_session, sample_account_data):
        """Test getting all accounts for a customer"""
        repo = AccountRepository(test_session)
        customer_id = UUID(sample_account_data["customer_id"])
        
        # Create multiple accounts for same customer
        account1 = Account.create(
            customer_id=customer_id,
            account_type=AccountType.SAVINGS,
            currency="USD"
        )
        
        account2 = Account.create(
            customer_id=customer_id,
            account_type=AccountType.CURRENT,
            currency="USD"
        )
        
        await repo.create(account1)
        await repo.create(account2)
        
        # Retrieve customer accounts
        accounts = await repo.get_by_customer_id(customer_id)
        
        assert len(accounts) == 2
        assert all(acc.customer_id == customer_id for acc in accounts)
    
    @pytest.mark.asyncio
    async def test_update_account(self, test_session, sample_account_data):
        """Test updating an account"""
        repo = AccountRepository(test_session)
        
        # Create account
        account = Account.create(
            customer_id=UUID(sample_account_data["customer_id"]),
            account_type=sample_account_data["account_type"],
            currency=sample_account_data["currency"]
        )
        
        created_account = await repo.create(account)
        
        # Update account
        created_account.notes = "Updated notes"
        created_account.updated_by = "test_updater"
        
        updated_account = await repo.update(created_account)
        
        assert updated_account.notes == "Updated notes"
        assert updated_account.updated_by == "test_updater"
    
    @pytest.mark.asyncio
    async def test_search_accounts(self, test_session):
        """Test searching accounts with filters"""
        repo = AccountRepository(test_session)
        customer_id = uuid4()
        
        # Create accounts with different types
        savings_account = Account.create(
            customer_id=customer_id,
            account_type=AccountType.SAVINGS,
            currency="USD",
            initial_deposit=Decimal("1000.00")
        )
        
        current_account = Account.create(
            customer_id=customer_id,
            account_type=AccountType.CURRENT,
            currency="USD",
            initial_deposit=Decimal("2000.00")
        )
        
        await repo.create(savings_account)
        await repo.create(current_account)
        
        # Search by account type
        savings_accounts, count = await repo.search(
            account_type=AccountType.SAVINGS,
            limit=10,
            offset=0
        )
        
        assert count >= 1
        assert all(acc.account_type == AccountType.SAVINGS for acc in savings_accounts)


class TestTransactionRepository:
    """Test Transaction repository"""
    
    @pytest.mark.asyncio
    async def test_create_transaction(self, test_session):
        """Test creating a transaction"""
        repo = TransactionRepository(test_session)
        account_id = uuid4()
        
        transaction = Transaction.create_deposit(
            account_id=account_id,
            amount=Money(Decimal("100.00"), "USD"),
            description="Test deposit"
        )
        
        created_transaction = await repo.create(transaction)
        
        assert created_transaction.id is not None
        assert created_transaction.account_id == account_id
        assert created_transaction.amount.amount == Decimal("100.00")
    
    @pytest.mark.asyncio
    async def test_get_account_transactions(self, test_session):
        """Test getting transactions for an account"""
        repo = TransactionRepository(test_session)
        account_id = uuid4()
        
        # Create multiple transactions
        transaction1 = Transaction.create_deposit(
            account_id=account_id,
            amount=Money(Decimal("100.00"), "USD"),
            description="Deposit 1"
        )
        
        transaction2 = Transaction.create_withdrawal(
            account_id=account_id,
            amount=Money(Decimal("50.00"), "USD"),
            description="Withdrawal 1"
        )
        
        await repo.create(transaction1)
        await repo.create(transaction2)
        
        # Retrieve transactions
        transactions, count = await repo.get_by_account_id(
            account_id=account_id,
            limit=10,
            offset=0
        )
        
        assert count == 2
        assert all(txn.account_id == account_id for txn in transactions)


class TestAccountAPI:
    """Test Account Service REST API"""
    
    def test_health_check(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "account-service"
        assert "status" in data
    
    @patch('account_service.interfaces.api.verify_token')
    @patch('account_service.infrastructure.repositories.AccountRepository.create')
    def test_create_account_api(self, mock_create, mock_verify, test_client):
        """Test create account API endpoint"""
        # Mock authentication
        mock_verify.return_value = {"user_id": "test_user", "role": "admin"}
        
        # Mock repository
        mock_account = Mock()
        mock_account.id = uuid4()
        mock_account.account_number = "ACC123456"
        mock_account.customer_id = uuid4()
        mock_account.account_type = AccountType.SAVINGS
        mock_account.status = AccountStatus.ACTIVE
        mock_account.balance = Money(Decimal("1000.00"), "USD")
        mock_account.created_at = datetime.utcnow()
        mock_account.updated_at = datetime.utcnow()
        mock_account.version = 1
        
        mock_create.return_value = mock_account
        
        # Test request
        request_data = {
            "customer_id": str(uuid4()),
            "account_type": "savings",
            "currency": "USD",
            "initial_deposit": 1000.00
        }
        
        response = test_client.post(
            "/api/v1/accounts",
            json=request_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "account" in data
    
    @patch('account_service.interfaces.api.verify_token')
    @patch('account_service.infrastructure.repositories.AccountRepository.get_by_id')
    def test_get_account_api(self, mock_get, mock_verify, test_client):
        """Test get account API endpoint"""
        # Mock authentication
        mock_verify.return_value = {"user_id": "test_user", "role": "admin"}
        
        # Mock repository
        account_id = uuid4()
        mock_account = Mock()
        mock_account.id = account_id
        mock_account.account_number = "ACC123456"
        mock_account.customer_id = uuid4()
        mock_account.account_type = AccountType.SAVINGS
        mock_account.status = AccountStatus.ACTIVE
        mock_account.balance = Money(Decimal("1000.00"), "USD")
        mock_account.created_at = datetime.utcnow()
        mock_account.updated_at = datetime.utcnow()
        mock_account.version = 1
        
        mock_get.return_value = mock_account
        
        # Test request
        response = test_client.get(
            f"/api/v1/accounts/{account_id}",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(account_id)
        assert data["account_number"] == "ACC123456"
    
    def test_get_account_not_found(self, test_client):
        """Test get account API endpoint with non-existent account"""
        non_existent_id = uuid4()
        
        with patch('account_service.interfaces.api.verify_token') as mock_verify:
            with patch('account_service.infrastructure.repositories.AccountRepository.get_by_id') as mock_get:
                mock_verify.return_value = {"user_id": "test_user", "role": "admin"}
                mock_get.return_value = None
                
                response = test_client.get(
                    f"/api/v1/accounts/{non_existent_id}",
                    headers={"Authorization": "Bearer test_token"}
                )
                
                assert response.status_code == 404


class TestDTOMappers:
    """Test DTO mapper functions"""
    
    def test_money_to_dto(self, sample_money):
        """Test Money to DTO conversion"""
        from account_service.application.dto import money_to_dto
        
        dto = money_to_dto(sample_money)
        
        assert dto.amount == sample_money.amount
        assert dto.currency == sample_money.currency
    
    def test_account_to_dto(self, sample_account_data):
        """Test Account to DTO conversion"""
        account = Account.create(
            customer_id=UUID(sample_account_data["customer_id"]),
            account_type=sample_account_data["account_type"],
            currency=sample_account_data["currency"]
        )
        
        dto = account_to_dto(account)
        
        assert dto.id == str(account.id)
        assert dto.account_number == account.account_number
        assert dto.customer_id == str(account.customer_id)
        assert dto.account_type == account.account_type.value
        assert dto.balance.amount == account.balance.amount


class TestPerformance:
    """Performance tests for critical operations"""
    
    @pytest.mark.asyncio
    async def test_bulk_account_creation_performance(self, test_session):
        """Test performance of bulk account creation"""
        repo = AccountRepository(test_session)
        start_time = datetime.utcnow()
        
        # Create 100 accounts
        accounts = []
        for i in range(100):
            account = Account.create(
                customer_id=uuid4(),
                account_type=AccountType.SAVINGS,
                currency="USD"
            )
            accounts.append(account)
        
        # Measure creation time
        for account in accounts:
            await repo.create(account)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert duration < 10.0  # 10 seconds for 100 accounts
        
        print(f"Created 100 accounts in {duration:.2f} seconds")
    
    @pytest.mark.asyncio
    async def test_transaction_query_performance(self, test_session):
        """Test performance of transaction queries"""
        account_repo = AccountRepository(test_session)
        transaction_repo = TransactionRepository(test_session)
        
        # Create account
        account = Account.create(
            customer_id=uuid4(),
            account_type=AccountType.SAVINGS,
            currency="USD"
        )
        created_account = await account_repo.create(account)
        
        # Create many transactions
        for i in range(500):
            transaction = Transaction.create_deposit(
                account_id=created_account.id,
                amount=Money(Decimal("10.00"), "USD"),
                description=f"Transaction {i}"
            )
            await transaction_repo.create(transaction)
        
        # Measure query time
        start_time = datetime.utcnow()
        
        transactions, count = await transaction_repo.get_by_account_id(
            account_id=created_account.id,
            limit=100,
            offset=0
        )
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Should complete quickly
        assert duration < 1.0  # 1 second for query
        assert len(transactions) == 100
        assert count == 500
        
        print(f"Queried 100 transactions from 500 in {duration:.3f} seconds")


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_duplicate_account_number_error(self, test_session):
        """Test handling of duplicate account numbers"""
        repo = AccountRepository(test_session)
        
        # Create first account
        account1 = Account.create(
            customer_id=uuid4(),
            account_type=AccountType.SAVINGS,
            currency="USD"
        )
        account1.account_number = "DUPLICATE123"
        
        await repo.create(account1)
        
        # Try to create account with same number
        account2 = Account.create(
            customer_id=uuid4(),
            account_type=AccountType.CURRENT,
            currency="USD"
        )
        account2.account_number = "DUPLICATE123"
        
        with pytest.raises(ValueError, match="already exists"):
            await repo.create(account2)
    
    def test_invalid_currency_error(self):
        """Test handling of invalid currency"""
        with pytest.raises(ValueError):
            Money(Decimal("100.00"), "")
    
    def test_negative_amount_error(self):
        """Test handling of negative amounts"""
        with pytest.raises(ValueError):
            Money(Decimal("-100.00"), "USD")


class TestConcurrency:
    """Test concurrent operations"""
    
    @pytest.mark.asyncio
    async def test_concurrent_transactions(self, test_session):
        """Test concurrent transaction processing"""
        account_repo = AccountRepository(test_session)
        transaction_repo = TransactionRepository(test_session)
        
        # Create account
        account = Account.create(
            customer_id=uuid4(),
            account_type=AccountType.SAVINGS,
            currency="USD",
            initial_deposit=Decimal("1000.00")
        )
        created_account = await account_repo.create(account)
        
        # Create concurrent transactions
        async def create_transaction(i):
            transaction = Transaction.create_deposit(
                account_id=created_account.id,
                amount=Money(Decimal("10.00"), "USD"),
                description=f"Concurrent transaction {i}"
            )
            return await transaction_repo.create(transaction)
        
        # Run 10 concurrent transactions
        tasks = [create_transaction(i) for i in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        successful_transactions = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_transactions) == 10


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
