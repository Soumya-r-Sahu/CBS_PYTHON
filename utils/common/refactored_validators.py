"""
Refactored Validators Module for CBS_PYTHON

This module provides a more DRY approach to validation with cleaner patterns
and reusable validator classes that follow consistent patterns.
"""

import re
import inspect
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable, Tuple, TypeVar, Generic
from datetime import datetime, date
from decimal import Decimal

# Import the unified error handling
from utils.unified_error_handling import ValidationException, ErrorCodes

# Type variable for generics
T = TypeVar('T')


class Validator(Generic[T], ABC):
    """
    Abstract base class for all validators.
    
    This provides a common interface for all validators and enables
    composition and chaining of validators.
    """
    
    @abstractmethod
    def validate(self, value: T) -> Tuple[bool, Optional[str]]:
        """
        Validate a value.
        
        Args:
            value: The value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    def __call__(self, value: T) -> Tuple[bool, Optional[str]]:
        """Make the validator callable"""
        return self.validate(value)
    
    def __and__(self, other: 'Validator[T]') -> 'CompositeValidator[T]':
        """Create an AND validator (both must pass)"""
        return CompositeValidator([self, other], require_all=True)
    
    def __or__(self, other: 'Validator[T]') -> 'CompositeValidator[T]':
        """Create an OR validator (at least one must pass)"""
        return CompositeValidator([self, other], require_all=False)
    
    def validate_or_raise(self, value: T, field_name: Optional[str] = None) -> T:
        """
        Validate a value and raise ValidationException if invalid.
        
        Args:
            value: The value to validate
            field_name: The name of the field being validated
            
        Returns:
            The original value if valid
            
        Raises:
            ValidationException: If the value is invalid
        """
        is_valid, error_message = self.validate(value)
        if not is_valid and error_message:
            raise ValidationException(
                message=error_message,
                field=field_name,
                error_code=ErrorCodes.VALIDATION_ERROR
            )
        return value


class CompositeValidator(Validator[T]):
    """
    Combines multiple validators using AND or OR logic.
    """
    
    def __init__(self, validators: List[Validator[T]], require_all: bool = True):
        """
        Initialize with list of validators.
        
        Args:
            validators: List of validators to combine
            require_all: If True, all validators must pass (AND logic)
                         If False, at least one must pass (OR logic)
        """
        self.validators = validators
        self.require_all = require_all
    
    def validate(self, value: T) -> Tuple[bool, Optional[str]]:
        """
        Validate using composite logic.
        
        Args:
            value: The value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        errors = []
        
        for validator in self.validators:
            is_valid, error = validator.validate(value)
            
            if self.require_all:
                # AND logic - fail on first error
                if not is_valid:
                    return False, error
            else:
                # OR logic - succeed on first success
                if is_valid:
                    return True, None
                errors.append(error)
        
        if self.require_all:
            # All validators passed for AND logic
            return True, None
        else:
            # All validators failed for OR logic
            return False, " OR ".join(err for err in errors if err)


class PatternValidator(Validator[str]):
    """
    Validates string against a regex pattern.
    """
    
    def __init__(self, pattern: str, error_message: str):
        """
        Initialize with regex pattern.
        
        Args:
            pattern: Regular expression pattern
            error_message: Error message when validation fails
        """
        self.pattern = re.compile(pattern)
        self.error_message = error_message
    
    def validate(self, value: str) -> Tuple[bool, Optional[str]]:
        """
        Validate string against pattern.
        
        Args:
            value: String to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not value:
            return False, "Value cannot be empty"
        
        if not isinstance(value, str):
            return False, f"Expected string but got {type(value).__name__}"
        
        if self.pattern.match(value):
            return True, None
        return False, self.error_message


class RangeValidator(Validator[Union[int, float, Decimal]]):
    """
    Validates numeric value within a range.
    """
    
    def __init__(self, min_value: Optional[float] = None, max_value: Optional[float] = None):
        """
        Initialize with range.
        
        Args:
            min_value: Minimum allowed value (inclusive)
            max_value: Maximum allowed value (inclusive)
        """
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Union[int, float, Decimal]) -> Tuple[bool, Optional[str]]:
        """
        Validate numeric value within range.
        
        Args:
            value: Numeric value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return False, f"Expected numeric value but got {type(value).__name__}"
        
        if self.min_value is not None and numeric_value < self.min_value:
            return False, f"Value must be at least {self.min_value}"
        
        if self.max_value is not None and numeric_value > self.max_value:
            return False, f"Value must be at most {self.max_value}"
        
        return True, None


class LengthValidator(Validator[Union[str, List, Dict]]):
    """
    Validates length of string, list or dict.
    """
    
    def __init__(self, min_length: Optional[int] = None, max_length: Optional[int] = None):
        """
        Initialize with length constraints.
        
        Args:
            min_length: Minimum allowed length (inclusive)
            max_length: Maximum allowed length (inclusive)
        """
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, value: Union[str, List, Dict]) -> Tuple[bool, Optional[str]]:
        """
        Validate length of value.
        
        Args:
            value: Value to validate length
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return False, "Value cannot be None"
        
        try:
            length = len(value)
        except (TypeError, AttributeError):
            return False, f"Cannot determine length of type {type(value).__name__}"
        
        if self.min_length is not None and length < self.min_length:
            return False, f"Length must be at least {self.min_length}"
        
        if self.max_length is not None and length > self.max_length:
            return False, f"Length must be at most {self.max_length}"
        
        return True, None


class DateValidator(Validator[Union[str, datetime, date]]):
    """
    Validates date values.
    """
    
    def __init__(
        self, 
        min_date: Optional[Union[str, datetime, date]] = None,
        max_date: Optional[Union[str, datetime, date]] = None,
        format_str: str = "%Y-%m-%d"
    ):
        """
        Initialize with date constraints.
        
        Args:
            min_date: Minimum allowed date (inclusive)
            max_date: Maximum allowed date (inclusive)
            format_str: Date format string for parsing str inputs
        """
        self.min_date = self._to_date(min_date, format_str) if min_date else None
        self.max_date = self._to_date(max_date, format_str) if max_date else None
        self.format_str = format_str
    
    def _to_date(self, value: Union[str, datetime, date], format_str: str) -> date:
        """Convert value to date"""
        if isinstance(value, datetime):
            return value.date()
        elif isinstance(value, date):
            return value
        elif isinstance(value, str):
            return datetime.strptime(value, format_str).date()
        else:
            raise TypeError(f"Cannot convert {type(value).__name__} to date")
    
    def validate(self, value: Union[str, datetime, date]) -> Tuple[bool, Optional[str]]:
        """
        Validate date value.
        
        Args:
            value: Date value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            date_value = self._to_date(value, self.format_str)
        except (TypeError, ValueError):
            return False, f"Invalid date format, expected format: {self.format_str}"
        
        if self.min_date and date_value < self.min_date:
            return False, f"Date must be on or after {self.min_date.strftime(self.format_str)}"
        
        if self.max_date and date_value > self.max_date:
            return False, f"Date must be on or before {self.max_date.strftime(self.format_str)}"
        
        return True, None


# Common validators for banking applications
ACCOUNT_NUMBER_VALIDATOR = PatternValidator(
    pattern=r'^[0-9]{10,16}$',
    error_message="Account number must be 10-16 digits"
)

CARD_NUMBER_VALIDATOR = PatternValidator(
    pattern=r'^[0-9]{16}$',
    error_message="Card number must be 16 digits"
)

IFSC_CODE_VALIDATOR = PatternValidator(
    pattern=r'^[A-Z]{4}0[A-Z0-9]{6}$',
    error_message="Invalid IFSC code format"
)

EMAIL_VALIDATOR = PatternValidator(
    pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    error_message="Invalid email address format"
)

MOBILE_NUMBER_VALIDATOR = PatternValidator(
    pattern=r'^[6-9][0-9]{9}$',
    error_message="Mobile number must be 10 digits starting with 6-9"
)

AMOUNT_VALIDATOR = RangeValidator(min_value=0.01, max_value=10000000.0)

# Helper method for validating multiple fields
def validate_fields(data: Dict[str, Any], validators: Dict[str, Validator]) -> List[Tuple[str, str]]:
    """
    Validate multiple fields with corresponding validators.
    
    Args:
        data: Dictionary of field values
        validators: Dictionary mapping field names to validators
        
    Returns:
        List of (field_name, error_message) tuples for invalid fields
    """
    errors = []
    
    for field_name, validator in validators.items():
        if field_name in data:
            is_valid, error = validator.validate(data[field_name])
            if not is_valid and error:
                errors.append((field_name, error))
    
    return errors


class SchemaValidator(Validator[Dict[str, Any]]):
    """
    Validates a dictionary against a schema of field validators.
    """
    
    def __init__(self, schema: Dict[str, Validator], require_all_fields: bool = False):
        """
        Initialize with schema.
        
        Args:
            schema: Dictionary mapping field names to validators
            require_all_fields: If True, all fields in schema must be present
        """
        self.schema = schema
        self.require_all_fields = require_all_fields
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate dictionary against schema.
        
        Args:
            data: Dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(data, dict):
            return False, f"Expected dictionary but got {type(data).__name__}"
        
        errors = []
        
        for field_name, validator in self.schema.items():
            if field_name in data:
                is_valid, error = validator.validate(data[field_name])
                if not is_valid and error:
                    errors.append(f"{field_name}: {error}")
            elif self.require_all_fields:
                errors.append(f"{field_name}: Required field is missing")
        
        if errors:
            return False, "; ".join(errors)
        return True, None
