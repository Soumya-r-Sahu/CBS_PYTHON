"""
Mock Notification Service Providers

This module provides mock implementations of notification delivery providers
for development and testing purposes.
"""

import time
import random
import logging
from typing import Dict, Any, Optional
from datetime import datetime


logger = logging.getLogger(__name__)


class MockSMSProvider:
    """Mock SMS notification provider"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.api_key = self.config.get('api_key', 'mock_sms_key')
        self.sender_id = self.config.get('sender_id', 'CBS_BANK')
        self.success_rate = self.config.get('success_rate', 0.95)  # 95% success rate
        self.delay_ms = self.config.get('delay_ms', 500)  # 500ms average delay
        
    def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS notification"""
        try:
            # Simulate network delay
            time.sleep(self.delay_ms / 1000)
            
            # Simulate random failures
            if random.random() > self.success_rate:
                return {
                    'success': False,
                    'error_code': 'SMS_DELIVERY_FAILED',
                    'error_message': 'SMS delivery failed due to network error',
                    'provider': 'mock_sms',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Simulate successful delivery
            message_id = f"SMS_{int(time.time())}_{random.randint(1000, 9999)}"
            
            logger.info(f"Mock SMS sent to {phone_number}: {message[:50]}...")
            
            return {
                'success': True,
                'message_id': message_id,
                'provider': 'mock_sms',
                'delivery_status': 'sent',
                'phone_number': phone_number,
                'message_length': len(message),
                'timestamp': datetime.utcnow().isoformat(),
                'cost': 0.05  # Mock cost per SMS
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_code': 'SMS_PROVIDER_ERROR',
                'error_message': f"SMS provider error: {str(e)}",
                'provider': 'mock_sms',
                'timestamp': datetime.utcnow().isoformat()
            }


class MockEmailProvider:
    """Mock email notification provider"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.smtp_host = self.config.get('smtp_host', 'mock.smtp.server')
        self.smtp_port = self.config.get('smtp_port', 587)
        self.from_email = self.config.get('from_email', 'noreply@cbsbank.com')
        self.success_rate = self.config.get('success_rate', 0.98)  # 98% success rate
        self.delay_ms = self.config.get('delay_ms', 800)  # 800ms average delay
        
    def send_email(self, email: str, subject: str, message: str, 
                   html_content: Optional[str] = None) -> Dict[str, Any]:
        """Send email notification"""
        try:
            # Simulate network delay
            time.sleep(self.delay_ms / 1000)
            
            # Simulate random failures
            if random.random() > self.success_rate:
                return {
                    'success': False,
                    'error_code': 'EMAIL_DELIVERY_FAILED',
                    'error_message': 'Email delivery failed due to SMTP error',
                    'provider': 'mock_email',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Simulate successful delivery
            message_id = f"EMAIL_{int(time.time())}_{random.randint(1000, 9999)}"
            
            logger.info(f"Mock Email sent to {email}: {subject}")
            
            return {
                'success': True,
                'message_id': message_id,
                'provider': 'mock_email',
                'delivery_status': 'sent',
                'email': email,
                'subject': subject,
                'message_length': len(message),
                'has_html': html_content is not None,
                'timestamp': datetime.utcnow().isoformat(),
                'cost': 0.01  # Mock cost per email
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_code': 'EMAIL_PROVIDER_ERROR',
                'error_message': f"Email provider error: {str(e)}",
                'provider': 'mock_email',
                'timestamp': datetime.utcnow().isoformat()
            }


class MockPushProvider:
    """Mock push notification provider"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.fcm_key = self.config.get('fcm_key', 'mock_fcm_key')
        self.apns_key = self.config.get('apns_key', 'mock_apns_key')
        self.success_rate = self.config.get('success_rate', 0.90)  # 90% success rate
        self.delay_ms = self.config.get('delay_ms', 300)  # 300ms average delay
        
    def send_push(self, device_token: str, title: str, message: str, 
                  data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send push notification"""
        try:
            # Simulate network delay
            time.sleep(self.delay_ms / 1000)
            
            # Simulate random failures
            if random.random() > self.success_rate:
                failure_reasons = [
                    'Device token invalid',
                    'App not installed',
                    'Device offline',
                    'Push service unavailable'
                ]
                error_reason = random.choice(failure_reasons)
                
                return {
                    'success': False,
                    'error_code': 'PUSH_DELIVERY_FAILED',
                    'error_message': f'Push delivery failed: {error_reason}',
                    'provider': 'mock_push',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Simulate successful delivery
            message_id = f"PUSH_{int(time.time())}_{random.randint(1000, 9999)}"
            
            logger.info(f"Mock Push sent to {device_token[:20]}...: {title}")
            
            return {
                'success': True,
                'message_id': message_id,
                'provider': 'mock_push',
                'delivery_status': 'sent',
                'device_token': device_token[:20] + "...",  # Masked for privacy
                'title': title,
                'message': message,
                'data_keys': list(data.keys()) if data else [],
                'timestamp': datetime.utcnow().isoformat(),
                'cost': 0.001  # Mock cost per push notification
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_code': 'PUSH_PROVIDER_ERROR',
                'error_message': f"Push provider error: {str(e)}",
                'provider': 'mock_push',
                'timestamp': datetime.utcnow().isoformat()
            }


class MockWebhookProvider:
    """Mock webhook notification provider"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.timeout_seconds = self.config.get('timeout_seconds', 30)
        self.success_rate = self.config.get('success_rate', 0.85)  # 85% success rate
        self.delay_ms = self.config.get('delay_ms', 1000)  # 1000ms average delay
        
    def send_webhook(self, webhook_url: str, payload: Dict[str, Any], 
                    headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Send webhook notification"""
        try:
            # Simulate network delay
            time.sleep(self.delay_ms / 1000)
            
            # Simulate random failures
            if random.random() > self.success_rate:
                failure_reasons = [
                    'Webhook endpoint unavailable',
                    'Connection timeout',
                    'HTTP 500 Internal Server Error',
                    'Invalid webhook URL'
                ]
                error_reason = random.choice(failure_reasons)
                
                return {
                    'success': False,
                    'error_code': 'WEBHOOK_DELIVERY_FAILED',
                    'error_message': f'Webhook delivery failed: {error_reason}',
                    'provider': 'mock_webhook',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Simulate successful delivery
            message_id = f"WEBHOOK_{int(time.time())}_{random.randint(1000, 9999)}"
            
            logger.info(f"Mock Webhook sent to {webhook_url}")
            
            return {
                'success': True,
                'message_id': message_id,
                'provider': 'mock_webhook',
                'delivery_status': 'sent',
                'webhook_url': webhook_url,
                'payload_size': len(str(payload)),
                'response_code': 200,
                'response_body': '{"status": "received"}',
                'timestamp': datetime.utcnow().isoformat(),
                'cost': 0.002  # Mock cost per webhook
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_code': 'WEBHOOK_PROVIDER_ERROR',
                'error_message': f"Webhook provider error: {str(e)}",
                'provider': 'mock_webhook',
                'timestamp': datetime.utcnow().isoformat()
            }


class MockInAppProvider:
    """Mock in-app notification provider"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.success_rate = self.config.get('success_rate', 0.99)  # 99% success rate
        self.delay_ms = self.config.get('delay_ms', 100)  # 100ms average delay
        self.storage = {}  # In-memory storage for demo
        
    def send_in_app(self, user_id: str, title: str, message: str, 
                    data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send in-app notification"""
        try:
            # Simulate minimal delay
            time.sleep(self.delay_ms / 1000)
            
            # Simulate random failures (very rare for in-app)
            if random.random() > self.success_rate:
                return {
                    'success': False,
                    'error_code': 'IN_APP_DELIVERY_FAILED',
                    'error_message': 'In-app notification storage failed',
                    'provider': 'mock_in_app',
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            # Simulate successful delivery
            message_id = f"IN_APP_{int(time.time())}_{random.randint(1000, 9999)}"
            
            # Store notification in mock storage
            if user_id not in self.storage:
                self.storage[user_id] = []
            
            notification = {
                'message_id': message_id,
                'title': title,
                'message': message,
                'data': data,
                'timestamp': datetime.utcnow().isoformat(),
                'read': False
            }
            
            self.storage[user_id].append(notification)
            
            logger.info(f"Mock In-App notification stored for user {user_id}: {title}")
            
            return {
                'success': True,
                'message_id': message_id,
                'provider': 'mock_in_app',
                'delivery_status': 'delivered',
                'user_id': user_id,
                'title': title,
                'message': message,
                'timestamp': datetime.utcnow().isoformat(),
                'cost': 0.0  # No cost for in-app notifications
            }
            
        except Exception as e:
            return {
                'success': False,
                'error_code': 'IN_APP_PROVIDER_ERROR',
                'error_message': f"In-app provider error: {str(e)}",
                'provider': 'mock_in_app',
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_user_notifications(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get in-app notifications for a user"""
        user_notifications = self.storage.get(user_id, [])
        return user_notifications[-limit:]  # Return latest notifications
    
    def mark_as_read(self, user_id: str, message_id: str) -> bool:
        """Mark in-app notification as read"""
        user_notifications = self.storage.get(user_id, [])
        for notification in user_notifications:
            if notification['message_id'] == message_id:
                notification['read'] = True
                return True
        return False


class MockNotificationProviderFactory:
    """Factory for creating mock notification providers"""
    
    @staticmethod
    def create_providers(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create all mock notification providers"""
        config = config or {}
        
        return {
            'mock_sms': MockSMSProvider(config.get('sms', {})),
            'mock_email': MockEmailProvider(config.get('email', {})),
            'mock_push': MockPushProvider(config.get('push', {})),
            'mock_webhook': MockWebhookProvider(config.get('webhook', {})),
            'mock_in_app': MockInAppProvider(config.get('in_app', {}))
        }
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default configuration for mock providers"""
        return {
            'sms': {
                'api_key': 'mock_sms_api_key',
                'sender_id': 'CBS_BANK',
                'success_rate': 0.95,
                'delay_ms': 500
            },
            'email': {
                'smtp_host': 'mock.smtp.cbsbank.com',
                'smtp_port': 587,
                'from_email': 'notifications@cbsbank.com',
                'success_rate': 0.98,
                'delay_ms': 800
            },
            'push': {
                'fcm_key': 'mock_fcm_server_key',
                'apns_key': 'mock_apns_key',
                'success_rate': 0.90,
                'delay_ms': 300
            },
            'webhook': {
                'timeout_seconds': 30,
                'success_rate': 0.85,
                'delay_ms': 1000
            },
            'in_app': {
                'success_rate': 0.99,
                'delay_ms': 100
            }
        }


# Enhanced mock provider with realistic banking scenarios
class BankingMockSMSProvider(MockSMSProvider):
    """Enhanced SMS provider with banking-specific scenarios"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.message_templates = {
            'transaction': 'Transaction Alert: {amount} {type} on A/c {account}. Balance: {balance}. Ref: {ref}',
            'security': 'Security Alert: {action} detected on your account. If not done by you, contact us immediately.',
            'payment': 'Payment of {amount} to {beneficiary} successful. Ref: {ref}',
            'loan': 'Loan EMI of {amount} due on {date}. Please ensure sufficient balance.',
            'otp': 'Your OTP for CBS Banking is {otp}. Valid for 5 minutes. Do not share with anyone.'
        }
    
    def send_banking_sms(self, phone_number: str, message_type: str, 
                        template_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send banking-specific SMS with template"""
        template = self.message_templates.get(message_type, '{message}')
        
        try:
            message = template.format(**template_data)
        except KeyError as e:
            return {
                'success': False,
                'error_code': 'TEMPLATE_ERROR',
                'error_message': f'Missing template variable: {e}',
                'provider': 'banking_mock_sms',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        result = self.send_sms(phone_number, message)
        result['message_type'] = message_type
        result['template_data'] = template_data
        
        return result


# Export all mock providers
__all__ = [
    'MockSMSProvider',
    'MockEmailProvider',
    'MockPushProvider',
    'MockWebhookProvider',
    'MockInAppProvider',
    'MockNotificationProviderFactory',
    'BankingMockSMSProvider'
]
