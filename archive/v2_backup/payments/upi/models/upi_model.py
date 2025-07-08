"""
UPI Payment Models.

Contains data models for UPI transactions and registrations.
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List


class TransactionStatus(Enum):
    """Enum representing transaction status"""
    INITIATED = "INITIATED"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class TransactionType(Enum):
    """Enum representing transaction type"""
    PAY = "PAY"           # Standard payment
    COLLECT = "COLLECT"   # Request payment
    REFUND = "REFUND"     # Refund transaction
    REVERSAL = "REVERSAL" # Transaction reversal


@dataclass
class UpiRegistration:
    """UPI registration model"""
    upi_id: str
    account_number: str
    mobile_number: str
    name: str
    status: str = "active"
    registration_id: str = None
    registration_date: str = None
    
    def __post_init__(self):
        """Initialize default fields if not provided"""
        import uuid
        from datetime import datetime
        
        if not self.registration_id:
            self.registration_id = str(uuid.uuid4())
        
        if not self.registration_date:
            self.registration_date = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class UpiTransaction:
    """UPI transaction model"""
    payer_upi_id: str
    payee_upi_id: str
    amount: float
    status: TransactionStatus = TransactionStatus.INITIATED
    transaction_type: TransactionType = TransactionType.PAY
    transaction_id: str = None
    reference_id: str = None
    note: str = None
    timestamp: str = None
    gateway_response: Dict[str, Any] = None
    meta_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default fields if not provided"""
        import uuid
        from datetime import datetime
        
        if not self.transaction_id:
            self.transaction_id = f"UPI{int(datetime.utcnow().timestamp())}{str(uuid.uuid4())[:8]}"
        
        if not self.reference_id:
            self.reference_id = f"REF{int(datetime.utcnow().timestamp())}"
        
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"
        
        # If status is provided as string, convert to enum
        if isinstance(self.status, str):
            self.status = TransactionStatus(self.status)
        
        # If transaction_type is provided as string, convert to enum
        if isinstance(self.transaction_type, str):
            self.transaction_type = TransactionType(self.transaction_type)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert enums to string values
        data['status'] = self.status.value
        data['transaction_type'] = self.transaction_type.value
        return data


@dataclass
class QRCode:
    """UPI QR code model"""
    upi_id: str
    merchant_name: str
    amount: Optional[float] = None
    transaction_note: Optional[str] = None
    transaction_ref: Optional[str] = None
    qr_data: Optional[str] = None
    qr_image_base64: Optional[str] = None
    
    def generate_upi_qr_data(self) -> str:
        """Generate UPI QR code data string"""
        # Format: upi://pay?pa=UPI_ID&pn=NAME&am=AMOUNT&tn=NOTE&tr=REF
        qr_parts = [f"upi://pay?pa={self.upi_id}&pn={self.merchant_name}"]
        
        if self.amount:
            qr_parts.append(f"am={self.amount}")
        
        if self.transaction_note:
            qr_parts.append(f"tn={self.transaction_note}")
            
        if self.transaction_ref:
            qr_parts.append(f"tr={self.transaction_ref}")
        
        self.qr_data = "&".join(qr_parts)
        return self.qr_data
