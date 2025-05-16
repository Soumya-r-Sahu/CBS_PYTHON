"""
Dependency Injection Container for Customer Management Module

This module sets up the dependency injection container for the Customer Management module,
wiring together all dependencies according to Clean Architecture principles.
"""

from dependency_injector import containers, providers
import os

# Domain Services
from .domain.services.kyc_rules_service import KycRulesService

# Application Use Cases
from .application.use_cases.create_customer import CreateCustomerUseCase
from .application.use_cases.verify_customer_kyc import VerifyCustomerKycUseCase

# Infrastructure
from .infrastructure.repositories.sql_customer_repository import SqlCustomerRepository

# Database Connection
from ..database.python.db_connection import get_database_connection


class CustomerManagementContainer(containers.DeclarativeContainer):
    """
    Dependency Injection Container for Customer Management module
    
    This container wires together all dependencies for the Customer Management module,
    following Clean Architecture principles with clear separation between
    domain, application, and infrastructure layers.
    """
    
    # Configuration
    config = providers.Configuration()
    
    # Set default configuration values
    config.set_default({
        'db_connection_string': os.environ.get('CBS_DB_CONNECTION', 'sqlite:///customer_management.db'),
        'kyc_rules': {
            'high_value_threshold': 1000000,
            'medium_value_threshold': 100000,
            'high_risk_countries': ['XY', 'YZ', 'ZZ'],  # Example fictional high-risk countries
            'documents_validity_period': 365
        }
    })
    
    # Domain Services
    kyc_rules_service = providers.Singleton(
        KycRulesService,
        config=config.kyc_rules
    )
    
    # Infrastructure Layer
    customer_repository = providers.Singleton(
        SqlCustomerRepository,
        connection_string=config.db_connection_string
    )
    
    # Application Layer - Use Cases
    create_customer_use_case = providers.Factory(
        CreateCustomerUseCase,
        customer_repository=customer_repository,
        kyc_rules_service=kyc_rules_service
    )
    
    verify_customer_kyc_use_case = providers.Factory(
        VerifyCustomerKycUseCase,
        customer_repository=customer_repository,
        kyc_rules_service=kyc_rules_service
    )


# Create a default container instance
def get_container():
    """Get configured dependency injection container"""
    container = CustomerManagementContainer()
    return container


# Helper functions to access use cases
def get_create_customer_use_case():
    """Get the create customer use case"""
    container = get_container()
    return container.create_customer_use_case()


def get_verify_customer_kyc_use_case():
    """Get the verify customer KYC use case"""
    container = get_container()
    return container.verify_customer_kyc_use_case()
