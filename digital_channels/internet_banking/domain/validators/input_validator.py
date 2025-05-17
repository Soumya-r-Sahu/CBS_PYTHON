"""
Input validators for the Internet Banking domain.
Contains validation logic for user inputs.
"""
import re
from typing import List, Optional, Tuple


class InputValidator:
    """Validator for user inputs in the Internet Banking domain."""
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """
        Validate an email address.
        
        Args:
            email: The email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Simple regex for email validation
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not email:
            return False, "Email cannot be empty"
            
        if not re.match(pattern, email):
            return False, "Invalid email format"
            
        return True, ""
    
    @staticmethod
    def validate_phone_number(phone: str) -> Tuple[bool, str]:
        """
        Validate a phone number.
        
        Args:
            phone: The phone number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Simple regex for phone validation (international format)
        pattern = r'^\+?[1-9]\d{1,14}$'
        
        if not phone:
            return False, "Phone number cannot be empty"
            
        # Remove spaces and dashes for validation
        clean_phone = re.sub(r'[\s-]', '', phone)
        
        if not re.match(pattern, clean_phone):
            return False, "Invalid phone number format"
            
        return True, ""
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        Validate a username.
        
        Args:
            username: The username to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not username:
            return False, "Username cannot be empty"
            
        if len(username) < 5:
            return False, "Username must be at least 5 characters long"
            
        # Only allow alphanumeric characters, dots, and underscores
        pattern = r'^[a-zA-Z0-9._]+$'
        if not re.match(pattern, username):
            return False, "Username can only contain letters, numbers, dots, and underscores"
            
        return True, ""
    
    @staticmethod
    def validate_ip_address(ip: str) -> Tuple[bool, str]:
        """
        Validate an IP address.
        
        Args:
            ip: The IP address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # IPv4 pattern
        ipv4_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        
        if not ip:
            return False, "IP address cannot be empty"
            
        match = re.match(ipv4_pattern, ip)
        if not match:
            return False, "Invalid IP address format"
            
        # Check each octet is between 0 and 255
        for octet in match.groups():
            if int(octet) > 255:
                return False, "Invalid IP address (octet > 255)"
                
        return True, ""
