"""
Core Banking Centralized Utilities

This module provides common utilities and helper functions for all components
of the Core Banking module. Centralizing these utilities reduces code duplication
and ensures consistent behavior across the module.
"""

import logging
import datetime
import uuid
import re
import json
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
import hashlib

# Setup logging
logger = logging.getLogger(__name__)

# Constants
ACCOUNT_NUMBER_REGEX = r'^\d{5}-\d{5}-\d{5}$'
CUSTOMER_ID_REGEX = r'^C\d{9}$'
TRANSACTION_ID_REGEX = r'^T\d{12}$'

class CoreBankingException(Exception):
    """Base exception class for all Core Banking exceptions"""
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ValidationException(CoreBankingException):
    """Exception raised for validation errors"""
    pass


class BusinessRuleException(CoreBankingException):
    """Exception raised for business rule violations"""
    pass


class DatabaseException(CoreBankingException):
    """Exception raised for database errors"""
    pass


class MoneyUtility:
    """Utility for money-related operations"""
    
    @staticmethod
    def format_money(amount: Decimal, currency: str = 'INR') -> str:
        """
        Format a decimal amount as a string with currency symbol
        
        Args:
            amount: Decimal amount to format
            currency: Currency code (default: INR)
            
        Returns:
            Formatted money string
        """
        currency_symbols = {
            'INR': '₹',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥'
        }
        
        symbol = currency_symbols.get(currency, currency)
        return f"{symbol} {amount:,.2f}"
    
    @staticmethod
    def calculate_interest(principal: Decimal, rate: Decimal, days: int) -> Decimal:
        """
        Calculate simple interest
        
        Args:
            principal: Principal amount
            rate: Interest rate as annual percentage
            days: Number of days
            
        Returns:
            Interest amount
        """
        return (principal * rate * Decimal(days)) / (Decimal(100) * Decimal(365))


class DateUtils:
    """Date and time utilities"""
    
    @staticmethod
    def is_business_day(date: datetime.date) -> bool:
        """
        Check if a date is a business day (not weekend)
        
        Args:
            date: Date to check
            
        Returns:
            True if business day, False otherwise
        """
        # 5 = Saturday, 6 = Sunday
        return date.weekday() < 5
    
    @staticmethod
    def next_business_day(date: datetime.date) -> datetime.date:
        """
        Get the next business day after the provided date
        
        Args:
            date: Starting date
            
        Returns:
            Next business day
        """
        next_day = date + datetime.timedelta(days=1)
        while not DateUtils.is_business_day(next_day):
            next_day += datetime.timedelta(days=1)
        return next_day
    
    @staticmethod
    def add_business_days(date: datetime.date, days: int) -> datetime.date:
        """
        Add a specified number of business days to a date
        
        Args:
            date: Starting date
            days: Number of business days to add
            
        Returns:
            Resulting date
        """
        result = date
        days_added = 0
        
        while days_added < days:
            result = result + datetime.timedelta(days=1)
            if DateUtils.is_business_day(result):
                days_added += 1
                
        return result


class ValidationUtils:
    """Validation utilities for Core Banking"""
    
    @staticmethod
    def validate_account_number(account_number: str) -> bool:
        """
        Validate an account number format
        
        Args:
            account_number: Account number to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not account_number:
            return False
        
        return bool(re.match(ACCOUNT_NUMBER_REGEX, account_number))
    
    @staticmethod
    def validate_customer_id(customer_id: str) -> bool:
        """
        Validate a customer ID format
        
        Args:
            customer_id: Customer ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not customer_id:
            return False
        
        return bool(re.match(CUSTOMER_ID_REGEX, customer_id))
    
    @staticmethod
    def validate_transaction_id(transaction_id: str) -> bool:
        """
        Validate a transaction ID format
        
        Args:
            transaction_id: Transaction ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not transaction_id:
            return False
        
        return bool(re.match(TRANSACTION_ID_REGEX, transaction_id))
    
    @staticmethod
    def generate_checksum(data: Dict) -> str:
        """
        Generate a checksum for data integrity verification
        
        Args:
            data: Dictionary of data to generate checksum for
            
        Returns:
            Checksum string
        """
        # Convert data to sorted JSON string for consistent hashing
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()


# Generate unique identifiers
def generate_account_number() -> str:
    """
    Generate a unique account number
    
    Returns:
        Account number in format XXXXX-XXXXX-XXXXX
    """
    # Use uuid to generate random numbers
    random_num = uuid.uuid4().int
    
    # Format as account number
    part1 = str(random_num)[:5]
    part2 = str(random_num)[5:10]
    part3 = str(random_num)[10:15]
    
    return f"{part1}-{part2}-{part3}"


def generate_transaction_id() -> str:
    """
    Generate a unique transaction ID
    
    Returns:
        Transaction ID in format TXXXXXXXXXX
    """
    timestamp = int(datetime.datetime.now().timestamp())
    random_part = uuid.uuid4().int % 10000
    
    return f"T{timestamp}{random_part:04d}"


def generate_reference_number(prefix: str = "REF") -> str:
    """
    Generate a reference number for various banking operations
    
    Args:
        prefix: Prefix for the reference number
        
    Returns:
        Reference number
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = str(uuid.uuid4().int)[:4]
    
    return f"{prefix}-{timestamp}-{random_part}"


# Audit logging function
def audit_log(
    action: str, 
    module: str, 
    user_id: str,
    data: Dict = None,
    status: str = "SUCCESS",
    entity_type: str = None,
    entity_id: str = None
) -> None:
    """
    Log an audit event for regulatory compliance
    
    Args:
        action: Action being performed (e.g., "CREATE", "UPDATE", "DELETE")
        module: Module where action is performed
        user_id: ID of user performing the action
        data: Optional data to log
        status: Status of the action ("SUCCESS" or "FAILURE")
        entity_type: Type of entity being acted upon
        entity_id: ID of entity being acted upon
    """
    timestamp = datetime.datetime.now().isoformat()
    
    log_data = {
        "timestamp": timestamp,
        "action": action,
        "module": module,
        "user_id": user_id,
        "status": status,
    }
    
    if entity_type:
        log_data["entity_type"] = entity_type
        
    if entity_id:
        log_data["entity_id"] = entity_id
        
    if data:
        log_data["data"] = data
        
    logger.info(f"AUDIT: {json.dumps(log_data)}")


# Currency conversion utility
def convert_currency(amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
    """
    Convert amount from one currency to another
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currency: Target currency code
        
    Returns:
        Converted amount
        
    Note:
        In a real implementation, this would call an external service
        for current exchange rates.
    """
    # This is a simplified implementation
    # In production, would use an external service for real-time rates
    exchange_rates = {
        "USD": {
            "INR": Decimal("83.50"),
            "EUR": Decimal("0.92"),
            "GBP": Decimal("0.79"),
            "JPY": Decimal("150.20")
        },
        "INR": {
            "USD": Decimal("0.012"),
            "EUR": Decimal("0.011"),
            "GBP": Decimal("0.0095"),
            "JPY": Decimal("1.80")
        },
        "EUR": {
            "USD": Decimal("1.09"),
            "INR": Decimal("91.20"),
            "GBP": Decimal("0.86"),
            "JPY": Decimal("164.25")
        }
    }
    
    # If same currency, return amount
    if from_currency == to_currency:
        return amount
    
    # If direct conversion available
    if from_currency in exchange_rates and to_currency in exchange_rates[from_currency]:
        return amount * exchange_rates[from_currency][to_currency]
    
    # If inverse conversion available
    if to_currency in exchange_rates and from_currency in exchange_rates[to_currency]:
        return amount / exchange_rates[to_currency][from_currency]
    
    # If no direct conversion, try via USD
    if from_currency in exchange_rates and "USD" in exchange_rates[from_currency]:
        usd_amount = amount * exchange_rates[from_currency]["USD"]
        if to_currency in exchange_rates["USD"]:
            return usd_amount * exchange_rates["USD"][to_currency]
    
    # If conversion not available
    raise ValueError(f"Currency conversion not available: {from_currency} to {to_currency}")
