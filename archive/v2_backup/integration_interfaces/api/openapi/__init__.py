"""
OpenAPI / Swagger Integration Module

This module initializes and configures Swagger UI for the Banking API, providing
interactive API documentation for developers.
"""

import os
from pathlib import Path
from flask import Blueprint, jsonify, json, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint

# Get the absolute path to the OpenAPI JSON file
current_dir = Path(__file__).resolve().parent
openapi_file_path = current_dir / 'openapi' / 'banking_api_openapi.json'

def register_openapi(app):
    """
    Register OpenAPI/Swagger UI with the Flask application
    
    Args:
        app: Flask application instance
    """
    # Create a blueprint to serve the OpenAPI JSON file
    openapi_bp = Blueprint('openapi', __name__)
    
    @openapi_bp.route('/openapi.json')
    def serve_openapi_spec():
        """Serve the OpenAPI specification as JSON"""
        try:
            with open(openapi_file_path, 'r') as f:
                return jsonify(json.load(f))
        except Exception as e:
            return jsonify({"error": f"Error loading OpenAPI specification: {str(e)}"}), 500
    
    # Register the OpenAPI blueprint
    app.register_blueprint(openapi_bp, url_prefix='/api/v1')
    
    # Configure Swagger UI
    swagger_url = '/api/docs'  # URL for accessing the Swagger UI
    swagger_blueprint = get_swaggerui_blueprint(
        swagger_url,
        '/api/v1/openapi.json',  # URL to fetch the OpenAPI JSON
        config={
            'app_name': "Banking API Documentation",
            'deepLinking': True,
            'defaultModelsExpandDepth': 2,
            'defaultModelExpandDepth': 2,
            'docExpansion': 'list',  # 'list', 'full', or 'none'
            'syntaxHighlight.theme': 'agate'
        }
    )
    
    # Register Swagger UI blueprint
    app.register_blueprint(swagger_blueprint, url_prefix=swagger_url)
    
    # Log successful registration
    print(f"OpenAPI documentation available at: {swagger_url}")
    
    return app
