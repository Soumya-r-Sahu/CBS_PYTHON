"""
UPI Payment Service Module.

Contains business logic for UPI payment processing.
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import base64
import time

from ..models.upi_model import UpiRegistration, UpiTransaction, TransactionStatus, TransactionType, QRCode
from ..repositories.upi_repository import upi_repository
from ..validators.upi_validators import (
    validate_registration_data, validate_transaction_data, validate_upi_id, validate_amount
)
from ..exceptions.upi_exceptions import (
    UpiBaseException, UpiValidationError, UpiNotFoundError, UpiRegistrationError,
    UpiAlreadyRegisteredError, UpiTransactionError, UpiAmountExceedsLimitError,
    UpiInvalidAccountError, UpiInsufficientFundsError, UpiGatewayError, UpiTimeoutError
)
from ..config.upi_config import upi_config

# Set up logging
logger = logging.getLogger(__name__)


class UpiService:
    """Service for UPI payment operations"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(UpiService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the UPI service"""
        self.env_name = upi_config.get('ENVIRONMENT', 'development')
        self.is_mock_mode = upi_config.get('USE_MOCK', True)
        self.validation_strict = upi_config.get('VALIDATION_STRICT', False)
        self.max_transaction_limit = upi_config.get('MAX_TRANSACTION_LIMIT', 50000)
        self.notification_enabled = upi_config.get('NOTIFICATION_ENABLED', True)
        
        # Try to import QR code module if available
        try:
            import qrcode
            self.qr_module_available = True
        except ImportError:
            logger.warning("QR code module not available. QR code generation will be simulated.")
            self.qr_module_available = False
        
        logger.info(f"UPI Service initialized - Environment: {self.env_name}, Mock mode: {self.is_mock_mode}")
    
    def register_user(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register a new user for UPI services.
        
        Args:
            registration_data: User registration data
            
        Returns:
            Dict: Registration data
            
        Raises:
            UpiValidationError: If registration data is invalid
            UpiAlreadyRegisteredError: If UPI ID is already registered
        """
        try:
            # Validate registration data
            validated_data = validate_registration_data(registration_data)
            
            # Check if UPI ID is already registered
            try:
                existing_reg = upi_repository.get_registration(validated_data['upi_id'])
                if existing_reg:
                    raise UpiAlreadyRegisteredError(validated_data['upi_id'])
            except UpiNotFoundError:
                # This is expected if the UPI ID is not registered yet
                pass
            
            # Create registration object
            registration = UpiRegistration(
                upi_id=validated_data['upi_id'],
                account_number=validated_data['account_number'],
                mobile_number=validated_data['mobile_number'],
                name=validated_data['name']
            )
            
            # Save registration
            result = upi_repository.save_registration(registration)
            
            logger.info(f"User registered successfully with UPI ID: {registration.upi_id}")
            return result
            
        except (UpiValidationError, UpiAlreadyRegisteredError) as e:
            # Re-raise known exceptions
            logger.warning(f"Registration failed: {str(e)}")
            raise
            
        except Exception as e:
            # Wrap unknown exceptions
            logger.error(f"Unexpected error during registration: {str(e)}")
            raise UpiRegistrationError(f"Failed to register UPI user: {str(e)}")
    
    def get_user_registration(self, upi_id: str) -> Dict[str, Any]:
        """
        Get user registration by UPI ID.
        
        Args:
            upi_id: UPI ID to retrieve
            
        Returns:
            Dict: Registration data
            
        Raises:
            UpiValidationError: If UPI ID is invalid
            UpiNotFoundError: If registration not found
        """
        try:
            # Validate UPI ID
            validate_upi_id(upi_id)
            
            # Get registration from repository
            registration = upi_repository.get_registration(upi_id)
            
            logger.info(f"Retrieved registration for UPI ID: {upi_id}")
            return registration
            
        except UpiValidationError:
            # Re-raise validation errors
            logger.warning(f"Invalid UPI ID: {upi_id}")
            raise
            
        except UpiNotFoundError:
            # Re-raise not found error
            logger.warning(f"Registration not found for UPI ID: {upi_id}")
            raise
            
        except Exception as e:
            # Wrap unknown exceptions
            logger.error(f"Unexpected error retrieving registration: {str(e)}")
            raise UpiBaseException(f"Failed to retrieve UPI registration: {str(e)}")
    
    def initiate_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate a UPI transaction.
        
        Args:
            transaction_data: Transaction data
            
        Returns:
            Dict: Transaction result
            
        Raises:
            UpiValidationError: If transaction data is invalid
            UpiInvalidAccountError: If account is invalid or inactive
            UpiAmountExceedsLimitError: If amount exceeds limit
        """
        try:
            # Validate transaction data
            validated_data = validate_transaction_data(transaction_data, self.max_transaction_limit)
            
            # Check if payer UPI ID is registered
            try:
                payer_reg = upi_repository.get_registration(validated_data['payer_upi_id'])
                if payer_reg.get('status') != 'active':
                    raise UpiInvalidAccountError(validated_data['payer_upi_id'])
            except UpiNotFoundError:
                raise UpiInvalidAccountError(validated_data['payer_upi_id'])
            
            # Check if payee UPI ID is registered
            try:
                payee_reg = upi_repository.get_registration(validated_data['payee_upi_id'])
                if payee_reg.get('status') != 'active':
                    raise UpiInvalidAccountError(validated_data['payee_upi_id'])
            except UpiNotFoundError:
                # For mock mode, we allow payments to unregistered UPI IDs for testing
                if self.validation_strict:
                    raise UpiInvalidAccountError(validated_data['payee_upi_id'])
            
            # Create transaction object
            transaction = UpiTransaction(
                payer_upi_id=validated_data['payer_upi_id'],
                payee_upi_id=validated_data['payee_upi_id'],
                amount=validated_data['amount'],
                note=validated_data.get('note'),
                transaction_type=TransactionType.PAY
            )
            
            # Save initial transaction
            saved_transaction = upi_repository.save_transaction(transaction)
            
            # Process transaction
            if self.is_mock_mode:
                logger.info(f"Processing mock transaction: {transaction.transaction_id}")
                # Simulate processing delay
                time.sleep(1)
                
                # Mock processing result (success or failure)
                success = True  # In mock mode, most transactions succeed
                if validated_data['amount'] > self.max_transaction_limit * 0.9:
                    # Simulate failure for large amounts
                    success = False
                
                # Update transaction status
                if success:
                    status = TransactionStatus.SUCCESS
                    gateway_response = {
                        "status": "SUCCESS",
                        "npci_ref": f"NPCI{int(time.time())}",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                else:
                    status = TransactionStatus.FAILED
                    gateway_response = {
                        "status": "FAILED",
                        "error_code": "INSUFFICIENT_FUNDS",
                        "error_message": "Insufficient funds in payer account",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                
                # Update transaction with result
                updated_transaction = upi_repository.update_transaction_status(
                    transaction.transaction_id, status, gateway_response
                )
                
                # Send notification if enabled
                if self.notification_enabled:
                    self._send_transaction_notification(updated_transaction)
                
                return updated_transaction
                
            else:
                # Real transaction processing would happen here
                # Connect to NPCI/UPI gateway and process payment
                # This is a placeholder for actual implementation
                logger.info(f"Processing real transaction: {transaction.transaction_id}")
                raise NotImplementedError("Real transaction processing not implemented yet")
            
        except (UpiValidationError, UpiInvalidAccountError, UpiAmountExceedsLimitError) as e:
            # Re-raise known exceptions
            logger.warning(f"Transaction initiation failed: {str(e)}")
            raise
            
        except Exception as e:
            # Wrap unknown exceptions
            logger.error(f"Unexpected error during transaction: {str(e)}")
            raise UpiTransactionError(f"Failed to process UPI transaction: {str(e)}")
    
    def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get transaction by ID.
        
        Args:
            transaction_id: Transaction ID to retrieve
            
        Returns:
            Dict: Transaction data
            
        Raises:
            UpiNotFoundError: If transaction not found
        """
        try:
            # Get transaction from repository
            transaction = upi_repository.get_transaction(transaction_id)
            
            logger.info(f"Retrieved transaction with ID: {transaction_id}")
            return transaction
            
        except UpiNotFoundError:
            # Re-raise not found error
            logger.warning(f"Transaction not found with ID: {transaction_id}")
            raise
            
        except Exception as e:
            # Wrap unknown exceptions
            logger.error(f"Unexpected error retrieving transaction: {str(e)}")
            raise UpiBaseException(f"Failed to retrieve UPI transaction: {str(e)}")
    
    def get_user_transactions(self, upi_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get transactions by UPI ID.
        
        Args:
            upi_id: UPI ID to search for
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List: List of transaction data dictionaries
            
        Raises:
            UpiValidationError: If UPI ID is invalid
        """
        try:
            # Validate UPI ID
            validate_upi_id(upi_id)
            
            # Get transactions from repository
            transactions = upi_repository.get_transactions_by_upi_id(upi_id, limit, offset)
            
            logger.info(f"Retrieved {len(transactions)} transactions for UPI ID: {upi_id}")
            return transactions
            
        except UpiValidationError:
            # Re-raise validation errors
            logger.warning(f"Invalid UPI ID: {upi_id}")
            raise
            
        except Exception as e:
            # Wrap unknown exceptions
            logger.error(f"Unexpected error retrieving transactions: {str(e)}")
            raise UpiBaseException(f"Failed to retrieve UPI transactions: {str(e)}")
    
    def generate_qr_code(self, upi_id: str, merchant_name: str, amount: Optional[float] = None,
                       transaction_note: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate UPI QR code.
        
        Args:
            upi_id: UPI ID for payment
            merchant_name: Merchant name
            amount: Optional fixed amount
            transaction_note: Optional transaction note
            
        Returns:
            Dict: QR code data including base64 encoded image
            
        Raises:
            UpiValidationError: If UPI ID is invalid
        """
        try:
            # Validate UPI ID
            validate_upi_id(upi_id)
            
            # Validate amount if provided
            if amount is not None:
                amount = validate_amount(amount, self.max_transaction_limit)
            
            # Create QR code object
            qr_code = QRCode(
                upi_id=upi_id,
                merchant_name=merchant_name,
                amount=amount,
                transaction_note=transaction_note,
                transaction_ref=f"QR{int(time.time())}"
            )
            
            # Generate UPI QR code data
            qr_data = qr_code.generate_upi_qr_data()
            
            # Generate QR code image
            if self.qr_module_available:
                import qrcode
                import io
                
                # Create QR code
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                # Create image
                img = qr.make_image(fill_color="black", back_color="white")
                
                # Convert to base64
                buffer = io.BytesIO()
                img.save(buffer, format="PNG")
                qr_image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                qr_code.qr_image_base64 = qr_image_base64
                
            else:
                # Mock QR code generation
                logger.warning("QR code module not available. Using mock QR code.")
                qr_code.qr_image_base64 = "MOCK_QR_CODE_BASE64_DATA"
            
            logger.info(f"Generated QR code for UPI ID: {upi_id}")
            
            # Return QR code data
            return {
                "upi_id": qr_code.upi_id,
                "merchant_name": qr_code.merchant_name,
                "amount": qr_code.amount,
                "transaction_note": qr_code.transaction_note,
                "transaction_ref": qr_code.transaction_ref,
                "qr_data": qr_code.qr_data,
                "qr_image_base64": qr_code.qr_image_base64
            }
            
        except UpiValidationError:
            # Re-raise validation errors
            logger.warning(f"Invalid UPI ID or amount for QR code generation")
            raise
            
        except Exception as e:
            # Wrap unknown exceptions
            logger.error(f"Unexpected error generating QR code: {str(e)}")
            raise UpiBaseException(f"Failed to generate UPI QR code: {str(e)}")
    
    def _send_transaction_notification(self, transaction: Dict[str, Any]) -> None:
        """
        Send transaction notification.
        
        Args:
            transaction: Transaction data
        """
        try:
            # This is a placeholder for actual notification logic
            logger.info(f"Sending notification for transaction: {transaction['transaction_id']}")
            
            # In a real implementation, this would send SMS/email/push notifications
            
            # For now, just log the notification
            status = transaction.get('status', 'UNKNOWN')
            amount = transaction.get('amount', 0)
            payer_id = transaction.get('payer_upi_id', '')
            payee_id = transaction.get('payee_upi_id', '')
            
            logger.info(f"Transaction notification: {status} - {amount} from {payer_id} to {payee_id}")
            
        except Exception as e:
            # Log error but don't raise - notifications shouldn't break core flow
            logger.error(f"Error sending transaction notification: {str(e)}")


# Create singleton instance
upi_service = UpiService()
