"""
Mobile Banking Module Entry Point (Clean Architecture Implementation).
"""
import logging
import os
from typing import Dict, Any
from flask import Flask, Blueprint

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import dependency injection container
from .di_container import MobileBankingDiContainer

# Import API controller
from .presentation.api.mobile_controller import register_blueprint


def get_config():
    """Get configuration for Mobile Banking module."""
    # This is a simple configuration
    # In a real system, this would be loaded from a config file or environment variables
    return {
        'daily_transaction_limit': 100000.0,
        'per_transaction_limit': 25000.0,
        'max_session_idle_minutes': 15,
        'failed_login_limit': 5,
        'enforce_device_binding': True,
        'db_path': os.path.join('database', 'mobile_banking.db'),
        'notification_type': 'sms',  # Options: 'sms', 'email', 'push'
        'sms_api_key': 'mock_api_key',
        'sms_sender_id': 'MOBBNK',
        'smtp_config': {
            'from_email': 'mobile-notifications@bank.com'
        },
        'HOST': '0.0.0.0',
        'PORT': 5001,
        'DEBUG': False,
        'ENVIRONMENT': 'development',
        'USE_MOCK': True
    }


def create_app() -> Flask:
    """
    Create and configure the Mobile Banking Flask application.
    
    Returns:
        Flask application instance
    """
    # Create and configure the app
    app = Flask(__name__)
    
    # Get configuration
    config = get_config()
      # Create dependency injection container
    container = MobileBankingDiContainer(config)
    
    # Register blueprints for presentation layer
    register_blueprint(app)
    
    # Add a simple health check route
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'module': 'mobile_banking'}
    
    # Add error handlers
    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server error: {str(e)}")
        return {'error': 'Internal server error'}, 500
    
    # Attach the container to the app for use in routes
    app.container = container
    
    return app


def main():
    """Main entry point for the Mobile Banking module."""
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
