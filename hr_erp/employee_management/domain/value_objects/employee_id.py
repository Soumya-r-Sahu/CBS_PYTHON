"""
Employee ID Value Object

This module defines the EmployeeId value object which represents
a unique identifier for employees within the HR-ERP system.
"""

from dataclasses import dataclass
import re
from datetime import datetime


@dataclass(frozen=True)
class EmployeeId:
    """
    Value object representing an employee ID
    
    Employee IDs follow the format EMP-YYYY-NNNN where:
    - YYYY is the year of joining
    - NNNN is a sequential number
    
    This is an immutable value object with no side effects.
    """
    value: str
    
    def __post_init__(self):
        """Validate the employee ID format"""
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate employee ID format
        
        Raises:
            ValueError: If ID format is invalid
        """
        # Employee ID format: EMP-YYYY-NNNN
        pattern = r'^EMP-\d{4}-\d{4}$'
        if not re.match(pattern, self.value):
            raise ValueError(f"Invalid employee ID format: {self.value}")
        
        # Extract and validate year
        year_part = int(self.value.split('-')[1])
        current_year = datetime.now().year
        
        if year_part < 1900 or year_part > current_year:
            raise ValueError(f"Invalid year in employee ID: {year_part}")
    
    @classmethod
    def create(cls, year: int, number: int) -> 'EmployeeId':
        """
        Create a new employee ID
        
        Args:
            year: Year of joining
            number: Sequential number (1-9999)
            
        Returns:
            A new EmployeeId instance
        
        Raises:
            ValueError: If parameters are invalid
        """
        if number < 1 or number > 9999:
            raise ValueError("Employee number must be between 1 and 9999")
            
        current_year = datetime.now().year
        if year < 1900 or year > current_year:
            raise ValueError(f"Year must be between 1900 and {current_year}")
        
        # Format: EMP-YYYY-NNNN
        id_value = f"EMP-{year:04d}-{number:04d}"
        return cls(id_value)
    
    def __str__(self) -> str:
        """String representation of the employee ID"""
        return self.value
    
    def get_year(self) -> int:
        """Extract the year from the employee ID"""
        return int(self.value.split('-')[1])
    
    def get_number(self) -> int:
        """Extract the sequential number from the employee ID"""
        return int(self.value.split('-')[2])
