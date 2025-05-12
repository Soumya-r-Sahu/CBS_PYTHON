"""
Mobile Banking API Routes Configuration

This module sets up API routes for the Core Banking System mobile application.
"""

from flask import Flask
from app.api.controllers.account_controller import account_api
from app.api.controllers.auth_controller import auth_api
from app.api.controllers.card_controller import card_api
from app.api.controllers.customer_controller import customer_api
from app.api.controllers.transaction_controller import transaction_api
from app.api.controllers.upi_controller import upi_api
from app.api.middleware.authentication import setup_auth_middleware
from app.api.middleware.error_handler import setup_error_handlers
from app.api.middleware.validation import setup_validation_middleware
from app.api.middleware.rate_limiter import setup_rate_limiting

def setup_routes(app: Flask):
    """
    Configure all API routes for the application
    
    Args:
        app: Flask application instance
    """
    # Register middleware
    setup_auth_middleware(app)
    setup_error_handlers(app)
    setup_validation_middleware(app)
    setup_rate_limiting(app)
    
    # API version prefix
    api_prefix = '/api/v1'
    
    # Register blueprints with the API prefix
    app.register_blueprint(auth_api, url_prefix=f'{api_prefix}/auth')
    app.register_blueprint(account_api, url_prefix=f'{api_prefix}/accounts')
    app.register_blueprint(customer_api, url_prefix=f'{api_prefix}/customers')
    app.register_blueprint(card_api, url_prefix=f'{api_prefix}/cards')
    app.register_blueprint(transaction_api, url_prefix=f'{api_prefix}/transactions')
    app.register_blueprint(upi_api, url_prefix=f'{api_prefix}/upi')
    
    # Base route for API health check
    @app.route(f'{api_prefix}/health')
    def health_check():
        return {'status': 'ok', 'version': '1.0.0'}
