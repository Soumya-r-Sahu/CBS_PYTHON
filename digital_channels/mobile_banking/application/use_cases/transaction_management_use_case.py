"""
Transaction management use cases for the Mobile Banking domain.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from ...domain.entities.mobile_transaction import MobileTransaction, TransactionStatus, TransactionType
from ...domain.entities.mobile_user import MobileBankingUser
from ...domain.services.mobile_security_policy_service import MobileSecurityPolicyService
from ..interfaces.mobile_transaction_repository_interface import MobileTransactionRepositoryInterface
from ..interfaces.mobile_user_repository_interface import MobileUserRepositoryInterface
from ..interfaces.notification_service_interface import NotificationServiceInterface, NotificationType
from ..interfaces.audit_log_service_interface import AuditLogServiceInterface, AuditEventType


@dataclass
class TransactionResult:
    """Result of a transaction operation."""
    success: bool
    message: str
    transaction: Optional[MobileTransaction] = None
    reference_number: Optional[str] = None
    needs_approval: bool = False
    needs_verification: bool = False


class TransactionManagementUseCase:
    """Use cases related to transaction management."""
    
    def __init__(
        self,
        transaction_repository: MobileTransactionRepositoryInterface,
        user_repository: MobileUserRepositoryInterface,
        notification_service: NotificationServiceInterface,
        audit_log_service: AuditLogServiceInterface,
        security_policy_service: MobileSecurityPolicyService
    ):
        """
        Initialize the transaction management use case.
        
        Args:
            transaction_repository: Repository for transaction operations
            user_repository: Repository for user operations
            notification_service: Service for sending notifications
            audit_log_service: Service for logging audit events
            security_policy_service: Domain service for security policies
        """
        self._transaction_repository = transaction_repository
        self._user_repository = user_repository
        self._notification_service = notification_service
        self._audit_log_service = audit_log_service
        self._security_policy_service = security_policy_service
    
    def initiate_transaction(
        self,
        user_id: UUID,
        transaction_type: TransactionType,
        amount: float,
        from_account: str,
        to_account: str,
        remarks: Optional[str] = None,
        ip_address: str = None,
        device_id: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None
    ) -> TransactionResult:
        """
        Initiate a transaction.
        
        Args:
            user_id: The ID of the user initiating the transaction
            transaction_type: The type of transaction
            amount: The amount to transfer
            from_account: The account to transfer from
            to_account: The account to transfer to
            remarks: Optional remarks for the transaction
            ip_address: The IP address of the request
            device_id: The device ID of the request
            location: The location of the request
            
        Returns:
            TransactionResult with result information
        """
        # Get the user
        user = self._user_repository.get_by_id(user_id)
        if user is None:
            return TransactionResult(
                success=False,
                message="User not found"
            )
        
        # Generate a reference number
        reference_number = self._generate_reference_number(transaction_type)
        
        # Check if the transaction is within limits
        if not self._security_policy_service.is_within_transaction_limits(user, amount, transaction_type):
            self._audit_log_service.log_event(
                event_type=AuditEventType.TRANSACTION_INITIATED,
                user_id=user_id,
                ip_address=ip_address,
                details={
                    "transaction_type": transaction_type.value,
                    "amount": amount,
                    "reference_number": reference_number,
                    "reason": "Transaction limit exceeded"
                },
                status="failure",
                device_info={"device_id": device_id} if device_id else None,
                location=location
            )
            
            return TransactionResult(
                success=False,
                message="Transaction amount exceeds your limits",
                reference_number=reference_number
            )
        
        # Check if the transaction needs additional verification
        needs_verification = self._security_policy_service.transaction_needs_verification(
            user, amount, transaction_type, from_account, to_account
        )
        
        # Check if the transaction is high risk
        risk_level = self._security_policy_service.assess_transaction_risk(
            user, amount, transaction_type, from_account, to_account, ip_address, device_id, location
        )
        
        # Create the transaction
        transaction = MobileTransaction(
            user_id=user_id,
            transaction_type=transaction_type,
            amount=amount,
            from_account=from_account,
            to_account=to_account,
            reference_number=reference_number,
            remarks=remarks,
            status=TransactionStatus.INITIATED,
            risk_level=risk_level,
            initiation_time=datetime.now(),
            ip_address=ip_address,
            device_id=device_id,
            location=location
        )
        
        # Determine if the transaction needs approval based on risk level
        needs_approval = risk_level >= 3  # High risk
        
        # Set transaction status accordingly
        if needs_approval:
            transaction.status = TransactionStatus.PENDING_APPROVAL
        elif needs_verification:
            transaction.status = TransactionStatus.PENDING_VERIFICATION
        
        # Save the transaction
        transaction = self._transaction_repository.save(transaction)
        
        # Log transaction initiation
        self._audit_log_service.log_event(
            event_type=AuditEventType.TRANSACTION_INITIATED,
            user_id=user_id,
            ip_address=ip_address,
            details={
                "transaction_id": str(transaction.id),
                "transaction_type": transaction_type.value,
                "amount": amount,
                "reference_number": reference_number,
                "risk_level": risk_level,
                "needs_approval": needs_approval,
                "needs_verification": needs_verification
            },
            status="success",
            device_info={"device_id": device_id} if device_id else None,
            location=location
        )
        
        return TransactionResult(
            success=True,
            message="Transaction initiated successfully",
            transaction=transaction,
            reference_number=reference_number,
            needs_approval=needs_approval,
            needs_verification=needs_verification
        )
    
    def verify_transaction(
        self,
        user_id: UUID,
        transaction_id: UUID,
        verification_code: str,
        ip_address: str
    ) -> TransactionResult:
        """
        Verify a transaction that requires verification.
        
        Args:
            user_id: The ID of the user verifying the transaction
            transaction_id: The ID of the transaction to verify
            verification_code: The verification code
            ip_address: The IP address of the request
            
        Returns:
            TransactionResult with result information
        """
        # Get the transaction
        transaction = self._transaction_repository.get_by_id(transaction_id)
        
        if transaction is None:
            return TransactionResult(
                success=False,
                message="Transaction not found"
            )
        
        # Check if the transaction belongs to the user
        if transaction.user_id != user_id:
            self._audit_log_service.log_event(
                event_type=AuditEventType.TRANSACTION_FAILED,
                user_id=user_id,
                ip_address=ip_address,
                details={
                    "transaction_id": str(transaction_id),
                    "reason": "Transaction does not belong to user"
                },
                status="failure"
            )
            
            return TransactionResult(
                success=False,
                message="Transaction not found"
            )
        
        # Check if the transaction is in the correct state
        if transaction.status != TransactionStatus.PENDING_VERIFICATION:
            return TransactionResult(
                success=False,
                message=f"Transaction is not pending verification (current status: {transaction.status.value})"
            )
        
        # Verify the verification code
        if not self._security_policy_service.verify_transaction_code(transaction.id, verification_code):
            self._audit_log_service.log_event(
                event_type=AuditEventType.TRANSACTION_FAILED,
                user_id=user_id,
                ip_address=ip_address,
                details={
                    "transaction_id": str(transaction_id),
                    "reason": "Invalid verification code"
                },
                status="failure"
            )
            
            return TransactionResult(
                success=False,
                message="Invalid verification code"
            )
        
        # Update the transaction status
        transaction.status = TransactionStatus.PROCESSING
        transaction.verification_time = datetime.now()
        self._transaction_repository.update(transaction)
        
        # Process the transaction (would call a separate service in a real implementation)
        
        # Log verification
        self._audit_log_service.log_event(
            event_type=AuditEventType.TRANSACTION_COMPLETED,
            user_id=user_id,
            ip_address=ip_address,
            details={
                "transaction_id": str(transaction_id),
                "reference_number": transaction.reference_number
            },
            status="success"
        )
        
        return TransactionResult(
            success=True,
            message="Transaction verified successfully",
            transaction=transaction,
            reference_number=transaction.reference_number
        )
    
    def complete_transaction(
        self,
        transaction_id: UUID,
        status: TransactionStatus,
        response_details: Optional[Dict[str, Any]] = None
    ) -> TransactionResult:
        """
        Complete a transaction with the final status.
        
        Args:
            transaction_id: The ID of the transaction to complete
            status: The final status of the transaction
            response_details: Optional details about the response
            
        Returns:
            TransactionResult with result information
        """
        # Get the transaction
        transaction = self._transaction_repository.get_by_id(transaction_id)
        
        if transaction is None:
            return TransactionResult(
                success=False,
                message="Transaction not found"
            )
        
        # Update the transaction
        transaction.status = status
        transaction.completion_time = datetime.now()
        transaction.response_details = response_details or {}
        self._transaction_repository.update(transaction)
        
        # Log transaction completion
        event_type = AuditEventType.TRANSACTION_COMPLETED if status == TransactionStatus.COMPLETED else AuditEventType.TRANSACTION_FAILED
        self._audit_log_service.log_event(
            event_type=event_type,
            user_id=transaction.user_id,
            ip_address=transaction.ip_address,
            details={
                "transaction_id": str(transaction_id),
                "reference_number": transaction.reference_number,
                "final_status": status.value,
                "response_details": response_details
            },
            status="success" if status == TransactionStatus.COMPLETED else "failure"
        )
        
        # Send notification
        notification_type = NotificationType.TRANSACTION_SUCCESS if status == TransactionStatus.COMPLETED else NotificationType.TRANSACTION_FAILURE
        self._notification_service.send_notification(
            user_id=transaction.user_id,
            notification_type=notification_type,
            details={
                "transaction_id": str(transaction_id),
                "reference_number": transaction.reference_number,
                "amount": transaction.amount,
                "status": status.value,
                "time": datetime.now().isoformat()
            }
        )
        
        return TransactionResult(
            success=status == TransactionStatus.COMPLETED,
            message="Transaction completed" if status == TransactionStatus.COMPLETED else "Transaction failed",
            transaction=transaction,
            reference_number=transaction.reference_number
        )
    
    def get_user_transactions(
        self,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[MobileTransaction]:
        """
        Get all transactions for a user, optionally within a date range.
        
        Args:
            user_id: The ID of the user
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering
            
        Returns:
            List of MobileTransaction objects
        """
        if start_date is not None and end_date is not None:
            return self._transaction_repository.get_by_user_id_and_date_range(
                user_id, start_date, end_date
            )
        else:
            return self._transaction_repository.get_by_user_id(user_id)
    
    def get_transaction_by_reference(self, reference_number: str) -> Optional[MobileTransaction]:
        """
        Get a transaction by its reference number.
        
        Args:
            reference_number: The reference number of the transaction
            
        Returns:
            MobileTransaction if found, None otherwise
        """
        return self._transaction_repository.get_by_reference_number(reference_number)
    
    def _generate_reference_number(self, transaction_type: TransactionType) -> str:
        """
        Generate a unique reference number for a transaction.
        
        Args:
            transaction_type: The type of transaction
            
        Returns:
            A unique reference number
        """
        prefix = {
            TransactionType.FUND_TRANSFER: "FT",
            TransactionType.BILL_PAYMENT: "BP",
            TransactionType.RECHARGE: "RC",
            TransactionType.CARD_PAYMENT: "CP"
        }.get(transaction_type, "TX")
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = str(uuid4().int)[:6]
        
        return f"{prefix}{timestamp}{random_part}"
