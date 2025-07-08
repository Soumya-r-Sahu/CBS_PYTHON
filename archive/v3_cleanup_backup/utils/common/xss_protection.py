"""
XSS Protection Utilities for Core Banking System

This module provides utilities for preventing Cross-Site Scripting (XSS) attacks
in the Core Banking System.
"""

import re
import html
import logging
import json
from typing import Dict, Any, List, Union

# Configure logger
logger = logging.getLogger(__name__)

# HTML and JavaScript tag patterns
HTML_TAG_PATTERN = re.compile(r'<[^>]*>')
JAVASCRIPT_PATTERN = re.compile(r'javascript:', re.IGNORECASE)
EVENT_HANDLER_PATTERN = re.compile(r'on\w+\s*=', re.IGNORECASE)
DATA_URI_PATTERN = re.compile(r'data:', re.IGNORECASE)

# Common XSS attack patterns
XSS_PATTERNS = [
    re.compile(r'<script.*?>.*?</script>', re.IGNORECASE | re.DOTALL),
    re.compile(r'<img.*?onerror=.*?>', re.IGNORECASE | re.DOTALL),
    re.compile(r'<iframe.*?>', re.IGNORECASE),
    re.compile(r'<object.*?>', re.IGNORECASE),
    re.compile(r'<embed.*?>', re.IGNORECASE),
    re.compile(r'<base.*?>', re.IGNORECASE),
    re.compile(r'<applet.*?>', re.IGNORECASE),
    re.compile(r'<link.*?>', re.IGNORECASE),
    re.compile(r'<style.*?>.*?</style>', re.IGNORECASE | re.DOTALL),
    re.compile(r'expression\s*\(', re.IGNORECASE)
]


def sanitize_html(text: str) -> str:
    """
    Sanitize HTML content by escaping special characters.
    
    Args:
        text: Text that may contain HTML
        
    Returns:
        Sanitized text with HTML escaped
    """
    if not text:
        return ""
    
    return html.escape(text)


def strip_tags(text: str) -> str:
    """
    Remove all HTML tags from text.
    
    Args:
        text: Text that may contain HTML tags
        
    Returns:
        Text with all HTML tags removed
    """
    if not text:
        return ""
    
    return HTML_TAG_PATTERN.sub('', text)


def detect_xss(text: str) -> bool:
    """
    Detect potential XSS attack in input text.
    
    Args:
        text: Text to check for XSS payloads
        
    Returns:
        True if potential XSS detected, False otherwise
    """
    if not text:
        return False
    
    # Check for JavaScript in URL
    if JAVASCRIPT_PATTERN.search(text):
        return True
    
    # Check for event handlers
    if EVENT_HANDLER_PATTERN.search(text):
        return True
    
    # Check for data URIs (potential for JavaScript execution)
    if DATA_URI_PATTERN.search(text):
        return True
    
    # Check common XSS patterns
    for pattern in XSS_PATTERNS:
        if pattern.search(text):
            return True
    
    return False


def sanitize_json(obj: Union[Dict, List, str, int, float, bool, None]) -> Union[Dict, List, str, int, float, bool, None]:
    """
    Recursively sanitize a JSON object to prevent XSS.
    
    Args:
        obj: JSON object to sanitize
        
    Returns:
        Sanitized JSON object
    """
    if isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json(item) for item in obj]
    elif isinstance(obj, str):
        return sanitize_html(obj)
    else:
        # Return non-string values unchanged
        return obj


def sanitize_query_params(params: Dict[str, str]) -> Dict[str, str]:
    """
    Sanitize query parameters to prevent XSS.
    
    Args:
        params: Dictionary of query parameters
        
    Returns:
        Dictionary with sanitized query parameters
    """
    return {k: sanitize_html(v) for k, v in params.items()}


def sanitize_url(url: str) -> str:
    """
    Sanitize a URL to prevent JavaScript injection and other attacks.
    
    Args:
        url: URL to sanitize
        
    Returns:
        Sanitized URL
    """
    if not url:
        return ""
    
    # Remove JavaScript protocol
    if JAVASCRIPT_PATTERN.search(url.lower()):
        return "#"
    
    # Remove data URIs
    if url.lower().startswith('data:'):
        return "#"
    
    # Remove newlines and carriage returns
    url = url.replace('\n', '').replace('\r', '')
    
    return url


def generate_content_security_policy(extra_directives: Dict[str, str] = None) -> str:
    """
    Generate a Content Security Policy header value.
    
    Args:
        extra_directives: Additional CSP directives to include
        
    Returns:
        CSP header value as string
    """
    # Default CSP directives
    directives = {
        "default-src": "'self'",
        "script-src": "'self'",
        "style-src": "'self'",
        "img-src": "'self'",
        "connect-src": "'self'",
        "font-src": "'self'",
        "object-src": "'none'",
        "media-src": "'self'",
        "frame-src": "'none'",
        "frame-ancestors": "'none'",
        "form-action": "'self'",
        "base-uri": "'none'"
    }
    
    # Add extra directives
    if extra_directives:
        directives.update(extra_directives)
    
    # Convert directives to string
    return "; ".join([f"{key} {value}" for key, value in directives.items()])


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent directory traversal and other attacks.
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return ""
    
    # Remove path separators and other dangerous characters
    dangerous_chars = ['/', '\\', '..', ':', '*', '?', '"', '<', '>', '|', ';', '$', '&', '!']
    for char in dangerous_chars:
        filename = filename.replace(char, '')
    
    # Keep only alphanumeric characters, dots, hyphens, and underscores
    filename = re.sub(r'[^\w\-\.]', '_', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename


def validate_redirect_url(url: str, allowed_hosts: List[str] = None) -> bool:
    """
    Validate that a redirect URL is safe.
    
    Args:
        url: URL to validate
        allowed_hosts: List of allowed hosts for redirects
        
    Returns:
        True if URL is safe, False otherwise
    """
    if not url:
        return False
    
    # Default allowed hosts if none provided
    allowed_hosts = allowed_hosts or ['localhost', '127.0.0.1']
    
    try:
        # Try to parse the URL
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        
        # Check for JavaScript protocol
        if parsed_url.scheme.lower() == 'javascript':
            return False
        
        # Check for data URI
        if parsed_url.scheme.lower() == 'data':
            return False
        
        # Allow relative URLs
        if not parsed_url.netloc:
            return True
        
        # Check against allowed hosts
        return any(parsed_url.netloc.endswith(host) for host in allowed_hosts)
    except Exception as e:
        logger.warning(f"Error validating redirect URL: {str(e)}")
        return False
