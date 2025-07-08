"""
Account Service

Provides functionality for account management in the Core Banking System.
"""

import logging
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple

from database.python.connection import db_session_scope
from app.models.models import Account, Customer, Transaction

# Import with fallback for backward compatibility
try:
    from utils.lib.id_generator import generate_account_number
except ImportError:
    # Fallback to old import path
    from app.lib.id_generator import generate_account_number


# Import with fallback for backward compatibility
try:
    from utils.lib.notification_service import notification_service
except ImportError:
    # Fallback to old import path
    from app.lib.notification_service import notification_service



# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
logger = logging.getLogger(__name__)

class AccountService:
    """
    Service class for account-related operations
    
    Features:
    - Account creation
    - Account status management
    - Balance inquiries
    - Interest calculation
    - Statement generation
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(AccountService, cls).__new__(cls)
        return cls._instance
    
    def create_account(self, customer_id: int, account_type: str, 
                     initial_deposit: Decimal = Decimal('0'),
                     currency: str = 'INR') -> Dict[str, Any]:
        """
        Create a new account for a customer
        
        Args:
            customer_id: ID of the customer
            account_type: Type of account (SAVINGS, CURRENT, etc.)
            initial_deposit: Initial deposit amount
            currency: Currency code (ISO)
            
        Returns:
            Dict containing account details or error information
        """
        try:
            with db_session_scope() as session:
                # Check if customer exists
                customer = session.query(Customer).filter_by(id=customer_id).first()
                
                if not customer:
                    return {
                        'success': False,
                        'error': 'Customer not found'
                    }
                
                # Validate account type
                valid_types = ['SAVINGS', 'CURRENT', 'SALARY', 'FIXED_DEPOSIT', 'LOAN', 'CREDIT']
                if account_type not in valid_types:
                    return {
                        'success': False,
                        'error': f'Invalid account type. Valid types are: {", ".join(valid_types)}'
                    }
                
                # Generate account number
                account_number = generate_account_number(account_type)
                
                # Set interest rate based on account type
                interest_rate = self._get_interest_rate(account_type)
                
                # Create account
                account = Account(
                    customer_id=customer_id,
                    account_number=account_number,
                    account_type=account_type,
                    balance=initial_deposit,
                    currency=currency,
                    status='ACTIVE',
                    interest_rate=interest_rate,
                    created_at=datetime.now()
                )
                
                session.add(account)
                session.flush()  # Flush to get the account ID
                
                # If initial deposit > 0, create deposit transaction
                if initial_deposit > 0:
                    transaction = Transaction(
                        account_id=account.id,
                        transaction_id=f"DEP{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4]}",
                        amount=initial_deposit,
                        transaction_type='INITIAL_DEPOSIT',
                        status='COMPLETED',
                        description='Initial deposit',
                        timestamp=datetime.now(),
                        balance_after=initial_deposit
                    )
                    session.add(transaction)
                
                # Commit changes
                session.commit()
                
                # Send welcome email to customer
                self._send_new_account_notification(customer, account)
                
                return {
                    'success': True,
                    'account_id': account.id,
                    'account_number': account_number,
                    'account_type': account_type,
                    'balance': str(initial_deposit),
                    'currency': currency,
                    'customer_id': customer_id,
                    'customer_name': f"{customer.first_name} {customer.last_name}",
                    'created_at': account.created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error creating account: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_account_by_number(self, account_number: str) -> Dict[str, Any]:
        """
        Get account details by account number
        
        Args:
            account_number: The account number
            
        Returns:
            Dict containing account details or error information
        """
        try:
            with db_session_scope() as session:
                account = session.query(Account).filter_by(account_number=account_number).first()
                
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Get customer details
                customer = session.query(Customer).filter_by(id=account.customer_id).first()
                
                # Format account details
                account_details = {
                    'success': True,
                    'account_id': account.id,
                    'account_number': account.account_number,
                    'account_type': account.account_type,
                    'balance': str(account.balance),
                    'available_balance': str(account.balance),
                    'currency': account.currency,
                    'status': account.status,
                    'created_at': account.created_at.isoformat(),
                    'interest_rate': str(account.interest_rate),
                    'customer': {
                        'id': customer.id,
                        'name': f"{customer.first_name} {customer.last_name}",
                        'email': customer.email,
                        'phone': customer.phone
                    } if customer else None
                }
                
                return account_details
                
        except Exception as e:
            logger.error(f"Error retrieving account: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_accounts_by_customer(self, customer_id: int) -> Dict[str, Any]:
        """
        Get all accounts for a specific customer
        
        Args:
            customer_id: ID of the customer
            
        Returns:
            Dict containing accounts list or error information
        """
        try:
            with db_session_scope() as session:
                # Check if customer exists
                customer = session.query(Customer).filter_by(id=customer_id).first()
                
                if not customer:
                    return {
                        'success': False,
                        'error': 'Customer not found'
                    }
                
                # Get customer accounts
                accounts = session.query(Account).filter_by(customer_id=customer_id).all()
                
                # Format accounts
                accounts_list = [{
                    'account_id': account.id,
                    'account_number': account.account_number,
                    'account_type': account.account_type,
                    'balance': str(account.balance),
                    'currency': account.currency,
                    'status': account.status
                } for account in accounts]
                
                return {
                    'success': True,
                    'customer': {
                        'id': customer.id,
                        'name': f"{customer.first_name} {customer.last_name}"
                    },
                    'accounts': accounts_list,
                    'total_accounts': len(accounts_list)
                }
                
        except Exception as e:
            logger.error(f"Error retrieving customer accounts: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_account_status(self, account_number: str, new_status: str) -> Dict[str, Any]:
        """
        Update account status
        
        Args:
            account_number: The account number
            new_status: New status (ACTIVE, DORMANT, CLOSED, FROZEN)
            
        Returns:
            Dict containing result of the operation
        """
        try:
            valid_statuses = ['ACTIVE', 'DORMANT', 'CLOSED', 'FROZEN']
            
            if new_status not in valid_statuses:
                return {
                    'success': False,
                    'error': f'Invalid status. Valid status values are: {", ".join(valid_statuses)}'
                }
            
            with db_session_scope() as session:
                account = session.query(Account).filter_by(account_number=account_number).first()
                
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Update status
                old_status = account.status
                account.status = new_status
                account.updated_at = datetime.now()
                
                # Log status change
                logger.info(f"Account {account_number} status changed from {old_status} to {new_status}")
                
                # Notify customer about status change
                self._send_status_change_notification(account)
                
                return {
                    'success': True,
                    'account_number': account_number,
                    'old_status': old_status,
                    'new_status': new_status
                }
                
        except Exception as e:
            logger.error(f"Error updating account status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_transaction_history(self, account_number: str, 
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              limit: int = 50,
                              offset: int = 0) -> Dict[str, Any]:
        """
        Get transaction history for an account
        
        Args:
            account_number: The account number
            start_date: Start date for filtering transactions
            end_date: End date for filtering transactions
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip (for pagination)
            
        Returns:
            Dict containing transactions or error information
        """
        try:
            with db_session_scope() as session:
                # Get account
                account = session.query(Account).filter_by(account_number=account_number).first()
                
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Build query
                query = session.query(Transaction).filter_by(account_id=account.id)
                
                # Apply date filters if provided
                if start_date:
                    query = query.filter(Transaction.timestamp >= start_date)
                
                if end_date:
                    query = query.filter(Transaction.timestamp <= end_date)
                
                # Get total count for pagination
                total_count = query.count()
                
                # Get transactions with limit and offset
                transactions = query.order_by(
                    Transaction.timestamp.desc()
                ).limit(limit).offset(offset).all()
                
                # Format transactions
                transactions_list = [{
                    'transaction_id': t.transaction_id,
                    'date': t.timestamp.isoformat(),
                    'description': t.description,
                    'amount': str(t.amount),
                    'type': t.transaction_type,
                    'status': t.status,
                    'balance_after': str(t.balance_after)
                } for t in transactions]
                
                return {
                    'success': True,
                    'account_number': account_number,
                    'account_type': account.account_type,
                    'currency': account.currency,
                    'transactions': transactions_list,
                    'pagination': {
                        'total': total_count,
                        'limit': limit,
                        'offset': offset,
                        'has_more': (offset + limit) < total_count
                    }
                }
                
        except Exception as e:
            logger.error(f"Error retrieving transaction history: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_interest(self, account_number: str) -> Dict[str, Any]:
        """
        Calculate interest for a savings account
        
        Args:
            account_number: The account number
            
        Returns:
            Dict containing interest calculation details
        """
        try:
            with db_session_scope() as session:
                # Get account
                account = session.query(Account).filter_by(account_number=account_number).first()
                
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Check if it's an interest-bearing account
                if account.account_type not in ['SAVINGS', 'FIXED_DEPOSIT']:
                    return {
                        'success': False,
                        'error': f'Interest calculation not applicable for {account.account_type} accounts'
                    }
                
                # Get interest rate from account or use default
                interest_rate = account.interest_rate or self._get_interest_rate(account.account_type)
                
                # Calculate daily interest (simple interest for demonstration)
                daily_rate = interest_rate / Decimal('365')
                daily_interest = account.balance * daily_rate
                
                # Calculate monthly and annual interest
                monthly_interest = daily_interest * Decimal('30')
                annual_interest = daily_interest * Decimal('365')
                
                return {
                    'success': True,
                    'account_number': account_number,
                    'balance': str(account.balance),
                    'interest_rate': str(interest_rate),
                    'daily_interest': str(daily_interest.quantize(Decimal('0.01'))),
                    'monthly_interest': str(monthly_interest.quantize(Decimal('0.01'))),
                    'annual_interest': str(annual_interest.quantize(Decimal('0.01')))
                }
                
        except Exception as e:
            logger.error(f"Error calculating interest: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_interest_rate(self, account_type: str) -> Decimal:
        """Get default interest rate based on account type"""
        rates = {
            'SAVINGS': Decimal('0.035'),     # 3.5%
            'FIXED_DEPOSIT': Decimal('0.06'),  # 6%
            'CURRENT': Decimal('0.0'),        # 0%
            'SALARY': Decimal('0.04'),        # 4%
            'LOAN': Decimal('0.0'),           # N/A for loans
            'CREDIT': Decimal('0.0')          # N/A for credit accounts
        }
        
        return rates.get(account_type, Decimal('0.0'))
    
    def _send_new_account_notification(self, customer, account):
        """Send notification to customer about new account"""
        if hasattr(customer, 'email') and customer.email:
            subject = f"Welcome to Your New {account.account_type} Account"
            message = f"""
            Dear {customer.first_name} {customer.last_name},
            
            Congratulations! Your new {account.account_type} account has been successfully opened.
            
            Your account details:
            Account Number: {account.account_number}
            Account Type: {account.account_type}
            Initial Balance: {account.balance} {account.currency}
            
            Thank you for choosing our banking services.
            
            Sincerely,
            The Banking Team
            """
            
            notification_service.send_email(
                recipient=customer.email,
                subject=subject,
                message=message
            )
            
        if hasattr(customer, 'phone') and customer.phone:
            sms_message = f"Your new {account.account_type} account is now active. Account number: {account.account_number[-4:]}. Thank you for banking with us."
            
            notification_service.send_sms(
                phone_number=customer.phone,
                message=sms_message
            )
    
    def _send_status_change_notification(self, account):
        """Send notification to customer about account status change"""
        try:
            with db_session_scope() as session:
                customer = session.query(Customer).filter_by(id=account.customer_id).first()
                
                if not customer:
                    logger.warning(f"Could not find customer for account {account.account_number}")
                    return
                
                if account.status in ['FROZEN', 'CLOSED']:
                    subject = f"Important: Your Account Status Has Changed"
                    message = f"""
                    Dear {customer.first_name} {customer.last_name},
                    
                    This is to inform you that your account {account.account_number} status has been changed to {account.status}.
                    
                    If you have any questions, please contact our customer support.
                    
                    Sincerely,
                    The Banking Team
                    """
                    
                    if hasattr(customer, 'email') and customer.email:
                        notification_service.send_email(
                            recipient=customer.email,
                            subject=subject,
                            message=message
                        )
                    
                    if hasattr(customer, 'phone') and customer.phone:
                        sms_message = f"Your account ending {account.account_number[-4:]} status has changed to {account.status}. Please contact customer support for details."
                        
                        notification_service.send_sms(
                            phone_number=customer.phone,
                            message=sms_message
                        )
                
        except Exception as e:
            logger.error(f"Error sending status change notification: {str(e)}")

# Create singleton instance
account_service = AccountService()
