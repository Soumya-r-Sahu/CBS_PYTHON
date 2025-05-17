"""
Domain service for validating UPI Virtual Payment Addresses.
"""
from typing import Dict, Any, List, Optional

from ..entities.virtual_payment_address import VirtualPaymentAddress


class VpaValidationService:
    """Domain service for validating UPI VPAs."""
    
    def __init__(self):
        # Valid UPI providers
        self.valid_providers = [
            'oksbi', 'okicici', 'okaxis', 'okhdfcbank', 'ybl', 'upi', 
            'paytm', 'gpay', 'phonepe', 'ibl', 'abl', 'axisbank', 
            'axl', 'sbi', 'icici', 'kotak', 'hsbc', 'yesbank'
        ]
        
        # Restricted usernames for security reasons
        self.restricted_usernames = [
            'admin', 'administrator', 'root', 'support', 'help',
            'bank', 'payment', 'finance', 'manager', 'service'
        ]
    
    def validate_vpa(self, vpa: str) -> Dict[str, Any]:
        """
        Validate a VPA string.
        
        Args:
            vpa: String representation of VPA to validate
            
        Returns:
            Dictionary with validation result:
            {
                'is_valid': bool,
                'message': Optional[str]
            }
        """
        try:
            vpa_obj = VirtualPaymentAddress.from_string(vpa)
            
            # Check if username is restricted
            if vpa_obj.username.lower() in self.restricted_usernames:
                return {
                    'is_valid': False,
                    'message': "Username is restricted"
                }
            
            # Check if provider is valid
            if vpa_obj.provider.lower() not in self.valid_providers:
                return {
                    'is_valid': False,
                    'message': "Invalid UPI provider"
                }
            
            # Check username format
            if not self._validate_username_format(vpa_obj.username):
                return {
                    'is_valid': False,
                    'message': "Username contains invalid characters"
                }
            
            return {
                'is_valid': True,
                'message': None
            }
            
        except ValueError as e:
            return {
                'is_valid': False,
                'message': str(e)
            }
    
    def _validate_username_format(self, username: str) -> bool:
        """
        Validate username format according to UPI guidelines.
        
        Args:
            username: Username part of VPA
            
        Returns:
            Boolean indicating if the username format is valid
        """
        # Username should be alphanumeric with dots, underscores or hyphens
        return all(c.isalnum() or c in '._-' for c in username)
