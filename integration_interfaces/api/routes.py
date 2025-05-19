"""
Mobile Banking API Routes Configuration

This module sets up API routes for the Core Banking System mobile application.
It handles all route registration to prevent circular imports between app.py and banking_api_endpoints.py.
"""

import os
import sys
import datetime
from pathlib import Path
from flask import Flask

# Add project root to path to enable imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# Import controllers
from integration_interfaces.api.controllers.account_controller import account_api
from integration_interfaces.api.controllers.auth_controller import auth_api
from integration_interfaces.api.controllers.card_controller import card_api
from integration_interfaces.api.controllers.customer_controller import customer_api
from integration_interfaces.api.controllers.transaction_controller import transaction_api
from integration_interfaces.api.controllers.upi_controller import upi_api

# Import middleware
from integration_interfaces.api.middleware.authentication import setup_auth_middleware
from integration_interfaces.api.middleware.error_handler import setup_error_handlers
from integration_interfaces.api.middleware.validation import setup_validation_middleware
from integration_interfaces.api.middleware.rate_limiter import setup_rate_limiting


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
def setup_routes(app: Flask):
    """
    Connect all banking services to their API endpoints
    
    This function registers all the different banking service controllers
    with their appropriate URL patterns, creating a well-organized API
    structure that's easy for developers to understand and use.
    """
    # Register authentication middleware
    setup_auth_middleware(app)
    
    # Register validation middleware
    setup_validation_middleware(app)
    
    # Register error handlers
    setup_error_handlers(app)
    
    # Register rate limiting
    setup_rate_limiting(app)
    
    # Register API blueprints
    app.register_blueprint(account_api, url_prefix='/api/v1/accounts')
    app.register_blueprint(auth_api, url_prefix='/api/v1/auth')
    app.register_blueprint(card_api, url_prefix='/api/v1/cards')
    app.register_blueprint(customer_api, url_prefix='/api/v1/customers')
    app.register_blueprint(transaction_api, url_prefix='/api/v1/transactions')
    app.register_blueprint(upi_api, url_prefix='/api/v1/upi')
    
    # Register health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint to verify API is running"""
        from flask import jsonify
        return jsonify({
            "status": "ok",
            "service": "CBS Banking API",
            "version": "1.0.0",
            "timestamp": str(datetime.datetime.now())
        })

    # Return the configured app
    return app
