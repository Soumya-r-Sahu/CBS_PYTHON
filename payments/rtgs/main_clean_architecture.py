"""
RTGS Module Entry Point (Clean Architecture Implementation).
"""
import logging
import os
from typing import Dict, Any
from flask import Flask

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import dependency injection container
from .di_container import RTGSDiContainer

# Import API controller
from .presentation.api import register_blueprint


def get_config():
    """Get configuration for RTGS module."""
    # This is a simple configuration
    # In a real system, this would be loaded from a config file or environment variables
    return {
        'per_transaction_limit': 100000000.0,  # 10 crores
        'min_transaction_limit': 200000.0,  # 2 lakhs, minimum for RTGS
        'rtgs_operating_window': (9, 16, 30),  # 9AM to 4:30PM
        'rtgs_cutoff_time': '16:00',  # 4PM cutoff
        'db_dir': os.path.join('database', 'payments'),
        'rbi_api_url': 'https://api.rbi.org.in',
        'rbi_api_key': 'mock_api_key',
        'notification_type': 'sms',  # Options: 'sms', 'email', 'push'
        'sms_api_url': 'https://api.sms.provider.com',
        'sms_api_key': 'mock_api_key',
        'sms_sender_id': 'RTGSBNK',
        'HOST': '0.0.0.0',
        'PORT': 5002,
        'DEBUG': False,
        'ENVIRONMENT': 'development',
        'USE_MOCK': True
    }


def create_app() -> Flask:
    """
    Create and configure the RTGS Flask application.
    
    Returns:
        Flask application instance
    """
    # Create and configure the app
    app = Flask(__name__)
    
    # Get configuration
    config = get_config()
    
    # Create dependency injection container
    container = RTGSDiContainer(config)
    
    # Register blueprints for presentation layer
    register_blueprint(app, container)
    
    # Add a simple health check route
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'module': 'rtgs'}
    
    # Add error handlers
    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {str(e)}")
        return {'error': 'Internal server error'}, 500
    
    return app


def main():
    """Main entry point for the RTGS module."""
    # Get configuration
    config = get_config()
    
    # Create the app
    app = create_app()
    
    # Run the app
    app.run(
        host=config['HOST'],
        port=config['PORT'],
        debug=config['DEBUG']
    )


if __name__ == '__main__':
    main()
