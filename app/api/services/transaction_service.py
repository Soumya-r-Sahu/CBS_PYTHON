"""
Transaction Service

Provides functionality for transaction processing in the Core Banking System.
"""

import logging
import time
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple

from database.connection import db_session_scope
from app.models.models import Account, Transaction, TransferRequest
from app.lib.notification_service import notification_service
from app.lib.id_generator import generate_transaction_id

logger = logging.getLogger(__name__)

class TransactionService:
    """
    Service class for transaction processing
    
    Features:
    - Fund transfers (internal and external)
    - Transaction validation
    - Transaction history and status tracking
    - Reversals and chargebacks
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(TransactionService, cls).__new__(cls)
        return cls._instance
    
    def transfer_funds(self, source_account_number: str, destination_account_number: str,
                     amount: Decimal, description: str = None,
                     reference: str = None) -> Dict[str, Any]:
        """
        Transfer funds between accounts
        
        Args:
            source_account_number: Source account number
            destination_account_number: Destination account number
            amount: Transfer amount
            description: Transaction description
            reference: Reference number
            
        Returns:
            Dict containing transaction status and details
        """
        try:
            # Validate basic inputs
            if not all([source_account_number, destination_account_number, amount]):
                return {
                    'success': False,
                    'error': 'Missing required fields'
                }
            
            # Check transfer amount
            if amount <= Decimal('0'):
                return {
                    'success': False,
                    'error': 'Transfer amount must be greater than zero'
                }
            
            # Generate reference if not provided
            if not reference:
                reference = f"TFR{time.strftime('%Y%m%d%H%M%S')}"
                
            # Use default description if not provided
            if not description:
                description = f"Funds transfer to {destination_account_number}"
            
            with db_session_scope() as session:
                # Get source and destination accounts
                source_account = session.query(Account).filter_by(
                    account_number=source_account_number
                ).first()
                
                destination_account = session.query(Account).filter_by(
                    account_number=destination_account_number
                ).first()
                
                # Validate accounts
                validation_result = self._validate_accounts_for_transfer(
                    source_account, destination_account, amount
                )
                
                if not validation_result['valid']:
                    return {
                        'success': False,
                        'error': validation_result['message']
                    }
                
                # Generate transaction ID
                transaction_id = generate_transaction_id('TRF')
                
                # Create debit transaction
                debit_transaction = Transaction(
                    transaction_id=f"D{transaction_id}",
                    account_id=source_account.id,
                    amount=-amount,
                    transaction_type='TRANSFER',
                    status='COMPLETED',
                    description=description,
                    reference=reference,
                    timestamp=datetime.now(),
                    balance_after=source_account.balance - amount
                )
                session.add(debit_transaction)
                
                # Create credit transaction
                credit_transaction = Transaction(
                    transaction_id=f"C{transaction_id}",
                    account_id=destination_account.id,
                    amount=amount,
                    transaction_type='TRANSFER',
                    status='COMPLETED',
                    description=f"Funds received from {source_account_number}",
                    reference=reference,
                    timestamp=datetime.now(),
                    balance_after=destination_account.balance + amount
                )
                session.add(credit_transaction)
                
                # Update account balances
                source_account.balance -= amount
                destination_account.balance += amount
                
                # Commit changes
                session.commit()
                
                # Send notifications
                self._send_transfer_notifications(
                    source_account, destination_account, amount, transaction_id
                )
                
                return {
                    'success': True,
                    'transaction_id': transaction_id,
                    'reference': reference,
                    'amount': str(amount),
                    'source_account': source_account_number,
                    'destination_account': destination_account_number,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error processing fund transfer: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get details of a specific transaction
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Dict containing transaction details
        """
        try:
            with db_session_scope() as session:
                # Transaction ID might be prefixed with D or C for debit/credit
                base_transaction_id = transaction_id
                if transaction_id.startswith('D') or transaction_id.startswith('C'):
                    base_transaction_id = transaction_id[1:]
                
                # Query for transactions with this ID or base ID
                transaction = session.query(Transaction).filter(
                    (Transaction.transaction_id == transaction_id) |
                    (Transaction.transaction_id == f"D{base_transaction_id}") |
                    (Transaction.transaction_id == f"C{base_transaction_id}")
                ).first()
                
                if not transaction:
                    return {
                        'success': False,
                        'error': 'Transaction not found'
                    }
                
                # Get account details
                account = session.query(Account).filter_by(id=transaction.account_id).first()
                
                # Format transaction details
                transaction_details = {
                    'success': True,
                    'transaction': {
                        'id': transaction.transaction_id,
                        'type': transaction.transaction_type,
                        'amount': str(transaction.amount),
                        'status': transaction.status,
                        'description': transaction.description,
                        'reference': transaction.reference,
                        'timestamp': transaction.timestamp.isoformat(),
                        'account_number': account.account_number if account else None,
                        'balance_after': str(transaction.balance_after)
                    }
                }
                
                # If this is part of a transfer, get the counterpart
                if transaction.transaction_type == 'TRANSFER':
                    counterpart_id = None
                    if transaction.transaction_id.startswith('D'):
                        counterpart_id = f"C{base_transaction_id}"
                    elif transaction.transaction_id.startswith('C'):
                        counterpart_id = f"D{base_transaction_id}"
                    
                    if counterpart_id:
                        counterpart = session.query(Transaction).filter_by(
                            transaction_id=counterpart_id
                        ).first()
                        
                        if counterpart:
                            counterpart_account = session.query(Account).filter_by(
                                id=counterpart.account_id
                            ).first()
                            
                            transaction_details['counterpart'] = {
                                'transaction_id': counterpart.transaction_id,
                                'account_number': counterpart_account.account_number if counterpart_account else None,
                                'amount': str(counterpart.amount)
                            }
                
                return transaction_details
                
        except Exception as e:
            logger.error(f"Error retrieving transaction: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def initiate_external_transfer(self, source_account_number: str, 
                                 beneficiary_name: str,
                                 beneficiary_account: str,
                                 beneficiary_bank_code: str,
                                 amount: Decimal,
                                 description: str = None) -> Dict[str, Any]:
        """
        Initiate a transfer to an external bank account
        
        Args:
            source_account_number: Source account number
            beneficiary_name: Name of the beneficiary
            beneficiary_account: Beneficiary account number
            beneficiary_bank_code: Bank code (IFSC/SWIFT/etc.)
            amount: Transfer amount
            description: Transaction description
            
        Returns:
            Dict containing transfer request status and details
        """
        try:
            # Validate inputs
            if not all([source_account_number, beneficiary_name, beneficiary_account, 
                       beneficiary_bank_code, amount]):
                return {
                    'success': False,
                    'error': 'Missing required fields'
                }
            
            if amount <= Decimal('0'):
                return {
                    'success': False,
                    'error': 'Transfer amount must be greater than zero'
                }
            
            with db_session_scope() as session:
                # Get source account
                source_account = session.query(Account).filter_by(
                    account_number=source_account_number
                ).first()
                
                if not source_account:
                    return {
                        'success': False,
                        'error': 'Source account not found'
                    }
                
                # Check account status
                if source_account.status != 'ACTIVE':
                    return {
                        'success': False,
                        'error': f'Source account is {source_account.status.lower()}'
                    }
                
                # Check if account has sufficient funds (including transfer fee)
                # Assume a 0.25% fee with min INR 5 and max INR 50
                fee = min(max(amount * Decimal('0.0025'), Decimal('5')), Decimal('50'))
                
                if source_account.balance < (amount + fee):
                    return {
                        'success': False,
                        'error': 'Insufficient funds'
                    }
                
                # Generate reference number
                reference = f"EXT{time.strftime('%Y%m%d%H%M%S')}"
                
                # Create transfer request
                transfer_request = TransferRequest(
                    source_account_id=source_account.id,
                    beneficiary_name=beneficiary_name,
                    beneficiary_account=beneficiary_account,
                    beneficiary_bank_code=beneficiary_bank_code,
                    amount=amount,
                    fee=fee,
                    description=description or f"External transfer to {beneficiary_name}",
                    reference=reference,
                    status='PENDING',
                    created_at=datetime.now()
                )
                
                session.add(transfer_request)
                session.flush()
                
                # Hold the funds
                hold_transaction = Transaction(
                    transaction_id=f"H{reference}",
                    account_id=source_account.id,
                    amount=-(amount + fee),
                    transaction_type='EXTERNAL_TRANSFER',
                    status='PENDING',
                    description=f"External transfer to {beneficiary_name} at {beneficiary_bank_code}",
                    reference=reference,
                    timestamp=datetime.now(),
                    balance_after=source_account.balance - (amount + fee)
                )
                
                session.add(hold_transaction)
                
                # Update account balance
                source_account.balance -= (amount + fee)
                
                # Commit changes
                session.commit()
                
                return {
                    'success': True,
                    'transfer_id': transfer_request.id,
                    'reference': reference,
                    'amount': str(amount),
                    'fee': str(fee),
                    'total': str(amount + fee),
                    'status': 'PENDING',
                    'estimated_completion': self._get_estimated_completion_time()
                }
                
        except Exception as e:
            logger.error(f"Error initiating external transfer: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def reverse_transaction(self, transaction_id: str, reason: str) -> Dict[str, Any]:
        """
        Reverse a transaction
        
        Args:
            transaction_id: ID of the transaction to reverse
            reason: Reason for the reversal
            
        Returns:
            Dict containing reversal status and details
        """
        try:
            with db_session_scope() as session:
                # Get the original transaction
                original_transaction = session.query(Transaction).filter_by(
                    transaction_id=transaction_id
                ).first()
                
                if not original_transaction:
                    return {
                        'success': False,
                        'error': 'Transaction not found'
                    }
                
                # Check if transaction is reversible
                if original_transaction.status != 'COMPLETED':
                    return {
                        'success': False,
                        'error': f'Cannot reverse a {original_transaction.status.lower()} transaction'
                    }
                
                # Check transaction type
                reversible_types = ['TRANSFER', 'DEPOSIT', 'WITHDRAWAL', 'FEE', 'CHARGE']
                if original_transaction.transaction_type not in reversible_types:
                    return {
                        'success': False,
                        'error': f'Cannot reverse a {original_transaction.transaction_type} transaction'
                    }
                
                # Mark original transaction as reversed
                original_transaction.status = 'REVERSED'
                
                # Get account
                account = session.query(Account).filter_by(id=original_transaction.account_id).first()
                
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Create reversal transaction with opposite amount
                reversal_amount = -original_transaction.amount
                
                reversal_transaction = Transaction(
                    transaction_id=f"REV{transaction_id}",
                    account_id=account.id,
                    amount=reversal_amount,
                    transaction_type='REVERSAL',
                    status='COMPLETED',
                    description=f"Reversal: {reason}",
                    reference=original_transaction.reference,
                    timestamp=datetime.now(),
                    balance_after=account.balance + reversal_amount
                )
                
                session.add(reversal_transaction)
                
                # Update account balance
                account.balance += reversal_amount
                
                # If this was a transfer, handle the counterpart
                if original_transaction.transaction_type == 'TRANSFER':
                    # Determine counterpart ID
                    base_id = transaction_id
                    counterpart_id = None
                    
                    if transaction_id.startswith('D'):
                        base_id = transaction_id[1:]
                        counterpart_id = f"C{base_id}"
                    elif transaction_id.startswith('C'):
                        base_id = transaction_id[1:]
                        counterpart_id = f"D{base_id}"
                    
                    if counterpart_id:
                        counterpart = session.query(Transaction).filter_by(
                            transaction_id=counterpart_id
                        ).first()
                        
                        if counterpart:
                            # Mark counterpart as reversed
                            counterpart.status = 'REVERSED'
                            
                            # Get counterpart account
                            counterpart_account = session.query(Account).filter_by(
                                id=counterpart.account_id
                            ).first()
                            
                            if counterpart_account:
                                # Create reversal for counterpart
                                counterpart_reversal = Transaction(
                                    transaction_id=f"REV{counterpart_id}",
                                    account_id=counterpart_account.id,
                                    amount=-counterpart.amount,
                                    transaction_type='REVERSAL',
                                    status='COMPLETED',
                                    description=f"Reversal: {reason}",
                                    reference=counterpart.reference,
                                    timestamp=datetime.now(),
                                    balance_after=counterpart_account.balance - counterpart.amount
                                )
                                
                                session.add(counterpart_reversal)
                                
                                # Update counterpart account balance
                                counterpart_account.balance -= counterpart.amount
                
                # Commit changes
                session.commit()
                
                # Send notification
                self._send_reversal_notification(account, original_transaction, reason)
                
                return {
                    'success': True,
                    'original_transaction_id': transaction_id,
                    'reversal_transaction_id': reversal_transaction.transaction_id,
                    'amount': str(reversal_amount),
                    'reason': reason,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error reversing transaction: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_accounts_for_transfer(self, source_account, destination_account, amount) -> Dict[str, Any]:
        """Validate accounts for a transfer"""
        # Check if accounts exist
        if not source_account:
            return {
                'valid': False,
                'message': 'Source account not found'
            }
        
        if not destination_account:
            return {
                'valid': False,
                'message': 'Destination account not found'
            }
        
        # Check if accounts are active
        if source_account.status != 'ACTIVE':
            return {
                'valid': False,
                'message': f'Source account is {source_account.status.lower()}'
            }
        
        if destination_account.status != 'ACTIVE':
            return {
                'valid': False,
                'message': f'Destination account is {destination_account.status.lower()}'
            }
        
        # Check if source account has sufficient funds
        if source_account.balance < amount:
            return {
                'valid': False,
                'message': 'Insufficient funds in source account'
            }
        
        # Check if source and destination are the same
        if source_account.id == destination_account.id:
            return {
                'valid': False,
                'message': 'Source and destination accounts cannot be the same'
            }
        
        return {
            'valid': True
        }
    
    def _send_transfer_notifications(self, source_account, destination_account, amount, transaction_id):
        """Send notifications for a completed transfer"""
        # Get source customer data
        source_customer = None
        if hasattr(source_account, 'customer'):
            source_customer = source_account.customer
        
        # Get destination customer data
        destination_customer = None
        if hasattr(destination_account, 'customer'):
            destination_customer = destination_account.customer
        
        # Send notification to source customer
        if source_customer:
            source_data = {
                'email': getattr(source_customer, 'email', None),
                'phone_number': getattr(source_customer, 'phone', None)
            }
            
            transaction_data = {
                'account_number': source_account.account_number,
                'type': 'Funds Transfer (Debit)',
                'amount': float(amount),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'balance': float(source_account.balance)
            }
            
            notification_service.send_transaction_alert(source_data, transaction_data)
        
        # Send notification to destination customer
        if destination_customer:
            destination_data = {
                'email': getattr(destination_customer, 'email', None),
                'phone_number': getattr(destination_customer, 'phone', None)
            }
            
            transaction_data = {
                'account_number': destination_account.account_number,
                'type': 'Funds Transfer (Credit)',
                'amount': float(amount),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'balance': float(destination_account.balance)
            }
            
            notification_service.send_transaction_alert(destination_data, transaction_data)
    
    def _send_reversal_notification(self, account, original_transaction, reason):
        """Send notification about a transaction reversal"""
        if hasattr(account, 'customer') and account.customer:
            customer = account.customer
            
            if hasattr(customer, 'email') and customer.email:
                # Send email notification
                subject = "Transaction Reversal Notification"
                message = f"""
                Dear {customer.first_name if hasattr(customer, 'first_name') else 'Customer'},
                
                A transaction on your account has been reversed.
                
                Original Transaction ID: {original_transaction.transaction_id}
                Amount: {abs(float(original_transaction.amount))}
                Reason for reversal: {reason}
                
                Your updated account balance is: {float(account.balance)}
                
                If you have any questions, please contact our customer support.
                
                Sincerely,
                The Banking Team
                """
                
                notification_service.send_email(
                    recipient=customer.email,
                    subject=subject,
                    message=message
                )
            
            if hasattr(customer, 'phone') and customer.phone:
                # Send SMS notification
                sms_message = f"Transaction {original_transaction.transaction_id[-4:]} for {abs(float(original_transaction.amount))} has been reversed. New balance: {float(account.balance)}"
                
                notification_service.send_sms(
                    phone_number=customer.phone,
                    message=sms_message
                )
    
    def _get_estimated_completion_time(self) -> str:
        """Get estimated time for external transfer completion"""
        # For now, just return a time 1 hour in the future
        return (datetime.now() + datetime.timedelta(hours=1)).isoformat()

# Create singleton instance
transaction_service = TransactionService()
