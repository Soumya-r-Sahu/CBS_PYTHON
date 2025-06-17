"""
Payment Service Application Services
Production-ready application services for payment processing
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal
import logging
import asyncio
from dataclasses import dataclass

from ...domain.entities import (
    Payment, PaymentAmount, PaymentParty, PaymentType, 
    PaymentStatus, FraudCheck, FraudRiskLevel
)


logger = logging.getLogger(__name__)


# Application Service Interfaces
class PaymentServiceInterface(ABC):
    """Payment service interface"""
    
    @abstractmethod
    async def create_payment(self, payment: Payment) -> Payment:
        """Create a new payment"""
        pass
    
    @abstractmethod
    async def process_payment(self, payment_id: str) -> Optional[Payment]:
        """Process a payment"""
        pass
    
    @abstractmethod
    async def cancel_payment(self, payment_id: str, reason: str) -> Optional[Payment]:
        """Cancel a payment"""
        pass
    
    @abstractmethod
    async def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Get payment by ID"""
        pass


class FraudDetectionServiceInterface(ABC):
    """Fraud detection service interface"""
    
    @abstractmethod
    async def analyze_payment(self, payment: Payment) -> FraudCheck:
        """Analyze payment for fraud risk"""
        pass


class PaymentGatewayServiceInterface(ABC):
    """Payment gateway service interface"""
    
    @abstractmethod
    async def submit_payment(self, payment: Payment) -> Dict[str, Any]:
        """Submit payment to gateway"""
        pass


class NotificationServiceInterface(ABC):
    """Notification service interface"""
    
    @abstractmethod
    async def send_payment_notification(self, payment: Payment, event: str) -> bool:
        """Send payment notification"""
        pass


# Use Cases
@dataclass
class CreatePaymentCommand:
    """Command to create a payment"""
    payment_type: PaymentType
    amount: PaymentAmount
    sender: PaymentParty
    receiver: PaymentParty
    channel: str
    description: str = ""
    upi_details: Optional[Dict[str, Any]] = None
    bill_details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    initiated_by: Optional[str] = None


@dataclass
class ProcessPaymentCommand:
    """Command to process a payment"""
    payment_id: str
    processed_by: Optional[str] = None
    force_process: bool = False


class CreatePaymentUseCase:
    """Use case for creating payments"""
    
    def __init__(
        self,
        payment_repository,
        fraud_service: FraudDetectionServiceInterface,
        notification_service: NotificationServiceInterface
    ):
        self.payment_repository = payment_repository
        self.fraud_service = fraud_service
        self.notification_service = notification_service
    
    async def execute(self, command: CreatePaymentCommand) -> Payment:
        """Execute create payment use case"""
        try:
            logger.info(f"Creating payment: {command.payment_type} for {command.amount.amount}")
            
            # Create payment entity
            payment = Payment(
                payment_type=command.payment_type,
                amount=command.amount,
                sender=command.sender,
                receiver=command.receiver,
                channel=command.channel,
                description=command.description,
                initiated_by=command.initiated_by,
                metadata=command.metadata or {}
            )
            
            # Add type-specific details
            if command.upi_details and command.payment_type == PaymentType.UPI:
                from ...domain.entities import UPIDetails
                payment.upi_details = UPIDetails(
                    vpa=command.upi_details['vpa'],
                    merchant_id=command.upi_details.get('merchant_id'),
                    qr_code=command.upi_details.get('qr_code'),
                    purpose=command.upi_details.get('purpose', 'PAYMENT')
                )
            
            if command.bill_details and command.payment_type == PaymentType.BILL_PAYMENT:
                from ...domain.entities import BillPaymentDetails
                bill_amount = None
                if command.bill_details.get('bill_amount'):
                    bill_amount = PaymentAmount(
                        amount=command.bill_details['bill_amount']['amount'],
                        currency=command.bill_details['bill_amount'].get('currency', 'USD')
                    )
                
                payment.bill_details = BillPaymentDetails(
                    biller_id=command.bill_details['biller_id'],
                    biller_name=command.bill_details['biller_name'],
                    bill_number=command.bill_details['bill_number'],
                    due_date=command.bill_details.get('due_date'),
                    bill_amount=bill_amount
                )
            
            # Run fraud detection
            fraud_check = await self.fraud_service.analyze_payment(payment)
            payment.set_fraud_check(fraud_check)
            
            # Save payment
            saved_payment = self.payment_repository.save(payment)
            
            # Send notification
            await self.notification_service.send_payment_notification(
                saved_payment, "payment_created"
            )
            
            logger.info(f"Payment created successfully: {saved_payment.payment_id}")
            return saved_payment
            
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            raise


class ProcessPaymentUseCase:
    """Use case for processing payments"""
    
    def __init__(
        self,
        payment_repository,
        payment_gateway: PaymentGatewayServiceInterface,
        notification_service: NotificationServiceInterface
    ):
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway
        self.notification_service = notification_service
    
    async def execute(self, command: ProcessPaymentCommand) -> Optional[Payment]:
        """Execute process payment use case"""
        try:
            logger.info(f"Processing payment: {command.payment_id}")
            
            # Get payment
            payment = self.payment_repository.find_by_id(command.payment_id)
            if not payment:
                logger.warning(f"Payment not found: {command.payment_id}")
                return None
            
            # Check if payment can be processed
            if not payment.can_process() and not command.force_process:
                logger.warning(f"Payment cannot be processed: {payment.payment_id}, status: {payment.status}")
                return payment
            
            # Mark as pending
            payment.mark_pending(command.processed_by or "system")
            self.payment_repository.save(payment)
            
            # Submit to payment gateway
            try:
                payment.mark_processing()
                self.payment_repository.save(payment)
                
                gateway_response = await self.payment_gateway.submit_payment(payment)
                
                if gateway_response.get('success'):
                    payment.mark_completed(gateway_response.get('transaction_id'))
                    await self.notification_service.send_payment_notification(
                        payment, "payment_completed"
                    )
                else:
                    payment.mark_failed(gateway_response.get('error', 'Gateway processing failed'))
                    await self.notification_service.send_payment_notification(
                        payment, "payment_failed"
                    )
                
            except Exception as gateway_error:
                logger.error(f"Gateway error processing payment {payment.payment_id}: {str(gateway_error)}")
                payment.mark_failed(f"Gateway error: {str(gateway_error)}")
                await self.notification_service.send_payment_notification(
                    payment, "payment_failed"
                )
            
            # Save final state
            saved_payment = self.payment_repository.save(payment)
            
            logger.info(f"Payment processing completed: {payment.payment_id}, status: {payment.status}")
            return saved_payment
            
        except Exception as e:
            logger.error(f"Error processing payment {command.payment_id}: {str(e)}")
            raise


class CancelPaymentUseCase:
    """Use case for cancelling payments"""
    
    def __init__(
        self,
        payment_repository,
        notification_service: NotificationServiceInterface
    ):
        self.payment_repository = payment_repository
        self.notification_service = notification_service
    
    async def execute(self, payment_id: str, reason: str, cancelled_by: str = "") -> Optional[Payment]:
        """Execute cancel payment use case"""
        try:
            logger.info(f"Cancelling payment: {payment_id}")
            
            # Get payment
            payment = self.payment_repository.find_by_id(payment_id)
            if not payment:
                logger.warning(f"Payment not found: {payment_id}")
                return None
            
            # Cancel payment
            payment.cancel(reason, cancelled_by)
            
            # Save payment
            saved_payment = self.payment_repository.save(payment)
            
            # Send notification
            await self.notification_service.send_payment_notification(
                saved_payment, "payment_cancelled"
            )
            
            logger.info(f"Payment cancelled successfully: {payment_id}")
            return saved_payment
            
        except Exception as e:
            logger.error(f"Error cancelling payment {payment_id}: {str(e)}")
            raise


# Main Application Service
class PaymentService(PaymentServiceInterface):
    """Main payment application service"""
    
    def __init__(
        self,
        payment_repository,
        fraud_service: FraudDetectionServiceInterface,
        payment_gateway: PaymentGatewayServiceInterface,
        notification_service: NotificationServiceInterface
    ):
        self.payment_repository = payment_repository
        self.fraud_service = fraud_service
        self.payment_gateway = payment_gateway
        self.notification_service = notification_service
        
        # Initialize use cases
        self.create_payment_use_case = CreatePaymentUseCase(
            payment_repository, fraud_service, notification_service
        )
        self.process_payment_use_case = ProcessPaymentUseCase(
            payment_repository, payment_gateway, notification_service
        )
        self.cancel_payment_use_case = CancelPaymentUseCase(
            payment_repository, notification_service
        )
    
    async def create_payment(self, payment: Payment) -> Payment:
        """Create a new payment"""
        command = CreatePaymentCommand(
            payment_type=payment.payment_type,
            amount=payment.amount,
            sender=payment.sender,
            receiver=payment.receiver,
            channel=payment.channel,
            description=payment.description,
            initiated_by=payment.initiated_by,
            metadata=payment.metadata
        )
        
        # Add UPI details if present
        if payment.upi_details:
            command.upi_details = {
                'vpa': payment.upi_details.vpa,
                'merchant_id': payment.upi_details.merchant_id,
                'qr_code': payment.upi_details.qr_code,
                'purpose': payment.upi_details.purpose
            }
        
        # Add bill details if present
        if payment.bill_details:
            command.bill_details = {
                'biller_id': payment.bill_details.biller_id,
                'biller_name': payment.bill_details.biller_name,
                'bill_number': payment.bill_details.bill_number,
                'due_date': payment.bill_details.due_date,
                'bill_amount': {
                    'amount': payment.bill_details.bill_amount.amount,
                    'currency': payment.bill_details.bill_amount.currency
                } if payment.bill_details.bill_amount else None
            }
        
        return await self.create_payment_use_case.execute(command)
    
    async def process_payment(self, payment_id: str) -> Optional[Payment]:
        """Process a payment"""
        command = ProcessPaymentCommand(payment_id=payment_id)
        return await self.process_payment_use_case.execute(command)
    
    async def cancel_payment(self, payment_id: str, reason: str) -> Optional[Payment]:
        """Cancel a payment"""
        return await self.cancel_payment_use_case.execute(payment_id, reason)
    
    async def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Get payment by ID"""
        return self.payment_repository.find_by_id(payment_id)
    
    async def get_payment_by_reference(self, reference_number: str) -> Optional[Payment]:
        """Get payment by reference number"""
        return self.payment_repository.find_by_reference(reference_number)
    
    async def list_payments(
        self, 
        filters: Dict[str, Any] = None, 
        page: int = 1, 
        page_size: int = 20
    ) -> Tuple[List[Payment], int]:
        """List payments with filters and pagination"""
        filters = filters or {}
        
        if 'account_number' in filters:
            payments = self.payment_repository.find_by_account(
                filters['account_number'], limit=page_size
            )
        elif 'status' in filters:
            payments = self.payment_repository.find_by_status(
                filters['status'], limit=page_size
            )
        else:
            # Default to recent payments
            payments = self.payment_repository.find_by_status(
                PaymentStatus.INITIATED, limit=page_size
            )
        
        return payments, len(payments)
    
    async def get_payment_summary(
        self, 
        account_number: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Get payment summary for account"""
        return self.payment_repository.get_payment_summary(
            account_number, start_date, end_date
        )
    
    async def get_high_value_payments(
        self, 
        amount_threshold: Decimal, 
        page: int = 1, 
        page_size: int = 20
    ) -> List[Payment]:
        """Get high value payments requiring approval"""
        return self.payment_repository.find_high_value_payments(
            amount_threshold, limit=page_size
        )
    
    async def get_suspicious_payments(self, risk_threshold: int = 70) -> List[Payment]:
        """Get payments flagged as suspicious"""
        return self.payment_repository.find_suspicious_payments(risk_threshold)
    
    async def process_bulk_payments(self, payment_ids: List[str]) -> Dict[str, Any]:
        """Process multiple payments in bulk"""
        results = {
            'successful': [],
            'failed': [],
            'total_processed': 0
        }
        
        tasks = []
        for payment_id in payment_ids:
            task = self.process_payment(payment_id)
            tasks.append(task)
        
        # Process payments concurrently
        processed_payments = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(processed_payments):
            payment_id = payment_ids[i]
            if isinstance(result, Exception):
                results['failed'].append({
                    'payment_id': payment_id,
                    'error': str(result)
                })
            else:
                results['successful'].append({
                    'payment_id': payment_id,
                    'status': result.status.value if result else 'not_found'
                })
            results['total_processed'] += 1
        
        return results


# Mock Services for Development
class MockFraudDetectionService(FraudDetectionServiceInterface):
    """Mock fraud detection service for development"""
    
    async def analyze_payment(self, payment: Payment) -> FraudCheck:
        """Mock fraud analysis"""
        # Simple rule-based mock detection
        risk_score = 10
        risk_level = FraudRiskLevel.LOW
        flags = []
        
        # High amount check
        if payment.amount.amount > Decimal('50000'):
            risk_score += 30
            flags.append('high_amount')
        
        # Same account check
        if payment.sender.account_number == payment.receiver.account_number:
            risk_score += 50
            flags.append('same_account_transfer')
        
        # Determine risk level
        if risk_score >= 80:
            risk_level = FraudRiskLevel.CRITICAL
        elif risk_score >= 60:
            risk_level = FraudRiskLevel.HIGH
        elif risk_score >= 30:
            risk_level = FraudRiskLevel.MEDIUM
        
        return FraudCheck(
            risk_level=risk_level,
            risk_score=min(risk_score, 100),
            flags=flags
        )


class MockPaymentGatewayService(PaymentGatewayServiceInterface):
    """Mock payment gateway service for development"""
    
    async def submit_payment(self, payment: Payment) -> Dict[str, Any]:
        """Mock payment submission"""
        # Simulate network delay
        await asyncio.sleep(0.1)
        
        # Mock success/failure based on amount
        if payment.amount.amount > Decimal('999999'):
            return {
                'success': False,
                'error': 'Amount exceeds gateway limit'
            }
        
        # Mock random failures for testing
        import random
        if random.random() < 0.05:  # 5% failure rate
            return {
                'success': False,
                'error': 'Gateway timeout'
            }
        
        return {
            'success': True,
            'transaction_id': f"GW{payment.payment_id[:8].upper()}",
            'gateway_reference': f"REF{payment.reference_number}",
            'processing_time': 120
        }


class MockNotificationService(NotificationServiceInterface):
    """Mock notification service for development"""
    
    async def send_payment_notification(self, payment: Payment, event: str) -> bool:
        """Mock notification sending"""
        logger.info(f"Notification: {event} for payment {payment.payment_id}")
        return True


# Export all services
__all__ = [
    'PaymentServiceInterface',
    'FraudDetectionServiceInterface', 
    'PaymentGatewayServiceInterface',
    'NotificationServiceInterface',
    'CreatePaymentCommand',
    'ProcessPaymentCommand',
    'CreatePaymentUseCase',
    'ProcessPaymentUseCase',
    'CancelPaymentUseCase',
    'PaymentService',
    'MockFraudDetectionService',
    'MockPaymentGatewayService',
    'MockNotificationService'
]
