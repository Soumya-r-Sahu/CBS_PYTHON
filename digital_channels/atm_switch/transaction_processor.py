"""
ATM Transaction Processor

Handles the processing of ATM transactions in the Core Banking System.
"""

import logging
import time
import random
import uuid
import sys
from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

# Import with fallback for backward compatibility
try:
    from utils.config.config_loader import config
except ImportError:
    # Fallback to old import path
    try:
        from app.config.config_loader import config
    except ImportError:
        # Define fallback implementation if needed
        pass  # No fallback implementation provided

# Import with fallback for backward compatibility
try:
    from utils.lib.notification_service import notification_service
except ImportError:
    # Fallback to old import path
    try:
        from app.lib.notification_service import notification_service
    except ImportError:
        # Define fallback implementation if needed
        pass  # No fallback implementation provided

# Import with fallback for backward compatibility
try:
    from utils.lib.task_manager import task_manager
except ImportError:
    # Fallback to old import path
    try:
        from app.lib.task_manager import task_manager
    except ImportError:
        # Define fallback implementation if needed
        pass  # No fallback implementation provided


from app.models.models import Transaction, Account, Card
from database.python.common.database_operations import db_session_scope
from security.common.encryption import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)

class ATMTransactionProcessor:
    """
    Processes ATM transactions
    
    Features:
    - Cash withdrawal
    - Balance inquiry
    - Mini statement
    - PIN change
    - Deposit (if supported)
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(ATMTransactionProcessor, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize ATM transaction processor"""
        # Load configuration
        self.withdrawal_fee = Decimal(config.get('atm.withdrawal_fee', '0'))
        self.daily_withdrawal_limit = Decimal(config.get('atm.daily_withdrawal_limit', '25000'))
        self.min_withdrawal = Decimal(config.get('atm.min_withdrawal', '100'))
        self.max_withdrawal = Decimal(config.get('atm.max_withdrawal', '10000'))
        self.allow_deposits = config.get('atm.allow_deposits', False)
        
        # Initialize transaction tracking
        self.transaction_cache = {}
        
        logger.info("ATM transaction processor initialized")
    
    def validate_card(self, card_number: str, pin: str) -> Dict[str, Any]:
        """
        Validate an ATM card and PIN
        
        Args:
            card_number: Card number
            pin: PIN code
            
        Returns:
            Dict containing validation result and account info if successful
        """
        try:
            with db_session_scope() as session:
                # Find the card
                card = session.query(Card).filter_by(card_number=card_number).first()
                
                if not card:
                    return {
                        'valid': False,
                        'message': 'Card not found'
                    }
                
                # Check if card is active
                if not card.status == 'ACTIVE':
                    return {
                        'valid': False,
                        'message': f'Card is {card.status.lower()}'
                    }
                
                # Check if card is expired
                if card.expiry_date < datetime.now().date():
                    return {
                        'valid': False,
                        'message': 'Card has expired'
                    }
                
                # Verify PIN
                if not self._verify_pin(card, pin):
                    # Update failed attempts
                    card.failed_pin_attempts += 1
                    
                    # Block card if too many failed attempts
                    if card.failed_pin_attempts >= 3:
                        card.status = 'BLOCKED'
                        logger.warning(f"Card {card_number[-4:]} blocked due to multiple failed PIN attempts")
                        
                        # Send notification about blocked card
                        self._send_card_blocked_notification(card)
                        
                        return {
                            'valid': False,
                            'message': 'Card blocked due to multiple failed PIN attempts'
                        }
                    
                    session.commit()
                    
                    return {
                        'valid': False,
                        'message': 'Invalid PIN'
                    }
                
                # Reset failed attempts on successful verification
                if card.failed_pin_attempts > 0:
                    card.failed_pin_attempts = 0
                    session.commit()
                
                # Get account information
                account = session.query(Account).filter_by(id=card.account_id).first()
                
                if not account:
                    return {
                        'valid': False,
                        'message': 'Account not found'
                    }
                
                # Check if account is active
                if account.status != 'ACTIVE':
                    return {
                        'valid': False,
                        'message': f'Account is {account.status.lower()}'
                    }
                
                # Create session token
                session_token = self._create_atm_session(card_number, account.id)
                
                return {
                    'valid': True,
                    'session_token': session_token,
                    'account_number': account.account_number,
                    'card_number_masked': f"{'*' * 12}{card_number[-4:]}",
                    'account_type': account.account_type,
                    'customer_name': self._get_customer_name(account)
                }
                
        except Exception as e:
            logger.error(f"Error validating card: {str(e)}")
            return {
                'valid': False,
                'message': 'System error occurred'
            }
    
    def withdraw(self, session_token: str, amount: Decimal) -> Dict[str, Any]:
        """
        Process a cash withdrawal transaction
        
        Args:
            session_token: ATM session token
            amount: Amount to withdraw
            
        Returns:
            Dict containing transaction status and details
        """
        try:
            # Validate session token
            session_data = self._validate_atm_session(session_token)
            if not session_data['valid']:
                return {
                    'success': False,
                    'message': session_data['message']
                }
            
            card_number = session_data['card_number']
            account_id = session_data['account_id']
            
            # Validate withdrawal amount
            if amount < self.min_withdrawal:
                return {
                    'success': False,
                    'message': f'Minimum withdrawal amount is {self.min_withdrawal}'
                }
            
            if amount > self.max_withdrawal:
                return {
                    'success': False,
                    'message': f'Maximum withdrawal amount is {self.max_withdrawal}'
                }
            
            # Check if amount is in valid denominations
            if not self._is_valid_denomination(amount):
                return {
                    'success': False,
                    'message': 'Invalid withdrawal amount. Please use valid denominations.'
                }
            
            with db_session_scope() as session:
                # Get account
                account = session.query(Account).filter_by(id=account_id).first()
                
                if not account:
                    return {
                        'success': False,
                        'message': 'Account not found'
                    }
                
                # Check daily withdrawal limit
                today_withdrawals = self._get_today_withdrawals(session, account_id)
                
                if today_withdrawals + amount > self.daily_withdrawal_limit:
                    return {
                        'success': False,
                        'message': f'Daily withdrawal limit of {self.daily_withdrawal_limit} would be exceeded'
                    }
                
                # Check if account has sufficient balance
                total_debit = amount
                if self.withdrawal_fee > 0:
                    total_debit += self.withdrawal_fee
                
                if account.balance < total_debit:
                    return {
                        'success': False,
                        'message': 'Insufficient funds'
                    }
                
                # Generate transaction ID
                transaction_id = f"ATM{time.strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
                
                # Create withdrawal transaction
                withdrawal_transaction = Transaction(
                    transaction_id=transaction_id,
                    account_id=account.id,
                    amount=-amount,
                    transaction_type='ATM_WITHDRAWAL',
                    status='COMPLETED',
                    description=f"ATM Cash Withdrawal",
                    timestamp=datetime.now(),
                    balance_after=account.balance - amount
                )
                session.add(withdrawal_transaction)
                
                # Create fee transaction if applicable
                if self.withdrawal_fee > 0:
                    fee_transaction = Transaction(
                        transaction_id=f"FEE{transaction_id}",
                        account_id=account.id,
                        amount=-self.withdrawal_fee,
                        transaction_type='ATM_FEE',
                        status='COMPLETED',
                        description=f"ATM Withdrawal Fee",
                        timestamp=datetime.now(),
                        balance_after=account.balance - amount - self.withdrawal_fee
                    )
                    session.add(fee_transaction)
                
                # Update account balance
                account.balance -= total_debit
                
                # Commit changes
                session.commit()
                
                # Send notifications
                self._send_withdrawal_notification(account, amount, transaction_id)
                
                return {
                    'success': True,
                    'transaction_id': transaction_id,
                    'amount': str(amount),
                    'fee': str(self.withdrawal_fee) if self.withdrawal_fee > 0 else '0',
                    'total': str(total_debit),
                    'balance': str(account.balance),
                    'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
        except Exception as e:
            logger.error(f"Error processing ATM withdrawal: {str(e)}")
            return {
                'success': False,
                'message': 'System error occurred'
            }
    
    def check_balance(self, session_token: str) -> Dict[str, Any]:
        """
        Get account balance
        
        Args:
            session_token: ATM session token
            
        Returns:
            Dict containing balance information
        """
        try:
            # Validate session token
            session_data = self._validate_atm_session(session_token)
            if not session_data['valid']:
                return {
                    'success': False,
                    'message': session_data['message']
                }
            
            account_id = session_data['account_id']
            
            with db_session_scope() as session:
                # Get account
                account = session.query(Account).filter_by(id=account_id).first()
                
                if not account:
                    return {
                        'success': False,
                        'message': 'Account not found'
                    }
                
                # Generate transaction ID for the inquiry
                inquiry_id = f"INQ{time.strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
                
                return {
                    'success': True,
                    'inquiry_id': inquiry_id,
                    'account_number': account.account_number,
                    'balance': str(account.balance),
                    'available_balance': str(account.balance),
                    'currency': account.currency or 'INR',
                    'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
        except Exception as e:
            logger.error(f"Error checking ATM balance: {str(e)}")
            return {
                'success': False,
                'message': 'System error occurred'
            }
    
    def get_mini_statement(self, session_token: str, 
                         max_transactions: int = 10) -> Dict[str, Any]:
        """
        Get mini statement with recent transactions
        
        Args:
            session_token: ATM session token
            max_transactions: Maximum number of transactions to include
            
        Returns:
            Dict containing mini statement data
        """
        try:
            # Validate session token
            session_data = self._validate_atm_session(session_token)
            if not session_data['valid']:
                return {
                    'success': False,
                    'message': session_data['message']
                }
            
            account_id = session_data['account_id']
            
            with db_session_scope() as session:
                # Get account
                account = session.query(Account).filter_by(id=account_id).first()
                
                if not account:
                    return {
                        'success': False,
                        'message': 'Account not found'
                    }
                
                # Get recent transactions
                transactions = session.query(Transaction).filter_by(
                    account_id=account_id
                ).order_by(
                    Transaction.timestamp.desc()
                ).limit(max_transactions).all()
                
                # Format transactions for mini statement
                transactions_list = [{
                    'date': t.timestamp.strftime('%d-%m-%Y'),
                    'description': t.description,
                    'amount': str(t.amount),
                    'type': 'CR' if t.amount > 0 else 'DR',
                    'balance': str(t.balance_after)
                } for t in transactions]
                
                return {
                    'success': True,
                    'account_number': account.account_number,
                    'transactions': transactions_list,
                    'current_balance': str(account.balance),
                    'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
        except Exception as e:
            logger.error(f"Error getting ATM mini statement: {str(e)}")
            return {
                'success': False,
                'message': 'System error occurred'
            }
    
    def change_pin(self, session_token: str, old_pin: str, 
                  new_pin: str) -> Dict[str, Any]:
        """
        Change card PIN
        
        Args:
            session_token: ATM session token
            old_pin: Current PIN
            new_pin: New PIN
            
        Returns:
            Dict containing status of PIN change
        """
        try:
            # Validate session token
            session_data = self._validate_atm_session(session_token)
            if not session_data['valid']:
                return {
                    'success': False,
                    'message': session_data['message']
                }
            
            card_number = session_data['card_number']
            
            # Validate new PIN
            if not self._validate_pin_format(new_pin):
                return {
                    'success': False,
                    'message': 'Invalid PIN format. PIN must be 4 digits.'
                }
            
            with db_session_scope() as session:
                # Get card
                card = session.query(Card).filter_by(card_number=card_number).first()
                
                if not card:
                    return {
                        'success': False,
                        'message': 'Card not found'
                    }
                
                # Verify old PIN
                if not self._verify_pin(card, old_pin):
                    return {
                        'success': False,
                        'message': 'Current PIN is incorrect'
                    }
                
                # Update PIN
                card.pin_hash = self._hash_pin(new_pin)
                card.pin_changed_at = datetime.now()
                
                # Log the PIN change
                logger.info(f"PIN changed for card ending in {card_number[-4:]}")
                
                return {
                    'success': True,
                    'message': 'PIN changed successfully'
                }
                
        except Exception as e:
            logger.error(f"Error changing ATM PIN: {str(e)}")
            return {
                'success': False,
                'message': 'System error occurred'
            }
    
    def deposit(self, session_token: str, amount: Decimal) -> Dict[str, Any]:
        """
        Process a cash deposit transaction
        
        Args:
            session_token: ATM session token
            amount: Amount to deposit
            
        Returns:
            Dict containing transaction status and details
        """
        # Check if deposits are allowed
        if not self.allow_deposits:
            return {
                'success': False,
                'message': 'Deposits are not supported at this ATM'
            }
        
        try:
            # Validate session token
            session_data = self._validate_atm_session(session_token)
            if not session_data['valid']:
                return {
                    'success': False,
                    'message': session_data['message']
                }
            
            account_id = session_data['account_id']
            
            # Validate deposit amount
            if amount <= Decimal('0'):
                return {
                    'success': False,
                    'message': 'Deposit amount must be greater than zero'
                }
            
            with db_session_scope() as session:
                # Get account
                account = session.query(Account).filter_by(id=account_id).first()
                
                if not account:
                    return {
                        'success': False,
                        'message': 'Account not found'
                    }
                
                # Generate transaction ID
                transaction_id = f"DEP{time.strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
                
                # Create deposit transaction
                deposit_transaction = Transaction(
                    transaction_id=transaction_id,
                    account_id=account.id,
                    amount=amount,
                    transaction_type='ATM_DEPOSIT',
                    status='COMPLETED',
                    description=f"ATM Cash Deposit",
                    timestamp=datetime.now(),
                    balance_after=account.balance + amount
                )
                session.add(deposit_transaction)
                
                # Update account balance
                account.balance += amount
                
                # Commit changes
                session.commit()
                
                # Send notifications
                self._send_deposit_notification(account, amount, transaction_id)
                
                return {
                    'success': True,
                    'transaction_id': transaction_id,
                    'amount': str(amount),
                    'balance': str(account.balance),
                    'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
        except Exception as e:
            logger.error(f"Error processing ATM deposit: {str(e)}")
            return {
                'success': False,
                'message': 'System error occurred'
            }
    
    def end_session(self, session_token: str) -> Dict[str, Any]:
        """
        End an ATM session
        
        Args:
            session_token: ATM session token
            
        Returns:
            Dict containing status of session termination
        """
        try:
            # Check if session exists
            if session_token in self.transaction_cache:
                # Remove session
                del self.transaction_cache[session_token]
                
                return {
                    'success': True,
                    'message': 'Session ended successfully'
                }
            else:
                return {
                    'success': False,
                    'message': 'Session not found or already ended'
                }
                
        except Exception as e:
            logger.error(f"Error ending ATM session: {str(e)}")
            return {
                'success': False,
                'message': 'System error occurred'
            }
    
    def _verify_pin(self, card: Any, pin: str) -> bool:
        """Verify card PIN"""
        # Hash the provided PIN and compare with stored hash
        pin_hash = self._hash_pin(pin)
        return pin_hash == card.pin_hash
    
    def _hash_pin(self, pin: str) -> str:
        """Hash PIN for secure storage"""
        import hashlib
        # In a real implementation, use a proper password hashing algorithm with salt
        # This is a simplified version for demonstration
        salt = "banking_system_salt"  # In real system, each card would have its own salt
        return hashlib.sha256(f"{pin}{salt}".encode()).hexdigest()
    
    def _validate_pin_format(self, pin: str) -> bool:
        """Validate PIN format"""
        return pin.isdigit() and len(pin) == 4
    
    def _create_atm_session(self, card_number: str, account_id: int) -> str:
        """Create an ATM session token"""
        session_token = str(uuid.uuid4())
        expiry_time = time.time() + 300  # 5 minute session
        
        self.transaction_cache[session_token] = {
            'card_number': card_number,
            'account_id': account_id,
            'expiry': expiry_time
        }
        
        return session_token
    
    def _validate_atm_session(self, session_token: str) -> Dict[str, Any]:
        """Validate an ATM session token"""
        if session_token not in self.transaction_cache:
            return {
                'valid': False,
                'message': 'Invalid or expired session'
            }
        
        session_data = self.transaction_cache[session_token]
        
        # Check if session has expired
        if time.time() > session_data['expiry']:
            del self.transaction_cache[session_token]
            return {
                'valid': False,
                'message': 'Session has expired'
            }
        
        # Extend session expiry time
        session_data['expiry'] = time.time() + 300
        
        return {
            'valid': True,
            'card_number': session_data['card_number'],
            'account_id': session_data['account_id']
        }
    
    def _get_today_withdrawals(self, session, account_id: int) -> Decimal:
        """Get total withdrawals for today"""
        from sqlalchemy import func
        
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Query sum of withdrawal transactions for today
        total = session.query(func.sum(Transaction.amount)).filter(
            Transaction.account_id == account_id,
            Transaction.transaction_type == 'ATM_WITHDRAWAL',
            Transaction.status == 'COMPLETED',
            Transaction.timestamp >= today_start,
            Transaction.timestamp <= today_end
        ).scalar()
        
        # Return absolute value (withdrawals are negative)
        if total is None:
            return Decimal('0')
        return abs(total)
    
    def _is_valid_denomination(self, amount: Decimal) -> bool:
        """Check if amount is in valid denominations"""
        # Most ATMs dispense only certain denominations (e.g., multiples of 100 or 500)
        return amount % 100 == 0
    
    def _get_customer_name(self, account: Any) -> str:
        """Get customer name from account"""
        if hasattr(account, 'customer') and account.customer:
            customer = account.customer
            if hasattr(customer, 'full_name'):
                return customer.full_name
            elif hasattr(customer, 'first_name'):
                return f"{customer.first_name} {customer.last_name if hasattr(customer, 'last_name') else ''}"
        
        return "Customer"
    
    def _send_withdrawal_notification(self, account, amount, transaction_id):
        """Send withdrawal notification to customer"""
        if hasattr(account, 'customer') and account.customer:
            customer = account.customer
            
            if hasattr(customer, 'email') or hasattr(customer, 'phone'):
                customer_data = {
                    'email': getattr(customer, 'email', None),
                    'phone_number': getattr(customer, 'phone', None)
                }
                
                transaction_data = {
                    'account_number': account.account_number,
                    'type': 'ATM Withdrawal',
                    'amount': float(amount),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'balance': float(account.balance)
                }
                
                # Send notification asynchronously
                task_manager.submit_task(
                    'app.lib.notification_service.send_transaction_alert',
                    customer_data,
                    transaction_data
                )
    
    def _send_deposit_notification(self, account, amount, transaction_id):
        """Send deposit notification to customer"""
        if hasattr(account, 'customer') and account.customer:
            customer = account.customer
            
            if hasattr(customer, 'email') or hasattr(customer, 'phone'):
                customer_data = {
                    'email': getattr(customer, 'email', None),
                    'phone_number': getattr(customer, 'phone', None)
                }
                
                transaction_data = {
                    'account_number': account.account_number,
                    'type': 'ATM Deposit',
                    'amount': float(amount),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'balance': float(account.balance)
                }
                
                # Send notification asynchronously
                task_manager.submit_task(
                    'app.lib.notification_service.send_transaction_alert',
                    customer_data,
                    transaction_data
                )
    
    def _send_card_blocked_notification(self, card):
        """Send notification about blocked card"""
        try:
            with db_session_scope() as session:
                # Get account
                account = session.query(Account).filter_by(id=card.account_id).first()
                
                if account and hasattr(account, 'customer') and account.customer:
                    customer = account.customer
                    
                    if hasattr(customer, 'email'):
                        email = customer.email
                        masked_card = f"{'*' * 12}{card.card_number[-4:]}"
                        
                        notification_service.send_email(
                            recipient=email,
                            subject="Important: Your Card Has Been Blocked",
                            message=f"""
                            Dear {self._get_customer_name(account)},
                            
                            This is to inform you that your card ending with {card.card_number[-4:]} has been blocked 
                            due to multiple incorrect PIN attempts.
                            
                            If this was not you, please contact our customer support immediately at 1800-XXX-XXXX.
                            
                            To unblock your card, please visit your nearest branch with valid identification.
                            
                            Thank you,
                            Bank Security Team
                            """
                        )
                        
                    if hasattr(customer, 'phone'):
                        phone = customer.phone
                        notification_service.send_sms(
                            phone_number=phone,
                            message=f"Alert: Card ending {card.card_number[-4:]} blocked due to multiple incorrect PIN attempts. Call 1800-XXX-XXXX for assistance."
                        )
                    
                    logger.info(f"Card blocked notification sent for card ending in {card.card_number[-4:]}")
                
        except Exception as e:
            logger.error(f"Error sending card blocked notification: {str(e)}")


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
# Create singleton instance
atm_processor = ATMTransactionProcessor()
