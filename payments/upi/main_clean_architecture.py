"""
UPI Payment Module Entry Point (Clean Architecture Implementation).
"""
import logging
import os
import sys
from typing import Dict, Any
from flask import Flask, Blueprint

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import dependency injection container
from .di_container import UpiDiContainer


def get_config():
    """Get configuration for UPI module."""
    # This is a simple configuration
    # In a real system, this would be loaded from a config file or environment variables
    return {
        'daily_transaction_limit': 100000.0,
        'per_transaction_limit': 25000.0,
        'db_path': os.path.join('database', 'upi_transactions.db'),
        'notification_type': 'sms',  # Options: 'sms', 'email'
        'sms_api_key': 'mock_api_key',
        'sms_sender_id': 'UPIPAY',
        'smtp_config': {
            'from_email': 'upi-notifications@bank.com'
        },
        'HOST': '0.0.0.0',
        'PORT': 5000,
        'DEBUG': False,
        'ENVIRONMENT': 'development',
        'USE_MOCK': True
    }


def create_app() -> Flask:
    """
    Create and configure the UPI Flask application.
    
    Returns:
        Flask application instance
    """
    # Create and configure the app
    app = Flask(__name__)
    
    # Get configuration
    config = get_config()
    app.config.update(config)
    
    # Initialize container
    container = UpiDiContainer(config)
    
    # Get controller blueprint
    upi_controller = container.get_upi_controller()
    
    # Register blueprint
    app.register_blueprint(upi_controller.blueprint, url_prefix='/api/upi')
    
    # Log startup information
    env_name = app.config.get('ENVIRONMENT', 'development')
    logger.info(f"UPI Module initialized in {env_name} environment")
    
    return app


def run_cli():
    """Run the UPI CLI."""
    container = UpiDiContainer(get_config())
    cli = container.get_upi_cli()
    cli.cmdloop()


def get_api_blueprint():
    """Get the Flask blueprint for UPI API."""
    container = UpiDiContainer(get_config())
    controller = container.get_upi_controller()
    return controller.blueprint


def initialize_module() -> Dict[str, Any]:
    """
    Initialize the UPI module components.
    
    Returns:
        Dictionary with initialization status
    """
    logger.info("Initializing UPI Payment Module")
    
    # Get configuration
    config = get_config()
    
    # Check configuration
    env_name = config.get('ENVIRONMENT', 'development')
    is_mock = config.get('USE_MOCK', True)
    
    logger.info(f"UPI Module - Environment: {env_name}, Mock Mode: {is_mock}")
    
    return {
        "status": "initialized",
        "environment": env_name,
        "mock_mode": is_mock
    }


if __name__ == "__main__":
    # Parse command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == 'cli':
        # Run CLI mode
        run_cli()
    else:
        # Initialize the module
        init_status = initialize_module()
        logger.info(f"UPI module initialization: {init_status}")
        
        # Create and run the app
        app = create_app()
        config = get_config()
        app.run(
            host=config.get('HOST', '0.0.0.0'),
            port=config.get('PORT', 5000),
            debug=config.get('DEBUG', False)
        )
