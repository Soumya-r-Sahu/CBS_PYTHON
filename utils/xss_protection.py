"""
Cross-Site Scripting (XSS) Prevention Utilities

This module provides utilities for preventing XSS attacks in the Core Banking System.
It includes functions for sanitizing user input, escaping HTML entities, and
validating input against allowlists.
"""

import re
import html
import logging
import bleach
from typing import List, Dict, Any, Optional, Union

# Set up logger
logger = logging.getLogger(__name__)

# Default allowed HTML tags and attributes for rich text
DEFAULT_ALLOWED_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 
    'p', 'strong', 'ul'
]

DEFAULT_ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'abbr': ['title'],
    'acronym': ['title']
}

def escape_html(content: str) -> str:
    """
    Escape HTML entities to prevent XSS attacks.
    
    Args:
        content: The content to escape
        
    Returns:
        Escaped content
    """
    if content is None:
        return ""
    
    return html.escape(str(content))

def sanitize_html(content: str, 
                 allowed_tags: List[str] = None, 
                 allowed_attributes: Dict[str, List[str]] = None) -> str:
    """
    Sanitize HTML content to prevent XSS attacks.
    
    Args:
        content: The HTML content to sanitize
        allowed_tags: List of allowed HTML tags
        allowed_attributes: Dictionary of allowed attributes for each tag
        
    Returns:
        Sanitized HTML content
    """
    if content is None:
        return ""
    
    # Use defaults if not provided
    if allowed_tags is None:
        allowed_tags = DEFAULT_ALLOWED_TAGS
    
    if allowed_attributes is None:
        allowed_attributes = DEFAULT_ALLOWED_ATTRIBUTES
    
    # Use bleach to sanitize HTML
    return bleach.clean(
        str(content),
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )

def sanitize_user_input(content: str, allow_html: bool = False) -> str:
    """
    Sanitize user input to prevent XSS attacks.
    
    Args:
        content: The user input to sanitize
        allow_html: Whether to allow some HTML tags
        
    Returns:
        Sanitized content
    """
    if content is None:
        return ""
    
    # Convert to string
    content = str(content)
    
    # If HTML is not allowed, escape everything
    if not allow_html:
        return escape_html(content)
    
    # If HTML is allowed, sanitize using bleach
    return sanitize_html(content)

def is_valid_input(content: str, pattern: str = None, max_length: int = None) -> bool:
    """
    Validate user input against a regex pattern and/or maximum length.
    
    Args:
        content: The content to validate
        pattern: Regex pattern to match against
        max_length: Maximum allowed length
        
    Returns:
        True if valid, False otherwise
    """
    if content is None:
        return False
    
    # Convert to string
    content = str(content)
    
    # Check length
    if max_length is not None and len(content) > max_length:
        return False
    
    # Check pattern
    if pattern is not None and not re.match(pattern, content):
        return False
    
    return True

def create_safe_json_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a safe JSON data structure by recursively sanitizing values.
    
    Args:
        data: Dictionary of data to sanitize
        
    Returns:
        Dictionary with sanitized values
    """
    if not isinstance(data, dict):
        return {}
    
    result = {}
    
    for key, value in data.items():
        # Sanitize the key
        safe_key = escape_html(str(key))
        
        # Recursively sanitize dictionary values
        if isinstance(value, dict):
            result[safe_key] = create_safe_json_data(value)
        # Sanitize list values
        elif isinstance(value, list):
            result[safe_key] = [
                create_safe_json_data(item) if isinstance(item, dict) 
                else escape_html(str(item)) 
                for item in value
            ]
        # Sanitize string values
        elif isinstance(value, str):
            result[safe_key] = escape_html(value)
        # Keep other types as is (numbers, booleans, etc.)
        else:
            result[safe_key] = value
    
    return result
