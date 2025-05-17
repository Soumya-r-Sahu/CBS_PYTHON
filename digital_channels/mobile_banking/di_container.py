"""
Dependency Injection container for Mobile Banking module.
"""
import os
import sqlite3
from typing import Dict, Any, Optional

# Domain layer
from .domain.services.mobile_authentication_service import MobileAuthenticationService
from .domain.services.mobile_security_policy_service import MobileSecurityPolicyService

# Application layer
from .application.use_cases.authentication_use_case import AuthenticationUseCase
from .application.use_cases.session_management_use_case import SessionManagementUseCase
from .application.use_cases.transaction_management_use_case import TransactionManagementUseCase
from .application.use_cases.user_management_use_case import UserManagementUseCase

# Infrastructure layer
from .infrastructure.repositories.sql_mobile_user_repository import SQLMobileUserRepository
from .infrastructure.repositories.sql_mobile_session_repository import SQLMobileSessionRepository
from .infrastructure.repositories.sql_mobile_transaction_repository import SQLMobileTransactionRepository
from .infrastructure.services.sql_audit_log_service import SQLAuditLogService
from .infrastructure.services.sms_notification_service import SMSNotificationService

# Presentation layer (will be added later)


class MobileBankingDiContainer:
    """Dependency Injection container for Mobile Banking module."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the container with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self._instances = {}
        
        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config['db_path']), exist_ok=True)
    
    def get_db_connection(self):
        """Get SQLite database connection."""
        if 'db_connection' not in self._instances:
            self._instances['db_connection'] = sqlite3.connect(
                self.config['db_path'],
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            # Enable foreign keys
            self._instances['db_connection'].execute("PRAGMA foreign_keys = ON")
        
        return self._instances['db_connection']
    
    # Domain layer services
    
    def get_authentication_service(self):
        """Get the authentication service."""
        if 'authentication_service' not in self._instances:
            self._instances['authentication_service'] = MobileAuthenticationService()
        
        return self._instances['authentication_service']
    
    def get_security_policy_service(self):
        """Get the security policy service."""
        if 'security_policy_service' not in self._instances:
            self._instances['security_policy_service'] = MobileSecurityPolicyService(
                per_transaction_limit=self.config.get('per_transaction_limit', 25000.0),
                daily_transaction_limit=self.config.get('daily_transaction_limit', 100000.0),
                max_session_idle_minutes=self.config.get('max_session_idle_minutes', 15),
                failed_login_limit=self.config.get('failed_login_limit', 5),
                enforce_device_binding=self.config.get('enforce_device_binding', True)
            )
        
        return self._instances['security_policy_service']
    
    # Repository layer
    
    def get_user_repository(self):
        """Get the user repository."""
        if 'user_repository' not in self._instances:
            self._instances['user_repository'] = SQLMobileUserRepository(
                db_connection=self.get_db_connection()
            )
        
        return self._instances['user_repository']
    
    def get_session_repository(self):
        """Get the session repository."""
        if 'session_repository' not in self._instances:
            self._instances['session_repository'] = SQLMobileSessionRepository(
                db_connection=self.get_db_connection()
            )
        
        return self._instances['session_repository']
    
    def get_transaction_repository(self):
        """Get the transaction repository."""
        if 'transaction_repository' not in self._instances:
            self._instances['transaction_repository'] = SQLMobileTransactionRepository(
                db_connection=self.get_db_connection()
            )
        
        return self._instances['transaction_repository']
    
    # Service layer
    
    def get_audit_log_service(self):
        """Get the audit log service."""
        if 'audit_log_service' not in self._instances:
            self._instances['audit_log_service'] = SQLAuditLogService(
                db_connection=self.get_db_connection()
            )
        
        return self._instances['audit_log_service']
    
    def get_notification_service(self):
        """Get the notification service."""
        if 'notification_service' not in self._instances:
            notification_type = self.config.get('notification_type', 'sms')
            
            if notification_type == 'sms':
                self._instances['notification_service'] = SMSNotificationService(
                    user_repository=self.get_user_repository(),
                    api_key=self.config.get('sms_api_key', ''),
                    sender_id=self.config.get('sms_sender_id', 'MOBBNK'),
                    use_mock=self.config.get('USE_MOCK', True)
                )
            else:
                # For future implementation of email or push notification service
                self._instances['notification_service'] = SMSNotificationService(
                    user_repository=self.get_user_repository(),
                    api_key=self.config.get('sms_api_key', ''),
                    sender_id=self.config.get('sms_sender_id', 'MOBBNK'),
                    use_mock=self.config.get('USE_MOCK', True)
                )
        
        return self._instances['notification_service']
    
    # Use case layer
    
    def get_authentication_use_case(self):
        """Get the authentication use case."""
        if 'authentication_use_case' not in self._instances:
            self._instances['authentication_use_case'] = AuthenticationUseCase(
                user_repository=self.get_user_repository(),
                session_repository=self.get_session_repository(),
                notification_service=self.get_notification_service(),
                audit_log_service=self.get_audit_log_service(),
                auth_service=self.get_authentication_service(),
                security_policy_service=self.get_security_policy_service()
            )
        
        return self._instances['authentication_use_case']
    
    def get_session_management_use_case(self):
        """Get the session management use case."""
        if 'session_management_use_case' not in self._instances:
            self._instances['session_management_use_case'] = SessionManagementUseCase(
                session_repository=self.get_session_repository(),
                user_repository=self.get_user_repository(),
                audit_log_service=self.get_audit_log_service(),
                security_policy_service=self.get_security_policy_service()
            )
        
        return self._instances['session_management_use_case']
    
    def get_transaction_management_use_case(self):
        """Get the transaction management use case."""
        if 'transaction_management_use_case' not in self._instances:
            self._instances['transaction_management_use_case'] = TransactionManagementUseCase(
                transaction_repository=self.get_transaction_repository(),
                user_repository=self.get_user_repository(),
                notification_service=self.get_notification_service(),
                audit_log_service=self.get_audit_log_service(),
                security_policy_service=self.get_security_policy_service()
            )
        
        return self._instances['transaction_management_use_case']
    
    def get_user_management_use_case(self):
        """Get the user management use case."""
        if 'user_management_use_case' not in self._instances:
            self._instances['user_management_use_case'] = UserManagementUseCase(
                user_repository=self.get_user_repository(),
                notification_service=self.get_notification_service(),
                audit_log_service=self.get_audit_log_service(),
                auth_service=self.get_authentication_service(),
                security_policy_service=self.get_security_policy_service()
            )
        
        return self._instances['user_management_use_case']
