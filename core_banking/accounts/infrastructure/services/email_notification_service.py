"""
Email Notification Service

This module provides implementation of notification service using email.
"""

import logging
import smtplib
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional

from ...interfaces.notification_service import NotificationServiceInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class EmailNotificationService(NotificationServiceInterface):
    """Email implementation of notification service"""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        customer_email_provider
    ):
        """
        Initialize email notification service
        
        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            smtp_user: SMTP server username
            smtp_password: SMTP server password
            from_email: From email address
            customer_email_provider: Provider for getting customer email address
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.customer_email_provider = customer_email_provider
        self.logger = logging.getLogger(__name__)
    
    def send_transaction_notification(self,
                                    account_number: str,
                                    transaction_type: str,
                                    amount: Decimal,
                                    balance: Decimal,
                                    timestamp: str,
                                    reference_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a notification for a transaction via email
        
        Args:
            account_number: The account number
            transaction_type: The transaction type
            amount: The transaction amount
            balance: The account balance after the transaction
            timestamp: The transaction timestamp
            reference_id: Optional reference ID
            
        Returns:
            Dictionary with notification result
        """
        try:
            customer_email = self._get_customer_email(account_number)
            if not customer_email:
                return {
                    "success": False,
                    "message": f"Customer email not found for account {account_number}"
                }
            
            subject = f"Transaction Notification - {transaction_type}"
            
            # Format amount and balance
            formatted_amount = f"{amount:,.2f}"
            formatted_balance = f"{balance:,.2f}"
            
            body = f"""
            <html>
            <body>
                <h3>Transaction Notification</h3>
                <p>Dear Customer,</p>
                <p>A {transaction_type} transaction has been completed on your account.</p>
                <p><strong>Details:</strong></p>
                <ul>
                    <li>Account Number: {self._mask_account_number(account_number)}</li>
                    <li>Transaction Type: {transaction_type}</li>
                    <li>Amount: {formatted_amount}</li>
                    <li>Balance: {formatted_balance}</li>
                    <li>Date/Time: {timestamp}</li>
                    <li>Reference: {reference_id or 'N/A'}</li>
                </ul>
                <p>If you did not authorize this transaction, please contact our customer service immediately.</p>
                <p>Thank you for banking with us.</p>
                <p><em>This is an automated message, please do not reply.</em></p>
            </body>
            </html>
            """
            
            self._send_email(customer_email, subject, body)
            
            return {
                "success": True,
                "message": f"Transaction notification sent to {self._mask_email(customer_email)}"
            }
        except Exception as e:
            self.logger.error(f"Error sending transaction notification: {e}")
            return {
                "success": False,
                "message": f"Failed to send transaction notification: {str(e)}"
            }
    
    def send_account_status_notification(self,
                                       account_number: str,
                                       status: str,
                                       timestamp: str,
                                       reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Send a notification for an account status change via email
        
        Args:
            account_number: The account number
            status: The new status
            timestamp: The timestamp of the change
            reason: Optional reason for the status change
            
        Returns:
            Dictionary with notification result
        """
        try:
            customer_email = self._get_customer_email(account_number)
            if not customer_email:
                return {
                    "success": False,
                    "message": f"Customer email not found for account {account_number}"
                }
            
            subject = f"Account Status Update - {status}"
            
            body = f"""
            <html>
            <body>
                <h3>Account Status Notification</h3>
                <p>Dear Customer,</p>
                <p>The status of your account has been updated.</p>
                <p><strong>Details:</strong></p>
                <ul>
                    <li>Account Number: {self._mask_account_number(account_number)}</li>
                    <li>New Status: {status}</li>
                    <li>Date/Time: {timestamp}</li>
                    <li>Reason: {reason or 'N/A'}</li>
                </ul>
                <p>If you have any questions, please contact our customer service.</p>
                <p>Thank you for banking with us.</p>
                <p><em>This is an automated message, please do not reply.</em></p>
            </body>
            </html>
            """
            
            self._send_email(customer_email, subject, body)
            
            return {
                "success": True,
                "message": f"Account status notification sent to {self._mask_email(customer_email)}"
            }
        except Exception as e:
            self.logger.error(f"Error sending account status notification: {e}")
            return {
                "success": False,
                "message": f"Failed to send account status notification: {str(e)}"
            }
    
    def _get_customer_email(self, account_number: str) -> Optional[str]:
        """
        Get customer email address from account number
        
        Args:
            account_number: The account number
            
        Returns:
            Customer email address
        """
        try:
            # Use the customer email provider to get the email address
            # This could be a service or repository that maps account numbers to customer emails
            return self.customer_email_provider.get_email_by_account(account_number)
        except Exception as e:
            self.logger.error(f"Error getting customer email: {e}")
            return None
    
    def _send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (HTML)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return False
    
    def _mask_account_number(self, account_number: str) -> str:
        """
        Mask account number for security
        
        Args:
            account_number: Full account number
            
        Returns:
            Masked account number
        """
        if len(account_number) <= 4:
            return account_number
            
        return "X" * (len(account_number) - 4) + account_number[-4:]
    
    def _mask_email(self, email: str) -> str:
        """
        Mask email address for security
        
        Args:
            email: Full email address
            
        Returns:
            Masked email address
        """
        parts = email.split('@')
        if len(parts) != 2:
            return email
            
        username = parts[0]
        domain = parts[1]
        
        if len(username) <= 2:
            masked_username = username
        else:
            masked_username = username[0] + "X" * (len(username) - 2) + username[-1]
            
        return f"{masked_username}@{domain}"
