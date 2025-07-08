"""
Banking Service API

This module serves as the main entry point for the Core Banking System API.
It initializes the Flask application and sets up all necessary configurations
for serving API requests securely across different environments.
"""

import os
import sys
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
import datetime
import logging
from logging.handlers import RotatingFileHandler

# Add project root to system path for easier imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

# Import API routes
from integration_interfaces.api.routes import setup_routes

# Import compatibility endpoints
from integration_interfaces.api.compatibility_endpoints import register_compatibility_routes

# Import compatibility endpoints
try:
    from integration_interfaces.api.compatibility_endpoints import register_compatibility_routes
except ImportError:
    def register_compatibility_routes(app):
        @app.route('/api/v1/compatibility/info', methods=['GET'])
        def compatibility_info_fallback():
            return jsonify({"status": "Compatibility endpoints not available"})
        print("WARNING: Could not import compatibility endpoints, using fallback")

# Import logging configuration
from utils.lib.logging_utils import get_logger, get_log_directory

# Import environment and API config
from utils.config.environment import (
    get_environment_name, 
    is_production,
    is_development,
    is_test,
    is_debug_enabled
)
from utils.config.api import get_api_config

# Define get_environment function
def get_environment():
    """Get current environment as a string"""
    if is_production():
        return "production"
    elif is_test():
        return "test"
    else:
        return "development"

# Define is_testing alias for compatibility
is_testing = is_test

def setup_logging(app, log_dir=None):
    """
    Configure comprehensive logging for the banking application
    
    This function sets up rotating file logs and console output with appropriate
    formatting based on the environment (development, testing, production).
    
    Args:
        app: Flask application instance
        log_dir: Directory for storing log files (default: project_root/logs)
    """
    # Create logs directory if it doesn't exist
    if log_dir is None:
        log_dir = os.path.join(project_root, 'logs')
    
    os.makedirs(log_dir, exist_ok=True)
    
    # Set appropriate log level based on environment
    log_level = logging.DEBUG if is_debug_enabled() else logging.INFO
    log_format = '%(asctime)s [%(levelname)s] %(module)s: %(message)s'
    
    # Set up rotating file handler for persistent logs
    log_file = os.path.join(log_dir, f'banking_api_{get_environment()}.log')
    file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)
    file_handler.setFormatter(logging.Formatter(log_format))
    file_handler.setLevel(log_level)
    
    # Set up console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    console_handler.setLevel(log_level)
    
    # Configure Flask logger
    app.logger.handlers = []
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)
    
    # Set up root logger for other modules
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger.setLevel(log_level)
    
    app.logger.info(f"Logging initialized in {get_environment_name()} environment")

def create_app():
    """
    Create and configure a secure banking API application
    
    This function initializes the Flask application with appropriate security settings,
    CORS configuration, request logging, routes, and error handlers based on the 
    current environment.
    
    Returns:
        Fully configured Flask application ready to serve API requests
    """
    # Create the Flask application
    app = Flask(__name__)
      # Load configuration
    api_config = get_api_config()
    
    # Import secure key generation
    import secrets
    
    # Use environment variable, or get from API config, or generate a secure key
    app.config['SECRET_KEY'] = os.environ.get('CBS_SECRET_KEY', 
                                            api_config.get('secret_key') or 
                                            secrets.token_hex(32))
    app.config['ENV'] = get_environment()
    app.config['DEBUG'] = is_debug_enabled()# Setup Cross-Origin Resource Sharing (CORS) security
    try:
        # Try to import from the new compatibility module
        from utils.config.compatibility import get_cors_settings
        cors_config = get_cors_settings()
        allowed_origins = cors_config["allowed_origins"]
        CORS(app, resources={r"/api/*": {
            "origins": allowed_origins,
            "methods": cors_config["allowed_methods"],
            "allow_headers": cors_config["allowed_headers"],
            "expose_headers": cors_config["expose_headers"],
            "supports_credentials": cors_config["supports_credentials"],
            "max_age": cors_config["max_age"]
        }})
    except ImportError:
        # Fallback to basic CORS configuration
        allowed_origins = api_config.get('allowed_origins', ['*'])
        CORS(app, resources={r"/api/*": {"origins": allowed_origins}})
    
    # Setup comprehensive logging
    setup_logging(app)
      # Request logging middleware for tracking API usage
    @app.before_request
    def log_request():
        app.logger.debug(f"Incoming request: {request.method} {request.path}")
    
    @app.after_request
    def log_response(response):
        app.logger.debug(f"Response: {response.status}")
        return response
    
    # Set up all API routes
    setup_routes(app)
    
    # Register compatibility endpoints
    register_compatibility_routes(app)
    
    # Register OpenAPI documentation
    try:
        from integration_interfaces.api.openapi import register_openapi
        register_openapi(app)
    except ImportError:
        app.logger.warning("Could not import OpenAPI module, API documentation will not be available")
    
    # Set up user-friendly error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Resource not found", 
            "code": 404,
            "message": "The requested API endpoint does not exist."
        }), 404
    
    @app.errorhandler(500)
    def server_error(error):
        app.logger.error(f"Server error: {error}")
        return jsonify({
            "error": "Internal server error", 
            "code": 500,
            "message": "An unexpected error occurred. Our team has been notified."
        }), 500
    
    # Add environment information endpoint
    @app.route('/api/environment')
    def environment():
        return jsonify({
            "environment": get_environment_name(),
            "production": is_production(),
            "development": is_development(),
            "debug": is_debug_enabled(),
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Get API configuration
    api_config = get_api_config()
    host = api_config.get('host', '0.0.0.0')
    port = api_config.get('port', 5000)
    debug = is_debug_enabled()
    
    # Start the application
    print(f"Starting API server in {get_environment_name()} mode")
    print(f"Running on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)

# Import logging utilities
from utils.lib.logging_utils import get_logger

# Use the same function for both info and error loggers for simplicity
def get_info_logger(name):
    return get_logger(name)

def get_error_logger(name):
    return get_logger(name)

def configure_root_logger():
    root_logger = get_logger("root")
    return root_logger

# Set up loggers
logger = get_info_logger(__name__)
error_logger = get_error_logger(__name__)

def create_app():
    """
    Create and configure the Flask application
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Configure app based on environment
    env_name = get_environment_name()
    
    # Get API configuration
    api_config = get_api_config()
    
    # Environment-specific configuration
    if is_production():
        app.config['SECRET_KEY'] = os.environ.get('CBS_SECRET_KEY', api_config['secret_key'])
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        app.config['ENV'] = 'production'
    elif is_testing() or is_test():
        app.config['SECRET_KEY'] = os.environ.get('CBS_SECRET_KEY', 'test-secret-key')
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        app.config['ENV'] = 'testing'
    else:  # development
        app.config['SECRET_KEY'] = os.environ.get('CBS_SECRET_KEY', 'dev-secret-key')
        app.config['DEBUG'] = True
        app.config['TESTING'] = False
        app.config['ENV'] = 'development'
      # Setup API routes
    setup_routes(app)
    
    # Setup OpenAPI/Swagger documentation
    try:
        from integration_interfaces.api.openapi import register_openapi
        app = register_openapi(app)
        logger.info("OpenAPI documentation registered successfully")
    except ImportError:
        logger.warning("Could not import OpenAPI module, API documentation will not be available")
    
    # Add environment info endpoint
    @app.route('/api/environment', methods=['GET'])
    def environment_info():
        if is_production():
            # In production, only return minimal info for security
            return jsonify({
                "environment": "production",
                "api_version": "1.0"
            })
        else:
            # In non-production, it's ok to return more details
            return jsonify({
                "environment": env_name,
                "debug_mode": is_debug_enabled(),
                "testing": is_testing() or is_test(),
                "api_version": "1.0",
                "flask_env": app.config['ENV']
            })
    
    return app

if __name__ == "__main__":
    app = create_app()
    
    # Get API configuration
    api_config = get_api_config()
    
    # Set host and port based on environment
    host = os.environ.get('CBS_API_HOST', api_config['host'])
    
    # Default port by environment
    if is_production():
        default_port = 5000
    elif is_testing() or is_test():
        default_port = 5001
    else:  # development
        default_port = 5002
        
    port = int(os.environ.get('CBS_API_PORT', default_port))
    debug = not is_production() and is_debug_enabled()
    
    logger.info(f"Starting API server in {get_environment_name().upper()} environment on {host}:{port}")
    app.run(host=host, port=port, debug=debug)
