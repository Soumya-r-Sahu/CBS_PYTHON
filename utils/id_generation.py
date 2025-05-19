"""
Centralized ID Generation Utility for Core Banking System

This module provides a unified approach to generating IDs and reference numbers
throughout the Core Banking System. It consolidates previously duplicated logic and
ensures consistent ID generation across all modules.

Functions:
----------
- generate_reference_id: Generic function for generating reference IDs
- generate_transaction_id: Generates transaction IDs with appropriate prefixes
- generate_payment_reference: Generates references for various payment methods
"""

import hashlib
import datetime
import uuid
from typing import Dict, Any, Optional

# Import singleton decorator
from utils.design_patterns import singleton

@singleton
class IDGenerator:
    """
    Centralized ID generator class implementing singleton pattern.
    Ensures consistent ID generation throughout the application.
    """
    
    def __init__(self):
        # Prefix mappings for different payment types
        self.payment_prefixes = {
            "NEFT": "NEFT",
            "RTGS": "RTGS",
            "IMPS": "IMPS",
            "UPI": "UPI"
        }
        
        # Initialize counters for different ID types
        self.counters = {
            "transaction": 0,
            "customer": 0,
            "account": 0,
            "employee": 0
        }
    
    def generate_reference_id(self, prefix: str, unique_data: str, 
                             timestamp: Optional[str] = None) -> str:
        """
        Generate a reference ID with the given prefix.
        
        Args:
            prefix: The prefix for the reference ID
            unique_data: Unique data to incorporate in the ID
            timestamp: Optional timestamp (if None, current time is used)
            
        Returns:
            Reference ID string
        """
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            
        # Create a unique hash using the inputs
        hash_input = f"{prefix}_{unique_data}_{timestamp}_{uuid.uuid4()}"
        hashed = hashlib.md5(hash_input.encode()).hexdigest()
        
        # Return formatted reference ID
        return f"{prefix}-{timestamp}-{hashed[:8]}"
    
    def generate_payment_reference(self, payment_type: str, account_number: str, 
                                 amount: float, timestamp: Optional[str] = None) -> str:
        """
        Generate a payment reference number for various payment methods.
        
        Args:
            payment_type: The type of payment (NEFT, RTGS, IMPS, UPI)
            account_number: The account number involved
            amount: The transaction amount
            timestamp: Optional timestamp (if None, current time is used)
            
        Returns:
            Payment reference number
        """
        # Get the prefix for the payment type
        prefix = self.payment_prefixes.get(payment_type.upper(), payment_type.upper())
        
        # Generate unique data
        unique_data = f"{account_number}_{amount}"
        
        # Generate and return the reference ID
        return self.generate_reference_id(prefix, unique_data, timestamp)

# Create a singleton instance for easy import
id_generator = IDGenerator()

# Convenience functions for backward compatibility
def generate_reference_id(prefix: str, unique_data: str, timestamp: Optional[str] = None) -> str:
    """Convenience function for generate_reference_id"""
    return id_generator.generate_reference_id(prefix, unique_data, timestamp)

def generate_payment_reference(payment_type: str, account_number: str, 
                             amount: float, timestamp: Optional[str] = None) -> str:
    """Convenience function for generate_payment_reference"""
    return id_generator.generate_payment_reference(payment_type, account_number, amount, timestamp)

# Specific payment reference generators for backward compatibility
def generate_neft_reference(account_number: str, amount: float, timestamp: Optional[str] = None) -> str:
    """Generate a NEFT reference number"""
    return generate_payment_reference("NEFT", account_number, amount, timestamp)

def generate_rtgs_reference(account_number: str, amount: float, timestamp: Optional[str] = None) -> str:
    """Generate a RTGS reference number"""
    return generate_payment_reference("RTGS", account_number, amount, timestamp)

def generate_imps_reference(account_number: str, amount: float, timestamp: Optional[str] = None) -> str:
    """Generate an IMPS reference number"""
    return generate_payment_reference("IMPS", account_number, amount, timestamp)

def generate_upi_reference(account_number: str, amount: float, timestamp: Optional[str] = None) -> str:
    """Generate a UPI reference number"""
    return generate_payment_reference("UPI", account_number, amount, timestamp)
