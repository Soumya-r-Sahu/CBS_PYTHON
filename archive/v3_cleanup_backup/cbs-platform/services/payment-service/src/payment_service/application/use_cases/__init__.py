"""
Payment Service Use Cases
Business logic for payment operations following Clean Architecture
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from ...domain.entities import (
    Payment, PaymentAmount, PaymentParty, UPIDetails, BillPaymentDetails, 
    FraudCheck, PaymentStatus, PaymentType, FraudRiskLevel
)
from ..dto import (
    CreatePaymentRequest, PaymentResponse, ProcessPaymentRequest,
    CancelPaymentRequest, RefundPaymentRequest, PaymentListRequest,
    PaymentListResponse, PaymentStatsRequest, PaymentStatsResponse,
    PaymentValidationResult, PaymentLimitCheckRequest, PaymentLimitCheckResponse,
    payment_to_response, payment_amount_to_dto
)


# Repository interfaces (to be implemented in infrastructure layer)

class PaymentRepository(ABC):
    """Payment repository interface"""
    
    @abstractmethod
    async def save(self, payment: Payment) -> Payment:
        """Save payment"""
        pass
    
    @abstractmethod
    async def find_by_id(self, payment_id: str) -> Optional[Payment]:
        """Find payment by ID"""
        pass
    
    @abstractmethod
    async def find_by_reference(self, reference_number: str) -> Optional[Payment]:
        """Find payment by reference number"""
        pass
    
    @abstractmethod
    async def find_by_criteria(self, request: PaymentListRequest) -> PaymentListResponse:
        """Find payments by criteria"""
        pass
    
    @abstractmethod
    async def get_payment_stats(self, request: PaymentStatsRequest) -> PaymentStatsResponse:
        """Get payment statistics"""
        pass
    
    @abstractmethod
    async def get_daily_amount(self, account_number: str, date: datetime) -> Decimal:
        """Get total amount paid today from account"""
        pass
    
    @abstractmethod
    async def get_monthly_amount(self, account_number: str, year: int, month: int) -> Decimal:
        """Get total amount paid this month from account"""
        pass


class FraudDetectionService(ABC):
    """Fraud detection service interface"""
    
    @abstractmethod
    async def check_payment(self, payment: Payment) -> FraudCheck:
        """Perform fraud check on payment"""
        pass


class PaymentGatewayService(ABC):
    """Payment gateway service interface"""
    
    @abstractmethod
    async def process_payment(self, payment: Payment) -> bool:
        """Process payment through gateway"""
        pass


class AccountService(ABC):
    """Account service interface"""
    
    @abstractmethod
    async def validate_account(self, account_number: str) -> bool:
        """Validate account exists and is active"""
        pass
    
    @abstractmethod
    async def check_balance(self, account_number: str, amount: Decimal) -> bool:
        """Check if account has sufficient balance"""
        pass
    
    @abstractmethod
    async def debit_account(self, account_number: str, amount: Decimal, reference: str) -> bool:
        """Debit amount from account"""
        pass
    
    @abstractmethod
    async def credit_account(self, account_number: str, amount: Decimal, reference: str) -> bool:
        """Credit amount to account"""
        pass


class NotificationService(ABC):
    """Notification service interface"""
    
    @abstractmethod
    async def send_payment_notification(self, payment: Payment, recipient: str) -> None:
        """Send payment notification"""
        pass


# Use Cases

class CreatePaymentUseCase:
    """Use case for creating a new payment"""
    
    def __init__(
        self,
        payment_repository: PaymentRepository,
        account_service: AccountService,
        fraud_detection_service: FraudDetectionService
    ):
        self.payment_repository = payment_repository
        self.account_service = account_service
        self.fraud_detection_service = fraud_detection_service
    
    async def execute(self, request: CreatePaymentRequest) -> PaymentResponse:
        """Create a new payment"""
        
        # Convert DTOs to domain entities
        amount = PaymentAmount(
            amount=request.amount.amount,
            currency=request.amount.currency
        )
        
        sender = PaymentParty(
            account_number=request.sender.account_number,
            account_name=request.sender.account_name,
            bank_code=request.sender.bank_code,
            bank_name=request.sender.bank_name,
            branch_code=request.sender.branch_code,
            ifsc_code=request.sender.ifsc_code
        )
        
        receiver = PaymentParty(
            account_number=request.receiver.account_number,
            account_name=request.receiver.account_name,
            bank_code=request.receiver.bank_code,
            bank_name=request.receiver.bank_name,
            branch_code=request.receiver.branch_code,
            ifsc_code=request.receiver.ifsc_code
        )
        
        # Create UPI details if provided
        upi_details = None
        if request.upi_details:
            upi_details = UPIDetails(
                vpa=request.upi_details.vpa,
                merchant_id=request.upi_details.merchant_id,
                qr_code=request.upi_details.qr_code,
                purpose=request.upi_details.purpose
            )
        
        # Create bill details if provided
        bill_details = None
        if request.bill_details:
            bill_amount = None
            if request.bill_details.bill_amount:
                bill_amount = PaymentAmount(
                    amount=request.bill_details.bill_amount.amount,
                    currency=request.bill_details.bill_amount.currency
                )
            
            bill_details = BillPaymentDetails(
                biller_id=request.bill_details.biller_id,
                biller_name=request.bill_details.biller_name,
                bill_number=request.bill_details.bill_number,
                due_date=request.bill_details.due_date,
                bill_amount=bill_amount
            )
        
        # Validate sender account
        if not await self.account_service.validate_account(sender.account_number):
            raise ValueError(f"Invalid sender account: {sender.account_number}")
        
        # Check sufficient balance for non-credit transactions
        if request.payment_type != PaymentType.INTERNAL_TRANSFER or sender.bank_code == receiver.bank_code:
            if not await self.account_service.check_balance(sender.account_number, amount.amount):
                raise ValueError("Insufficient balance")
        
        # Create payment
        payment = Payment(
            payment_type=request.payment_type,
            amount=amount,
            sender=sender,
            receiver=receiver,
            channel=request.channel,
            description=request.description,
            upi_details=upi_details,
            bill_details=bill_details,
            initiated_by=request.initiated_by,
            metadata=request.metadata.copy()
        )
        
        # Perform fraud check
        fraud_check = await self.fraud_detection_service.check_payment(payment)
        payment.set_fraud_check(fraud_check)
        
        # Save payment
        saved_payment = await self.payment_repository.save(payment)
        
        return payment_to_response(saved_payment)


class ProcessPaymentUseCase:
    """Use case for processing a payment"""
    
    def __init__(
        self,
        payment_repository: PaymentRepository,
        payment_gateway_service: PaymentGatewayService,
        account_service: AccountService,
        notification_service: NotificationService
    ):
        self.payment_repository = payment_repository
        self.payment_gateway_service = payment_gateway_service
        self.account_service = account_service
        self.notification_service = notification_service
    
    async def execute(self, request: ProcessPaymentRequest) -> PaymentResponse:
        """Process a payment"""
        
        # Find payment
        payment = await self.payment_repository.find_by_id(request.payment_id)
        if not payment:
            raise ValueError(f"Payment not found: {request.payment_id}")
        
        # Check if payment can be processed
        if not payment.can_process():
            raise ValueError(f"Payment cannot be processed in current status: {payment.status}")
        
        try:
            # Mark as pending
            payment.mark_pending(request.processed_by)
            await self.payment_repository.save(payment)
            
            # Mark as processing
            payment.mark_processing()
            await self.payment_repository.save(payment)
            
            # Process through gateway
            success = await self.payment_gateway_service.process_payment(payment)
            
            if success:
                # Debit sender account
                debit_success = await self.account_service.debit_account(
                    payment.sender.account_number,
                    payment.amount.amount,
                    payment.reference_number
                )
                
                if debit_success:
                    # Credit receiver account
                    credit_success = await self.account_service.credit_account(
                        payment.receiver.account_number,
                        payment.amount.amount,
                        payment.reference_number
                    )
                    
                    if credit_success:
                        # Mark as completed
                        payment.mark_completed()
                        await self.payment_repository.save(payment)
                        
                        # Send notifications
                        await self.notification_service.send_payment_notification(
                            payment, payment.sender.account_number
                        )
                        await self.notification_service.send_payment_notification(
                            payment, payment.receiver.account_number
                        )
                    else:
                        # Rollback debit
                        await self.account_service.credit_account(
                            payment.sender.account_number,
                            payment.amount.amount,
                            f"ROLLBACK-{payment.reference_number}"
                        )
                        payment.mark_failed("Failed to credit receiver account")
                        await self.payment_repository.save(payment)
                else:
                    payment.mark_failed("Failed to debit sender account")
                    await self.payment_repository.save(payment)
            else:
                payment.mark_failed("Payment gateway processing failed")
                await self.payment_repository.save(payment)
                
        except Exception as e:
            payment.mark_failed(f"Processing error: {str(e)}")
            await self.payment_repository.save(payment)
            raise
        
        return payment_to_response(payment)


class CancelPaymentUseCase:
    """Use case for cancelling a payment"""
    
    def __init__(
        self,
        payment_repository: PaymentRepository,
        notification_service: NotificationService
    ):
        self.payment_repository = payment_repository
        self.notification_service = notification_service
    
    async def execute(self, request: CancelPaymentRequest) -> PaymentResponse:
        """Cancel a payment"""
        
        # Find payment
        payment = await self.payment_repository.find_by_id(request.payment_id)
        if not payment:
            raise ValueError(f"Payment not found: {request.payment_id}")
        
        # Cancel payment
        payment.cancel(request.reason, request.cancelled_by)
        
        # Save payment
        saved_payment = await self.payment_repository.save(payment)
        
        # Send notification
        await self.notification_service.send_payment_notification(
            saved_payment, saved_payment.sender.account_number
        )
        
        return payment_to_response(saved_payment)


class RefundPaymentUseCase:
    """Use case for refunding a payment"""
    
    def __init__(
        self,
        payment_repository: PaymentRepository,
        account_service: AccountService,
        notification_service: NotificationService
    ):
        self.payment_repository = payment_repository
        self.account_service = account_service
        self.notification_service = notification_service
    
    async def execute(self, request: RefundPaymentRequest) -> PaymentResponse:
        """Refund a payment"""
        
        # Find original payment
        original_payment = await self.payment_repository.find_by_id(request.payment_id)
        if not original_payment:
            raise ValueError(f"Payment not found: {request.payment_id}")
        
        # Create refund amount
        refund_amount = None
        if request.refund_amount:
            refund_amount = PaymentAmount(
                amount=request.refund_amount.amount,
                currency=request.refund_amount.currency
            )
        
        # Create refund payment
        refund_payment = original_payment.refund(
            refund_amount=refund_amount,
            reason=request.reason,
            refunded_by=request.refunded_by
        )
        
        # Save both payments
        await self.payment_repository.save(original_payment)
        saved_refund = await self.payment_repository.save(refund_payment)
        
        # Process refund (debit from receiver, credit to sender)
        debit_success = await self.account_service.debit_account(
            original_payment.receiver.account_number,
            refund_payment.amount.amount,
            refund_payment.reference_number
        )
        
        if debit_success:
            credit_success = await self.account_service.credit_account(
                original_payment.sender.account_number,
                refund_payment.amount.amount,
                refund_payment.reference_number
            )
            
            if credit_success:
                saved_refund.mark_completed()
                await self.payment_repository.save(saved_refund)
                
                # Send notifications
                await self.notification_service.send_payment_notification(
                    saved_refund, original_payment.sender.account_number
                )
                await self.notification_service.send_payment_notification(
                    saved_refund, original_payment.receiver.account_number
                )
            else:
                # Rollback debit
                await self.account_service.credit_account(
                    original_payment.receiver.account_number,
                    refund_payment.amount.amount,
                    f"ROLLBACK-{refund_payment.reference_number}"
                )
                saved_refund.mark_failed("Failed to credit original sender")
                await self.payment_repository.save(saved_refund)
        else:
            saved_refund.mark_failed("Failed to debit original receiver")
            await self.payment_repository.save(saved_refund)
        
        return payment_to_response(saved_refund)


class GetPaymentUseCase:
    """Use case for retrieving a payment"""
    
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository
    
    async def execute(self, payment_id: str) -> Optional[PaymentResponse]:
        """Get payment by ID"""
        payment = await self.payment_repository.find_by_id(payment_id)
        if payment:
            return payment_to_response(payment)
        return None


class ListPaymentsUseCase:
    """Use case for listing payments"""
    
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository
    
    async def execute(self, request: PaymentListRequest) -> PaymentListResponse:
        """List payments with filters"""
        return await self.payment_repository.find_by_criteria(request)


class GetPaymentStatsUseCase:
    """Use case for getting payment statistics"""
    
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository
    
    async def execute(self, request: PaymentStatsRequest) -> PaymentStatsResponse:
        """Get payment statistics"""
        return await self.payment_repository.get_payment_stats(request)


class ValidatePaymentUseCase:
    """Use case for validating payment"""
    
    def __init__(
        self,
        account_service: AccountService,
        payment_repository: PaymentRepository
    ):
        self.account_service = account_service
        self.payment_repository = payment_repository
    
    async def execute(self, request: CreatePaymentRequest) -> PaymentValidationResult:
        """Validate payment request"""
        errors = []
        
        # Validate amount
        if request.amount.amount <= 0:
            errors.append({
                "field": "amount",
                "message": "Amount must be greater than zero",
                "code": "INVALID_AMOUNT"
            })
        
        # Validate accounts
        if not await self.account_service.validate_account(request.sender.account_number):
            errors.append({
                "field": "sender.account_number",
                "message": "Invalid sender account",
                "code": "INVALID_SENDER_ACCOUNT"
            })
        
        if not await self.account_service.validate_account(request.receiver.account_number):
            errors.append({
                "field": "receiver.account_number", 
                "message": "Invalid receiver account",
                "code": "INVALID_RECEIVER_ACCOUNT"
            })
        
        # Check balance
        if not await self.account_service.check_balance(request.sender.account_number, request.amount.amount):
            errors.append({
                "field": "amount",
                "message": "Insufficient balance",
                "code": "INSUFFICIENT_BALANCE"
            })
        
        return PaymentValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )


class CheckPaymentLimitsUseCase:
    """Use case for checking payment limits"""
    
    def __init__(self, payment_repository: PaymentRepository):
        self.payment_repository = payment_repository
    
    async def execute(self, request: PaymentLimitCheckRequest) -> PaymentLimitCheckResponse:
        """Check payment limits"""
        today = datetime.utcnow().date()
        current_month = today.month
        current_year = today.year
        
        # Get current usage
        daily_usage = await self.payment_repository.get_daily_amount(
            request.account_number, datetime.combine(today, datetime.min.time())
        )
        monthly_usage = await self.payment_repository.get_monthly_amount(
            request.account_number, current_year, current_month
        )
        
        # Default limits if not provided
        daily_limit = request.daily_limit or Decimal('100000')
        monthly_limit = request.monthly_limit or Decimal('1000000')
        
        # Check violations
        violations = []
        new_daily_total = daily_usage + request.amount.amount
        new_monthly_total = monthly_usage + request.amount.amount
        
        if new_daily_total > daily_limit:
            violations.append(f"Daily limit exceeded: {new_daily_total} > {daily_limit}")
        
        if new_monthly_total > monthly_limit:
            violations.append(f"Monthly limit exceeded: {new_monthly_total} > {monthly_limit}")
        
        return PaymentLimitCheckResponse(
            is_within_limits=len(violations) == 0,
            daily_usage=payment_amount_to_dto(PaymentAmount(daily_usage, request.amount.currency)),
            monthly_usage=payment_amount_to_dto(PaymentAmount(monthly_usage, request.amount.currency)),
            daily_limit=payment_amount_to_dto(PaymentAmount(daily_limit, request.amount.currency)),
            monthly_limit=payment_amount_to_dto(PaymentAmount(monthly_limit, request.amount.currency)),
            violations=violations
        )
