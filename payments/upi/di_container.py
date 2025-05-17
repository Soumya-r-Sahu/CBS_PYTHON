"""
Dependency Injection container for UPI module.
"""
import os
from typing import Dict, Any, Optional

# Domain layer
from .domain.services.transaction_rules_service import UpiTransactionRulesService
from .domain.services.vpa_validation_service import VpaValidationService

# Application layer
from .application.use_cases.send_money_use_case import SendMoneyUseCase
from .application.use_cases.complete_transaction_use_case import CompleteTransactionUseCase

# Infrastructure layer
from .infrastructure.repositories.sql_upi_transaction_repository import SqlUpiTransactionRepository
from .infrastructure.services.sms_notification_service import SmsNotificationService
from .infrastructure.services.email_notification_service import EmailNotificationService

# Presentation layer
from .presentation.api.upi_controller import UpiController
from .presentation.cli.upi_cli import UpiCli


class UpiDiContainer:
    """Dependency Injection container for UPI module."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the container with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self._instances = {}
    
    def get_vpa_phone_mapper(self):
        """Get the function to map VPA to phone number."""
        # This is a placeholder implementation
        # In a real system, this would query a database or service
        def map_vpa_to_phone(vpa: str) -> Optional[str]:
            # Mock implementation - in real system would query a database
            mock_mappings = {
                'john@oksbi': '+919876543210',
                'jane@okicici': '+919876543211',
                'alice@ybl': '+919876543212',
                'bob@paytm': '+919876543213',
            }
            return mock_mappings.get(vpa)
        
        return map_vpa_to_phone
    
    def get_vpa_email_mapper(self):
        """Get the function to map VPA to email address."""
        # This is a placeholder implementation
        # In a real system, this would query a database or service
        def map_vpa_to_email(vpa: str) -> Optional[str]:
            # Mock implementation - in real system would query a database
            parts = vpa.split('@')
            if len(parts) == 2:
                username = parts[0]
                return f"{username}@example.com"
            return None
        
        return map_vpa_to_email
    
    def get_transaction_rules_service(self):
        """Get the transaction rules service instance."""
        if 'transaction_rules_service' not in self._instances:
            self._instances['transaction_rules_service'] = UpiTransactionRulesService(
                daily_transaction_limit=self.config.get('daily_transaction_limit', 100000.0),
                per_transaction_limit=self.config.get('per_transaction_limit', 25000.0)
            )
        return self._instances['transaction_rules_service']
    
    def get_vpa_validation_service(self):
        """Get the VPA validation service instance."""
        if 'vpa_validation_service' not in self._instances:
            self._instances['vpa_validation_service'] = VpaValidationService()
        return self._instances['vpa_validation_service']
    
    def get_transaction_repository(self):
        """Get the transaction repository instance."""
        if 'transaction_repository' not in self._instances:
            db_path = self.config.get('db_path', os.path.join('database', 'upi_transactions.db'))
            self._instances['transaction_repository'] = SqlUpiTransactionRepository(db_path)
        return self._instances['transaction_repository']
    
    def get_notification_service(self):
        """Get the notification service instance."""
        if 'notification_service' not in self._instances:
            notification_type = self.config.get('notification_type', 'sms')
            
            if notification_type == 'email':
                smtp_config = self.config.get('smtp_config', {
                    'from_email': 'upi-notifications@bank.com'
                })
                self._instances['notification_service'] = EmailNotificationService(
                    smtp_config=smtp_config,
                    vpa_email_mapper=self.get_vpa_email_mapper()
                )
            else:
                # Default to SMS
                self._instances['notification_service'] = SmsNotificationService(
                    sms_api_key=self.config.get('sms_api_key', 'mock_api_key'),
                    sms_sender_id=self.config.get('sms_sender_id', 'UPIPAY'),
                    vpa_phone_mapper=self.get_vpa_phone_mapper()
                )
        
        return self._instances['notification_service']
    
    def get_send_money_use_case(self):
        """Get the send money use case instance."""
        if 'send_money_use_case' not in self._instances:
            self._instances['send_money_use_case'] = SendMoneyUseCase(
                transaction_repository=self.get_transaction_repository(),
                notification_service=self.get_notification_service(),
                transaction_rules_service=self.get_transaction_rules_service(),
                vpa_validation_service=self.get_vpa_validation_service()
            )
        return self._instances['send_money_use_case']
    
    def get_complete_transaction_use_case(self):
        """Get the complete transaction use case instance."""
        if 'complete_transaction_use_case' not in self._instances:
            self._instances['complete_transaction_use_case'] = CompleteTransactionUseCase(
                transaction_repository=self.get_transaction_repository(),
                notification_service=self.get_notification_service()
            )
        return self._instances['complete_transaction_use_case']
    
    def get_upi_controller(self):
        """Get the UPI controller instance."""
        if 'upi_controller' not in self._instances:
            self._instances['upi_controller'] = UpiController(
                send_money_use_case=self.get_send_money_use_case(),
                complete_transaction_use_case=self.get_complete_transaction_use_case()
            )
        return self._instances['upi_controller']
    
    def get_upi_cli(self):
        """Get the UPI CLI instance."""
        if 'upi_cli' not in self._instances:
            self._instances['upi_cli'] = UpiCli(
                send_money_use_case=self.get_send_money_use_case(),
                complete_transaction_use_case=self.get_complete_transaction_use_case()
            )
        return self._instances['upi_cli']
