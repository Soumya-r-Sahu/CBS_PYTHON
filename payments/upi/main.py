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

# Import controllers with blueprints
from .controllers.transaction_controller import upi_transaction_api
from .controllers.registration_controller import upi_registration_api

# Import config
from .config.upi_config import UpiConfig

# Create Blueprint for UPI APIs
upi_api_blueprint = Blueprint('upi_api', __name__)

# Register API routes
upi_api_blueprint.register_blueprint(upi_transaction_api, url_prefix='/transactions')
upi_api_blueprint.register_blueprint(upi_registration_api, url_prefix='/registration')


def create_app() -> Flask:
    """
    Create and configure the UPI Flask application.
    
    Returns:
        Flask application instance
    """
    # Create and configure the app
    app = Flask(__name__)
    
    # Get configuration
    upi_config = UpiConfig()
    
    # Load configuration
    app.config.update(upi_config.get_all())
    
    # Register blueprints
    app.register_blueprint(upi_api_blueprint, url_prefix='/api/upi')
    
    # Log startup information
    env_name = app.config.get('ENVIRONMENT', 'development')
    logger.info(f"UPI Module initialized in {env_name} environment")
    
    return app


def initialize_module() -> Dict[str, Any]:
    """
    Initialize the UPI module components.
    
    Returns:
        Dictionary with initialization status
    """
    logger.info("Initializing UPI Payment Module")
    
    # Get configuration
    upi_config = UpiConfig()
    
    # Check configuration
    env_name = upi_config.get('ENVIRONMENT', 'development')
    is_mock = upi_config.get('USE_MOCK', True)
    
    logger.info(f"UPI Module - Environment: {env_name}, Mock Mode: {is_mock}")
    
    return {
        "status": "initialized",
        "environment": env_name,
        "mock_mode": is_mock
    }


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize the module
    init_status = initialize_module()
    logger.info(f"UPI module initialization: {init_status}")
    
    # Get configuration
    upi_config = UpiConfig()
    
    # Create and run the app
    app = create_app()
    app.run(
        host=upi_config.get('HOST', '0.0.0.0'),
        port=upi_config.get('PORT', 5000),
        debug=upi_config.get('DEBUG', False)
    )
