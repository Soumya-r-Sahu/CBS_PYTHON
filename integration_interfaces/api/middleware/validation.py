"""
Request validation middleware for Mobile Banking API

Provides input validation for API requests using Marshmallow schemas
"""

from flask import Flask, request, jsonify
from functools import wraps
import json
from marshmallow import Schema, ValidationError
import logging

# Set up logging
logger = logging.getLogger(__name__)

def setup_validation_middleware(app: Flask):
    """
    Set up request validation middleware
    
    Args:
        app: Flask application instance
    """
    # Nothing to initialize at the app level
    pass

def validate_request_schema(schema_class):
    """
    Decorator for validating request data against a Marshmallow schema
    
    Args:
        schema_class: A Marshmallow Schema class to use for validation
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                # Get JSON data from request
                json_data = request.get_json()
                if not json_data:
                    return jsonify({
                        'status': 'FAILED',
                        'message': 'No JSON data provided',
                        'errors': {'json': 'Missing request data'}
                    }), 400
                
                try:
                    # Create schema instance
                    schema = schema_class()
                    
                    # Validate data against schema
                    result = schema.load(json_data)
                    
                    # Add the validated data to the request context
                    request.validated_data = result
                    
                    return f(*args, **kwargs)
                    
                except ValidationError as e:
                    logger.warning(f"Validation error: {e.messages}")
                    return jsonify({
                        'status': 'FAILED',
                        'message': 'Validation error',
                        'errors': e.messages
                    }), 400
            else:
                # For GET and other methods, pass through
                return f(*args, **kwargs)
                
        return decorated_function
        
    return decorator

def validate_query_params(schema_class):
    """
    Decorator for validating query parameters against a Marshmallow schema
    
    Args:
        schema_class: A Marshmallow Schema class to use for validation
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get query parameters
            query_data = {k: v for k, v in request.args.items()}
            
            try:
                # Create schema instance
                schema = schema_class()
                
                # Validate query params against schema
                result = schema.load(query_data)
                
                # Add the validated data to the request context
                request.validated_query = result
                
                return f(*args, **kwargs)
                
            except ValidationError as e:
                logger.warning(f"Validation error in query parameters: {e.messages}")
                return jsonify({
                    'status': 'FAILED',
                    'message': 'Validation error in query parameters',
                    'errors': e.messages
                }), 400
                
        return decorated_function
        
    return decorator

# Legacy function for backward compatibility
def validate_schema(schema):
    """
    Legacy decorator for validating request data against jsonschema
    
    Args:
        schema: JSON schema for validation
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                json_data = request.get_json()
                
                if not json_data:
                    return jsonify({
                        'status': 'FAILED',
                        'message': 'No JSON data provided',
                        'errors': {'json': 'Missing request data'}
                    }), 400
                    
                try:
                    from jsonschema import validate as jsonschema_validate
                    jsonschema_validate(instance=json_data, schema=schema)
                    return f(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"JSON Schema validation error: {str(e)}")
                    return jsonify({
                        'status': 'FAILED',
                        'message': 'Validation error',
                        'errors': {'validation': str(e)}
                    }), 400
            else:
                return f(*args, **kwargs)
                
        return decorated_function
        
    return decorator

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
