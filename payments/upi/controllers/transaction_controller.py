"""
UPI Transaction Controller Module.

API endpoints for UPI transactions.
"""
import logging
from typing import Dict, Any
from flask import Blueprint, request, jsonify

from ..services.upi_service import upi_service
from ..validators.upi_validators import validate_upi_id, validate_amount
from ..exceptions.upi_exceptions import (
    UpiBaseException, UpiValidationError, UpiNotFoundError, UpiTransactionError
)

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint for transaction APIs
upi_transaction_api = Blueprint('upi_transaction_api', __name__)


@upi_transaction_api.route('/', methods=['POST'])
def initiate_transaction():
    """
    Initiate a UPI transaction.
    
    Request body:
    {
        "payer_upi_id": "user@upi",
        "payee_upi_id": "merchant@upi",
        "amount": 100.0,
        "note": "Payment for order #12345"
    }
    
    Returns:
        JSON with transaction details and status
    """
    try:
        # Get transaction data from request
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "Missing request body"
            }), 400
        
        # Initiate transaction
        result = upi_service.initiate_transaction(data)
        
        # Return success response
        return jsonify({
            "status": "success",
            "message": "Transaction initiated successfully",
            "transaction": result
        }), 200
        
    except UpiValidationError as e:
        logger.warning(f"Validation error in transaction: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "details": getattr(e, 'details', {})
        }), 400
        
    except UpiTransactionError as e:
        logger.warning(f"Transaction error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "details": getattr(e, 'details', {})
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error in transaction: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred while processing the transaction"
        }), 500


@upi_transaction_api.route('/<transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """
    Get UPI transaction by ID.
    
    Args:
        transaction_id: Transaction ID to retrieve
    
    Returns:
        JSON with transaction details
    """
    try:
        # Get transaction by ID
        transaction = upi_service.get_transaction(transaction_id)
        
        # Return success response
        return jsonify({
            "status": "success",
            "transaction": transaction
        }), 200
        
    except UpiNotFoundError as e:
        logger.warning(f"Transaction not found: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving transaction: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred while retrieving the transaction"
        }), 500


@upi_transaction_api.route('/user/<upi_id>', methods=['GET'])
def get_user_transactions(upi_id):
    """
    Get UPI transactions by UPI ID.
    
    Args:
        upi_id: UPI ID to search for
    
    Returns:
        JSON with transaction list
    """
    try:
        # Get limit and offset parameters
        limit = request.args.get('limit', default=10, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        # Validate UPI ID
        validate_upi_id(upi_id)
        
        # Get user transactions
        transactions = upi_service.get_user_transactions(upi_id, limit, offset)
        
        # Return success response
        return jsonify({
            "status": "success",
            "upi_id": upi_id,
            "transactions": transactions,
            "count": len(transactions),
            "limit": limit,
            "offset": offset
        }), 200
        
    except UpiValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving transactions: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred while retrieving transactions"
        }), 500


@upi_transaction_api.route('/qrcode', methods=['POST'])
def generate_qr_code():
    """
    Generate UPI QR code.
    
    Request body:
    {
        "upi_id": "merchant@upi",
        "merchant_name": "My Store",
        "amount": 100.0,  # Optional
        "transaction_note": "Payment for order #12345"  # Optional
    }
    
    Returns:
        JSON with QR code data including base64 encoded image
    """
    try:
        # Get QR code data from request
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "Missing request body"
            }), 400
        
        # Validate required fields
        if 'upi_id' not in data or 'merchant_name' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required fields: upi_id, merchant_name"
            }), 400
        
        # Generate QR code
        qr_code = upi_service.generate_qr_code(
            upi_id=data['upi_id'],
            merchant_name=data['merchant_name'],
            amount=data.get('amount'),
            transaction_note=data.get('transaction_note')
        )
        
        # Return success response
        return jsonify({
            "status": "success",
            "qr_code": qr_code
        }), 200
        
    except UpiValidationError as e:
        logger.warning(f"Validation error in QR code generation: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error generating QR code: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred while generating QR code"
        }), 500
