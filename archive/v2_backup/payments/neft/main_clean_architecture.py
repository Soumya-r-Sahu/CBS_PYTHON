"""
NEFT Payment Module Entry Point (Clean Architecture Implementation).
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
from .di_container import NEFTDiContainer


def get_config():
    """Get configuration for NEFT module."""
    # This is a simple configuration
    # In a real system, this would be loaded from a config file or environment variables
    return {
        'per_transaction_limit': 10000000.0,  # 1 crore limit for NEFT
        'db_path': os.path.join('database', 'neft_transactions.db'),
        'batch_times': ["00:30", "10:30", "13:30", "16:30"],
        'hold_minutes': 10,
        'notification_type': 'sms',
        'sms_api_key': 'mock_api_key',
        'sms_sender_id': 'NEFTPY',
        'admin_phone_numbers': [],
        'rbi_neft_service_url': 'https://rbi-neft-api.example.com',
        'connection_timeout_seconds': 30,
        'request_timeout_seconds': 60,
        'rbi_api_key': 'mock_api_key',
        'bank_code': 'TESTBNK',
        'HOST': '0.0.0.0',
        'PORT': 5001,
        'DEBUG': False,
        'ENVIRONMENT': 'development',
        'mock_mode': True
    }


def create_app() -> Flask:
    """
    Create and configure the NEFT Flask application.
    
    Returns:
        Flask application instance
    """
    # Create and configure the app
    app = Flask(__name__)
    
    # Get configuration
    config = get_config()
    app.config.update(config)
    
    # Initialize container
    container = NEFTDiContainer(config)
    
    # Get controller blueprint
    neft_controller = container.get_neft_controller()
    
    # Register blueprint
    app.register_blueprint(neft_controller.blueprint, url_prefix='/api/neft')
    
    # Log startup information
    env_name = app.config.get('ENVIRONMENT', 'development')
    logger.info(f"NEFT Module initialized in {env_name} environment")
    
    return app


def run_cli():
    """Run the NEFT CLI."""
    container = NEFTDiContainer(get_config())
    cli = container.get_neft_cli()
    cli.cmdloop()


def get_api_blueprint():
    """Get the Flask blueprint for NEFT API."""
    container = NEFTDiContainer(get_config())
    controller = container.get_neft_controller()
    return controller.blueprint


def initialize_module() -> Dict[str, Any]:
    """
    Initialize the NEFT module components.
    
    Returns:
        Dictionary with initialization status
    """
    logger.info("Initializing NEFT Payment Module")
    
    # Get configuration
    config = get_config()
    
    # Check configuration
    env_name = config.get('ENVIRONMENT', 'development')
    is_mock = config.get('mock_mode', True)
    
    logger.info(f"NEFT Module - Environment: {env_name}, Mock Mode: {is_mock}")
    
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
        logger.info(f"NEFT module initialization: {init_status}")
        
        # Create and run the app
        app = create_app()
        config = get_config()
        app.run(
            host=config.get('HOST', '0.0.0.0'),
            port=config.get('PORT', 5001),
            debug=config.get('DEBUG', False)
        )
