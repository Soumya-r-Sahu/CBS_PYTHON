"""
Main application module for CBS-python

Initializes the Flask application and sets up routes
"""

import os
import sys
from pathlib import Path
from flask import Flask, jsonify

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

# Import routes - try new paths first, fall back to old paths for compatibility
try:
    from integration_interfaces.api.routes import setup_routes
except ImportError:
    # Fallback: define a dummy setup_routes if import fails
    def setup_routes(app):
        @app.route('/api/fallback', methods=['GET'])
        def fallback():
            return jsonify({"status": "API routes not found"})
        print("WARNING: Could not import API routes, using fallback")

# Import from compatibility layer - try new paths first
try:
    from utils.config.environment import (
        get_environment,
        get_environment_name, 
        is_production,
        is_development,
        is_testing,
        is_test,
        is_debug_enabled
    )
    from utils.config.api import get_api_config
except ImportError:
    try:
        from app.config.environment import (
            get_environment,
            get_environment_name, 
            is_production,
            is_development,
            is_testing,
            is_test,
            is_debug_enabled
        )
        from app.config.api import get_api_config
    except ImportError:
        # Define fallback environment functions if neither import works
        def get_environment(): return os.environ.get("CBS_ENVIRONMENT", "development")
        def get_environment_name(): return get_environment()
        def is_production(): return get_environment() == "production"
        def is_development(): return get_environment() == "development"
        def is_testing(): return get_environment() in ("test", "testing")
        def is_test(): return is_testing()
        def is_debug_enabled(): return os.environ.get("DEBUG", "0").lower() in ("1", "true", "yes")
        def get_api_config(): return {"host": "0.0.0.0", "port": 5000, "secret_key": "default-secret-key"}

# Import logging utilities - try new paths first
try:
    from utils.lib.logging import (
        get_info_logger,
        get_error_logger,
        configure_root_logger
    )
except ImportError:
    try:
        from app.lib.logging_utils import (
            get_info_logger,
            get_error_logger,
            configure_root_logger
        )
    except ImportError:
        # Define minimal logging fallback
        import logging
        def get_info_logger(name): return logging.getLogger(name)
        def get_error_logger(name): return logging.getLogger(name)
        def configure_root_logger(): pass

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
