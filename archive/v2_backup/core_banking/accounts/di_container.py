"""
Dependency Injection Container for Accounts Module

This module sets up the dependency injection container for the Accounts module,
wiring together all dependencies according to Clean Architecture principles.
"""

import os
from decimal import Decimal
from typing import Dict, Any

from dependency_injector import containers, providers

# Domain Services
from .domain.services.interest_calculator import InterestCalculator
from .domain.services.account_rules import AccountRules

# Application Use Cases
from .application.use_cases.create_account import CreateAccountUseCase
from .application.use_cases.deposit_funds import DepositFundsUseCase
from .application.use_cases.withdraw_funds import WithdrawFundsUseCase
from .application.use_cases.transfer_funds import TransferFundsUseCase
from .application.use_cases.get_account_details import GetAccountDetailsUseCase
from .application.use_cases.close_account import CloseAccountUseCase
from .application.use_cases.get_account_statement import GetAccountStatementUseCase
# Import other use cases as they are implemented

# Application Services
from .application.services.account_service import AccountService

# Repositories
from .infrastructure.repositories.sql_account_repository import SqlAccountRepository
from .infrastructure.repositories.sql_transaction_repository import SqlTransactionRepository

# Infrastructure Services
from .infrastructure.services.email_notification_service import EmailNotificationService
from .infrastructure.services.sms_notification_service import SmsNotificationService

# Database Connection
# This is an example - you would typically import your database connection from a central place
from ...database.python.db_connection import get_database_connection

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class AccountsContainer(containers.DeclarativeContainer):
    """
    Dependency Injection Container for Accounts module
    
    This container wires together all dependencies for the Accounts module,
    following Clean Architecture principles with clear separation between
    domain, application, and infrastructure layers.
    """
    
    # Configuration
    config = providers.Configuration()
    
    # Database Connection
    db_connection = providers.Singleton(get_database_connection)
    
    # Domain Services
    interest_calculator = providers.Factory(
        InterestCalculator,
        base_rate=config.interest.base_rate,
        premium_rate=config.interest.premium_rate
    )
    
    account_rules = providers.Factory(
        AccountRules,
        min_balance=config.account.min_balance,
        withdrawal_limit=config.account.withdrawal_limit
    )
    
    # Repositories
    account_repository = providers.Singleton(
        SqlAccountRepository,
        db_connection=db_connection
    )
    
    transaction_repository = providers.Singleton(
        SqlTransactionRepository,
        db_connection=db_connection
    )
    
    # Infrastructure Services
    email_notification_service = providers.Singleton(
        EmailNotificationService,
        smtp_host=config.email.smtp_host,
        smtp_port=config.email.smtp_port,
        smtp_user=config.email.smtp_user,
        smtp_password=config.email.smtp_password,
        from_email=config.email.from_email,
        customer_email_provider=config.services.customer_email_provider
    )
    
    sms_notification_service = providers.Singleton(
        SmsNotificationService,
        sms_gateway_url=config.sms.gateway_url,
        sms_api_key=config.sms.api_key,
        customer_phone_provider=config.services.customer_phone_provider
    )
    
    # Default notification service (can be switched between email and sms)
    notification_service = providers.Selector(
        config.notifications.default_channel,
        email=email_notification_service,
        sms=sms_notification_service
    )
    
    # Application Use Cases
    create_account_use_case = providers.Factory(
        CreateAccountUseCase,
        account_repository=account_repository,
        notification_service=notification_service
    )
    deposit_funds_use_case = providers.Factory(
        DepositFundsUseCase,
        account_repository=account_repository,
        transaction_repository=transaction_repository,
        notification_service=notification_service
    )
    
    withdraw_funds_use_case = providers.Factory(
        WithdrawFundsUseCase,
        account_repository=account_repository,
        transaction_repository=transaction_repository,
        notification_service=notification_service,
        account_rules=account_rules
    )
    
    transfer_funds_use_case = providers.Factory(
        TransferFundsUseCase,
        account_repository=account_repository,
        transaction_repository=transaction_repository,
        notification_service=notification_service,
        account_rules=account_rules
    )
    
    get_account_details_use_case = providers.Factory(
        GetAccountDetailsUseCase,
        account_repository=account_repository
    )
    close_account_use_case = providers.Factory(
        CloseAccountUseCase,
        account_repository=account_repository,
        notification_service=notification_service,
        account_rules=account_rules
    )
    
    get_account_statement_use_case = providers.Factory(
        GetAccountStatementUseCase,
        account_repository=account_repository,
        transaction_repository=transaction_repository
    )    # Application Service - Orchestration Layer
    account_service = providers.Factory(
        AccountService,
        create_account_use_case=create_account_use_case,
        deposit_funds_use_case=deposit_funds_use_case,
        withdraw_funds_use_case=withdraw_funds_use_case,
        transfer_funds_use_case=transfer_funds_use_case,
        get_account_details_use_case=get_account_details_use_case,
        close_account_use_case=close_account_use_case,
        get_account_statement_use_case=get_account_statement_use_case
    )


# Create a global container instance
container = AccountsContainer()

# Configure from environment variables or configuration files
container.config.from_dict({
    "interest": {
        "base_rate": Decimal("3.5"),
        "premium_rate": Decimal("4.5")
    },
    "account": {
        "min_balance": Decimal("1000.0"),
        "withdrawal_limit": Decimal("50000.0")
    },
    "email": {
        "smtp_host": os.environ.get("CBS_SMTP_HOST", "smtp.cbs.local"),
        "smtp_port": int(os.environ.get("CBS_SMTP_PORT", "587")),
        "smtp_user": os.environ.get("CBS_SMTP_USER", "notification@cbs.local"),
        "smtp_password": os.environ.get("CBS_SMTP_PASSWORD", "default_password"),
        "from_email": os.environ.get("CBS_FROM_EMAIL", "banking@cbs.local")
    },
    "sms": {
        "gateway_url": os.environ.get("CBS_SMS_GATEWAY", "https://sms.cbs.local/api"),
        "api_key": os.environ.get("CBS_SMS_API_KEY", "default_key")
    },
    "notifications": {
        "default_channel": os.environ.get("CBS_DEFAULT_NOTIFICATION", "email")
    },
    "services": {
        "customer_email_provider": "customer_repository", 
        "customer_phone_provider": "customer_repository"
    }
})
