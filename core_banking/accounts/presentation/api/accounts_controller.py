"""
Accounts API Controller

This module provides REST API endpoints for the Accounts module using Flask.
"""

import logging
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from flask import Blueprint, request, jsonify, current_app
import json

from ..di_container import container

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
accounts_api = Blueprint('accounts_api', __name__)


class DecimalEncoder(json.JSONEncoder):
    """JSON Encoder that handles Decimal values"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)


@accounts_api.route('/', methods=['POST'])
def create_account():
    """
    Create a new account
    
    Endpoint: POST /api/v1/accounts/
    """
    try:
        # Get account service from container
        account_service = container.account_service()
        
        # Parse request JSON
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['customer_id', 'account_type']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Get optional fields
        initial_deposit = Decimal(data.get('initial_deposit', '0'))
        currency = data.get('currency', 'INR')
        
        # Call the service
        result = account_service.create_account(
            customer_id=UUID(data['customer_id']),
            account_type=data['account_type'],
            initial_deposit=initial_deposit,
            currency=currency
        )
        
        # Return the result
        return jsonify(result), 201
        
    except ValueError as e:
        logger.error(f"Validation error in create_account: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error in create_account: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@accounts_api.route('/<account_id>', methods=['GET'])
def get_account_details(account_id):
    """
    Get account details
    
    Endpoint: GET /api/v1/accounts/{account_id}
    """
    try:
        # Get account service from container
        account_service = container.account_service()
        
        # Call the service
        result = account_service.get_account_details(
            account_id=UUID(account_id)
        )
        
        # Return the result
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Validation error in get_account_details: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error in get_account_details: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@accounts_api.route('/<account_id>/deposit', methods=['POST'])
def deposit_funds(account_id):
    """
    Deposit funds to an account
    
    Endpoint: POST /api/v1/accounts/{account_id}/deposit
    """
    try:
        # Get account service from container
        account_service = container.account_service()
        
        # Parse request JSON
        data = request.get_json()
        
        # Validate required fields
        if 'amount' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing required field: amount'
            }), 400
        
        # Get optional fields
        description = data.get('description')
        reference_id = data.get('reference_id')
        
        # Call the service
        result = account_service.deposit(
            account_id=UUID(account_id),
            amount=Decimal(data['amount']),
            description=description,
            reference_id=reference_id
        )
        
        # Return the result
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Validation error in deposit_funds: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error in deposit_funds: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@accounts_api.route('/<account_id>/withdraw', methods=['POST'])
def withdraw_funds(account_id):
    """
    Withdraw funds from an account
    
    Endpoint: POST /api/v1/accounts/{account_id}/withdraw
    """
    try:
        # Get account service from container
        account_service = container.account_service()
        
        # Parse request JSON
        data = request.get_json()
        
        # Validate required fields
        if 'amount' not in data:
            return jsonify({
                'success': False,
                'message': 'Missing required field: amount'
            }), 400
        
        # Get optional fields
        description = data.get('description')
        reference_id = data.get('reference_id')
        
        # Call the service
        result = account_service.withdraw(
            account_id=UUID(account_id),
            amount=Decimal(data['amount']),
            description=description,
            reference_id=reference_id
        )
        
        # Return the result
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Validation error in withdraw_funds: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error in withdraw_funds: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@accounts_api.route('/transfer', methods=['POST'])
def transfer_funds():
    """
    Transfer funds between accounts
    
    Endpoint: POST /api/v1/accounts/transfer
    
    Request body:
    {
        "source_account_id": "12345678-1234-5678-1234-567812345678",
        "target_account_id": "87654321-4321-8765-4321-876543210987",
        "amount": "1000.00",
        "description": "Rent payment",
        "reference_id": "TRF123456"
    }
    """
    try:
        # Get account service from container
        account_service = container.account_service()
        
        # Parse request JSON
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['source_account_id', 'target_account_id', 'amount']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Get optional fields
        description = data.get('description')
        reference_id = data.get('reference_id')
        
        # Call the service
        result = account_service.transfer(
            source_account_id=UUID(data['source_account_id']),
            target_account_id=UUID(data['target_account_id']),
            amount=Decimal(data['amount']),
            description=description,
            reference_id=reference_id
        )
        
        # Return the result
        return jsonify(result), 200
        
    except ValueError as e:
        logger.error(f"Validation error in transfer_funds: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error in transfer_funds: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


def register_accounts_api(app):
    """Register the accounts API with the Flask application"""
    app.register_blueprint(accounts_api, url_prefix='/api/v1/accounts')
    app.json_encoder = DecimalEncoder
