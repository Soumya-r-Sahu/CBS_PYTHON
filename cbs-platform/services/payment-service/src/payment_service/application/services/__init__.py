"""
Payment Service Application Services
High-level application services that orchestrate use cases
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


class PaymentApplicationService:
    """
    Payment application service
    Orchestrates payment operations and coordinates between use cases
    """
    
    def __init__(
        self,
        payment_repository: PaymentRepository,
        fraud_detection_service: FraudDetectionService,
        payment_gateway_service: PaymentGatewayService,
        account_service: AccountService,
        notification_service: NotificationService
    ):
        self.payment_repository = payment_repository
        self.fraud_detection_service = fraud_detection_service
        self.payment_gateway_service = payment_gateway_service
        self.account_service = account_service
        self.notification_service = notification_service
        
        # Initialize use cases
        self.create_payment_use_case = CreatePaymentUseCase(
            payment_repository, account_service, fraud_detection_service
        )
        self.process_payment_use_case = ProcessPaymentUseCase(
            payment_repository, payment_gateway_service, account_service, notification_service
        )
        self.cancel_payment_use_case = CancelPaymentUseCase(
            payment_repository, notification_service
        )
        self.refund_payment_use_case = RefundPaymentUseCase(
            payment_repository, account_service, notification_service
        )
        self.get_payment_use_case = GetPaymentUseCase(payment_repository)
        self.list_payments_use_case = ListPaymentsUseCase(payment_repository)
        self.get_payment_stats_use_case = GetPaymentStatsUseCase(payment_repository)
        self.validate_payment_use_case = ValidatePaymentUseCase(
            account_service, payment_repository
        )
        self.check_payment_limits_use_case = CheckPaymentLimitsUseCase(payment_repository)
    
    async def create_payment(self, request: CreatePaymentRequest) -> PaymentResponse:
        """
        Create a new payment
        
        Args:
            request: Payment creation request
            
        Returns:
            PaymentResponse: Created payment details
            
        Raises:
            ValueError: If validation fails
        """
        # Validate payment first
        validation_result = await self.validate_payment_use_case.execute(request)
        if not validation_result.is_valid:
            error_messages = [error.message for error in validation_result.errors]
            raise ValueError(f"Payment validation failed: {', '.join(error_messages)}")
        
        # Check payment limits
        limit_check_request = PaymentLimitCheckRequest(
            account_number=request.sender.account_number,
            payment_type=request.payment_type,
            amount=request.amount
        )
        limit_check = await self.check_payment_limits_use_case.execute(limit_check_request)
        if not limit_check.is_within_limits:
            raise ValueError(f"Payment limits exceeded: {', '.join(limit_check.violations)}")
        
        # Create payment
        return await self.create_payment_use_case.execute(request)
    
    async def process_payment(self, request: ProcessPaymentRequest) -> PaymentResponse:
        """
        Process a payment
        
        Args:
            request: Payment processing request
            
        Returns:
            PaymentResponse: Updated payment details
            
        Raises:
            ValueError: If payment cannot be processed
        """
        return await self.process_payment_use_case.execute(request)
    
    async def cancel_payment(self, request: CancelPaymentRequest) -> PaymentResponse:
        """
        Cancel a payment
        
        Args:
            request: Payment cancellation request
            
        Returns:
            PaymentResponse: Updated payment details
            
        Raises:
            ValueError: If payment cannot be cancelled
        """
        return await self.cancel_payment_use_case.execute(request)
    
    async def refund_payment(self, request: RefundPaymentRequest) -> PaymentResponse:
        """
        Refund a payment
        
        Args:
            request: Payment refund request
            
        Returns:
            PaymentResponse: Refund payment details
            
        Raises:
            ValueError: If payment cannot be refunded
        """
        return await self.refund_payment_use_case.execute(request)
    
    async def get_payment(self, payment_id: str) -> Optional[PaymentResponse]:
        """
        Get payment by ID
        
        Args:
            payment_id: Payment identifier
            
        Returns:
            PaymentResponse: Payment details if found, None otherwise
        """
        return await self.get_payment_use_case.execute(payment_id)
    
    async def get_payment_by_reference(self, reference_number: str) -> Optional[PaymentResponse]:
        """
        Get payment by reference number
        
        Args:
            reference_number: Payment reference number
            
        Returns:
            PaymentResponse: Payment details if found, None otherwise
        """
        payment = await self.payment_repository.find_by_reference(reference_number)
        if payment:
            from ..dto import payment_to_response
            return payment_to_response(payment)
        return None
    
    async def list_payments(self, request: PaymentListRequest) -> PaymentListResponse:
        """
        List payments with filters
        
        Args:
            request: Payment list request with filters
            
        Returns:
            PaymentListResponse: Paginated payment list
        """
        return await self.list_payments_use_case.execute(request)
    
    async def get_payment_stats(self, request: PaymentStatsRequest) -> PaymentStatsResponse:
        """
        Get payment statistics
        
        Args:
            request: Payment statistics request
            
        Returns:
            PaymentStatsResponse: Payment statistics
        """
        return await self.get_payment_stats_use_case.execute(request)
    
    async def validate_payment(self, request: CreatePaymentRequest) -> PaymentValidationResult:
        """
        Validate payment request
        
        Args:
            request: Payment creation request
            
        Returns:
            PaymentValidationResult: Validation result
        """
        return await self.validate_payment_use_case.execute(request)
    
    async def check_payment_limits(self, request: PaymentLimitCheckRequest) -> PaymentLimitCheckResponse:
        """
        Check payment limits
        
        Args:
            request: Payment limit check request
            
        Returns:
            PaymentLimitCheckResponse: Limit check result
        """
        return await self.check_payment_limits_use_case.execute(request)
    
    async def initiate_and_process_payment(
        self, 
        create_request: CreatePaymentRequest,
        process_request: ProcessPaymentRequest
    ) -> PaymentResponse:
        """
        Convenience method to create and immediately process a payment
        
        Args:
            create_request: Payment creation request
            process_request: Payment processing request
            
        Returns:
            PaymentResponse: Processed payment details
            
        Raises:
            ValueError: If creation or processing fails
        """
        # Create payment
        payment_response = await self.create_payment(create_request)
        
        # Update process request with created payment ID
        process_request.payment_id = payment_response.payment_id
        
        # Process payment
        return await self.process_payment(process_request)
    
    async def get_account_payment_summary(
        self, 
        account_number: str,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> dict:
        """
        Get payment summary for an account
        
        Args:
            account_number: Account number
            from_date: Start date for summary
            to_date: End date for summary
            
        Returns:
            dict: Payment summary with totals and counts
        """
        # Set default date range if not provided
        if not to_date:
            to_date = datetime.utcnow()
        if not from_date:
            from_date = datetime(to_date.year, to_date.month, 1)  # Start of current month
        
        # Get sent payments
        sent_request = PaymentListRequest(
            account_number=account_number,
            from_date=from_date,
            to_date=to_date,
            size=1000  # Get all for summary
        )
        sent_payments = await self.list_payments(sent_request)
        
        # Calculate summary
        total_sent = sum(p.amount.amount for p in sent_payments.payments 
                        if p.sender.account_number == account_number)
        total_received = sum(p.amount.amount for p in sent_payments.payments 
                           if p.receiver.account_number == account_number)
        
        successful_sent = sum(p.amount.amount for p in sent_payments.payments 
                            if p.sender.account_number == account_number and p.status == "completed")
        successful_received = sum(p.amount.amount for p in sent_payments.payments 
                                if p.receiver.account_number == account_number and p.status == "completed")
        
        return {
            "account_number": account_number,
            "period": {
                "from_date": from_date.isoformat(),
                "to_date": to_date.isoformat()
            },
            "sent": {
                "total_amount": float(total_sent),
                "successful_amount": float(successful_sent),
                "count": len([p for p in sent_payments.payments 
                             if p.sender.account_number == account_number])
            },
            "received": {
                "total_amount": float(total_received),
                "successful_amount": float(successful_received),
                "count": len([p for p in sent_payments.payments 
                             if p.receiver.account_number == account_number])
            },
            "net_amount": float(successful_received - successful_sent)
        }


class PaymentBatchService:
    """
    Service for handling batch payment operations
    """
    
    def __init__(self, payment_service: PaymentApplicationService):
        self.payment_service = payment_service
    
    async def process_batch_payments(
        self, 
        payment_requests: List[CreatePaymentRequest],
        process_immediately: bool = False
    ) -> List[PaymentResponse]:
        """
        Process a batch of payments
        
        Args:
            payment_requests: List of payment creation requests
            process_immediately: Whether to process payments immediately after creation
            
        Returns:
            List[PaymentResponse]: List of processed payments
        """
        results = []
        
        for request in payment_requests:
            try:
                if process_immediately:
                    process_request = ProcessPaymentRequest(
                        payment_id="",  # Will be set in initiate_and_process_payment
                        processed_by=request.initiated_by or "batch_processor"
                    )
                    payment = await self.payment_service.initiate_and_process_payment(
                        request, process_request
                    )
                else:
                    payment = await self.payment_service.create_payment(request)
                
                results.append(payment)
                
            except Exception as e:
                # Create error response for failed payments
                error_payment = PaymentResponse(
                    payment_id="",
                    payment_type=request.payment_type,
                    amount=request.amount,
                    sender=request.sender,
                    receiver=request.receiver,
                    status="failed",
                    channel=request.channel,
                    reference_number="",
                    description=request.description,
                    initiated_at=datetime.utcnow(),
                    failure_reason=str(e),
                    metadata={"batch_error": True}
                )
                results.append(error_payment)
        
        return results
    
    async def retry_failed_payments(
        self, 
        payment_ids: List[str],
        retry_by: str
    ) -> List[PaymentResponse]:
        """
        Retry failed payments
        
        Args:
            payment_ids: List of payment IDs to retry
            retry_by: User who initiated the retry
            
        Returns:
            List[PaymentResponse]: List of retry results
        """
        results = []
        
        for payment_id in payment_ids:
            try:
                payment = await self.payment_service.get_payment(payment_id)
                if not payment:
                    continue
                
                if payment.status == "failed":
                    process_request = ProcessPaymentRequest(
                        payment_id=payment_id,
                        processed_by=retry_by
                    )
                    updated_payment = await self.payment_service.process_payment(process_request)
                    results.append(updated_payment)
                else:
                    results.append(payment)
                    
            except Exception as e:
                # Get original payment for error response
                payment = await self.payment_service.get_payment(payment_id)
                if payment:
                    payment.failure_reason = f"Retry failed: {str(e)}"
                    results.append(payment)
        
        return results
