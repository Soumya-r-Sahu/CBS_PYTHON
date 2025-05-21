"""
Request Validation Middleware

This module provides request validation functionality to ensure API
requests contain valid and properly formatted data.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from flask import Flask, request

# Try importing jsonschema, if not available use a simple validation fallback
try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    logging.warning("jsonschema not installed, using simple validation fallback")

# Configure logger
logger = logging.getLogger(__name__)


class RequestValidator:
    """
    Request validation middleware
    
    Validates incoming API requests against JSON schemas or custom rules
    to ensure they meet expected formats and constraints.
    """
    
    def __init__(self):
        """Initialize the validator"""
        self.app = None
        self.schemas = {}
    
    def init_app(self, app: Flask):
        """
        Initialize with Flask application
        
        Args:
            app: Flask application instance
        """
        self.app = app
    
    def register_schema(self, schema_name: str, schema: Dict[str, Any]):
        """
        Register a JSON schema for validation
        
        Args:
            schema_name: Name to identify the schema
            schema: JSON schema definition
        """
        if JSONSCHEMA_AVAILABLE:
            # Validate the schema itself
            try:
                jsonschema.Draft7Validator.check_schema(schema)
            except jsonschema.exceptions.SchemaError as e:
                logger.error(f"Invalid schema '{schema_name}': {str(e)}")
                return
        
        self.schemas[schema_name] = schema
        logger.info(f"Registered validation schema '{schema_name}'")
    
    def validate_request(self, req: request, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a request against a schema
        
        Args:
            req: Flask request object
            schema: Schema to validate against
            
        Returns:
            Dict with validation results
        """
        # Get request data
        try:
            if req.is_json:
                data = req.get_json()
            else:
                data = req.form.to_dict()
                
                # If there are files, add them to the data
                if req.files:
                    for key, file in req.files.items():
                        data[key] = {
                            'filename': file.filename,
                            'content_type': file.content_type,
                            'size': len(file.read())
                        }
                        file.seek(0)  # Reset file pointer after reading
        except Exception as e:
            logger.error(f"Error parsing request data: {str(e)}")
            return {
                'valid': False,
                'errors': [{'message': 'Could not parse request data'}]
            }
        
        # Validate with jsonschema if available
        if JSONSCHEMA_AVAILABLE:
            try:
                jsonschema.validate(instance=data, schema=schema)
                return {'valid': True, 'errors': []}
            except jsonschema.exceptions.ValidationError as e:
                logger.warning(f"Validation error: {str(e)}")
                return {
                    'valid': False,
                    'errors': [{'path': e.path, 'message': e.message}]
                }
        else:
            # Simple validation fallback
            return self._simple_validate(data, schema)
    
    def _simple_validate(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simple validation fallback when jsonschema is not available
        
        Args:
            data: Request data
            schema: Schema definition
            
        Returns:
            Dict with validation results
        """
        errors = []
        
        # Check required properties
        if 'required' in schema:
            for field in schema['required']:
                if field not in data:
                    errors.append({
                        'path': field,
                        'message': f"Required field '{field}' is missing"
                    })
        
        # Check property types
        if 'properties' in schema:
            for field, props in schema['properties'].items():
                if field in data and 'type' in props:
                    # Skip validation for null values when nullable is true
                    if data[field] is None and props.get('nullable', False):
                        continue
                    
                    # Validate types
                    if props['type'] == 'string' and not isinstance(data[field], str):
                        errors.append({
                            'path': field,
                            'message': f"Field '{field}' must be a string"
                        })
                    elif props['type'] == 'number' and not isinstance(data[field], (int, float)):
                        errors.append({
                            'path': field,
                            'message': f"Field '{field}' must be a number"
                        })
                    elif props['type'] == 'integer' and not isinstance(data[field], int):
                        errors.append({
                            'path': field,
                            'message': f"Field '{field}' must be an integer"
                        })
                    elif props['type'] == 'boolean' and not isinstance(data[field], bool):
                        errors.append({
                            'path': field,
                            'message': f"Field '{field}' must be a boolean"
                        })
                    elif props['type'] == 'array' and not isinstance(data[field], list):
                        errors.append({
                            'path': field,
                            'message': f"Field '{field}' must be an array"
                        })
                    elif props['type'] == 'object' and not isinstance(data[field], dict):
                        errors.append({
                            'path': field,
                            'message': f"Field '{field}' must be an object"
                        })
        
        # Return validation result
        if errors:
            return {'valid': False, 'errors': errors}
        else:
            return {'valid': True, 'errors': []}
            
    def get_schema(self, schema_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a registered schema by name
        
        Args:
            schema_name: Name of the schema
            
        Returns:
            Schema definition or None if not found
        """
        return self.schemas.get(schema_name)
