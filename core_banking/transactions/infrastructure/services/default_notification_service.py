"""
Default Notification Service

Implementation of notification service interface for transaction notifications.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from core_banking.utils.notification_service import send_transaction_notification as core_send_notification
from core_banking.utils.audit_logger import log_event

from ...application.interfaces.notification_service_interface import NotificationServiceInterface
from ...domain.entities.transaction import Transaction

class DefaultNotificationService(NotificationServiceInterface):
    """Default implementation of notification service"""
    
    def __init__(self, environment: str = "development"):
        """
        Initialize the notification service
        
        Args:
            environment: Current environment (development, test, production)
        """
        self._environment = environment
        self._logger = logging.getLogger(__name__)
    
    def send_transaction_notification(self, transaction: Transaction, account_data: Dict[str, Any]) -> bool:
        """
        Send a notification for a transaction
        
        Args:
            transaction: Transaction to send notification for
            account_data: Account data including customer information
            
        Returns:
            True if notification was sent successfully
        """
        try:
            # Extract customer information
            customer_id = account_data.get("customer_id")
            customer_name = account_data.get("customer_name", "Customer")
            
            # Build notification data
            notification_data = {
                "transaction_id": str(transaction.transaction_id),
                "account_id": str(transaction.account_id),
                "account_number": account_data.get("account_number"),
                "amount": str(transaction.amount),
                "transaction_type": transaction.transaction_type.value if transaction.transaction_type else "unknown",
                "status": transaction.status.value,
                "timestamp": transaction.timestamp.isoformat(),
                "description": transaction.description,
                "customer_id": customer_id,
                "customer_name": customer_name
            }
            
            # Add transfer details if applicable
            if transaction.to_account_id:
                notification_data["to_account_id"] = str(transaction.to_account_id)
            
            # Log the notification
            self._logger.info(f"Sending transaction notification: {notification_data}")
            
            # Use core notification service
            core_send_notification(notification_data)
            
            # Audit log
            log_event(
                event_type="transaction_notification",
                entity_type="transaction",
                entity_id=str(transaction.transaction_id),
                description=f"Transaction notification sent for {transaction.transaction_type.value if transaction.transaction_type else 'unknown'} transaction",
                data=notification_data
            )
            
            return True
            
        except Exception as e:
            self._logger.error(f"Error sending transaction notification: {str(e)}")
            
            # Log the error but don't propagate it
            # Transaction processing should continue even if notification fails
            return False
    
    def send_error_notification(self, transaction_id: Optional[UUID], error: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send an error notification
        
        Args:
            transaction_id: Transaction ID if available
            error: Error message
            metadata: Additional error metadata
            
        Returns:
            True if notification was sent successfully
        """
        try:
            # Build error notification data
            error_data = {
                "error": error,
                "timestamp": datetime.now().isoformat(),
                "transaction_id": str(transaction_id) if transaction_id else None,
                "environment": self._environment,
                "metadata": metadata or {}
            }
            
            # Log the error
            self._logger.error(f"Transaction error: {json.dumps(error_data)}")
            
            # In production, we might send to a monitoring system or alert channel
            if self._environment.lower() == "production":
                # Send to alert system
                # This is a placeholder - actual implementation would integrate with
                # a monitoring or alerting system
                pass
            
            # Audit log
            log_event(
                event_type="transaction_error",
                entity_type="transaction",
                entity_id=str(transaction_id) if transaction_id else "unknown",
                description=f"Transaction error: {error}",
                data=error_data
            )
            
            return True
            
        except Exception as e:
            self._logger.error(f"Error sending error notification: {str(e)}")
            return False
    
    def send_security_alert(self, account_id: UUID, alert_type: str, details: Dict[str, Any]) -> bool:
        """
        Send a security alert
        
        Args:
            account_id: Account ID
            alert_type: Type of security alert
            details: Alert details
            
        Returns:
            True if alert was sent successfully
        """
        try:
            # Build security alert data
            alert_data = {
                "account_id": str(account_id),
                "alert_type": alert_type,
                "timestamp": datetime.now().isoformat(),
                "environment": self._environment,
                "details": details
            }
            
            # Log the alert
            self._logger.warning(f"Security alert: {json.dumps(alert_data)}")
            
            # In production, route to security monitoring
            if self._environment.lower() == "production":
                # This would integrate with security monitoring systems
                # For now, just log at high priority
                self._logger.critical(f"SECURITY ALERT: {alert_type} for account {account_id}")
            
            # Audit log
            log_event(
                event_type="security_alert",
                entity_type="account",
                entity_id=str(account_id),
                description=f"Security alert: {alert_type}",
                data=alert_data
            )
            
            return True
            
        except Exception as e:
            self._logger.error(f"Error sending security alert: {str(e)}")
            return False
