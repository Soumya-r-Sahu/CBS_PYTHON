"""
UPI Payment Utility Module for QR code generation.
"""
import base64
import io
import logging
from typing import Dict, Any, Optional

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
        """
        # Format: upi://pay?pa=UPI_ID&pn=NAME&am=AMOUNT&tn=NOTE&tr=REF
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
            # Try to import QR code module
            import qrcode
            
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
            
        except ImportError:
            logger.warning("QR code module not available. QR code generation failed.")
            return None
            
        except Exception as e:
            logger.error(f"Error generating QR code image: {str(e)}")
            return None
    
    @staticmethod
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
        # Generate UPI QR code data string
        qr_data = QRCodeGenerator.generate_upi_qr_string(upi_id, name, amount, note, reference)
        
        # Generate QR code image
        qr_image_base64 = QRCodeGenerator.generate_qr_code_image(qr_data)
        
        # Return QR code data
        result = {
            "upi_id": upi_id,
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
