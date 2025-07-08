"""
GDPR Compliance Utilities

This module provides utilities for ensuring GDPR compliance when handling
Personally Identifiable Information (PII) in the Core Banking System.
It includes functions for masking, encrypting, and logging PII access.
"""

import re
import json
import logging
import hashlib
import datetime
from typing import Dict, Any, List, Optional, Union, Tuple, Set

# Set up logger
logger = logging.getLogger(__name__)

# Define PII fields to mask by default
DEFAULT_PII_FIELDS = {
    'email', 'phone', 'phone_number', 'mobile', 'mobile_number',
    'address', 'street', 'city', 'state', 'zip', 'zipcode', 'postal_code',
    'ssn', 'social_security', 'tax_id', 'passport', 'driver_license',
    'credit_card', 'card_number', 'cvv', 'expiry', 'birth_date', 'dob',
    'age', 'gender', 'first_name', 'last_name', 'middle_name', 'full_name'
}

class PIIHandler:
    """
    Handler for Personally Identifiable Information (PII) in accordance with GDPR.
    """
    
    def __init__(self, additional_pii_fields: Set[str] = None):
        """
        Initialize PII Handler.
        
        Args:
            additional_pii_fields: Additional PII field names to mask
        """
        self.pii_fields = DEFAULT_PII_FIELDS.copy()
        
        if additional_pii_fields:
            self.pii_fields.update(additional_pii_fields)
    
    def mask_pii(self, data: Dict[str, Any], fields_to_mask: Set[str] = None) -> Dict[str, Any]:
        """
        Mask PII in a dictionary.
        
        Args:
            data: Dictionary containing data to mask
            fields_to_mask: Specific fields to mask (defaults to all PII fields)
            
        Returns:
            Dictionary with masked PII
        """
        if not isinstance(data, dict):
            return {}
        
        # Use default PII fields if none specified
        if fields_to_mask is None:
            fields_to_mask = self.pii_fields
        
        result = {}
        
        for key, value in data.items():
            # Check if key is a PII field (case-insensitive)
            is_pii = key.lower() in {f.lower() for f in fields_to_mask}
            
            # Recursively mask PII in nested dictionaries
            if isinstance(value, dict):
                result[key] = self.mask_pii(value, fields_to_mask)
            # Process list values
            elif isinstance(value, list):
                result[key] = [
                    self.mask_pii(item, fields_to_mask) if isinstance(item, dict) 
                    else self._mask_value(item) if is_pii else item 
                    for item in value
                ]
            # Mask PII values
            elif is_pii and value is not None:
                result[key] = self._mask_value(value)
            # Keep non-PII values as is
            else:
                result[key] = value
        
        return result
    
    def _mask_value(self, value: Any) -> str:
        """
        Mask a single PII value.
        
        Args:
            value: Value to mask
            
        Returns:
            Masked value
        """
        if value is None:
            return None
        
        # Convert to string
        value_str = str(value)
        
        # Different masking strategies for different types of data
        
        # Email: mask everything except first character and domain
        if '@' in value_str and '.' in value_str.split('@')[1]:
            username, domain = value_str.split('@')
            if len(username) > 1:
                masked_username = username[0] + '*' * (len(username) - 1)
                return f"{masked_username}@{domain}"
        
        # Phone number: mask middle digits
        if re.match(r'^\+?[\d\s\(\)\-\.]+$', value_str):
            # Keep first 3 and last 2 digits visible
            if len(value_str) > 5:
                visible_prefix = value_str[:3]
                visible_suffix = value_str[-2:]
                masked_part = '*' * (len(value_str) - 5)
                return f"{visible_prefix}{masked_part}{visible_suffix}"
        
        # Credit card: mask all except last 4 digits
        if re.match(r'^[\d\s\-]+$', value_str) and len(re.sub(r'[\s\-]', '', value_str)) >= 13:
            # Keep only last 4 digits visible
            visible_suffix = value_str[-4:]
            masked_part = '*' * (len(value_str) - 4)
            return f"{masked_part}{visible_suffix}"
        
        # Default masking: keep first and last character, mask the rest
        if len(value_str) > 2:
            return value_str[0] + '*' * (len(value_str) - 2) + value_str[-1]
        # For very short strings, mask everything
        else:
            return '*' * len(value_str)
    
    def log_pii_access(self, 
                      user_id: str, 
                      access_type: str, 
                      data_type: str, 
                      reason: str,
                      record_ids: List[str] = None) -> None:
        """
        Log access to PII for GDPR compliance.
        
        Args:
            user_id: ID of user accessing the data
            access_type: Type of access (view, edit, export, etc.)
            data_type: Type of data being accessed
            reason: Business reason for access
            record_ids: List of record IDs accessed
        """
        timestamp = datetime.datetime.now().isoformat()
        
        log_entry = {
            'timestamp': timestamp,
            'user_id': user_id,
            'access_type': access_type,
            'data_type': data_type,
            'reason': reason,
            'record_ids': record_ids or []
        }
        
        # Log the access with a special logger for GDPR auditing
        logger.info(f"GDPR_ACCESS_LOG: {json.dumps(log_entry)}")
    
    def anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fully anonymize data by replacing PII with hashed values.
        
        Args:
            data: Dictionary containing data to anonymize
            
        Returns:
            Dictionary with anonymized data
        """
        if not isinstance(data, dict):
            return {}
        
        result = {}
        
        for key, value in data.items():
            # Check if key is a PII field (case-insensitive)
            is_pii = key.lower() in {f.lower() for f in self.pii_fields}
            
            # Recursively anonymize PII in nested dictionaries
            if isinstance(value, dict):
                result[key] = self.anonymize_data(value)
            # Process list values
            elif isinstance(value, list):
                result[key] = [
                    self.anonymize_data(item) if isinstance(item, dict) 
                    else self._hash_value(item) if is_pii else item 
                    for item in value
                ]
            # Anonymize PII values
            elif is_pii and value is not None:
                result[key] = self._hash_value(value)
            # Keep non-PII values as is
            else:
                result[key] = value
        
        return result
    
    def _hash_value(self, value: Any) -> str:
        """
        Hash a value for anonymization.
        
        Args:
            value: Value to hash
            
        Returns:
            Hashed value
        """
        if value is None:
            return None
        
        # Convert to string and hash
        value_str = str(value)
        hashed = hashlib.sha256(value_str.encode()).hexdigest()
        
        return hashed

# Create singleton instance
pii_handler = PIIHandler()
