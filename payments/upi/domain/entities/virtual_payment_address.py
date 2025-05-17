"""VPA entity representing a UPI Virtual Payment Address."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class VirtualPaymentAddress:
    """
    Represents a UPI Virtual Payment Address (VPA) in the format username@provider.
    Encapsulates VPA validation and formatting rules.
    """
    username: str
    provider: str
    display_name: Optional[str] = None
    
    @property
    def address(self) -> str:
        """Returns the complete VPA address in the format username@provider."""
        return f"{self.username}@{self.provider}"
    
    @classmethod
    def from_string(cls, vpa_string: str, display_name: Optional[str] = None) -> 'VirtualPaymentAddress':
        """Create a VPA object from a string in the format username@provider."""
        if '@' not in vpa_string:
            raise ValueError("Invalid VPA format: Must contain '@' symbol")
        
        parts = vpa_string.split('@')
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError("Invalid VPA format: Must be in format username@provider")
        
        return cls(username=parts[0], provider=parts[1], display_name=display_name)
    
    def is_valid(self) -> bool:
        """Check if the VPA is valid according to UPI guidelines."""
        # Username should be alphanumeric with dots, underscores or hyphens
        if not all(c.isalnum() or c in '._-' for c in self.username):
            return False
        
        # Provider should be a valid UPI provider
        valid_providers = [
            'oksbi', 'okicici', 'okaxis', 'okhdfcbank', 'ybl', 'upi', 
            'paytm', 'gpay', 'phonepe', 'ibl', 'abl', 'axisbank', 
            'axl', 'sbi', 'icici', 'kotak', 'hsbc', 'yesbank'
        ]
        
        return self.provider.lower() in valid_providers
