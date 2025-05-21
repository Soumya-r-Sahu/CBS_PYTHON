"""
Address Value Object

This module defines the Address value object which represents
a physical address within the HR-ERP system.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Address:
    """
    Value object representing a physical address
    
    This is an immutable value object with validation rules.
    """
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    street2: Optional[str] = None
    
    def __post_init__(self):
        """Validate the address"""
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate address fields
        
        Raises:
            ValueError: If address fields are invalid
        """
        if not self.street:
            raise ValueError("Street is required")
        
        if not self.city:
            raise ValueError("City is required")
        
        if not self.state:
            raise ValueError("State/Province is required")
        
        if not self.postal_code:
            raise ValueError("Postal code is required")
        
        if not self.country:
            raise ValueError("Country is required")
        
        # Basic postal code format validation (simple example)
        if len(self.postal_code) < 4 or len(self.postal_code) > 12:
            raise ValueError("Postal code format is invalid")
    
    def __str__(self) -> str:
        """String representation of the address"""
        address_parts = [self.street]
        
        if self.street2:
            address_parts.append(self.street2)
            
        address_parts.append(f"{self.city}, {self.state} {self.postal_code}")
        address_parts.append(self.country)
        
        return "\n".join(address_parts)
    
    def is_same_city(self, other: 'Address') -> bool:
        """Check if two addresses are in the same city"""
        return (self.city.lower() == other.city.lower() and 
                self.state.lower() == other.state.lower() and
                self.country.lower() == other.country.lower())
    
    def is_same_country(self, other: 'Address') -> bool:
        """Check if two addresses are in the same country"""
        return self.country.lower() == other.country.lower()
