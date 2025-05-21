"""
Example module demonstrating the use of all improved patterns and frameworks.

This module shows how to use the unified error handling, design patterns,
dependency injection, and refactored validators in a real application module.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Import our improved frameworks
from utils.unified_error_handling import (
    ValidationException, NotFoundException, BusinessRuleException,
    ErrorCodes
)
from utils.common.design_patterns import (
    singleton, Observer, Factory, Strategy
)
from utils.common.dependency_injection import (
    DependencyContainer, Repository, Service
)
from utils.common.refactored_validators import (
    SchemaValidator, PatternValidator, RangeValidator,
    ACCOUNT_NUMBER_VALIDATOR, EMAIL_VALIDATOR
)

# Configure logger
logger = logging.getLogger(__name__)

#--------------------------------------
# Domain Models
#--------------------------------------
class Transaction:
    """Transaction domain model"""
    
    def __init__(
        self,
        transaction_id: str,
        account_id: str,
        amount: float,
        transaction_type: str,
        description: Optional[str] = None,
        status: str = "pending",
        timestamp: Optional[datetime] = None
    ):
        self.transaction_id = transaction_id
        self.account_id = account_id
        self.amount = amount
        self.transaction_type = transaction_type
        self.description = description
        self.status = status
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "transaction_id": self.transaction_id,
            "account_id": self.account_id,
            "amount": self.amount,
            "transaction_type": self.transaction_type,
            "description": self.description,
            "status": self.status,
            "timestamp": self.timestamp.isoformat()
        }


class Account:
    """Account domain model"""
    
    def __init__(
        self,
        account_id: str,
        customer_id: str,
        account_type: str,
        balance: float,
        status: str = "active",
        currency: str = "INR",
        created_at: Optional[datetime] = None
    ):
        self.account_id = account_id
        self.customer_id = customer_id
        self.account_type = account_type
        self.balance = balance
        self.status = status
        self.currency = currency
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "account_id": self.account_id,
            "customer_id": self.customer_id,
            "account_type": self.account_type,
            "balance": self.balance,
            "status": self.status,
            "currency": self.currency,
            "created_at": self.created_at.isoformat()
        }


#--------------------------------------
# Repositories
#--------------------------------------
class AccountRepository(Repository[Account]):
    """Repository for Account entities"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_by_id(self, id: str) -> Optional[Account]:
        """Get account by ID"""
        # This would normally query the database
        # For example only
        if id == "test-account":
            return Account(
                account_id=id,
                customer_id="test-customer",
                account_type="savings",
                balance=1000.0
            )
        return None
    
    def get_all(self) -> List[Account]:
        """Get all accounts"""
        # Implementation...
        return []
    
    def add(self, entity: Account) -> Account:
        """Add a new account"""
        # Implementation...
        return entity
    
    def update(self, entity: Account) -> Account:
        """Update an existing account"""
        # Implementation...
        return entity
    
    def delete(self, id: str) -> bool:
        """Delete an account by ID"""
        # Implementation...
        return True


class TransactionRepository(Repository[Transaction]):
    """Repository for Transaction entities"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def get_by_id(self, id: str) -> Optional[Transaction]:
        """Get transaction by ID"""
        # Implementation...
        return None
    
    def get_all(self) -> List[Transaction]:
        """Get all transactions"""
        # Implementation...
        return []
    
    def add(self, entity: Transaction) -> Transaction:
        """Add a new transaction"""
        # Implementation...
        return entity
    
    def update(self, entity: Transaction) -> Transaction:
        """Update an existing transaction"""
        # Implementation...
        return entity
    
    def delete(self, id: str) -> bool:
        """Delete a transaction by ID"""
        # Implementation...
        return True
    
    def get_by_account_id(self, account_id: str) -> List[Transaction]:
        """Get transactions for an account"""
        # Implementation...
        return []


#--------------------------------------
# Transaction Processors (Strategy Pattern)
#--------------------------------------
class TransactionProcessor(Strategy):
    """Interface for transaction processors"""
    
    def process(self, account: Account, amount: float) -> Transaction:
        """Process a transaction"""
        raise NotImplementedError


class DepositProcessor(TransactionProcessor):
    """Processor for deposit transactions"""
    
    def __init__(self, transaction_repository: TransactionRepository):
        self.transaction_repository = transaction_repository
    
    def process(self, account: Account, amount: float) -> Transaction:
        """Process a deposit transaction"""
        # Validate amount
        if amount <= 0:
            raise ValidationException(
                message="Deposit amount must be positive",
                field="amount"
            )
        
        # Create transaction
        transaction = Transaction(
            transaction_id=f"DEP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            account_id=account.account_id,
            amount=amount,
            transaction_type="deposit",
            status="completed"
        )
        
        # Update account balance
        account.balance += amount
        
        # Save transaction
        return self.transaction_repository.add(transaction)


class WithdrawalProcessor(TransactionProcessor):
    """Processor for withdrawal transactions"""
    
    def __init__(self, transaction_repository: TransactionRepository):
        self.transaction_repository = transaction_repository
    
    def process(self, account: Account, amount: float) -> Transaction:
        """Process a withdrawal transaction"""
        # Validate amount
        if amount <= 0:
            raise ValidationException(
                message="Withdrawal amount must be positive",
                field="amount"
            )
        
        # Check sufficient funds
        if account.balance < amount:
            raise BusinessRuleException(
                message="Insufficient funds",
                rule="minimum_balance",
                error_code=ErrorCodes.INSUFFICIENT_FUNDS
            )
        
        # Create transaction
        transaction = Transaction(
            transaction_id=f"WDL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            account_id=account.account_id,
            amount=amount,
            transaction_type="withdrawal",
            status="completed"
        )
        
        # Update account balance
        account.balance -= amount
        
        # Save transaction
        return self.transaction_repository.add(transaction)


#--------------------------------------
# Services
#--------------------------------------
class AccountService(Service[Account]):
    """Service for account operations"""
    
    def __init__(
        self, 
        account_repository: AccountRepository,
        transaction_repository: TransactionRepository,
        notification_center: Observer
    ):
        self.account_repository = account_repository
        self.transaction_repository = transaction_repository
        self.notification_center = notification_center
        self.transaction_processors = {}
    
    def register_transaction_processor(self, transaction_type: str, processor: TransactionProcessor):
        """Register a transaction processor"""
        self.transaction_processors[transaction_type] = processor
    
    def get_account(self, account_id: str) -> Account:
        """Get account by ID"""
        account = self.account_repository.get_by_id(account_id)
        if not account:
            raise NotFoundException(
                message=f"Account not found",
                resource_type="Account",
                resource_id=account_id
            )
        return account
    
    def create_account(self, account_data: Dict[str, Any]) -> Account:
        """Create a new account"""
        # Validate account data
        validator = SchemaValidator({
            "customer_id": PatternValidator(r'^[A-Za-z0-9-]+$', "Invalid customer ID format"),
            "account_type": PatternValidator(r'^[a-z_]+$', "Invalid account type"),
            "initial_balance": RangeValidator(min_value=0)
        })
        
        is_valid, error = validator.validate(account_data)
        if not is_valid:
            raise ValidationException(message=error)
        
        # Create account
        account = Account(
            account_id=f"ACC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            customer_id=account_data["customer_id"],
            account_type=account_data["account_type"],
            balance=account_data.get("initial_balance", 0)
        )
        
        # Save account
        saved_account = self.account_repository.add(account)
        
        # Notify listeners
        self.notification_center.notify(
            "account.created", 
            {"account_id": saved_account.account_id}
        )
        
        return saved_account
    
    def process_transaction(
        self, 
        account_id: str, 
        transaction_type: str, 
        amount: float
    ) -> Transaction:
        """Process a transaction"""
        # Get account
        account = self.get_account(account_id)
        
        # Check if account is active
        if account.status != "active":
            raise BusinessRuleException(
                message=f"Cannot process transaction - account is {account.status}",
                rule="account_status",
                error_code=ErrorCodes.ACCOUNT_BLOCKED
            )
        
        # Get the appropriate processor
        processor = self.transaction_processors.get(transaction_type)
        if not processor:
            raise ValidationException(
                message=f"Unsupported transaction type: {transaction_type}",
                field="transaction_type"
            )
        
        # Process transaction
        transaction = processor.process(account, amount)
        
        # Update account
        self.account_repository.update(account)
        
        # Notify listeners
        self.notification_center.notify(
            "transaction.processed", 
            {"transaction_id": transaction.transaction_id}
        )
        
        return transaction


#--------------------------------------
# Notification Handlers (Observer Pattern)
#--------------------------------------
def email_notification_handler(event_data: Dict[str, Any]):
    """Handle email notifications"""
    logger.info(f"Sending email notification: {event_data}")
    # Implementation...


def sms_notification_handler(event_data: Dict[str, Any]):
    """Handle SMS notifications"""
    logger.info(f"Sending SMS notification: {event_data}")
    # Implementation...


def audit_log_handler(event_data: Dict[str, Any]):
    """Handle audit logging"""
    logger.info(f"Recording audit log: {event_data}")
    # Implementation...


#--------------------------------------
# Application Setup
#--------------------------------------
@singleton
class ApplicationContext:
    """Application context using dependency injection"""
    
    def __init__(self):
        # Create DI container
        self.container = DependencyContainer()
        
        # Create notification center (observer pattern)
        self.notification_center = Observer()
        self.notification_center.subscribe("account.created", email_notification_handler)
        self.notification_center.subscribe("account.created", audit_log_handler)
        self.notification_center.subscribe("transaction.processed", email_notification_handler)
        self.notification_center.subscribe("transaction.processed", sms_notification_handler)
        self.notification_center.subscribe("transaction.processed", audit_log_handler)
        
        # Register dependencies
        self.register_dependencies()
        
        # Create transaction processor factory
        self.transaction_processor_factory = Factory()
        self.register_transaction_processors()
    
    def register_dependencies(self):
        """Register dependencies in the container"""
        # Register mock DB connection
        self.container.register_instance("db_connection", {})
        
        # Register repositories
        self.container.register(AccountRepository, AccountRepository)
        self.container.register(TransactionRepository, TransactionRepository)
        
        # Register notification center
        self.container.register_instance(Observer, self.notification_center)
        
        # Register services
        self.container.register_singleton(AccountService, AccountService)
    
    def register_transaction_processors(self):
        """Register transaction processors"""
        transaction_repository = self.container.resolve(TransactionRepository)
        
        # Create processors
        deposit_processor = DepositProcessor(transaction_repository)
        withdrawal_processor = WithdrawalProcessor(transaction_repository)
        
        # Register with factory
        self.transaction_processor_factory.register("deposit", lambda: deposit_processor)
        self.transaction_processor_factory.register("withdrawal", lambda: withdrawal_processor)
        
        # Register with account service
        account_service = self.container.resolve(AccountService)
        account_service.register_transaction_processor("deposit", deposit_processor)
        account_service.register_transaction_processor("withdrawal", withdrawal_processor)
    
    def get_account_service(self) -> AccountService:
        """Get the account service"""
        return self.container.resolve(AccountService)


# Initialize application
app_context = ApplicationContext()


#--------------------------------------
# API Layer
#--------------------------------------
def create_account_api(customer_id: str, account_type: str, initial_balance: float) -> Dict[str, Any]:
    """API endpoint for account creation"""
    try:
        account_service = app_context.get_account_service()
        
        account = account_service.create_account({
            "customer_id": customer_id,
            "account_type": account_type,
            "initial_balance": initial_balance
        })
        
        return {
            "status": "success",
            "data": account.to_dict()
        }
    except ValidationException as e:
        return {
            "status": "error",
            "error": e.to_dict()
        }
    except Exception as e:
        logger.exception("Unexpected error creating account")
        return {
            "status": "error",
            "error": {
                "message": "An unexpected error occurred",
                "code": "INTERNAL_ERROR"
            }
        }


def process_transaction_api(
    account_id: str, 
    transaction_type: str, 
    amount: float
) -> Dict[str, Any]:
    """API endpoint for processing transactions"""
    try:
        account_service = app_context.get_account_service()
        
        transaction = account_service.process_transaction(
            account_id=account_id,
            transaction_type=transaction_type,
            amount=amount
        )
        
        return {
            "status": "success",
            "data": transaction.to_dict()
        }
    except (ValidationException, NotFoundException, BusinessRuleException) as e:
        return {
            "status": "error",
            "error": e.to_dict()
        }
    except Exception as e:
        logger.exception("Unexpected error processing transaction")
        return {
            "status": "error",
            "error": {
                "message": "An unexpected error occurred",
                "code": "INTERNAL_ERROR"
            }
        }


#--------------------------------------
# Usage Example
#--------------------------------------
if __name__ == "__main__":
    # Create an account
    result = create_account_api(
        customer_id="CUST001",
        account_type="savings",
        initial_balance=1000.0
    )
    print(f"Create account result: {result}")
    
    if result["status"] == "success":
        account_id = result["data"]["account_id"]
        
        # Process a deposit
        deposit_result = process_transaction_api(
            account_id=account_id,
            transaction_type="deposit",
            amount=500.0
        )
        print(f"Deposit result: {deposit_result}")
        
        # Process a withdrawal
        withdrawal_result = process_transaction_api(
            account_id=account_id,
            transaction_type="withdrawal",
            amount=200.0
        )
        print(f"Withdrawal result: {withdrawal_result}")
        
        # Try an invalid withdrawal (too much)
        invalid_withdrawal = process_transaction_api(
            account_id=account_id,
            transaction_type="withdrawal",
            amount=5000.0
        )
        print(f"Invalid withdrawal result: {invalid_withdrawal}")
