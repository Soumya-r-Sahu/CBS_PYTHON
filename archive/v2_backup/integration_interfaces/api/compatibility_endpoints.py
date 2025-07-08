"""
Framework Compatibility API Endpoints

This module provides endpoints specifically designed to test and demonstrate
compatibility with various frontend frameworks (Django, React, Angular, Vue.js).
"""

import json
import time
from typing import Dict, Any, List, Optional
from flask import Blueprint, request, jsonify, Response, current_app

# Import compatibility utilities
try:
    from utils.config.compatibility import (
        get_api_client_config,
        get_cors_settings,
        get_authentication_scheme,
        detect_framework_from_request
    )
except ImportError:
    # Fallback for detect_framework_from_request if not in compatibility.py
    def detect_framework_from_request(user_agent=None, headers=None):
        """Fallback implementation"""
        if headers is None:
            headers = {}
        
        user_agent = user_agent or headers.get("User-Agent", "")
        
        if "angular" in user_agent.lower():
            return "angular"
        elif "react" in user_agent.lower():
            return "react"
        elif "vue" in user_agent.lower():
            return "vue"
        elif headers.get("X-CSRFToken") or "csrftoken" in headers.get("Cookie", ""):
            return "django"
        
        return "generic"
        
    def get_api_client_config(framework="generic"):
        """Fallback implementation"""
        return {
            "base_url": "http://localhost:5000/api/v1",
            "timeout": 30000,
            "retry_attempts": 3
        }
        
    def get_cors_settings():
        """Fallback implementation"""
        return {
            "allowed_origins": ["*"],
            "allowed_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allowed_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
        
    def get_authentication_scheme(framework="generic"):
        """Fallback implementation"""
        return "Bearer"

# Try to import enhanced framework compatibility utilities
try:
    from utils.framework_compatibility import (
        detect_framework_from_headers,
        get_framework_specific_config,
        get_framework_compatibility_issues,
        generate_framework_sample_code
    )
    ENHANCED_COMPATIBILITY = True
except ImportError:
    ENHANCED_COMPATIBILITY = False
    # Define minimal versions if enhanced utilities are not available
    def detect_framework_from_headers(headers):
        """Minimal implementation"""
        return detect_framework_from_request(
            user_agent=headers.get('User-Agent', ''),
            headers=headers
        )
    
    def get_framework_specific_config(framework):
        """Minimal implementation"""
        return {"framework": framework}
    
    def get_framework_compatibility_issues(framework):
        """Minimal implementation"""
        return []
    
    def generate_framework_sample_code(framework, endpoint):
        """Minimal implementation"""
        return f"// Sample code for {framework} accessing {endpoint}"

# Create a blueprint for compatibility endpoints
compatibility_api = Blueprint('compatibility_api', __name__)

@compatibility_api.route('/compatibility/info', methods=['GET'])
def compatibility_info() -> Response:
    """
    Get compatibility information for the requesting client
    
    This endpoint detects the client's framework and returns configuration
    information to help with compatibility testing.
    
    Returns:
        JSON response with compatibility information
    """
    # Detect framework from request
    framework = detect_framework_from_request(
        user_agent=request.headers.get('User-Agent'),
        headers=dict(request.headers)
    )
    
    # Get client configuration for the detected framework
    client_config = get_api_client_config(framework)
    
    # Get CORS settings
    cors_settings = get_cors_settings()
    
    # Create response with compatibility information
    response_data = {
        "detected_framework": framework,
        "api_version": "1.0.0",
        "compatible_frameworks": ["django", "react", "angular", "vue"],
        "client_config": client_config,
        "cors_settings": {
            "allowed_origins": cors_settings["allowed_origins"],
            "allowed_methods": cors_settings["allowed_methods"],
            "supports_credentials": cors_settings["supports_credentials"]
        },
        "authentication": {
            "scheme": get_authentication_scheme(framework),
            "token_header": "Authorization",
            "token_prefix": "Bearer",
            "token_storage_key": client_config.get("token_storage_key", "jwt_token")
        },
        "timestamp": int(time.time())
    }
    
    return jsonify(response_data)

@compatibility_api.route('/compatibility/test', methods=['POST'])
def compatibility_test() -> Response:
    """
    Test API compatibility with the client framework
    
    This endpoint allows clients to send a test payload and receive a standardized
    response to verify API compatibility.
    
    Returns:
        JSON response with test results
    """
    # Get JSON payload from request
    payload = request.get_json() or {}
    
    # Detect framework from request
    framework = detect_framework_from_request(
        user_agent=request.headers.get('User-Agent'),
        headers=dict(request.headers)
    )
    
    # Prepare response data
    response_data = {
        "framework": framework,
        "test_status": "success",
        "features_supported": {
            "authentication": True,
            "csrf_protection": framework == "django",
            "json_content_type": True,
            "cors": True,
            "request_validation": True
        },
        "echo": payload,
        "headers_received": {
            key: value for key, value in request.headers.items()
            if key.lower() in [
                "user-agent", "content-type", "accept", 
                "x-requested-with", "origin"
            ]
        }
    }
    
    return jsonify(response_data)

@compatibility_api.route('/compatibility/frameworks', methods=['GET'])
def supported_frameworks() -> Response:
    """
    Get information about supported frontend frameworks
    
    Returns:
        JSON response with details about supported frameworks
    """
    frameworks_info = {
        "django": {
            "name": "Django",
            "client_library": "django_banking_api",
            "recommended_version": ">=3.2",
            "documentation": "/api/docs/frameworks/django"
        },
        "react": {
            "name": "React",
            "client_library": "@cbs/react-banking-api",
            "recommended_version": ">=17.0.0",
            "documentation": "/api/docs/frameworks/react"
        },
        "angular": {
            "name": "Angular",
            "client_library": "@cbs/angular-banking-api",
            "recommended_version": ">=14.0.0",
            "documentation": "/api/docs/frameworks/angular"
        },
        "vue": {
            "name": "Vue.js",
            "client_library": "@cbs/vue-banking-api",
            "recommended_version": ">=3.0.0",
            "documentation": "/api/docs/frameworks/vue"
        }
    }
    
    return jsonify({
        "supported_frameworks": frameworks_info,
        "default_framework": "react",
        "api_version": "1.0.0"
    })

def register_compatibility_routes(app):
    """
    Register compatibility API routes with Flask application
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(compatibility_api, url_prefix='/api/v1')
