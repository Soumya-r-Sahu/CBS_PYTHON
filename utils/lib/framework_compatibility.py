"""
Framework Detection and Compatibility Utilities

This module provides utilities for detecting and supporting different frontend frameworks
that interact with the CBS_PYTHON backend. It helps ensure seamless integration with
Django, React, Angular, Vue.js and other frameworks.
"""

import re
from typing import Dict, Any, Optional, List, Tuple

def detect_framework_from_headers(headers: Dict[str, str]) -> str:
    """
    Detect the frontend framework based on request headers
    
    Args:
        headers: HTTP request headers dictionary
    
    Returns:
        Detected framework name or 'generic' if unknown
    """
    user_agent = headers.get('User-Agent', '').lower()
    
    # Check for framework-specific headers
    if 'X-Django-CSRF-Token' in headers or 'csrftoken' in headers.get('Cookie', ''):
        return 'django'
        
    if 'X-Requested-By' in headers and headers['X-Requested-By'] == 'Angular':
        return 'angular'
        
    # Check user agent for clues
    if 'react' in user_agent:
        return 'react'
        
    if 'vue' in user_agent:
        return 'vue'
        
    # Default to generic
    return 'generic'

def format_response_for_framework(data: Any, framework: str) -> Dict[str, Any]:
    """
    Format response data according to the detected frontend framework's expectations
    
    Args:
        data: The data to format
        framework: The detected framework
    
    Returns:
        Formatted response data
    """
    if framework == 'django':
        # Django REST Framework style response
        return {
            'status': 'success',
            'data': data
        }
        
    elif framework == 'angular':
        # Angular expects a specific format
        return {
            'success': True,
            'result': data,
            'error': None
        }
        
    elif framework == 'react':
        # Simple format for React
        return {
            'data': data,
            'error': None
        }
        
    elif framework == 'vue':
        # Vue.js format
        return {
            'ok': True,
            'data': data
        }
        
    # Generic format
    return {
        'result': data
    }

def format_error_for_framework(message: str, code: str, framework: str) -> Dict[str, Any]:
    """
    Format error response according to the detected frontend framework's expectations
    
    Args:
        message: Error message
        code: Error code
        framework: The detected framework
    
    Returns:
        Formatted error response
    """
    if framework == 'django':
        # Django REST Framework style error
        return {
            'status': 'error',
            'error': {
                'message': message,
                'code': code
            }
        }
        
    elif framework == 'angular':
        # Angular error format
        return {
            'success': False,
            'result': None,
            'error': {
                'message': message,
                'code': code
            }
        }
        
    elif framework == 'react':
        # React error format
        return {
            'data': None,
            'error': {
                'message': message,
                'code': code
            }
        }
        
    elif framework == 'vue':
        # Vue.js error format
        return {
            'ok': False,
            'error': {
                'message': message,
                'code': code
            }
        }
        
    # Generic error format
    return {
        'error': message,
        'code': code
    }

def convert_data_for_framework(data: Any, source_framework: str, target_framework: str) -> Any:
    """
    Convert data between different framework formats
    
    Args:
        data: The data to convert
        source_framework: Original framework format
        target_framework: Target framework format
    
    Returns:
        Converted data
    """
    # Extract the raw data from the source format
    raw_data = None
    
    if source_framework == 'django':
        raw_data = data.get('data', data)
    elif source_framework == 'angular':
        raw_data = data.get('result', data)
    elif source_framework == 'react':
        raw_data = data.get('data', data)
    elif source_framework == 'vue':
        raw_data = data.get('data', data)
    else:
        raw_data = data.get('result', data)
    
    # Format the raw data for the target framework
    return format_response_for_framework(raw_data, target_framework)

def get_compatibility_headers(framework: str) -> Dict[str, str]:
    """
    Get compatibility headers for different frameworks
    
    Args:
        framework: Target framework
    
    Returns:
        Dictionary of headers
    """
    headers = {
        'Content-Type': 'application/json'
    }
    
    if framework == 'angular':
        headers['X-Angular-Compatible'] = 'true'
    elif framework == 'react':
        headers['X-React-Compatible'] = 'true'
    elif framework == 'vue':
        headers['X-Vue-Compatible'] = 'true'
    
    return headers

def sanitize_data_for_framework(data: Any, framework: str) -> Any:
    """
    Sanitize data for a specific framework to prevent security issues
    
    Args:
        data: Data to sanitize
        framework: Target framework
    
    Returns:
        Sanitized data
    """
    # Framework-specific sanitization rules
    if framework == 'angular':
        # Angular has issues with certain characters in JSON
        if isinstance(data, str):
            # Escape potentially dangerous sequences for Angular
            return data.replace('</', '<\\/')
    
    # Common sanitization for all frameworks
    return data
