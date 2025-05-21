"""
Refactored UPI Transaction Processor

This module implements the UPI transaction processor using the new design patterns
and unified error handling framework.
"""

import logging
import uuid
import hashlib
import json
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, date

# Import unified error handling and new patterns
from utils.unified_error_handling import handle_exception
from utils.common.design_patterns import singleton, Observer
from utils.common.refactored_validators import (
    SchemaValidator, RangeValidator, PatternValidator
)

# Import UPI-specific exceptions
from payments.upi.exceptions.refactored_upi_exceptions import (
    UpiTransactionException, UpiAmountExceedsLimitException,
    UpiInvalidAccountException, UpiDailyLimitExceededException,
    UpiInvalidPinException
)

# Import application dependencies
from app.config.config_loader import config
from app.models.models import Transaction, Account, UPITransaction
from database.python.common.database_operations import db_session_scope
from security.common.encryption import encrypt_data, decrypt_data

# Configure logger
logger = logging.getLogger(__name__)


@singleton
class UPITransactionProcessor:
    """
    Processes UPI transactions
    
    Features:
    - Validate UPI transactions
    - Process different types of UPI transactions (P2P, P2M, etc.)
    - Handle callbacks and confirmations
    - Record transaction details
    """
    
    def __init__(self):
        """Initialize UPI transaction processor"""
        # Load configuration
        self._load_configuration()
        
        # Set up validators
        self._setup_validators()
        
        # Create notification observer
        self.notification_center = Observer()
        self._register_notification_handlers()
    
    def _load_configuration(self):
        """Load configuration values"""
        self.processing_fee = Decimal(config.get('upi.processing_fee', '0'))
        self.daily_limit = Decimal(config.get('upi.daily_limit', '100000'))
        self.transaction_limit = Decimal(config.get('upi.transaction_limit', '20000'))
        self.merchant_discount_rate = Decimal(config.get('upi.merchant_discount_rate', '0.0025'))  # 0.25%
    
    def _setup_validators(self):
        """Set up validators for UPI transactions"""
        # UPI ID validator
        self.upi_id_validator = PatternValidator(
            pattern=r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$',
            error_message="Invalid UPI ID format"
        )
        
        # Transaction amount validator
        self.amount_validator = RangeValidator(
            min_value=1.0,
            max_value=float(self.transaction_limit)
        )
        
        # UPI PIN validator (simple 6-digit check)
        self.pin_validator = PatternValidator(
            pattern=r'^\d{6}$',
            error_message="UPI PIN must be 6 digits"
        )
        
        # Transaction schema validator
        self.transaction_validator = SchemaValidator({
            "upi_id": self.upi_id_validator,
            "amount": self.amount_validator,
            "recipient_upi_id": self.upi_id_validator,
            "reference": PatternValidator(
                pattern=r'^[A-Za-z0-9\s-]{1,35}$',
                error_message="Reference must be alphanumeric, max 35 characters"
            )
        })
    
    def _register_notification_handlers(self):
        """Register notification handlers"""
        # These would be implemented elsewhere and registered here
        from app.lib.notification_service import (
            sms_notification_handler, 
            email_notification_handler,
            audit_log_handler
        )
        
        # Register handlers for different events
        self.notification_center.subscribe(
            "upi.transaction.initiated", audit_log_handler
        )
        self.notification_center.subscribe(
            "upi.transaction.completed", sms_notification_handler
        )
        self.notification_center.subscribe(
            "upi.transaction.completed", email_notification_handler
        )
        self.notification_center.subscribe(
            "upi.transaction.completed", audit_log_handler
        )
        self.notification_center.subscribe(
            "upi.transaction.failed", audit_log_handler
        )
    
    @handle_exception
    def process_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a UPI transaction
        
        Args:
            transaction_data: Transaction details including:
                - upi_id: Sender's UPI ID
                - recipient_upi_id: Recipient's UPI ID
                - amount: Transaction amount
                - reference: Transaction reference
                - pin: UPI PIN (encrypted)
                - transaction_type: Type of transaction (P2P, P2M)
        
        Returns:
            Transaction result with transaction ID and status
        
        Raises:
            UpiValidationException: If validation fails
            UpiTransactionException: If transaction processing fails
            UpiAmountExceedsLimitException: If amount exceeds transaction limit
            UpiDailyLimitExceededException: If daily limit is exceeded
            UpiInvalidPinException: If UPI PIN is invalid
        """
        # Generate transaction ID
        transaction_id = self._generate_transaction_id()
        
        try:
            # Validate transaction data
            self._validate_transaction(transaction_data)
            
            # Validate UPI PIN
            self._validate_pin(transaction_data.get('pin'), transaction_data['upi_id'])
            
            # Check limits
            amount = Decimal(str(transaction_data['amount']))
            self._check_transaction_limit(amount, transaction_id)
            self._check_daily_limit(transaction_data['upi_id'], amount, transaction_id)
            
            # Notify about transaction initiation
            self.notification_center.notify(
                "upi.transaction.initiated",
                {
                    "transaction_id": transaction_id,
                    "upi_id": transaction_data['upi_id'],
                    "amount": str(amount),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Process the transaction based on type
            transaction_type = transaction_data.get('transaction_type', 'P2P')
            if transaction_type == 'P2M':  # Person to Merchant
                result = self._process_p2m_transaction(transaction_data, transaction_id)
            else:  # Default: Person to Person
                result = self._process_p2p_transaction(transaction_data, transaction_id)
            
            # Notify about transaction completion
            self.notification_center.notify(
                "upi.transaction.completed",
                {
                    "transaction_id": transaction_id,
                    "upi_id": transaction_data['upi_id'],
                    "recipient_upi_id": transaction_data['recipient_upi_id'],
                    "amount": str(amount),
                    "timestamp": datetime.now().isoformat(),
                    "status": "completed"
                }
            )
            
            return result
            
        except Exception as e:
            # Log the error and notify about transaction failure
            logger.error(f"UPI transaction failed: {str(e)}", exc_info=True)
            
            self.notification_center.notify(
                "upi.transaction.failed",
                {
                    "transaction_id": transaction_id,
                    "upi_id": transaction_data.get('upi_id'),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            # Re-raise the exception for proper handling
            raise
    
    def _generate_transaction_id(self) -> str:
        """Generate a unique transaction ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        random_component = uuid.uuid4().hex[:8]
        return f"UPI{timestamp}{random_component}"
    
    def _validate_transaction(self, transaction_data: Dict[str, Any]) -> None:
        """
        Validate transaction data
        
        Args:
            transaction_data: Transaction details
            
        Raises:
            UpiValidationException: If validation fails
        """
        # Use schema validator
        is_valid, error = self.transaction_validator.validate(transaction_data)
        if not is_valid:
            raise UpiInvalidAccountException(
                account_id=transaction_data.get('upi_id', 'unknown'),
                message=f"Invalid transaction data: {error}"
            )
        
        # Verify that sender and recipient are different
        if transaction_data['upi_id'] == transaction_data['recipient_upi_id']:
            raise UpiValidationException(
                message="Sender and recipient UPI IDs cannot be the same",
                field="recipient_upi_id"
            )
    
    def _validate_pin(self, encrypted_pin: str, upi_id: str) -> None:
        """
        Validate UPI PIN
        
        Args:
            encrypted_pin: Encrypted UPI PIN
            upi_id: UPI ID of the user
            
        Raises:
            UpiInvalidPinException: If PIN is invalid
        """
        if not encrypted_pin:
            raise UpiInvalidPinException(message="UPI PIN is required")
        
        try:
            # Decrypt PIN (implementation would depend on encryption method)
            decrypted_pin = decrypt_data(encrypted_pin)
            
            # Validate format
            is_valid, error = self.pin_validator.validate(decrypted_pin)
            if not is_valid:
                raise UpiInvalidPinException(message=error)
            
            # Verify PIN against stored value (example implementation)
            # In a real system, this would check against a stored hash
            with db_session_scope() as session:
                stored_pin_hash = session.query(UPITransaction).filter_by(upi_id=upi_id).first()
                if not stored_pin_hash:
                    raise UpiInvalidPinException(message="UPI PIN not found for this UPI ID")
                
                # Hash the provided PIN for comparison
                provided_pin_hash = hashlib.sha256(decrypted_pin.encode()).hexdigest()
                
                # Compare hashes
                if provided_pin_hash != stored_pin_hash:
                    # Track failed attempts (implementation would depend on your authentication system)
                    attempts_left = self._track_failed_pin_attempt(upi_id)
                    raise UpiInvalidPinException(
                        message="Invalid UPI PIN provided",
                        attempts_left=attempts_left
                    )
        
        except Exception as e:
            if isinstance(e, UpiInvalidPinException):
                raise
            
            # Log the error but don't expose details
            logger.error(f"PIN validation error: {str(e)}", exc_info=True)
            raise UpiInvalidPinException()
    
    def _track_failed_pin_attempt(self, upi_id: str) -> int:
        """
        Track failed PIN attempts and return attempts left
        
        Args:
            upi_id: UPI ID of the user
            
        Returns:
            Number of attempts left before lockout
        """
        # Implementation would depend on your authentication tracking system
        # This is a placeholder
        max_attempts = 3
        current_attempts = 1  # Get from database
        
        return max_attempts - current_attempts
    
    def _check_transaction_limit(self, amount: Decimal, transaction_id: str) -> None:
        """
        Check if transaction amount is within allowed limits
        
        Args:
            amount: Transaction amount
            transaction_id: Transaction ID for reference
            
        Raises:
            UpiAmountExceedsLimitException: If amount exceeds limit
        """
        if amount > self.transaction_limit:
            raise UpiAmountExceedsLimitException(
                amount=float(amount),
                limit=float(self.transaction_limit),
                transaction_id=transaction_id
            )
    
    def _check_daily_limit(self, upi_id: str, amount: Decimal, transaction_id: str) -> None:
        """
        Check if transaction would exceed daily limit
        
        Args:
            upi_id: UPI ID of the user
            amount: Transaction amount
            transaction_id: Transaction ID for reference
            
        Raises:
            UpiDailyLimitExceededException: If daily limit would be exceeded
        """
        # Get total transactions for today
        today = date.today()
        
        with db_session_scope() as session:
            # This is a simplified example - actual implementation would depend on your model
            today_transactions = session.query(
                UPITransaction
            ).filter(
                UPITransaction.upi_id == upi_id,
                UPITransaction.transaction_date == today
            ).all()
            
            # Calculate total amount
            daily_total = sum(t.amount for t in today_transactions)
            
            # Add current transaction
            new_total = daily_total + amount
            
            if new_total > self.daily_limit:
                raise UpiDailyLimitExceededException(
                    daily_total=float(new_total),
                    daily_limit=float(self.daily_limit)
                )
    
    def _process_p2p_transaction(
        self, 
        transaction_data: Dict[str, Any], 
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        Process Person to Person transaction
        
        Args:
            transaction_data: Transaction details
            transaction_id: Transaction ID
            
        Returns:
            Transaction result
        """
        # Implementation details would depend on your system
        # This is a simplified example
        with db_session_scope() as session:
            # Debit sender account
            sender_account = self._get_account_by_upi_id(session, transaction_data['upi_id'])
            if not sender_account:
                raise UpiInvalidAccountException(account_id=transaction_data['upi_id'])
            
            # Credit recipient account
            recipient_account = self._get_account_by_upi_id(session, transaction_data['recipient_upi_id'])
            if not recipient_account:
                raise UpiInvalidAccountException(account_id=transaction_data['recipient_upi_id'])
            
            amount = Decimal(str(transaction_data['amount']))
            
            # Update balances
            sender_account.balance -= amount
            recipient_account.balance += amount
            
            # Create transaction record
            transaction = UPITransaction(
                transaction_id=transaction_id,
                upi_id=transaction_data['upi_id'],
                recipient_upi_id=transaction_data['recipient_upi_id'],
                amount=amount,
                reference=transaction_data.get('reference', ''),
                transaction_date=date.today(),
                transaction_time=datetime.now(),
                status='completed',
                transaction_type='P2P'
            )
            
            session.add(transaction)
            
            # Return result
            return {
                'transaction_id': transaction_id,
                'status': 'completed',
                'timestamp': datetime.now().isoformat(),
                'amount': str(amount),
                'message': f"Transaction to {transaction_data['recipient_upi_id']} successful"
            }
    
    def _process_p2m_transaction(
        self, 
        transaction_data: Dict[str, Any], 
        transaction_id: str
    ) -> Dict[str, Any]:
        """
        Process Person to Merchant transaction
        
        Args:
            transaction_data: Transaction details
            transaction_id: Transaction ID
            
        Returns:
            Transaction result
        """
        # Similar to P2P but with merchant discount rate
        with db_session_scope() as session:
            # Debit sender account
            sender_account = self._get_account_by_upi_id(session, transaction_data['upi_id'])
            if not sender_account:
                raise UpiInvalidAccountException(account_id=transaction_data['upi_id'])
            
            # Credit merchant account
            merchant_account = self._get_account_by_upi_id(session, transaction_data['recipient_upi_id'])
            if not merchant_account:
                raise UpiInvalidAccountException(account_id=transaction_data['recipient_upi_id'])
            
            amount = Decimal(str(transaction_data['amount']))
            
            # Calculate merchant fee
            merchant_fee = amount * self.merchant_discount_rate
            
            # Update balances
            sender_account.balance -= amount
            merchant_account.balance += (amount - merchant_fee)
            
            # Create transaction record
            transaction = UPITransaction(
                transaction_id=transaction_id,
                upi_id=transaction_data['upi_id'],
                recipient_upi_id=transaction_data['recipient_upi_id'],
                amount=amount,
                merchant_fee=merchant_fee,
                reference=transaction_data.get('reference', ''),
                transaction_date=date.today(),
                transaction_time=datetime.now(),
                status='completed',
                transaction_type='P2M'
            )
            
            session.add(transaction)
            
            # Return result
            return {
                'transaction_id': transaction_id,
                'status': 'completed',
                'timestamp': datetime.now().isoformat(),
                'amount': str(amount),
                'merchant_fee': str(merchant_fee),
                'message': f"Payment to merchant {transaction_data['recipient_upi_id']} successful"
            }
    
    def _get_account_by_upi_id(self, session, upi_id: str) -> Optional[Account]:
        """Get account by UPI ID"""
        # Implementation depends on your data model
        return session.query(Account).join(
            UPITransaction, UPITransaction.account_id == Account.id
        ).filter(
            UPITransaction.upi_id == upi_id
        ).first()
