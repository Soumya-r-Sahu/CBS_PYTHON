"""
Employee Management DI Container

This module implements a simple dependency injection container for the 
employee management component. It wires together the various layers of
the clean architecture.
"""

import logging
from functools import lru_cache
from typing import Optional

from .application.use_cases.onboard_employee_use_case import OnboardEmployeeUseCase
from .application.interfaces.notification_service import NotificationService
from .application.interfaces.document_service import DocumentService
from .domain.repositories.employee_repository import EmployeeRepository
from .infrastructure.repositories.sql_employee_repository import SqlEmployeeRepository
from .infrastructure.notification.email_notification_service import EmailNotificationService
from .infrastructure.document.file_system_document_service import FileSystemDocumentService

# Import database connection
from ..utils.db_connection import get_db_connection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Service instances
_employee_repository: Optional[EmployeeRepository] = None
_notification_service: Optional[NotificationService] = None
_document_service: Optional[DocumentService] = None


@lru_cache(maxsize=1)
def get_employee_repository() -> EmployeeRepository:
    """
    Get the employee repository instance
    
    Returns:
        An implementation of EmployeeRepository
    """
    global _employee_repository
    if _employee_repository is None:
        db_connection = get_db_connection()
        _employee_repository = SqlEmployeeRepository(db_connection)
    return _employee_repository


@lru_cache(maxsize=1)
def get_notification_service() -> NotificationService:
    """
    Get the notification service instance
    
    Returns:
        An implementation of NotificationService
    """
    global _notification_service
    if _notification_service is None:
        _notification_service = EmailNotificationService()
    return _notification_service


@lru_cache(maxsize=1)
def get_document_service() -> DocumentService:
    """
    Get the document service instance
    
    Returns:
        An implementation of DocumentService
    """
    global _document_service
    if _document_service is None:
        _document_service = FileSystemDocumentService()
    return _document_service


@lru_cache(maxsize=1)
def get_employee_onboarding_use_case() -> OnboardEmployeeUseCase:
    """
    Get the employee onboarding use case instance
    
    Returns:
        An instance of OnboardEmployeeUseCase
    """
    return OnboardEmployeeUseCase(
        employee_repository=get_employee_repository(),
        notification_service=get_notification_service(),
        document_service=get_document_service()
    )