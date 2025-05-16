"""
Request Validation Middleware for Core Banking System

This middleware validates incoming requests against defined schemas,
ensuring data integrity before processing.
"""

import logging
import json
from functools import wraps
from flask import request, jsonify

# Configure logger
logger = logging.getLogger(__name__)


def validate_json_request(schema):
    """
    Decorator to validate JSON request body against a schema.
    
    Args:
        schema: The schema to validate against (e.g., marshmallow schema)
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check Content-Type header
            if request.content_type != 'application/json':
                logger.warning(f"Invalid content type: {request.content_type}")
                return jsonify({
                    "error": "Invalid Content-Type",
                    "message": "Content-Type must be application/json"
                }), 415
            
            # Parse JSON
            try:
                json_data = request.get_json()
                if json_data is None:
                    raise ValueError("Empty JSON body")
            except Exception as e:
                logger.warning(f"Invalid JSON: {str(e)}")
                return jsonify({
                    "error": "Invalid JSON",
                    "message": "Request body must be valid JSON"
                }), 400
            
            # Validate against schema
            errors = schema.validate(json_data)
            if errors:
                logger.warning(f"Schema validation failed: {errors}")
                return jsonify({
                    "error": "Validation Error",
                    "details": errors
                }), 400
            
            # Validation passed, call the original function
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def sanitize_input(f):
    """
    Decorator to sanitize input data to prevent injection attacks.
    
    Args:
        f: The function to wrap
        
    Returns:
        The wrapped function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # For GET requests, sanitize query parameters
        if request.method == 'GET':
            for key, value in request.args.items():
                # Basic sanitization (replace with more robust solution in production)
                if isinstance(value, str) and any(char in value for char in ['<', '>', ';', '--', '/*', '*/']):
                    logger.warning(f"Potentially malicious input detected: {value}")
                    return jsonify({"error": "Invalid input detected"}), 400
        
        # For POST/PUT requests, sanitize JSON body
        elif request.method in ['POST', 'PUT', 'PATCH'] and request.is_json:
            json_data = request.get_json()
            # Check if there are any suspicious patterns in string values
            if _check_suspicious_patterns(json_data):
                logger.warning(f"Potentially malicious JSON input detected")
                return jsonify({"error": "Invalid input detected"}), 400
        
        # Continue processing the request
        return f(*args, **kwargs)
    
    return decorated_function


def _check_suspicious_patterns(data):
    """
    Recursively check for suspicious patterns in data structure.
    
    Args:
        data: Data to check
        
    Returns:
        bool: True if suspicious patterns found, False otherwise
    """
    suspicious_patterns = ['<script>', '<?php', 'eval(', '<!--', '-->', ';--', '/*', '*/']
    
    if isinstance(data, dict):
        for key, value in data.items():
            if _check_suspicious_patterns(value):
                return True
    elif isinstance(data, list):
        for item in data:
            if _check_suspicious_patterns(item):
                return True
    elif isinstance(data, str):
        for pattern in suspicious_patterns:
            if pattern.lower() in data.lower():
                return True
    
    return False
