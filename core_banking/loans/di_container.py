"""
Dependency Injection Container for Loans Module

This module sets up the dependency injection container for the Loans module,
wiring together all dependencies according to Clean Architecture principles.
"""

from dependency_injector import containers, providers
import os

# Domain Services
from .domain.services.loan_rules_service import LoanRulesService

# Application Interfaces
from .application.interfaces.loan_repository_interface import LoanRepositoryInterface
from .application.interfaces.notification_service_interface import NotificationServiceInterface
from .application.interfaces.document_storage_interface import DocumentStorageInterface

# Application Use Cases
from .application.use_cases.loan_application_use_case import LoanApplicationUseCase
from .application.use_cases.loan_approval_use_case import LoanApprovalUseCase
from .application.use_cases.loan_disbursement_use_case import LoanDisbursementUseCase

# Application Services
from .application.services.loan_calculator_service import LoanCalculatorService

# Infrastructure Implementations
from .infrastructure.repositories.sql_loan_repository import SqlLoanRepository
from .infrastructure.services.email_notification_service import EmailNotificationService
from .infrastructure.services.sms_notification_service import SmsNotificationService
from .infrastructure.services.file_system_document_storage import FileSystemDocumentStorage

# Database Connection
from ..database.python.db_connection import get_database_connection


class LoansContainer(containers.DeclarativeContainer):
    """
    Dependency Injection Container for Loans module
    
    This container wires together all dependencies for the Loans module,
    following Clean Architecture principles with clear separation between
    domain, application, and infrastructure layers.
    """
    
    # Configuration
    config = providers.Configuration()
    
    # Set default configuration values
    config.set_default({
        'db_connection_string': os.environ.get('CBS_DB_CONNECTION', 'sqlite:///loans.db'),
        'document_storage_path': os.path.join(os.getcwd(), 'loan_documents'),
        'notification': {
            'email': {
                'smtp_server': 'smtp.example.com',
                'smtp_port': 587,
                'sender_email': 'loans@bank.example.com'
            },
            'sms': {
                'sms_provider': 'default_provider',
                'sender_id': 'BANKNAME'
            }
        },
        'loan_rules': {
            'interest_rate_limits': {
                'personal': '0.25',
                'home': '0.12',
                'auto': '0.15',
                'education': '0.08',
                'business': '0.20',
                'secured': '0.10',
                'unsecured': '0.25'
            },
            'max_loan_amounts': {
                'personal': '100000',
                'home': '10000000',
                'auto': '500000',
                'education': '500000',
                'business': '5000000',
                'secured': '10000000',
                'unsecured': '200000'
            }
        }
    })
    
    # Domain Services
    loan_rules_service = providers.Singleton(
        LoanRulesService,
        config=config.loan_rules
    )
    
    # Infrastructure Layer - Repositories
    loan_repository = providers.Singleton(
        SqlLoanRepository,
        connection_string=config.db_connection_string
    )
    
    # Infrastructure Layer - Services
    email_notification_service = providers.Singleton(
        EmailNotificationService,
        config=config.notification.email
    )
    
    sms_notification_service = providers.Singleton(
        SmsNotificationService,
        config=config.notification.sms
    )
    document_storage = providers.Singleton(
        FileSystemDocumentStorage,
        base_path=config.document_storage_path
    )
    
    # Application Services
    loan_calculator_service = providers.Singleton(
        LoanCalculatorService
    )
    
    # Application Use Cases
    loan_application_use_case = providers.Factory(
        LoanApplicationUseCase,
        loan_repository=loan_repository,
        notification_service=email_notification_service,
        document_storage=document_storage
    )
    
    loan_approval_use_case = providers.Factory(
        LoanApprovalUseCase,
        loan_repository=loan_repository,
        notification_service=email_notification_service
    )
    
    loan_disbursement_use_case = providers.Factory(
        LoanDisbursementUseCase,
        loan_repository=loan_repository,
        notification_service=email_notification_service
    )


# Create a default container instance
def get_container():
    """Get configured dependency injection container"""
    container = LoansContainer()
    return container


# Helper functions to access repositories and services
def get_loan_repository() -> LoanRepositoryInterface:
    """Get the loan repository"""
    container = get_container()
    return container.loan_repository()


def get_loan_rules_service() -> LoanRulesService:
    """Get the loan rules service"""
    container = get_container()
    return container.loan_rules_service()


def get_email_notification_service() -> NotificationServiceInterface:
    """Get the email notification service"""
    container = get_container()
    return container.email_notification_service()


def get_sms_notification_service() -> NotificationServiceInterface:
    """Get the SMS notification service"""
    container = get_container()
    return container.sms_notification_service()


def get_document_storage() -> DocumentStorageInterface:
    """Get the document storage service"""
    container = get_container()
    return container.document_storage()


def get_loan_calculator_service() -> LoanCalculatorService:
    """Get the loan calculator service"""
    container = get_container()
    return container.loan_calculator_service()


def get_loan_application_use_case() -> LoanApplicationUseCase:
    """Get the loan application use case"""
    container = get_container()
    return container.loan_application_use_case()


def get_loan_approval_use_case() -> LoanApprovalUseCase:
    """Get the loan approval use case"""
    container = get_container()
    return container.loan_approval_use_case()


def get_loan_disbursement_use_case() -> LoanDisbursementUseCase:
    """Get the loan disbursement use case"""
    container = get_container()
    return container.loan_disbursement_use_case()
