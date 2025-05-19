"""
Mobile transaction entity in the Mobile Banking domain.
This entity represents mobile banking transactions.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class MobileTransactionType(Enum):
    """Types of Mobile Banking transactions."""
    FUNDS_TRANSFER = "funds_transfer"
    BILL_PAYMENT = "bill_payment"
    RECHARGE = "recharge"
    QR_PAYMENT = "qr_payment"
    UPI_PAYMENT = "upi_payment"
    ACCOUNT_STATEMENT = "account_statement"
    CARD_MANAGEMENT = "card_management"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"


class MobileTransactionStatus(Enum):
    """Status of Mobile Banking transactions."""
    INITIATED = "initiated"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class MobileTransaction:
    """Mobile Banking transaction entity."""
    
    # Identity attributes
    transaction_id: UUID
    user_id: UUID
    session_id: UUID
    
    # Transaction attributes
    transaction_type: MobileTransactionType
    amount: Optional[float]
    source_account: Optional[str]
    destination_account: Optional[str]
    transaction_date: datetime
    status: MobileTransactionStatus
    
    # Device information
    device_id: str
    ip_address: Optional[str]
    
    # Metadata
    reference_number: Optional[str] = None
    description: Optional[str] = None
    failure_reason: Optional[str] = None
    
    @classmethod
    def create(cls, user_id: UUID, session_id: UUID, device_id: str,
               transaction_type: MobileTransactionType, amount: Optional[float] = None,
               source_account: Optional[str] = None, destination_account: Optional[str] = None,
               ip_address: Optional[str] = None, description: Optional[str] = None) -> 'MobileTransaction':
        """
        Create a new Mobile Banking transaction.
        
        Args:
            user_id: ID of the user
            session_id: ID of the session
            device_id: ID of the device
            transaction_type: Type of transaction
            amount: Transaction amount (optional)
            source_account: Source account number (optional)
            destination_account: Destination account number (optional)
            ip_address: IP address (optional)
            description: Transaction description (optional)
            
        Returns:
            New MobileTransaction instance
        """
        # Validate required fields based on transaction type
        if transaction_type in [MobileTransactionType.FUNDS_TRANSFER, 
                              MobileTransactionType.BILL_PAYMENT, 
                              MobileTransactionType.RECHARGE, 
                              MobileTransactionType.QR_PAYMENT,
                              MobileTransactionType.UPI_PAYMENT,
                              MobileTransactionType.DEPOSIT,
                              MobileTransactionType.WITHDRAWAL]:
            if amount is None or amount <= 0:
                raise ValueError("Amount must be greater than zero for this transaction type")
                
        if transaction_type == MobileTransactionType.FUNDS_TRANSFER:
            if not source_account or not destination_account:
                raise ValueError("Source and destination accounts are required for funds transfer")
        
        return cls(
            transaction_id=uuid4(),
            user_id=user_id,
            session_id=session_id,
            transaction_type=transaction_type,
            amount=amount,
            source_account=source_account,
            destination_account=destination_account,
            transaction_date=datetime.now(),
            status=MobileTransactionStatus.INITIATED,
            device_id=device_id,
            ip_address=ip_address,
            description=description
        )
    
    def complete(self, reference_number: str) -> None:
        """
        Mark the transaction as completed.
        
        Args:
            reference_number: Reference number for the completed transaction
        """
        if self.status not in [MobileTransactionStatus.INITIATED, MobileTransactionStatus.PENDING]:
            raise ValueError(f"Cannot complete transaction with status: {self.status}")
        
        self.status = MobileTransactionStatus.COMPLETED
        self.reference_number = reference_number
    
    def fail(self, failure_reason: str) -> None:
        """
        Mark the transaction as failed.
        
        Args:
            failure_reason: Reason for failure
        """
        if self.status not in [MobileTransactionStatus.INITIATED, MobileTransactionStatus.PENDING]:
            raise ValueError(f"Cannot fail transaction with status: {self.status}")
        
        self.status = MobileTransactionStatus.FAILED
        self.failure_reason = failure_reason
    
    def cancel(self) -> None:
        """Cancel the transaction."""
        if self.status not in [MobileTransactionStatus.INITIATED, MobileTransactionStatus.PENDING]:
            raise ValueError(f"Cannot cancel transaction with status: {self.status}")
        
        self.status = MobileTransactionStatus.CANCELLED
    
    def set_pending(self) -> None:
        """Mark the transaction as pending."""
        if self.status != MobileTransactionStatus.INITIATED:
            raise ValueError(f"Cannot set transaction to pending with status: {self.status}")
        
        self.status = MobileTransactionStatus.PENDING
    
    def update_description(self, description: str) -> None:
        """
        Update the transaction description.
        
        Args:
            description: New description
        """
        self.description = description
