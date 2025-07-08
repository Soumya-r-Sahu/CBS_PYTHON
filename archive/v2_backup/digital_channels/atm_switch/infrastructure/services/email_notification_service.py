"""
Email Notification Service

This module implements the notification service interface using email.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime

from ...application.interfaces.notification_service import NotificationServiceInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class EmailNotificationService(NotificationServiceInterface):
    """Email implementation of notification service"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize notification service with configuration
        
        Args:
            config: Email configuration dictionary
        """
        self.config = config
        self.smtp_host = config.get('smtp_host', 'smtp.example.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.smtp_user = config.get('smtp_user', '')
        self.smtp_pass = config.get('smtp_pass', '')
        self.sender = config.get('sender', 'notifications@bank.com')
        self.logger = logging.getLogger(__name__)
    
    def _send_email(self, recipient: str, subject: str, body: str) -> bool:
        """
        Send email to recipient
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body (HTML)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_pass)
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return False
    
    def _get_customer_email(self, account_number: str) -> str:
        """
        Get customer email address for account
        
        Args:
            account_number: Account number
            
        Returns:
            Customer email address
        """
        # In a real implementation, this would query the database
        # For now, we'll just return a placeholder
        return f"customer_{account_number}@example.com"
    
    def send_withdrawal_notification(
        self,
        account_number: str,
        amount: Decimal,
        transaction_id: str,
        balance: Decimal,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send withdrawal notification
        
        Args:
            account_number: Account number
            amount: Withdrawal amount
            transaction_id: Transaction ID
            balance: Remaining balance
            timestamp: Transaction timestamp
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        recipient = self._get_customer_email(account_number)
        subject = f"ATM Withdrawal Notification - {account_number[-4:]}"
        
        body = f"""
        <html>
        <body>
            <h2>ATM Withdrawal Notification</h2>
            <p>Dear Customer,</p>
            <p>A withdrawal has been made from your account.</p>
            <table>
                <tr>
                    <td><strong>Account:</strong></td>
                    <td>XXXX{account_number[-4:]}</td>
                </tr>
                <tr>
                    <td><strong>Amount:</strong></td>
                    <td>${amount}</td>
                </tr>
                <tr>
                    <td><strong>Date/Time:</strong></td>
                    <td>{timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
                <tr>
                    <td><strong>Transaction ID:</strong></td>
                    <td>{transaction_id}</td>
                </tr>
                <tr>
                    <td><strong>Available Balance:</strong></td>
                    <td>${balance}</td>
                </tr>
            </table>
            <p>If you did not make this withdrawal, please contact our customer service immediately.</p>
            <p>Thank you for banking with us.</p>
        </body>
        </html>
        """
        
        return self._send_email(recipient, subject, body)
    
    def send_deposit_notification(
        self,
        account_number: str,
        amount: Decimal,
        transaction_id: str,
        balance: Decimal,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send deposit notification
        
        Args:
            account_number: Account number
            amount: Deposit amount
            transaction_id: Transaction ID
            balance: Updated balance
            timestamp: Transaction timestamp
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        recipient = self._get_customer_email(account_number)
        subject = f"ATM Deposit Notification - {account_number[-4:]}"
        
        body = f"""
        <html>
        <body>
            <h2>ATM Deposit Notification</h2>
            <p>Dear Customer,</p>
            <p>A deposit has been made to your account.</p>
            <table>
                <tr>
                    <td><strong>Account:</strong></td>
                    <td>XXXX{account_number[-4:]}</td>
                </tr>
                <tr>
                    <td><strong>Amount:</strong></td>
                    <td>${amount}</td>
                </tr>
                <tr>
                    <td><strong>Date/Time:</strong></td>
                    <td>{timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
                <tr>
                    <td><strong>Transaction ID:</strong></td>
                    <td>{transaction_id}</td>
                </tr>
                <tr>
                    <td><strong>Available Balance:</strong></td>
                    <td>${balance}</td>
                </tr>
            </table>
            <p>Thank you for banking with us.</p>
        </body>
        </html>
        """
        
        return self._send_email(recipient, subject, body)
    
    def send_balance_notification(
        self,
        account_number: str,
        balance: Decimal,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send balance inquiry notification
        
        Args:
            account_number: Account number
            balance: Account balance
            timestamp: Inquiry timestamp
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        recipient = self._get_customer_email(account_number)
        subject = f"Balance Inquiry Notification - {account_number[-4:]}"
        
        body = f"""
        <html>
        <body>
            <h2>Balance Inquiry Notification</h2>
            <p>Dear Customer,</p>
            <p>A balance inquiry was performed on your account.</p>
            <table>
                <tr>
                    <td><strong>Account:</strong></td>
                    <td>XXXX{account_number[-4:]}</td>
                </tr>
                <tr>
                    <td><strong>Date/Time:</strong></td>
                    <td>{timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
                <tr>
                    <td><strong>Available Balance:</strong></td>
                    <td>${balance}</td>
                </tr>
            </table>
            <p>Thank you for banking with us.</p>
        </body>
        </html>
        """
        
        return self._send_email(recipient, subject, body)
    
    def send_pin_change_notification(
        self,
        account_number: str,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send PIN change notification
        
        Args:
            account_number: Account number
            timestamp: Change timestamp
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        recipient = self._get_customer_email(account_number)
        subject = f"PIN Change Notification - {account_number[-4:]}"
        
        body = f"""
        <html>
        <body>
            <h2>PIN Change Notification</h2>
            <p>Dear Customer,</p>
            <p>The PIN for your ATM card associated with account XXXX{account_number[-4:]} has been changed.</p>
            <p><strong>Date/Time:</strong> {timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>If you did not make this change, please contact our customer service immediately.</p>
            <p>Thank you for banking with us.</p>
        </body>
        </html>
        """
        
        return self._send_email(recipient, subject, body)
    
    def send_transaction_notification(
        self,
        account_number: str,
        transaction_type: str,
        amount: Decimal,
        transaction_id: str,
        balance: Optional[Decimal] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Send generic transaction notification
        
        Args:
            account_number: Account number
            transaction_type: Type of transaction
            amount: Transaction amount
            transaction_id: Transaction ID
            balance: Account balance after transaction
            timestamp: Transaction timestamp
            
        Returns:
            True if notification sent successfully, False otherwise
        """
        if transaction_type.lower() == "withdrawal":
            return self.send_withdrawal_notification(
                account_number, amount, transaction_id, balance or Decimal('0'), timestamp
            )
        elif transaction_type.lower() == "deposit":
            return self.send_deposit_notification(
                account_number, amount, transaction_id, balance or Decimal('0'), timestamp
            )
        
        # Generic notification for other types
        if timestamp is None:
            timestamp = datetime.now()
        
        recipient = self._get_customer_email(account_number)
        subject = f"Transaction Notification - {account_number[-4:]}"
        
        body = f"""
        <html>
        <body>
            <h2>Transaction Notification</h2>
            <p>Dear Customer,</p>
            <p>A {transaction_type} transaction has been performed on your account.</p>
            <table>
                <tr>
                    <td><strong>Account:</strong></td>
                    <td>XXXX{account_number[-4:]}</td>
                </tr>
                <tr>
                    <td><strong>Transaction Type:</strong></td>
                    <td>{transaction_type.upper()}</td>
                </tr>
                <tr>
                    <td><strong>Amount:</strong></td>
                    <td>${amount}</td>
                </tr>
                <tr>
                    <td><strong>Date/Time:</strong></td>
                    <td>{timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>
                </tr>
                <tr>
                    <td><strong>Transaction ID:</strong></td>
                    <td>{transaction_id}</td>
                </tr>
                {f"<tr><td><strong>Available Balance:</strong></td><td>${balance}</td></tr>" if balance else ""}
            </table>
            <p>Thank you for banking with us.</p>
        </body>
        </html>
        """
        
        return self._send_email(recipient, subject, body)
