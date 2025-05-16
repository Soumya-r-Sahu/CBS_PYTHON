"""
Account Processor

Handles the processing of account operations in the Core Banking System.
"""
from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

# Updated imports for the new directory structure
try:
    from utils.config import config
except ImportError:
    # Mock config if not available
    config = {}

try:
    from core_banking.database.models import Account, Customer, Transaction, Base
    from core_banking.database import SessionLocal
except ImportError:
    # For testing without the full models
    from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
    from sqlalchemy.orm import relationship
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    Base = declarative_base()
    engine = create_engine("sqlite:////:memory:")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    class Customer(Base):
        """Customer model"""
        __tablename__ = "customers"
        id = Column(Integer, primary_key=True, autoincrement=True)
        customer_id = Column(String(20), unique=True, nullable=False)
        first_name = Column(String(50), nullable=False)
        last_name = Column(String(50), nullable=False)
        date_of_birth = Column(DateTime, nullable=False)
        email = Column(String(100))
        phone = Column(String(20))
    
    class Account(Base):
        """Account model"""
        __tablename__ = "accounts"
        id = Column(Integer, primary_key=True, autoincrement=True)
        account_number = Column(String(20), unique=True, nullable=False)
        customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
        account_type = Column(String(20), nullable=False)
        branch_code = Column(String(20), nullable=False)
        ifsc_code = Column(String(20), nullable=False)
        balance = Column(Float, default=0.0)
        currency = Column(String(3), default="INR")
        interest_rate = Column(Float, default=0.0)
    
    class Transaction(Base):
        pass

try:
    from security.encryption import encrypt_data, decrypt_data
    from security.access_control import check_access
except ImportError:
    # Mock security functions if not available
    def encrypt_data(data): return data
    def decrypt_data(data): return data
    def check_access(user, resource): return True

# Import notification service
try:
    # Import from core_banking structure
    from core_banking.utils.notification_service import notification_service
except ImportError:
    # Mock notification service if not available
    class NotificationService:
        pass
    notification_service = NotificationService()

# Import ID generator
try:
    # Import from core_banking structure
    from core_banking.utils.id_generator import generate_account_number, AccountType
except ImportError:
    # Mock ID generator if not available
    from enum import Enum
    class AccountType(Enum):
        SAVINGS = "SAVINGS"
        CURRENT = "CURRENT"
        SALARY = "SALARY"
    def generate_account_number(state_code="14", branch_code="MAH00001"):
        return f"{state_code}{branch_code}{datetime.now().strftime('%Y%m%d%H%M%S')}"

import logging
logger = logging.getLogger(__name__)

class AccountProcessor:
    """
    Handles all account-related operations including:
    - Account creation and management
    - Balance checks
    - Account status changes
    - Interest calculations
    - Account statements generation
    """
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def create_account(self, customer_id: int, account_type: str, 
                      initial_deposit: Decimal = Decimal('0.0'),
                      branch_code: str = "MAH00001",
                      currency: str = "INR") -> Dict[str, Any]:
        """
        Create a new account for an existing customer
        
        Args:
            customer_id: ID of the customer
            account_type: Type of account (SAVINGS, CURRENT, etc.)
            initial_deposit: Initial deposit amount
            branch_code: Branch code
            currency: Account currency (default: INR)
            
        Returns:
            Dict containing account creation status and details
        """
        try:
            # Validate inputs
            if not customer_id:
                return {
                    'success': False,
                    'error': 'Customer ID is required'
                }
                
            # Convert account type to enum if needed
            try:
                account_type = AccountType(account_type)
            except ValueError:
                return {
                    'success': False,
                    'error': f"Invalid account type: {account_type}"
                }
            
            # Validate initial deposit based on account type
            min_deposit = self._get_minimum_deposit(account_type)
            
            if initial_deposit < min_deposit:
                return {
                    'success': False,
                    'error': f"Minimum initial deposit for {account_type} is {min_deposit}"
                }
            
            # Get database session
            db = SessionLocal()
            try:
                # Check if customer exists
                customer = db.query(Customer).filter_by(id=customer_id).first()
                
                if not customer:
                    return {
                        'success': False,
                        'error': 'Customer not found'
                    }
                
                # Generate account number
                account_number = generate_account_number(
                    state_code=branch_code[:2] if len(branch_code) >= 2 else "14",
                    branch_code=branch_code
                )
                
                # Set IFSC code (SBI standard)
                ifsc_code = f"SBIN0{branch_code[-5:]}" if len(branch_code) >= 5 else "SBIN000001"
                
                # Default interest rate based on account type
                interest_rate = self._get_default_interest_rate(account_type)
                
                # Create account
                new_account = Account(
                    account_number=account_number,
                    customer_id=customer_id,
                    account_type=account_type.value,
                    branch_code=branch_code,
                    ifsc_code=ifsc_code,
                    balance=float(initial_deposit),
                    currency=currency,
                    interest_rate=float(interest_rate),
                    opening_date=datetime.now(),
                    is_active=True
                )
                
                db.add(new_account)
                db.flush()  # Flush to get the ID
                
                # If initial deposit is greater than 0, create a deposit transaction
                if initial_deposit > Decimal('0'):
                    deposit_transaction = Transaction(
                        account_id=new_account.id,
                        transaction_type='DEPOSIT',
                        amount=float(initial_deposit),
                        balance_before=0.0,
                        balance_after=float(initial_deposit),
                        description='Initial deposit',
                        transaction_date=datetime.now(),
                        status='COMPLETED'
                    )
                    db.add(deposit_transaction)
                
                # Commit changes
                db.commit()
                
                # Send notification
                self._send_account_creation_notification(customer, new_account)
                
                return {
                    'success': True,
                    'account_id': new_account.id,
                    'account_number': account_number,
                    'account_type': account_type.value,
                    'ifsc_code': ifsc_code,
                    'balance': str(initial_deposit),
                    'currency': currency
                }
            
            except Exception as e:
                db.rollback()
                raise e
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error creating account: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_account_details(self, account_number: str) -> Dict[str, Any]:
        """
        Get detailed information about an account
        
        Args:
            account_number: Account number
            
        Returns:
            Dict containing account details
        """
        try:
            db = SessionLocal()
            try:
                account = db.query(Account).filter_by(account_number=account_number).first()
                
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Get customer details
                customer = db.query(Customer).filter_by(id=account.customer_id).first()
                
                # Format account information
                account_details = {
                    'success': True,
                    'account': {
                        'account_number': account.account_number,
                        'account_type': account.account_type,
                        'branch_code': account.branch_code,
                        'ifsc_code': account.ifsc_code,
                        'balance': str(account.balance),
                        'currency': account.currency,
                        'interest_rate': str(account.interest_rate),
                        'status': 'Active' if account.is_active else 'Inactive',
                        'opening_date': account.opening_date.strftime('%Y-%m-%d'),
                        'minimum_balance': str(account.minimum_balance)
                    },
                    'customer': {
                        'customer_id': customer.customer_id if customer else None,
                        'name': f"{customer.first_name} {customer.last_name}" if customer else None
                    }
                }
                
                return account_details
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error retrieving account details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
            
    def get_account_balance(self, account_number: str) -> Dict[str, Any]:
        """
        Get account balance
        
        Args:
            account_number: Account number
            
        Returns:
            Dict containing account balance information
        """
        try:
            db = SessionLocal()
            try:
                account = db.query(Account).filter_by(account_number=account_number).first()
                
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                return {
                    'success': True,
                    'account_number': account_number,
                    'balance': str(account.balance),
                    'available_balance': str(account.balance),
                    'currency': account.currency,
                    'account_status': 'Active' if account.is_active else 'Inactive'
                }
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error retrieving account balance: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def change_account_status(self, account_number: str, new_status: bool, 
                            reason: str = None) -> Dict[str, Any]:
        """
        Change account status (active/inactive)
        
        Args:
            account_number: Account number
            new_status: New status (True for active, False for inactive)
            reason: Reason for status change
            
        Returns:
            Dict containing status change result
        """
        try:
            db = SessionLocal()
            try:
                account = db.query(Account).filter_by(account_number=account_number).first()
                
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Update status
                old_status = account.is_active
                account.is_active = new_status
                
                # Update last modified timestamp
                account.updated_at = datetime.now()
                
                # Add status change reason if provided
                status_change_description = f"Account {'activated' if new_status else 'deactivated'}"
                if reason:
                    status_change_description += f": {reason}"
                
                # Commit changes
                db.commit()
                
                # If status changed, send notification
                if old_status != new_status:
                    self._send_status_change_notification(account, new_status, reason)
                
                return {
                    'success': True,
                    'account_number': account_number,
                    'new_status': 'Active' if new_status else 'Inactive',
                    'previous_status': 'Active' if old_status else 'Inactive',
                    'timestamp': datetime.now().isoformat()
                }
            except Exception as e:
                db.rollback()
                raise e
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error changing account status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_account_statement(self, account_number: str, start_date: datetime, 
                           end_date: datetime = None, 
                           transaction_types: List[str] = None) -> Dict[str, Any]:
        """
        Generate account statement
        
        Args:
            account_number: Account number
            start_date: Start date for statement period
            end_date: End date for statement period (defaults to current date)
            transaction_types: Filter by transaction types
            
        Returns:
            Dict containing account statement
        """
        try:
            # Default end date to current date if not provided
            if not end_date:
                end_date = datetime.now()
                
            db = SessionLocal()
            try:
                # Check if account exists
                account = db.query(Account).filter_by(account_number=account_number).first()
                
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Build query for transactions
                query = db.query(Transaction).filter(
                    Transaction.account_id == account.id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date
                )
                
                # Apply transaction type filter if provided
                if transaction_types:
                    query = query.filter(Transaction.transaction_type.in_(transaction_types))
                
                # Order by date
                transactions = query.order_by(Transaction.transaction_date).all()
                
                # Format transactions
                transaction_list = []
                opening_balance = None
                closing_balance = None
                
                for i, txn in enumerate(transactions):
                    # For the first transaction, use balance_before as opening balance
                    if i == 0:
                        opening_balance = txn.balance_before
                    
                    # For the last transaction, use balance_after as closing balance
                    if i == len(transactions) - 1:
                        closing_balance = txn.balance_after
                    
                    transaction_list.append({
                        'transaction_id': txn.transaction_id,
                        'date': txn.transaction_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'description': txn.description,
                        'amount': str(txn.amount),
                        'type': txn.transaction_type,
                        'balance': str(txn.balance_after)
                    })
                
                # If no transactions found, get current balance for closing
                if not transactions:
                    closing_balance = account.balance
                    # Try to find last transaction before start_date for opening balance
                    last_prior_txn = db.query(Transaction).filter(
                        Transaction.account_id == account.id,
                        Transaction.transaction_date < start_date
                    ).order_by(Transaction.transaction_date.desc()).first()
                    
                    if last_prior_txn:
                        opening_balance = last_prior_txn.balance_after
                    else:
                        opening_balance = account.balance
                
                # Get account holder information
                customer = db.query(Customer).filter_by(id=account.customer_id).first()
                
                statement = {
                    'success': True,
                    'account_number': account_number,
                    'account_type': account.account_type,
                    'customer_name': f"{customer.first_name} {customer.last_name}" if customer else "Unknown",
                    'statement_period': {
                        'from': start_date.strftime('%Y-%m-%d'),
                        'to': end_date.strftime('%Y-%m-%d')
                    },
                    'opening_balance': str(opening_balance) if opening_balance is not None else "0.00",
                    'closing_balance': str(closing_balance) if closing_balance is not None else str(account.balance),
                    'currency': account.currency,
                    'transactions': transaction_list,
                    'transaction_count': len(transaction_list),
                    'generation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                # Logging
                logger.info(f"Generated account statement for account {account_number}")
                
                return statement
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error generating account statement: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_minimum_deposit(self, account_type: AccountType) -> Decimal:
        """Get minimum initial deposit for an account type"""
        min_deposits = {
            AccountType.SAVINGS: Decimal('500.00'),
            AccountType.CURRENT: Decimal('1000.00'),
            AccountType.FIXED_DEPOSIT: Decimal('5000.00'),
            AccountType.RECURRING_DEPOSIT: Decimal('500.00'),
            AccountType.SALARY: Decimal('0.00'),
            AccountType.NRI: Decimal('1000.00'),
            AccountType.PENSION: Decimal('0.00')
        }
        
        return min_deposits.get(account_type, Decimal('500.00'))
    
    def _get_default_interest_rate(self, account_type: AccountType) -> Decimal:
        """Get default interest rate for an account type"""
        interest_rates = {
            AccountType.SAVINGS: Decimal('3.50'),
            AccountType.CURRENT: Decimal('0.00'),
            AccountType.FIXED_DEPOSIT: Decimal('5.50'),
            AccountType.RECURRING_DEPOSIT: Decimal('5.00'),
            AccountType.SALARY: Decimal('3.50'),
            AccountType.NRI: Decimal('4.00'),
            AccountType.PENSION: Decimal('4.00')
        }
        
        return interest_rates.get(account_type, Decimal('0.00'))
    
    def _get_minimum_balance_requirement(self, account_type: AccountType) -> Decimal:
        """Get minimum balance requirement for an account type"""
        min_balances = {
            AccountType.SAVINGS: Decimal('500.00'),
            AccountType.CURRENT: Decimal('5000.00'),
            AccountType.FIXED_DEPOSIT: Decimal('0.00'),  # No minimum after initial deposit
            AccountType.RECURRING_DEPOSIT: Decimal('0.00'),  # No minimum after initial deposit
            AccountType.SALARY: Decimal('0.00'),
            AccountType.NRI: Decimal('1000.00'),
            AccountType.PENSION: Decimal('0.00')
        }
        
        return min_balances.get(account_type, Decimal('500.00'))
    
    def _send_account_creation_notification(self, customer, account):
        """Send notification about account creation"""
        if hasattr(customer, 'email') or hasattr(customer, 'phone'):
            customer_data = {
                'email': getattr(customer, 'email', None),
                'phone_number': getattr(customer, 'phone', None)
            }
            
            notification_data = {
                'subject': 'Account Created Successfully',
                'message': f"""
                    Dear {customer.first_name if hasattr(customer, 'first_name') else 'Valued Customer'},
                    
                    Your new {account.account_type} account has been created successfully.
                    
                    Account Details:
                    - Account Number: {account.account_number}
                    - Branch: {account.branch_code}
                    - IFSC Code: {account.ifsc_code}
                    - Initial Balance: {account.balance} {account.currency}
                    
                    Thank you for banking with us.
                    
                    Regards,
                    Core Banking System
                """
            }
            
            try:
                notification_service.send_email(
                    recipient=customer_data['email'], 
                    subject=notification_data['subject'],
                    message=notification_data['message']
                )
                
                if customer_data.get('phone_number'):
                    sms_message = (
                        f"Your {account.account_type} account {account.account_number} "
                        f"has been created successfully with balance {account.balance} {account.currency}."
                    )
                    notification_service.send_sms(
                        phone_number=customer_data['phone_number'],
                        message=sms_message
                    )
            except Exception as e:
                logger.error(f"Failed to send account creation notification: {str(e)}")
    
    def _send_status_change_notification(self, account, new_status, reason=None):
        """Send notification about account status change"""
        try:
            db = SessionLocal()
            try:
                customer = db.query(Customer).filter_by(id=account.customer_id).first()
                
                if customer and (hasattr(customer, 'email') or hasattr(customer, 'phone')):
                    status_text = "activated" if new_status else "deactivated"
                    
                    customer_data = {
                        'email': getattr(customer, 'email', None),
                        'phone_number': getattr(customer, 'phone', None)
                    }
                    
                    notification_data = {
                        'subject': f'Account {status_text.capitalize()}',
                        'message': f"""
                            Dear {customer.first_name if hasattr(customer, 'first_name') else 'Valued Customer'},
                            
                            Your account {account.account_number} has been {status_text}.
                            {f"Reason: {reason}" if reason else ""}
                            
                            If you did not request this change or have any questions, please contact our customer support immediately.
                            
                            Regards,
                            Core Banking System
                        """
                    }
                    
                    notification_service.send_email(
                        recipient=customer_data['email'], 
                        subject=notification_data['subject'],
                        message=notification_data['message']
                    )
                    
                    if customer_data.get('phone_number'):
                        sms_message = (
                            f"Your account {account.account_number} has been {status_text}. "
                            f"{f'Reason: {reason}' if reason else 'Contact support for assistance.'}"
                        )
                        notification_service.send_sms(
                            phone_number=customer_data['phone_number'],
                            message=sms_message
                        )
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to send status change notification: {str(e)}")
    
    def _send_account_closure_notification(self, customer, account, reason):
        """Send notification about account closure"""
        try:
            if customer and (hasattr(customer, 'email') or hasattr(customer, 'phone')):
                customer_data = {
                    'email': getattr(customer, 'email', None),
                    'phone_number': getattr(customer, 'phone', None)
                }
                
                notification_data = {
                    'subject': 'Account Closure Confirmation',
                    'message': f"""
                        Dear {customer.first_name if hasattr(customer, 'first_name') else 'Valued Customer'},
                        
                        Your {account.account_type} account {account.account_number} has been closed successfully.
                        
                        Reason for closure: {reason}
                        
                        If you did not request this closure or have any questions, please contact our customer support immediately.
                        
                        Thank you for your business.
                        
                        Regards,
                        Core Banking System
                    """
                }
                
                notification_service.send_email(
                    recipient=customer_data['email'], 
                    subject=notification_data['subject'],
                    message=notification_data['message']
                )
                
                if customer_data.get('phone_number'):
                    sms_message = (
                        f"Your account {account.account_number} has been closed. "
                        f"Reason: {reason}. Contact support for any queries."
                    )
                    notification_service.send_sms(
                        phone_number=customer_data['phone_number'],
                        message=sms_message
                    )
        except Exception as e:
            logger.error(f"Failed to send account closure notification: {str(e)}")
