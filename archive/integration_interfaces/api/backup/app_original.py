"""
Main application module for CBS-python

Initializes the Flask application and sets up routes
"""

import os
from flask import Flask, jsonify
from app.api.routes import setup_routes

# Try to import environment module
try:
    from app.config.environment import (
        get_environment_name, is_production, is_development, 
        is_test, is_debug_enabled
    )
except ImportError:
    # Fallback environment detection
    env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    def is_production(): return env_str == "production"
    def is_development(): return env_str == "development"
    def is_test(): return env_str == "test"
    def is_debug_enabled(): return os.environ.get("CBS_DEBUG", "true").lower() in ("true", "1", "yes")
    def get_environment_name(): return env_str

def create_app():
    """
    Create and configure the Flask application
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Configure app based on environment
    env_name = get_environment_name()
    
    # Environment-specific configuration
    if is_production():
        app.config['SECRET_KEY'] = os.environ.get('CBS_SECRET_KEY')
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        app.config['ENV'] = 'production'
    elif is_test():
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
                "testing": is_test(),
                "api_version": "1.0",
                "flask_env": app.config['ENV']
            })
    
    return app

if __name__ == "__main__":
    app = create_app()
    
    # Set host and port based on environment
    host = os.environ.get('CBS_API_HOST', '0.0.0.0')
    
    # Default port by environment
    if is_production():
        default_port = 5000
    elif is_test():
        default_port = 5001
    else:  # development
        default_port = 5002
        
    port = int(os.environ.get('CBS_API_PORT', default_port))
    debug = not is_production() and is_debug_enabled()
    
    print(f"Starting API server in {get_environment_name().upper()} environment")
    print(f"API server listening on {host}:{port}")
    
    app.run(debug=debug, host=host, port=port)