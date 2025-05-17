"""
RTGS Dependency Injection Container.
"""
import os
from typing import Dict, Any

from .domain.services.rtgs_validation_service import RTGSValidationService
from .domain.services.rtgs_batch_service import RTGSBatchService

from .application.use_cases.transaction_creation_use_case import RTGSTransactionCreationUseCase
from .application.use_cases.transaction_processing_use_case import RTGSTransactionProcessingUseCase
from .application.use_cases.transaction_query_use_case import RTGSTransactionQueryUseCase
from .application.use_cases.batch_processing_use_case import RTGSBatchProcessingUseCase
from .application.use_cases.batch_query_use_case import RTGSBatchQueryUseCase

from .infrastructure.repositories.sql_rtgs_transaction_repository import SQLRTGSTransactionRepository
from .infrastructure.repositories.sql_rtgs_batch_repository import SQLRTGSBatchRepository
from .infrastructure.services.rtgs_rbi_interface_service import RTGSRBIInterfaceService
from .infrastructure.services.sms_notification_service import SMSNotificationService
from .infrastructure.services.sql_audit_log_service import SQLAuditLogService


class RTGSDiContainer:
    """Dependency Injection Container for RTGS module."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the container.
        
        Args:
            config: Module configuration
        """
        self.config = config
        self._setup_paths()
        
        # Lazily initialized components
        self._transaction_repository = None
        self._batch_repository = None
        self._validation_service = None
        self._batch_service = None
        self._rbi_interface_service = None
        self._notification_service = None
        self._audit_log_service = None
        
        # Use cases
        self._transaction_creation_use_case = None
        self._transaction_processing_use_case = None
        self._transaction_query_use_case = None
        self._batch_processing_use_case = None
        self._batch_query_use_case = None
    
    def _setup_paths(self):
        """Set up paths for database files."""
        db_dir = self.config.get('db_dir', os.path.join('database', 'payments'))
        os.makedirs(db_dir, exist_ok=True)
        
        self.db_path = os.path.join(db_dir, 'rtgs.db')
    
    # Domain services
    
    def get_validation_service(self) -> RTGSValidationService:
        """Get the validation service."""
        if not self._validation_service:
            per_transaction_limit = self.config.get('per_transaction_limit', 100000000.0)  # 10 crores default
            self._validation_service = RTGSValidationService(per_transaction_limit)
        return self._validation_service
    
    def get_batch_service(self) -> RTGSBatchService:
        """Get the batch service."""
        if not self._batch_service:
            operating_window = self.config.get('rtgs_operating_window', (9, 16, 30))  # 9AM to 4:30PM default
            cutoff_time = self.config.get('rtgs_cutoff_time', '16:00')  # 4PM default
            self._batch_service = RTGSBatchService(operating_window, cutoff_time)
        return self._batch_service
    
    # Repositories
    
    def get_transaction_repository(self) -> SQLRTGSTransactionRepository:
        """Get the transaction repository."""
        if not self._transaction_repository:
            self._transaction_repository = SQLRTGSTransactionRepository(self.db_path)
        return self._transaction_repository
    
    def get_batch_repository(self) -> SQLRTGSBatchRepository:
        """Get the batch repository."""
        if not self._batch_repository:
            self._batch_repository = SQLRTGSBatchRepository(self.db_path)
        return self._batch_repository
    
    # Infrastructure services
    
    def get_rbi_interface_service(self) -> RTGSRBIInterfaceService:
        """Get the RBI interface service."""
        if not self._rbi_interface_service:
            api_url = self.config.get('rbi_api_url', 'https://api.rbi.org.in')
            api_key = self.config.get('rbi_api_key', 'mock_api_key')
            use_mock = self.config.get('USE_MOCK', True)
            self._rbi_interface_service = RTGSRBIInterfaceService(api_url, api_key, use_mock)
        return self._rbi_interface_service
    
    def get_notification_service(self) -> SMSNotificationService:
        """Get the notification service."""
        if not self._notification_service:
            api_url = self.config.get('sms_api_url', 'https://api.sms.provider.com')
            api_key = self.config.get('sms_api_key', 'mock_api_key')
            sender_id = self.config.get('sms_sender_id', 'RTGSBNK')
            use_mock = self.config.get('USE_MOCK', True)
            self._notification_service = SMSNotificationService(api_url, api_key, sender_id, use_mock)
        return self._notification_service
    
    def get_audit_log_service(self) -> SQLAuditLogService:
        """Get the audit log service."""
        if not self._audit_log_service:
            self._audit_log_service = SQLAuditLogService(self.db_path)
        return self._audit_log_service
    
    # Use cases
    
    def get_transaction_creation_use_case(self) -> RTGSTransactionCreationUseCase:
        """Get the transaction creation use case."""
        if not self._transaction_creation_use_case:
            self._transaction_creation_use_case = RTGSTransactionCreationUseCase(
                transaction_repository=self.get_transaction_repository(),
                validation_service=self.get_validation_service(),
                audit_log_service=self.get_audit_log_service(),
                notification_service=self.get_notification_service()
            )
        return self._transaction_creation_use_case
    
    def get_transaction_processing_use_case(self) -> RTGSTransactionProcessingUseCase:
        """Get the transaction processing use case."""
        if not self._transaction_processing_use_case:
            self._transaction_processing_use_case = RTGSTransactionProcessingUseCase(
                transaction_repository=self.get_transaction_repository(),
                batch_repository=self.get_batch_repository(),
                rbi_interface_service=self.get_rbi_interface_service(),
                batch_service=self.get_batch_service(),
                audit_log_service=self.get_audit_log_service(),
                notification_service=self.get_notification_service()
            )
        return self._transaction_processing_use_case
    
    def get_transaction_query_use_case(self) -> RTGSTransactionQueryUseCase:
        """Get the transaction query use case."""
        if not self._transaction_query_use_case:
            self._transaction_query_use_case = RTGSTransactionQueryUseCase(
                transaction_repository=self.get_transaction_repository()
            )
        return self._transaction_query_use_case
    
    def get_batch_processing_use_case(self) -> RTGSBatchProcessingUseCase:
        """Get the batch processing use case."""
        if not self._batch_processing_use_case:
            self._batch_processing_use_case = RTGSBatchProcessingUseCase(
                batch_repository=self.get_batch_repository(),
                transaction_repository=self.get_transaction_repository(),
                rbi_interface_service=self.get_rbi_interface_service(),
                batch_service=self.get_batch_service(),
                audit_log_service=self.get_audit_log_service()
            )
        return self._batch_processing_use_case
    
    def get_batch_query_use_case(self) -> RTGSBatchQueryUseCase:
        """Get the batch query use case."""
        if not self._batch_query_use_case:
            self._batch_query_use_case = RTGSBatchQueryUseCase(
                batch_repository=self.get_batch_repository(),
                transaction_repository=self.get_transaction_repository()
            )
        return self._batch_query_use_case
