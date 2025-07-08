"""
Dependency Injection container for NEFT module.
"""
import os
import sqlite3
from typing import Dict, Any

# Domain layer
from .domain.services.neft_validation_service import NEFTValidationService
from .domain.services.neft_batch_service import NEFTBatchService

# Application layer
from .application.use_cases.transaction_creation_use_case import NEFTTransactionCreationUseCase
from .application.use_cases.transaction_processing_use_case import NEFTTransactionProcessingUseCase
from .application.use_cases.batch_processing_use_case import NEFTBatchProcessingUseCase
from .application.use_cases.transaction_query_use_case import NEFTTransactionQueryUseCase
from .application.use_cases.batch_query_use_case import NEFTBatchQueryUseCase

# Infrastructure layer
from .infrastructure.repositories.sql_neft_transaction_repository import SQLNEFTTransactionRepository
from .infrastructure.repositories.sql_neft_batch_repository import SQLNEFTBatchRepository
from .infrastructure.services.sms_notification_service import SMSNotificationService
from .infrastructure.services.neft_rbi_interface_service import NEFTRbiInterfaceService
from .infrastructure.services.sql_audit_log_service import SQLNEFTAuditLogService

# Presentation layer
from .presentation.api.neft_controller import NEFTController
from .presentation.cli.neft_cli import NEFTCli


class NEFTDiContainer:
    """Dependency Injection container for NEFT module."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the container with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self._instances = {}
        
        # Create database connection
        self._create_db_connection()
    
    def _create_db_connection(self):
        """Create and initialize database connection."""
        db_path = self.config.get('db_path', os.path.join('database', 'neft_transactions.db'))
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Create database connection
        self._db_connection = sqlite3.connect(db_path, check_same_thread=False)
        
        # Enable foreign keys
        self._db_connection.execute("PRAGMA foreign_keys = ON")
        
        # Initialize database schema
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Initialize database schema if not exists."""
        cursor = self._db_connection.cursor()
        
        # Create transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS neft_transactions (
                id TEXT PRIMARY KEY,
                transaction_reference TEXT NOT NULL,
                utr_number TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                processed_at TEXT,
                completed_at TEXT,
                batch_number TEXT,
                return_reason TEXT,
                error_message TEXT,
                customer_id TEXT,
                metadata TEXT,
                payment_details TEXT NOT NULL
            )
        """)
        
        # Create batches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS neft_batches (
                id TEXT PRIMARY KEY,
                batch_number TEXT NOT NULL UNIQUE,
                batch_time TEXT NOT NULL,
                total_transactions INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                completed_transactions INTEGER NOT NULL,
                failed_transactions INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                submitted_at TEXT,
                completed_at TEXT,
                transaction_ids TEXT,
                metadata TEXT
            )
        """)
        
        # Create audit logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS neft_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                action TEXT NOT NULL,
                previous_state TEXT,
                current_state TEXT NOT NULL,
                details TEXT,
                timestamp TEXT NOT NULL,
                user_id TEXT
            )
        """)
        
        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_status ON neft_transactions (status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_customer ON neft_transactions (customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_batch ON neft_transactions (batch_number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_batches_status ON neft_batches (status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_batches_time ON neft_batches (batch_time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_entity ON neft_audit_logs (entity_type, entity_id)")
        
        self._db_connection.commit()
    
    # Domain services
    
    def get_validation_service(self):
        """Get the validation service instance."""
        if 'validation_service' not in self._instances:
            self._instances['validation_service'] = NEFTValidationService(
                per_transaction_limit=self.config.get('per_transaction_limit', 10000000.0)
            )
        return self._instances['validation_service']
    
    def get_batch_service(self):
        """Get the batch service instance."""
        if 'batch_service' not in self._instances:
            self._instances['batch_service'] = NEFTBatchService(
                batch_times=self.config.get('batch_times', ["00:30", "10:30", "13:30", "16:30"]),
                hold_minutes=self.config.get('hold_minutes', 10)
            )
        return self._instances['batch_service']
    
    # Infrastructure repositories
    
    def get_transaction_repository(self):
        """Get the transaction repository instance."""
        if 'transaction_repository' not in self._instances:
            self._instances['transaction_repository'] = SQLNEFTTransactionRepository(
                db_connection=self._db_connection
            )
        return self._instances['transaction_repository']
    
    def get_batch_repository(self):
        """Get the batch repository instance."""
        if 'batch_repository' not in self._instances:
            self._instances['batch_repository'] = SQLNEFTBatchRepository(
                db_connection=self._db_connection
            )
        return self._instances['batch_repository']
    
    # Infrastructure services
    
    def get_notification_service(self):
        """Get the notification service instance."""
        if 'notification_service' not in self._instances:
            self._instances['notification_service'] = SMSNotificationService(
                config={
                    'sms_api_key': self.config.get('sms_api_key', 'mock_api_key'),
                    'sms_sender_id': self.config.get('sms_sender_id', 'NEFTPY'),
                    'admin_phone_numbers': self.config.get('admin_phone_numbers', [])
                },
                mock_mode=self.config.get('mock_mode', True)
            )
        return self._instances['notification_service']
    
    def get_rbi_interface_service(self):
        """Get the RBI interface service instance."""
        if 'rbi_interface_service' not in self._instances:
            self._instances['rbi_interface_service'] = NEFTRbiInterfaceService(
                config={
                    'rbi_neft_service_url': self.config.get('rbi_neft_service_url', 'https://rbi-neft-api.example.com'),
                    'connection_timeout_seconds': self.config.get('connection_timeout_seconds', 30),
                    'request_timeout_seconds': self.config.get('request_timeout_seconds', 60),
                    'rbi_api_key': self.config.get('rbi_api_key', 'mock_api_key'),
                    'bank_code': self.config.get('bank_code', 'MOCK1')
                },
                mock_mode=self.config.get('mock_mode', True)
            )
        return self._instances['rbi_interface_service']
    
    def get_audit_log_service(self):
        """Get the audit log service instance."""
        if 'audit_log_service' not in self._instances:
            self._instances['audit_log_service'] = SQLNEFTAuditLogService(
                db_connection=self._db_connection
            )
        return self._instances['audit_log_service']
    
    # Application use cases
    
    def get_transaction_creation_use_case(self):
        """Get the transaction creation use case instance."""
        if 'transaction_creation_use_case' not in self._instances:
            self._instances['transaction_creation_use_case'] = NEFTTransactionCreationUseCase(
                transaction_repository=self.get_transaction_repository(),
                validation_service=self.get_validation_service(),
                audit_log_service=self.get_audit_log_service(),
                notification_service=self.get_notification_service()
            )
        return self._instances['transaction_creation_use_case']
    
    def get_transaction_processing_use_case(self):
        """Get the transaction processing use case instance."""
        if 'transaction_processing_use_case' not in self._instances:
            self._instances['transaction_processing_use_case'] = NEFTTransactionProcessingUseCase(
                transaction_repository=self.get_transaction_repository(),
                batch_repository=self.get_batch_repository(),
                batch_service=self.get_batch_service(),
                audit_log_service=self.get_audit_log_service(),
                notification_service=self.get_notification_service()
            )
        return self._instances['transaction_processing_use_case']
    
    def get_batch_processing_use_case(self):
        """Get the batch processing use case instance."""
        if 'batch_processing_use_case' not in self._instances:
            self._instances['batch_processing_use_case'] = NEFTBatchProcessingUseCase(
                batch_repository=self.get_batch_repository(),
                transaction_repository=self.get_transaction_repository(),
                rbi_interface_service=self.get_rbi_interface_service(),
                audit_log_service=self.get_audit_log_service(),
                notification_service=self.get_notification_service(),
                mock_mode=self.config.get('mock_mode', True)
            )
        return self._instances['batch_processing_use_case']
    
    def get_transaction_query_use_case(self):
        """Get the transaction query use case instance."""
        if 'transaction_query_use_case' not in self._instances:
            self._instances['transaction_query_use_case'] = NEFTTransactionQueryUseCase(
                transaction_repository=self.get_transaction_repository(),
                audit_log_service=self.get_audit_log_service()
            )
        return self._instances['transaction_query_use_case']
    
    def get_batch_query_use_case(self):
        """Get the batch query use case instance."""
        if 'batch_query_use_case' not in self._instances:
            self._instances['batch_query_use_case'] = NEFTBatchQueryUseCase(
                batch_repository=self.get_batch_repository(),
                audit_log_service=self.get_audit_log_service()
            )
        return self._instances['batch_query_use_case']
    
    # Presentation controllers
    
    def get_neft_controller(self):
        """Get the NEFT API controller instance."""
        if 'neft_controller' not in self._instances:
            self._instances['neft_controller'] = NEFTController(
                transaction_creation_use_case=self.get_transaction_creation_use_case(),
                transaction_processing_use_case=self.get_transaction_processing_use_case(),
                batch_processing_use_case=self.get_batch_processing_use_case(),
                transaction_query_use_case=self.get_transaction_query_use_case(),
                batch_query_use_case=self.get_batch_query_use_case()
            )
        return self._instances['neft_controller']
    
    def get_neft_cli(self):
        """Get the NEFT CLI instance."""
        if 'neft_cli' not in self._instances:
            self._instances['neft_cli'] = NEFTCli(
                transaction_creation_use_case=self.get_transaction_creation_use_case(),
                transaction_processing_use_case=self.get_transaction_processing_use_case(),
                batch_processing_use_case=self.get_batch_processing_use_case(),
                transaction_query_use_case=self.get_transaction_query_use_case(),
                batch_query_use_case=self.get_batch_query_use_case()
            )
        return self._instances['neft_cli']
