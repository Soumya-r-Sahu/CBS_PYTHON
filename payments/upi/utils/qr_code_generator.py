"""
UPI Payment Utility Module for QR code generation.
This module uses consolidated utilities from the utils.common module.
"""
import base64
import io
import logging
from typing import Dict, Any, Optional
import qrcode

# Import common utilities
from utils.lib.payment_utils import generate_upi_reference
from utils.common import mask_account_number, mask_mobile_number

# Set up logging
logger = logging.getLogger(__name__)


class QRCodeGenerator:
    """Utility class for generating UPI QR codes"""
    
    @staticmethod
    def generate_upi_qr_string(upi_id: str, name: str, amount: Optional[float] = None, 
                            note: Optional[str] = None, reference: Optional[str] = None) -> str:
        """
        Generate UPI QR code data string.
        
        Args:
            upi_id: UPI ID for payment
            name: Merchant/recipient name
            amount: Optional fixed amount
            note: Optional transaction note
            reference: Optional transaction reference
            
        Returns:
            str: UPI QR code data string
        """        # Format: upi://pay?pa=UPI_ID&pn=NAME&am=AMOUNT&tn=NOTE&tr=REF
        qr_parts = [f"upi://pay?pa={upi_id}&pn={name}"]
        
        if amount is not None:
            qr_parts.append(f"am={amount}")
        
        if note is not None:
            qr_parts.append(f"tn={note}")
            
        if reference is not None:
            qr_parts.append(f"tr={reference}")
        
        return "&".join(qr_parts)
    
    @staticmethod
    def generate_qr_code_image(data: str) -> Optional[str]:
        """
        Generate QR code image and return as base64 string.
        
        Args:
            data: QR code data string
            
        Returns:
            str: Base64 encoded QR code image or None if generation fails
        """
        
        try:
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Create image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            qr_image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return qr_image_base64
            
        except Exception as e:
            logger.error(f"Error generating QR code image: {str(e)}")
            return None    @staticmethod
    def generate_upi_qr_code(upi_id: str, name: str, amount: Optional[float] = None,
                          note: Optional[str] = None, reference: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate UPI QR code data and image.
        
        Args:
            upi_id: UPI ID for payment
            name: Merchant/recipient name
            amount: Optional fixed amount
            note: Optional transaction note
            reference: Optional transaction reference
            
        Returns:
            Dict: QR code data and base64 encoded image
        """
        # If no reference is provided, generate one
        if reference is None and amount is not None:
            reference = generate_upi_reference(upi_id, amount)
            
        # Generate UPI QR code data string
        qr_data = QRCodeGenerator.generate_upi_qr_string(upi_id, name, amount, note, reference)
        
        # Generate QR code image
        qr_image_base64 = QRCodeGenerator.generate_qr_code_image(qr_data)
        
        # Return QR code data with masked UPI ID for security
        result = {
            "upi_id": mask_upi_id(upi_id),
            "name": name,
            "qr_data": qr_data
        }
        
        if amount is not None:
            result["amount"] = amount
            
        if note is not None:
            result["note"] = note
            
        if reference is not None:
            result["reference"] = reference
            
        if qr_image_base64 is not None:
            result["qr_image_base64"] = qr_image_base64
        
        return result


def generate_upi_transaction_reference(upi_id: str, amount: float, timestamp: str = None) -> str:
    """
    Generate a reference ID for UPI transactions.
    
    Args:
        upi_id: UPI ID for payment
        amount: Payment amount
        timestamp: Optional timestamp
        
    Returns:
        str: Generated reference ID
    """
    return generate_upi_reference(upi_id, amount, timestamp)


def mask_upi_id(upi_id: str) -> str:
    """
    Mask UPI ID for display/logging.
    
    Args:
        upi_id: UPI ID to mask
        
    Returns:
        str: Masked UPI ID
    """
    if not upi_id or '@' not in upi_id:
        return upi_id
    
    # Split UPI ID into username and provider
    parts = upi_id.split('@')
    username = parts[0]
    provider = parts[1]
    
    # Mask the username portion
    if len(username) > 4:
        masked_username = username[:2] + '*' * (len(username) - 4) + username[-2:]
    else:
        # If username is too short, just show first and last char
        masked_username = username[0] + '*' * (len(username) - 2) + username[-1] if len(username) > 2 else username
    
    return f"{masked_username}@{provider}"
