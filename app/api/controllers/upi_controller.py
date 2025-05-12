"""
UPI Controller for Mobile Banking API

This module handles UPI-related operations through the API.
"""

from flask import Blueprint, request, jsonify
from app.api.middleware.authentication import token_required
from app.api.middleware.validation import validate_request_schema
from app.api.middleware.rate_limiter import rate_limit
from app.api.middleware.error_handler import APIException
from app.api.schemas.upi_schemas import (
    UPIRegistrationSchema, 
    UPITransactionSchema,
    UPIPinChangeSchema,
    UPIBalanceSchema,
    QRCodeGenerationSchema,
    UPICollectRequestSchema,
    UPICollectResponseSchema
)
from upi.upi_transactions import UpiTransactions
from upi.upi_registration import UpiRegistration
from app.lib.encryption import hash_password, verify_password
from database.connection import DatabaseConnection
from app.api.services.notification_service import NotificationService
import uuid
import datetime
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
upi_api = Blueprint('upi_api', __name__)

# Initialize services
database_connection = DatabaseConnection()
upi_transaction_service = UpiTransactions(database_connection)
upi_registration_service = UpiRegistration(database_connection)
notification_service = NotificationService(database_connection)


@upi_api.route('/register', methods=['POST'])
@token_required
@validate_request_schema(UPIRegistrationSchema)
@rate_limit(limit=5, period=60)
def register_upi():
    """
    Register a new UPI ID
    
    Request body:
        {
            "account_number": "1234567890",
            "username": "user123",
            "device_info": {
                "device_id": "device123",
                "device_model": "Model X",
                "os_version": "Android 12"
            },
            "upi_pin": "123456"
        }
    
    Returns:
        200 - UPI ID registration successful
        400 - Invalid request data
        401 - Unauthorized
        500 - Server error
    """
    try:
        data = request.get_json()

        
        customer_id = request.user.get('customer_id')
        
        # Create UPI ID with SBI format
        upi_id = f"{data['username']}@sbi"
        
        # Hash the UPI PIN for secure storage
        pin_salt = uuid.uuid4().hex
        pin_hash = hash_password(data['upi_pin'], pin_salt)
        
        result = upi_registration_service.register_upi_id(
            customer_id=customer_id,
            account_number=data['account_number'],
            upi_id=upi_id,
            pin_hash=pin_hash,
            pin_salt=pin_salt,
            device_id=data['device_info']['device_id']
        )
        
        if result.get('status') == 'SUCCESS':
            # Send notification
            notification_service.send_notification(
                customer_id=customer_id,
                notification_type="UPI_REGISTRATION",
                message=f"Your UPI ID {upi_id} has been successfully registered.",
                channel="SMS"
            )
            
            return jsonify({
                'status': 'SUCCESS',
                'message': 'UPI ID registered successfully',
                'data': {
                    'upi_id': upi_id,
                    'created_at': datetime.datetime.now().isoformat()
                }
            }), 200
        else:
            return jsonify({
                'status': 'FAILED',
                'message': result.get('error', 'Failed to register UPI ID')
            }), 400
            
    except Exception as e:
        logger.error(f"Error in UPI registration: {str(e)}")
        raise APIException(f"Failed to register UPI ID: {str(e)}", 500)


@upi_api.route('/transaction', methods=['POST'])
@token_required
@validate_request_schema(UPITransactionSchema)
@rate_limit(limit=10, period=60)
def upi_transaction():
    """
    Make a UPI transaction
    
    Request body:
        {
            "sender_upi_id": "user123@sbi",
            "receiver_upi_id": "merchant@upi",
            "amount": 100.50,
            "purpose": "Payment for goods",
            "upi_pin": "123456"
        }
        
    Returns:
        200 - Transaction successful
        400 - Invalid transaction request
        401 - Unauthorized
        403 - PIN validation failed
        500 - Server error
    """
    try:
        data = request.get_json()
        customer_id = request.user.get('customer_id')
        
        # Verify UPI PIN
        pin_verified = upi_transaction_service.verify_upi_pin(
            data['sender_upi_id'], 
            data['upi_pin']
        )
        
        if not pin_verified:
            return jsonify({
                'status': 'FAILED',
                'message': 'Invalid UPI PIN'
            }), 403
            
        # Process transaction
        result = upi_transaction_service.initiate_transaction(
            sender_upi_id=data['sender_upi_id'],
            receiver_upi_id=data['receiver_upi_id'],
            amount=data['amount'],
            purpose=data.get('purpose', 'PAYMENT')
        )
        
        if result.get('status') == 'SUCCESS':
            # Send notification
            notification_service.send_upi_notification(
                customer_id=customer_id,
                data={
                    'amount': data['amount'],
                    'sender_upi_id': data['sender_upi_id'],
                    'receiver_upi_id': data['receiver_upi_id'],
                    'is_debit': True,
                    'reference_number': result.get('reference_number')
                }
            )
            
            return jsonify({
                'status': 'SUCCESS',
                'message': 'Transaction completed successfully',
                'data': {
                    'transaction_id': result.get('transaction_id'),
                    'reference_number': result.get('reference_number'),
                    'timestamp': result.get('timestamp').isoformat() if result.get('timestamp') else datetime.datetime.now().isoformat(),
                    'amount': data['amount'],
                    'sender_upi_id': data['sender_upi_id'],
                    'receiver_upi_id': data['receiver_upi_id'],
                    'purpose': data.get('purpose', 'PAYMENT')
                }
            }), 200
        else:
            return jsonify({
                'status': 'FAILED',
                'message': result.get('error', 'Transaction failed'),
                'error_code': result.get('error_code', 'TRANSACTION_FAILED')
            }), 400
            
    except Exception as e:
        logger.error(f"Error in UPI transaction: {str(e)}")
        raise APIException(f"Failed to process transaction: {str(e)}", 500)


@upi_api.route('/balance', methods=['POST'])
@token_required
@validate_request_schema(UPIBalanceSchema)
@rate_limit(limit=20, period=60)
def upi_balance():
    """
    Check balance for a UPI ID
    
    Request body:
        {
            "upi_id": "user123@sbi"
        }
        
    Returns:
        200 - Balance inquiry successful
        400 - Invalid request
        401 - Unauthorized
        500 - Server error
    """
    try:
        data = request.get_json()
        customer_id = request.user.get('customer_id')
        
        result = upi_transaction_service.get_upi_balance(data['upi_id'])
        
        if result.get('status') == 'SUCCESS':
            return jsonify({
                'status': 'SUCCESS',
                'message': 'Balance inquiry successful',
                'data': {
                    'upi_id': data['upi_id'],
                    'balance': result.get('balance', 0.0),
                    'currency': result.get('currency', 'INR'),
                    'timestamp': datetime.datetime.now().isoformat()
                }
            }), 200
        else:
            return jsonify({
                'status': 'FAILED',
                'message': result.get('error', 'Failed to retrieve balance')
            }), 400
            
    except Exception as e:
        logger.error(f"Error in UPI balance inquiry: {str(e)}")
        raise APIException(f"Failed to retrieve balance: {str(e)}", 500)


@upi_api.route('/pin/change', methods=['POST'])
@token_required
@validate_request_schema(UPIPinChangeSchema)
@rate_limit(limit=3, period=300)  # More restrictive rate limit for security operations
def change_upi_pin():
    """
    Change UPI PIN
    
    Request body:
        {
            "upi_id": "user123@sbi",
            "old_pin": "123456",
            "new_pin": "654321",
            "confirm_pin": "654321"
        }
        
    Returns:
        200 - PIN changed successfully
        400 - Invalid request
        401 - Unauthorized
        403 - Old PIN validation failed
        500 - Server error
    """
    try:
        data = request.get_json()
        customer_id = request.user.get('customer_id')
        
        # Verify old PIN
        pin_verified = upi_transaction_service.verify_upi_pin(
            data['upi_id'], 
            data['old_pin']
        )
        
        if not pin_verified:
            return jsonify({
                'status': 'FAILED',
                'message': 'Invalid old UPI PIN'
            }), 403
        
        # Hash the new PIN
        pin_salt = uuid.uuid4().hex
        pin_hash = hash_password(data['new_pin'], pin_salt)
        
        result = upi_transaction_service.update_upi_pin(
            upi_id=data['upi_id'],
            pin_hash=pin_hash,
            pin_salt=pin_salt
        )
        
        if result.get('status') == 'SUCCESS':
            # Send security alert
            notification_service.send_security_alert(
                customer_id=customer_id,
                data={
                    'alert_type': 'PIN_CHANGE',
                    'pin_type': 'UPI PIN',
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
            
            return jsonify({
                'status': 'SUCCESS',
                'message': 'UPI PIN changed successfully',
                'data': {
                    'upi_id': data['upi_id'],
                    'updated_at': datetime.datetime.now().isoformat()
                }
            }), 200
        else:
            return jsonify({
                'status': 'FAILED',
                'message': result.get('error', 'Failed to change UPI PIN')
            }), 400
            
    except Exception as e:
        logger.error(f"Error changing UPI PIN: {str(e)}")
        raise APIException(f"Failed to change UPI PIN: {str(e)}", 500)


@upi_api.route('/qr/generate', methods=['POST'])
@token_required
@validate_request_schema(QRCodeGenerationSchema)
@rate_limit(limit=10, period=60)
def generate_qr_code():
    """
    Generate QR code for UPI payment
    
    Request body:
        {
            "upi_id": "user123@sbi",
            "amount": 100.50,
            "purpose": "Payment",
            "qr_type": "STATIC"
        }
        
    Returns:
        200 - QR code generated successfully
        400 - Invalid request
        401 - Unauthorized
        500 - Server error
    """
    try:
        data = request.get_json()
        customer_id = request.user.get('customer_id')
        
        result = upi_transaction_service.generate_qr_code(
            upi_id=data['upi_id'],
            amount=data.get('amount'),
            purpose=data.get('purpose'),
            qr_type=data.get('qr_type', 'STATIC')
        )
        
        if result.get('status') == 'SUCCESS':
            return jsonify({
                'status': 'SUCCESS',
                'message': 'QR code generated successfully',
                'data': {
                    'qr_code': result.get('qr_code'),
                    'upi_id': data['upi_id'],
                    'amount': data.get('amount'),
                    'purpose': data.get('purpose'),
                    'expiry': result.get('expiry')
                }
            }), 200
        else:
            return jsonify({
                'status': 'FAILED',
                'message': result.get('error', 'Failed to generate QR code')
            }), 400
            
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        raise APIException(f"Failed to generate QR code: {str(e)}", 500)


@upi_api.route('/transactions/history', methods=['GET'])
@token_required
@rate_limit(limit=10, period=60)
def upi_transaction_history():
    """
    Get UPI transaction history
    
    Query parameters:
        upi_id: UPI ID to get history for
        from_date: Start date (optional)
        to_date: End date (optional)
        limit: Number of transactions to return (optional, default 20)
        offset: Offset for pagination (optional, default 0)
    
    Returns:
        200 - Transaction history retrieved successfully
        400 - Invalid request
        401 - Unauthorized
        500 - Server error
    """
    try:
        upi_id = request.args.get('upi_id')
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        
        if not upi_id:
            return jsonify({
                'status': 'FAILED',
                'message': 'UPI ID is required'
            }), 400
            
        result = upi_transaction_service.get_transaction_history(
            upi_id=upi_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset
        )
        
        if result.get('status') == 'SUCCESS':
            return jsonify({
                'status': 'SUCCESS',
                'message': 'Transaction history retrieved successfully',
                'data': {
                    'transactions': result.get('transactions', []),
                    'total_count': result.get('total_count', 0),
                    'has_more': result.get('has_more', False)
                }
            }), 200
        else:
            return jsonify({
                'status': 'FAILED',
                'message': result.get('error', 'Failed to retrieve transaction history')
            }), 400
            
    except Exception as e:
        logger.error(f"Error retrieving UPI transaction history: {str(e)}")
        raise APIException(f"Failed to retrieve transaction history: {str(e)}", 500)


@upi_api.route('/collect/request', methods=['POST'])
@token_required
@validate_request_schema(UPICollectRequestSchema)
@rate_limit(limit=10, period=60)
def request_collect():
    """
    Create a UPI collect request
    
    Request body:
        {
            "requester_upi_id": "user123@sbi",
            "payer_upi_id": "merchant@upi",
            "amount": 100.50,
            "purpose": "Payment for goods"
        }
        
    Returns:
        200 - Collect request created successfully
        400 - Invalid request data
        401 - Unauthorized
        500 - Server error
    """
    try:
        data = request.get_json()
        customer_id = request.user.get('customer_id')
        
        result = upi_transaction_service.process_collect_request(
            requester_upi_id=data['requester_upi_id'],
            payer_upi_id=data['payer_upi_id'],
            amount=data['amount'],
            purpose=data.get('purpose', 'PAYMENT')
        )
        
        if result.get('status') == 'SUCCESS':
            # Send notification to payer
            notification_service.send_notification(
                customer_id=customer_id,
                notification_type="UPI_COLLECT_REQUEST",
                message=f"UPI Collect Request: {data['requester_upi_id']} has requested INR {data['amount']} from you. Ref: {result.get('reference_number')}",
                channel="SMS"
            )
            
            return jsonify({
                'status': 'SUCCESS',
                'message': 'Collect request sent successfully',
                'data': {
                    'collect_id': result.get('collect_id'),
                    'reference_number': result.get('reference_number'),
                    'amount': data['amount'],
                    'timestamp': result.get('timestamp')
                }
            }), 200
        else:
            return jsonify({
                'status': 'FAILED',
                'message': result.get('error', 'Failed to create collect request')
            }), 400
            
    except Exception as e:
        logger.error(f"Error in UPI collect request: {str(e)}")
        raise APIException(f"Failed to process collect request: {str(e)}", 500)


@upi_api.route('/collect/response', methods=['POST'])
@token_required
@validate_request_schema(UPICollectResponseSchema)
@rate_limit(limit=10, period=60)
def respond_collect():
    """
    Respond to a UPI collect request
    
    Request body:
        {
            "collect_id": "COLLECT20250511123456",
            "action": "ACCEPT" or "REJECT",
            "upi_pin": "123456" (required only for ACCEPT)
        }
        
    Returns:
        200 - Response processed successfully
        400 - Invalid request data
        401 - Unauthorized
        403 - PIN validation failed
        500 - Server error
    """
    try:
        data = request.get_json()
        customer_id = request.user.get('customer_id')
        
        result = upi_transaction_service.respond_to_collect_request(
            collect_id=data['collect_id'],
            action=data['action'],
            upi_pin=data.get('upi_pin')
        )
        
        if result.get('status') == 'SUCCESS':
            # Send notification about the response
            action_text = "accepted" if data['action'] == 'ACCEPT' else "rejected"
            
            notification_service.send_notification(
                customer_id=customer_id,
                notification_type="UPI_COLLECT_RESPONSE",
                message=f"UPI Collect Request {data['collect_id']} has been {action_text}.",
                channel="SMS"
            )
            
            return jsonify({
                'status': 'SUCCESS',
                'message': f'Collect request {action_text} successfully',
                'data': {
                    'collect_id': data['collect_id'],
                    'transaction_id': result.get('transaction_id'),
                    'reference_number': result.get('reference_number')
                }
            }), 200
        else:
            return jsonify({
                'status': 'FAILED',
                'message': result.get('error', f'Failed to {data["action"].lower()} collect request')
            }), 400
            
    except Exception as e:
        logger.error(f"Error in UPI collect response: {str(e)}")
        raise APIException(f"Failed to process collect response: {str(e)}", 500)


@upi_api.route('/collect/pending', methods=['GET'])
@token_required
@rate_limit(limit=20, period=60)
def get_pending_collects():
    """
    Get pending collect requests for a UPI ID
    
    Query Parameters:
        upi_id: UPI ID to check pending requests for
        
    Returns:
        200 - List of pending requests
        400 - Invalid request parameters
        401 - Unauthorized
        500 - Server error
    """
    try:
        upi_id = request.args.get('upi_id')
        
        if not upi_id:
            return jsonify({
                'status': 'FAILED',
                'message': 'UPI ID is required'
            }), 400
            
        result = upi_transaction_service.get_pending_collect_requests(upi_id)
        
        if result.get('status') == 'SUCCESS':
            return jsonify({
                'status': 'SUCCESS',
                'message': f'Found {result.get("count", 0)} pending collect requests',
                'data': {
                    'pending_requests': result.get('pending_requests', []),
                    'count': result.get('count', 0)
                }
            }), 200
        else:
            return jsonify({
                'status': 'FAILED',
                'message': result.get('error', 'Failed to retrieve pending collect requests')
            }), 400
            
    except Exception as e:
        logger.error(f"Error getting pending collect requests: {str(e)}")
        raise APIException(f"Failed to retrieve pending collect requests: {str(e)}", 500)
