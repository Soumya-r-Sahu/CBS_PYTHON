"""
Contact Information Value Object

This module defines the ContactInfo value object which represents
contact information like phone numbers and email addresses.
"""

from dataclasses import dataclass
import re
from typing import Optional


@dataclass(frozen=True)
class ContactInfo:
    """
    Value object representing contact information
    
    This is an immutable value object with validation rules
    for phone numbers and email addresses.
    """
    email: str
    phone: str
    alternate_email: Optional[str] = None
    mobile: Optional[str] = None
    
    def __post_init__(self):
        """Validate contact information"""
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate contact information fields
        
        Raises:
            ValueError: If contact fields are invalid
        """
        # Validate primary email
        if not self._is_valid_email(self.email):
            raise ValueError(f"Invalid email format: {self.email}")
        
        # Validate alternate email if present
        if self.alternate_email and not self._is_valid_email(self.alternate_email):
            raise ValueError(f"Invalid alternate email format: {self.alternate_email}")
        
        # Validate phone (basic validation)
        if not self._is_valid_phone(self.phone):
            raise ValueError(f"Invalid phone format: {self.phone}")
        
        # Validate mobile if present
        if self.mobile and not self._is_valid_phone(self.mobile):
            raise ValueError(f"Invalid mobile format: {self.mobile}")
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """
        Validate email format
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Basic email validation pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """
        Validate phone number format
        
        Args:
            phone: Phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        # This is a simplified validation for demonstration
        # Real implementation might handle international formats
        # Strip all non-numeric characters except + for country code
        digits_only = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Check length and basic structure
        if len(digits_only) < 7:  # Minimum reasonable length
            return False
            
        if len(digits_only) > 15:  # Maximum per E.164 standard
            return False
            
        return True
    
    def has_mobile(self) -> bool:
        """Check if mobile number is provided"""
        return self.mobile is not None and self.mobile != ""
    
    def has_alternate_email(self) -> bool:
        """Check if alternate email is provided"""
        return self.alternate_email is not None and self.alternate_email != ""
