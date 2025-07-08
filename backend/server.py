#!/usr/bin/env python
"""
Core Banking System - Backend Server

This is the main backend server that handles all business logic and data processing.
It provides secure APIs for the frontend to consume and integrates with all core banking modules.
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import centralized import system
from utils.lib.packages import fix_path, is_production, is_development, is_test, is_debug_enabled
fix_path()

# Import encryption service
from backend.encryption.encryption_service import EncryptionService

# Import configuration
from config import DATABASE_CONFIG, API_CONFIG, SECURITY_CONFIG

# Set up logging
logging.basicConfig(
    level=logging.INFO if not is_debug_enabled() else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize encryption service
encryption_service = EncryptionService()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure CORS
    CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])
    
    # Set up encryption middleware
    @app.before_request
    def before_request():
        """Middleware to handle request encryption/decryption."""
        if request.method == 'POST' and request.is_json:
            try:
                # Decrypt sensitive data if needed
                if 'encrypted_data' in request.get_json():
                    encrypted_data = request.get_json()['encrypted_data']
                    decrypted_data = encryption_service.decrypt_data(encrypted_data)
                    request.json = json.loads(decrypted_data)
            except Exception as e:
                logger.error(f"Error decrypting request data: {e}")
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'environment': 'production' if is_production() else 'development'
        })
    
    # API v1 routes
    @app.route('/api/v1/auth/login', methods=['POST'])
    def login():
        """User authentication endpoint."""
        try:
            from backend.controllers.auth_controller import AuthController
            controller = AuthController(encryption_service)
            return controller.login()
        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({'error': 'Authentication failed'}), 500
    
    @app.route('/api/v1/auth/logout', methods=['POST'])
    def logout():
        """User logout endpoint."""
        try:
            from backend.controllers.auth_controller import AuthController
            controller = AuthController(encryption_service)
            return controller.logout()
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return jsonify({'error': 'Logout failed'}), 500
    
    @app.route('/api/v1/accounts', methods=['GET'])
    def get_accounts():
        """Get user accounts."""
        try:
            from backend.controllers.accounts_controller import AccountsController
            controller = AccountsController(encryption_service)
            return controller.get_accounts()
        except Exception as e:
            logger.error(f"Get accounts error: {e}")
            return jsonify({'error': 'Failed to retrieve accounts'}), 500
    
    @app.route('/api/v1/accounts/<account_id>', methods=['GET'])
    def get_account(account_id):
        """Get specific account details."""
        try:
            from backend.controllers.accounts_controller import AccountsController
            controller = AccountsController(encryption_service)
            return controller.get_account(account_id)
        except Exception as e:
            logger.error(f"Get account error: {e}")
            return jsonify({'error': 'Failed to retrieve account'}), 500
    
    @app.route('/api/v1/accounts/<account_id>/balance', methods=['GET'])
    def get_account_balance(account_id):
        """Get account balance."""
        try:
            from backend.controllers.accounts_controller import AccountsController
            controller = AccountsController(encryption_service)
            return controller.get_account_balance(account_id)
        except Exception as e:
            logger.error(f"Get balance error: {e}")
            return jsonify({'error': 'Failed to retrieve balance'}), 500
    
    @app.route('/api/v1/transactions', methods=['GET'])
    def get_transactions():
        """Get transactions."""
        try:
            from backend.controllers.transactions_controller import TransactionsController
            controller = TransactionsController(encryption_service)
            return controller.get_transactions()
        except Exception as e:
            logger.error(f"Get transactions error: {e}")
            return jsonify({'error': 'Failed to retrieve transactions'}), 500
    
    @app.route('/api/v1/transactions', methods=['POST'])
    def create_transaction():
        """Create a new transaction."""
        try:
            from backend.controllers.transactions_controller import TransactionsController
            controller = TransactionsController(encryption_service)
            return controller.create_transaction()
        except Exception as e:
            logger.error(f"Create transaction error: {e}")
            return jsonify({'error': 'Failed to create transaction'}), 500
    
    @app.route('/api/v1/customers', methods=['GET'])
    def get_customers():
        """Get customers."""
        try:
            from backend.controllers.customers_controller import CustomersController
            controller = CustomersController(encryption_service)
            return controller.get_customers()
        except Exception as e:
            logger.error(f"Get customers error: {e}")
            return jsonify({'error': 'Failed to retrieve customers'}), 500
    
    @app.route('/api/v1/customers', methods=['POST'])
    def create_customer():
        """Create a new customer."""
        try:
            from backend.controllers.customers_controller import CustomersController
            controller = CustomersController(encryption_service)
            return controller.create_customer()
        except Exception as e:
            logger.error(f"Create customer error: {e}")
            return jsonify({'error': 'Failed to create customer'}), 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

def main():
    """Main entry point for the backend server."""
    app = create_app()
    
    # Get configuration
    host = API_CONFIG.get('HOST', '127.0.0.1')
    port = API_CONFIG.get('PORT', 5000)
    debug = is_debug_enabled()
    
    logger.info(f"Starting backend server on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Environment: {'production' if is_production() else 'development'}")
    
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    main()
