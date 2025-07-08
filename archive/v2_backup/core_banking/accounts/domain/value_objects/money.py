"""
Money Value Object

This module defines the Money value object representing an amount with currency.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



@dataclass(frozen=True)
class Money:
    """
    Money value object
    
    Represents an amount with a specific currency.
    """
    amount: Decimal
    currency: str = "INR"  # Default currency is Indian Rupee
    
    def __post_init__(self):
        """Validate the money object after initialization"""
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, 'amount', Decimal(str(self.amount)))
            
        if not isinstance(self.currency, str) or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO currency code")
            
    def __add__(self, other):
        """Add two Money objects"""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot add Money and {type(other)}")
            
        if self.currency != other.currency:
            raise ValueError("Cannot add Money with different currencies")
            
        return Money(amount=self.amount + other.amount, currency=self.currency)
        
    def __sub__(self, other):
        """Subtract two Money objects"""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot subtract {type(other)} from Money")
            
        if self.currency != other.currency:
            raise ValueError("Cannot subtract Money with different currencies")
            
        return Money(amount=self.amount - other.amount, currency=self.currency)
        
    def __mul__(self, multiplier):
        """Multiply Money by a number"""
        if isinstance(multiplier, (int, float, Decimal)):
            return Money(amount=self.amount * Decimal(str(multiplier)), currency=self.currency)
        raise TypeError(f"Cannot multiply Money by {type(multiplier)}")
        
    def __gt__(self, other):
        """Greater than comparison"""
        self._validate_comparison(other)
        return self.amount > other.amount
        
    def __ge__(self, other):
        """Greater than or equal comparison"""
        self._validate_comparison(other)
        return self.amount >= other.amount
        
    def __lt__(self, other):
        """Less than comparison"""
        self._validate_comparison(other)
        return self.amount < other.amount
        
    def __le__(self, other):
        """Less than or equal comparison"""
        self._validate_comparison(other)
        return self.amount <= other.amount
        
    def __eq__(self, other):
        """Equality comparison"""
        if other is None:
            return False
            
        if not isinstance(other, Money):
            return False
            
        return self.currency == other.currency and self.amount == other.amount
        
    def _validate_comparison(self, other):
        """Validate money comparison"""
        if not isinstance(other, Money):
            raise TypeError(f"Cannot compare Money with {type(other)}")
            
        if self.currency != other.currency:
            raise ValueError("Cannot compare Money with different currencies")
            
    def is_positive(self) -> bool:
        """
        Check if the amount is positive
        
        Returns:
            True if the amount is positive, False otherwise
        """
        return self.amount > Decimal('0')
    
    def is_negative(self) -> bool:
        """
        Check if the amount is negative
        
        Returns:
            True if the amount is negative, False otherwise
        """
        return self.amount < Decimal('0')
        
    def is_zero(self) -> bool:
        """
        Check if the amount is zero
        
        Returns:
            True if the amount is zero, False otherwise
        """
        return self.amount == Decimal('0')
