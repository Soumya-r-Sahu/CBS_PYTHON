"""
UserId Value Object

This module defines the UserId value object which
represents a unique identifier for users in the system.
"""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class UserId:
    """
    Value object representing a user ID
    
    User IDs follow a specific format for different user types:
    - Internal users: INT-[numeric id]
    - External users: EXT-[numeric id]
    - System users: SYS-[numeric id]
    
    This is an immutable value object with validation logic.
    """
    value: str
    
    def __post_init__(self):
        """Validate the user ID format"""
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate user ID format
        
        Raises:
            ValueError: If user ID is invalid
        """
        if not self.value:
            raise ValueError("User ID cannot be empty")
            
        # Check format using regex
        pattern = r'^(INT|EXT|SYS)-\d+$'
        if not re.match(pattern, self.value):
            raise ValueError(
                "User ID must follow format: [INT|EXT|SYS]-[numeric_id]"
            )
    
    def is_internal(self) -> bool:
        """
        Check if this is an internal user ID
        
        Returns:
            True if internal user ID, False otherwise
        """
        return self.value.startswith("INT-")
    
    def is_external(self) -> bool:
        """
        Check if this is an external user ID
        
        Returns:
            True if external user ID, False otherwise
        """
        return self.value.startswith("EXT-")
    
    def is_system(self) -> bool:
        """
        Check if this is a system user ID
        
        Returns:
            True if system user ID, False otherwise
        """
        return self.value.startswith("SYS-")
    
    def numeric_part(self) -> int:
        """
        Get the numeric part of the user ID
        
        Returns:
            Numeric part as integer
        """
        # Extract everything after the hyphen
        return int(self.value.split('-')[1])
