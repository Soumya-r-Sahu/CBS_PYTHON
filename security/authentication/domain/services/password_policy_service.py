"""
Password Policy Service

This module defines the domain service for password policy enforcement.
It encapsulates business rules and policies related to password management.
"""

import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict


class PasswordPolicyService:
    """
    Domain service for password policy enforcement
    
    This service encapsulates password policy rules and validation logic
    that doesn't belong to a specific entity.
    """
    
    def __init__(
        self,
        min_length: int = 12,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = True,
        max_age_days: int = 90,
        prevent_reuse_count: int = 5
    ):
        """
        Initialize with configurable policy parameters
        
        Args:
            min_length: Minimum password length
            require_uppercase: Whether uppercase letters are required
            require_lowercase: Whether lowercase letters are required
            require_digit: Whether digits are required
            require_special: Whether special characters are required
            max_age_days: Maximum password age in days
            prevent_reuse_count: Number of previous passwords to prevent reusing
        """
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special
        self.max_age_days = max_age_days
        self.prevent_reuse_count = prevent_reuse_count
    
    def validate_password_strength(self, password: str) -> Dict[str, bool]:
        """
        Validate if a password meets security requirements
        
        Args:
            password: Password to validate
            
        Returns:
            Dictionary with validation results for each rule
        """
        results = {
            "valid": True,
            "length_valid": len(password) >= self.min_length,
            "uppercase_valid": not self.require_uppercase or bool(re.search(r'[A-Z]', password)),
            "lowercase_valid": not self.require_lowercase or bool(re.search(r'[a-z]', password)),
            "digit_valid": not self.require_digit or bool(re.search(r'\d', password)),
            "special_valid": not self.require_special or bool(re.search(r'[^A-Za-z0-9]', password)),
        }
        
        # Set overall validity
        results["valid"] = all([
            results["length_valid"],
            results["uppercase_valid"],
            results["lowercase_valid"],
            results["digit_valid"],
            results["special_valid"]
        ])
        
        return results
    
    def is_password_expired(self, last_changed_date: datetime) -> bool:
        """
        Check if a password has expired
        
        Args:
            last_changed_date: When the password was last changed
            
        Returns:
            True if password has expired, False otherwise
        """
        if not self.max_age_days:  # No expiration if max_age_days is 0
            return False
            
        expiry_date = last_changed_date + timedelta(days=self.max_age_days)
        return datetime.now() > expiry_date
    
    def days_until_expiry(self, last_changed_date: datetime) -> int:
        """
        Calculate days until password expires
        
        Args:
            last_changed_date: When the password was last changed
            
        Returns:
            Number of days until expiry (negative if already expired)
        """
        if not self.max_age_days:  # No expiration if max_age_days is 0
            return 36500  # Return 100 years
            
        expiry_date = last_changed_date + timedelta(days=self.max_age_days)
        delta = expiry_date - datetime.now()
        return delta.days
    
    def can_reuse_password(
        self, 
        new_password: str,
        password_history: List[Dict[str, str]]
    ) -> bool:
        """
        Check if a new password can be used based on history
        
        Args:
            new_password: New password to check
            password_history: List of previous password hashes with salt
            
        Returns:
            True if password can be reused, False if it matches a recent password
        """
        # Implement this method in the infrastructure layer where
        # actual password verification happens
        return True  # Placeholder
    
    def generate_password_requirements_description(self) -> str:
        """
        Generate a human-readable description of password requirements
        
        Returns:
            String describing password requirements
        """
        requirements = [f"At least {self.min_length} characters"]
        
        if self.require_uppercase:
            requirements.append("At least one uppercase letter")
        
        if self.require_lowercase:
            requirements.append("At least one lowercase letter")
        
        if self.require_digit:
            requirements.append("At least one digit")
        
        if self.require_special:
            requirements.append("At least one special character")
        
        if self.max_age_days > 0:
            requirements.append(f"Must be changed every {self.max_age_days} days")
        
        if self.prevent_reuse_count > 0:
            requirements.append(f"Cannot reuse the last {self.prevent_reuse_count} passwords")
        
        return "Password requirements:\n- " + "\n- ".join(requirements)
