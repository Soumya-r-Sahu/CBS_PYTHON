"""
UPI Transaction Processor

Handles the processing of UPI transactions in the Core Banking System.
"""

import logging
import uuid
import time
import hashlib
import json
import random
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from app.config.config_loader import config
from app.lib.notification_service import notification_service
from app.models.models import Transaction, Account, UPITransaction
from database.connection import db_session_scope
from security.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)

class UPITransactionProcessor:
    """
    Processes UPI transactions
    
    Features:
    - Validate UPI transactions
    - Process different types of UPI transactions (P2P, P2M, etc.)
    - Handle callbacks and confirmations
    - Record transaction details
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(UPITransactionProcessor, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize UPI transaction processor"""
        # Load configuration
        self.processing_fee = Decimal(config.get('upi.processing_fee', '0'))
        self.daily_limit = Decimal(config.get('upi.daily_limit', '100000'))
        self.transaction_limit = Decimal(config.get('upi.transaction_limit', '20000'))
        self.merchant_discount_rate = Decimal(config.get('upi.merchant_discount_rate', '0.0025'))  # 0.25%
        
        # Load UPI network configuration
        self.upi_network_timeout = config.get('upi.network.timeout', 30)
        self.upi_network_retry = config.get('upi.network.retry', 2)
        
        logger.info("UPI transaction processor initialized")
    
    def process_payment(self, sender_upi_id: str, receiver_upi_id: str, 
                       amount: Decimal, reference: str, 
                       note: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a UPI payment
        
        Args:
            sender_upi_id: UPI ID of the sender
            receiver_upi_id: UPI ID of the receiver
            amount: Transaction amount
            reference: Reference number for the transaction
            note: Optional note for the transaction
            
        Returns:
            Dict containing transaction status and details
        """
        try:
            logger.info(f"Processing UPI payment: {sender_upi_id} -> {receiver_upi_id}, Amount: {amount}")
            
            # Generate transaction ID
            transaction_id = f"UPI{time.strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
            
            # Validate transaction
            validation_result = self._validate_transaction(sender_upi_id, receiver_upi_id, amount)
            if not validation_result['valid']:
                logger.warning(f"UPI payment validation failed: {validation_result['reason']}")
                return {
                    'status': 'FAILED',
                    'transaction_id': transaction_id,
                    'error': validation_result['reason']
                }
            
            # Process transaction
            with db_session_scope() as session:
                # Get sender and receiver accounts
                sender_account = self._get_account_by_upi_id(session, sender_upi_id)
                receiver_account = self._get_account_by_upi_id(session, receiver_upi_id)
                
                if not sender_account:
                    return {
                        'status': 'FAILED',
                        'transaction_id': transaction_id,
                        'error': 'Sender account not found'
                    }
                
                if not receiver_account:
                    return {
                        'status': 'FAILED',
                        'transaction_id': transaction_id,
                        'error': 'Receiver account not found'
                    }
                
                # Check if sender has sufficient balance
                if sender_account.balance < amount:
                    return {
                        'status': 'FAILED',
                        'transaction_id': transaction_id,
                        'error': 'Insufficient balance'
                    }
                
                # Check if transaction is P2M (Person to Merchant)
                is_merchant = self._is_merchant_account(receiver_account)
                
                # Calculate fees if applicable
                fee = Decimal('0')
                if self.processing_fee > 0:
                    fee = self.processing_fee
                
                # Calculate merchant discount if applicable
                merchant_fee = Decimal('0')
                if is_merchant:
                    merchant_fee = (amount * self.merchant_discount_rate).quantize(Decimal('0.01'))
                
                # Create UPI transaction record
                upi_transaction = UPITransaction(
                    transaction_id=transaction_id,
                    sender_upi_id=sender_upi_id,
                    receiver_upi_id=receiver_upi_id,
                    amount=amount,
                    fee=fee,
                    merchant_fee=merchant_fee,
                    reference=reference,
                    note=note or '',
                    status='PROCESSING',
                    timestamp=datetime.now()
                )
                session.add(upi_transaction)
                
                # Create transaction records
                
                # Debit from sender
                debit_transaction = Transaction(
                    transaction_id=f"D{transaction_id}",
                    account_id=sender_account.id,
                    amount=-amount,
                    transaction_type='UPI_PAYMENT',
                    status='PROCESSING',
                    description=f"UPI Payment to {receiver_upi_id}" + (f" - {note}" if note else ""),
                    timestamp=datetime.now(),
                    reference=reference,
                    balance_after=sender_account.balance - amount
                )
                session.add(debit_transaction)
                
                # Credit to receiver
                receiver_amount = amount
                if is_merchant:
                    receiver_amount -= merchant_fee
                
                credit_transaction = Transaction(
                    transaction_id=f"C{transaction_id}",
                    account_id=receiver_account.id,
                    amount=receiver_amount,
                    transaction_type='UPI_PAYMENT',
                    status='PROCESSING',
                    description=f"UPI Payment from {sender_upi_id}" + (f" - {note}" if note else ""),
                    timestamp=datetime.now(),
                    reference=reference,
                    balance_after=receiver_account.balance + receiver_amount
                )
                session.add(credit_transaction)
                
                # Create fee transaction if applicable
                if fee > 0:
                    fee_transaction = Transaction(
                        transaction_id=f"F{transaction_id}",
                        account_id=sender_account.id,
                        amount=-fee,
                        transaction_type='UPI_FEE',
                        status='PROCESSING',
                        description=f"UPI Transaction Fee for {transaction_id}",
                        timestamp=datetime.now(),
                        reference=reference,
                        balance_after=sender_account.balance - amount - fee
                    )
                    session.add(fee_transaction)
                
                # Create merchant fee transaction if applicable
                if merchant_fee > 0:
                    # This would typically go to a bank revenue account
                    pass
                
                # Simulate UPI network processing
                network_result = self._send_to_upi_network(transaction_id, sender_upi_id, receiver_upi_id, amount)
                
                if network_result['success']:
                    # Update transaction statuses
                    upi_transaction.status = 'COMPLETED'
                    debit_transaction.status = 'COMPLETED'
                    credit_transaction.status = 'COMPLETED'
                    
                    if fee > 0:
                        fee_transaction.status = 'COMPLETED'
                    
                    # Update account balances
                    sender_account.balance -= (amount + fee)
                    receiver_account.balance += receiver_amount
                    
                    logger.info(f"UPI payment successful: {transaction_id}")
                    
                    # Send notifications
                    self._send_transaction_notifications(
                        sender_account, receiver_account, 
                        amount, transaction_id, is_merchant
                    )
                    
                    return {
                        'status': 'SUCCESS',
                        'transaction_id': transaction_id,
                        'timestamp': datetime.now().isoformat(),
                        'amount': str(amount),
                        'fee': str(fee),
                        'reference': reference
                    }
                else:
                    # Update transaction statuses to failed
                    upi_transaction.status = 'FAILED'
                    debit_transaction.status = 'FAILED'
                    credit_transaction.status = 'FAILED'
                    
                    if fee > 0:
                        fee_transaction.status = 'FAILED'
                    
                    logger.warning(f"UPI payment failed at network: {network_result['error']}")
                    
                    return {
                        'status': 'FAILED',
                        'transaction_id': transaction_id,
                        'error': f"Payment processing failed: {network_result['error']}"
                    }
                
        except Exception as e:
            logger.error(f"Error processing UPI payment: {str(e)}")
            return {
                'status': 'ERROR',
                'transaction_id': transaction_id if 'transaction_id' in locals() else 'UNKNOWN',
                'error': str(e)
            }
    
    def verify_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Verify the status of a UPI transaction
        
        Args:
            transaction_id: UPI transaction ID
            
        Returns:
            Dict containing transaction status and details
        """
        try:
            with db_session_scope() as session:
                # Query UPI transaction
                transaction = session.query(UPITransaction).filter_by(
                    transaction_id=transaction_id
                ).first()
                
                if not transaction:
                    return {
                        'status': 'UNKNOWN',
                        'transaction_id': transaction_id,
                        'error': 'Transaction not found'
                    }
                
                return {
                    'status': transaction.status,
                    'transaction_id': transaction_id,
                    'sender': transaction.sender_upi_id,
                    'receiver': transaction.receiver_upi_id,
                    'amount': str(transaction.amount),
                    'fee': str(transaction.fee),
                    'timestamp': transaction.timestamp.isoformat(),
                    'reference': transaction.reference
                }
                
        except Exception as e:
            logger.error(f"Error verifying UPI transaction: {str(e)}")
            return {
                'status': 'ERROR',
                'transaction_id': transaction_id,
                'error': str(e)
            }
    
    def collect_request(self, requester_upi_id: str, payer_upi_id: str, 
                       amount: Decimal, reference: str, 
                       expiry_minutes: int = 30,
                       note: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a collect request (pull payment request)
        
        Args:
            requester_upi_id: UPI ID of the requester
            payer_upi_id: UPI ID of the payer
            amount: Requested amount
            reference: Reference number for the request
            expiry_minutes: Expiry time for the request in minutes
            note: Optional note for the request
            
        Returns:
            Dict containing request status and details
        """
        # Implementation would be similar to process_payment but with request creation
        # instead of immediate transaction processing
        
        # For this example, we'll return a simple structure
        request_id = f"UPIREQ{time.strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
        
        return {
            'status': 'REQUEST_CREATED',
            'request_id': request_id,
            'requester': requester_upi_id,
            'payer': payer_upi_id,
            'amount': str(amount),
            'reference': reference,
            'expiry': (datetime.now() + datetime.timedelta(minutes=expiry_minutes)).isoformat()
        }
    
    def _validate_transaction(self, sender_upi_id: str, receiver_upi_id: str, 
                             amount: Decimal) -> Dict[str, Any]:
        """Validate a UPI transaction"""
        # Check sender and receiver are different
        if sender_upi_id == receiver_upi_id:
            return {
                'valid': False,
                'reason': 'Sender and receiver cannot be the same'
            }
        
        # Check amount is positive
        if amount <= Decimal('0'):
            return {
                'valid': False,
                'reason': 'Amount must be greater than zero'
            }
        
        # Check amount is within transaction limit
        if amount > self.transaction_limit:
            return {
                'valid': False,
                'reason': f'Amount exceeds transaction limit of {self.transaction_limit}'
            }
        
        # Check daily limit (would require querying today's transactions)
        # This is simplified - in a real system, you'd check actual daily totals
        
        # Validate UPI IDs format
        if not self._is_valid_upi_id(sender_upi_id):
            return {
                'valid': False,
                'reason': 'Invalid sender UPI ID format'
            }
        
        if not self._is_valid_upi_id(receiver_upi_id):
            return {
                'valid': False,
                'reason': 'Invalid receiver UPI ID format'
            }
        
        return {
            'valid': True
        }
    
    def _is_valid_upi_id(self, upi_id: str) -> bool:
        """Check if UPI ID format is valid"""
        # Basic validation - in real system would be more comprehensive
        if '@' not in upi_id:
            return False
        
        parts = upi_id.split('@')
        if len(parts) != 2 or not parts[0] or not parts[1]:
            return False
        
        return True
    
    def _get_account_by_upi_id(self, session, upi_id: str) -> Optional[Any]:
        """Get account by UPI ID"""
        # In a real implementation, this would query the database
        # This is a simplified version for demonstration
        from app.models.models import UPIHandle
        
        upi_handle = session.query(UPIHandle).filter_by(upi_id=upi_id).first()
        
        if not upi_handle:
            return None
        
        return session.query(Account).filter_by(id=upi_handle.account_id).first()
    
    def _is_merchant_account(self, account: Any) -> bool:
        """Check if an account is a merchant account"""
        # In a real implementation, this would check account attributes
        # This is a simplified version
        return hasattr(account, 'account_type') and account.account_type == 'MERCHANT'
    
    def _send_to_upi_network(self, transaction_id: str, sender: str, 
                            receiver: str, amount: Decimal) -> Dict[str, Any]:
        """
        Simulate sending the transaction to the UPI network
        
        In a real implementation, this would interact with the UPI network API
        """
        # Simulate network communication
        time.sleep(0.5)
        
        # Simulate 95% success rate
        if random.random() < 0.95:
            return {
                'success': True,
                'reference': f"NPCI{int(time.time())}"
            }
        else:
            return {
                'success': False,
                'error': 'Network communication failure'
            }
    
    def _send_transaction_notifications(self, sender_account: Any, receiver_account: Any,
                                       amount: Decimal, transaction_id: str,
                                       is_merchant: bool) -> None:
        """Send notifications for a completed transaction"""
        # Get sender customer data
        sender_customer = None
        if hasattr(sender_account, 'customer'):
            sender_customer = sender_account.customer
        
        # Get receiver customer data
        receiver_customer = None
        if hasattr(receiver_account, 'customer'):
            receiver_customer = receiver_account.customer
        
        # Send notification to sender
        if sender_customer:
            sender_data = {
                'email': getattr(sender_customer, 'email', None),
                'phone_number': getattr(sender_customer, 'phone', None)
            }
            
            transaction_data = {
                'account_number': sender_account.account_number,
                'type': 'UPI Payment',
                'amount': float(amount),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'balance': float(sender_account.balance)
            }
            
            notification_service.send_transaction_alert(sender_data, transaction_data)
        
        # Send notification to receiver
        if receiver_customer and not is_merchant:
            receiver_data = {
                'email': getattr(receiver_customer, 'email', None),
                'phone_number': getattr(receiver_customer, 'phone', None)
            }
            
            transaction_data = {
                'account_number': receiver_account.account_number,
                'type': 'UPI Receipt',
                'amount': float(amount),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'balance': float(receiver_account.balance)
            }
            
            notification_service.send_transaction_alert(receiver_data, transaction_data)

# Create singleton instance
upi_processor = UPITransactionProcessor()
