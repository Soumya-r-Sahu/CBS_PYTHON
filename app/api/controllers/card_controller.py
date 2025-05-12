"""
Card Management Controller for Mobile Banking API

Handles card-related operations including activation, PIN management, and limits
"""

from flask import Blueprint, request, jsonify
from app.api.middleware.authentication import token_required
from app.api.middleware.validation import validate_request_schema
from app.api.middleware.error_handler import APIException
from app.api.middleware.rate_limiter import rate_limit
from app.api.schemas.card_schemas import (
    CardActivationSchema, 
    CardPINSetSchema, 
    CardPINChangeSchema, 
    CardBlockSchema, 
    CardLimitUpdateSchema
)
from app.lib.encryption import hash_password, verify_password
from database.connection import DatabaseConnection
from app.api.services.notification_service import NotificationService
import datetime
import uuid
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
card_api = Blueprint('card_api', __name__)

# Initialize services
db_connection = DatabaseConnection()
notification_service = NotificationService(db_connection)


@card_api.route('/activate', methods=['POST'])
@token_required
@validate_request_schema(CardActivationSchema)
@rate_limit(limit=3, period=300)  # Restrictive rate limit for security operations
def activate_card():
    """
    Activate a new card
    
    Request body:
        {
            "card_number": "1234567890123456",
            "expiry_date": "12/25",
            "cvv": "123"
        }
        
    Returns:
        200 - Card activated successfully
        400 - Invalid card details
        401 - Unauthorized
        500 - Server error
    """
    try:
        data = request.get_json()
        customer_id = request.user.get('customer_id')
        
        # Mask card number for logging
        masked_card = f"{'*' * 12}{data['card_number'][-4:]}"
        logger.info(f"Card activation request for {masked_card}")
        
        # Validate card details in database
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute(
                """
                SELECT c.id, c.card_number, c.expiry_date, c.cvv, c.status,
                       c.customer_id, cu.email
                FROM cards c
                JOIN customers cu ON c.customer_id = cu.id
                WHERE c.card_number = %s 
                AND c.expiry_date = %s 
                AND c.cvv = %s
                """,
                (data['card_number'], data['expiry_date'], data['cvv'])
            )
            
            card = cursor.fetchone()
            
            if not card:
                return jsonify({
                    'status': 'FAILED',
                    'message': 'Invalid card details'
                }), 400
                
            if card['status'] != 'ISSUED':
                return jsonify({
                    'status': 'FAILED',
                    'message': f"Card cannot be activated. Current status: {card['status']}"
                }), 400
                
            if str(card['customer_id']) != customer_id:
                return jsonify({
                    'status': 'FAILED',
                    'message': 'Card does not belong to this customer'
                }), 403
                
            # Update card status
            cursor.execute(
                """
                UPDATE cards
                SET status = 'ACTIVE', activated_at = NOW()
                WHERE id = %s
                """,
                (card['id'],)
            )
            
            conn.commit()
            
            # Send notification
            notification_service.send_notification(
                customer_id=customer_id,
                notification_type="CARD_ACTIVATION",
                message=f"Your card ending with {masked_card[-4:]} has been activated successfully.",
                channel="EMAIL",
                data={
                    'card_id': card['id'],
                    'masked_card': masked_card,
                    'activated_at': datetime.datetime.now().isoformat()
                }
            )
            
            return jsonify({
                'status': 'SUCCESS',
                'message': 'Card activated successfully',
                'data': {
                    'card_id': card['id'],
                    'masked_card_number': masked_card,
                    'status': 'ACTIVE',
                    'activated_at': datetime.datetime.now().isoformat()
                }
            }), 200
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error during card activation: {str(e)}")
            raise
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error in card activation: {str(e)}")
        raise APIException(f"Failed to activate card: {str(e)}", 500)


@card_api.route('/pin/set', methods=['POST'])
@token_required
@validate_request_schema(CardPINSetSchema)
@rate_limit(limit=3, period=300)  # Restrictive rate limit for security operations
def set_card_pin():
    """
    Set PIN for a card
    
    Request body:
        {
            "card_number": "1234567890123456",
            "pin": "1234",
            "confirm_pin": "1234"
        }
        
    Returns:
        200 - PIN set successfully
        400 - Invalid request data
        401 - Unauthorized
        500 - Server error
    """
    try:
        data = request.get_json()
        customer_id = request.user.get('customer_id')
        
        # Mask card number for logging
        masked_card = f"{'*' * 12}{data['card_number'][-4:]}"
        logger.info(f"Card PIN set request for {masked_card}")
        
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Validate card ownership
            cursor.execute(
                """
                SELECT id, card_number, status, customer_id
                FROM cards
                WHERE card_number = %s
                """,
                (data['card_number'],)
            )
            
            card = cursor.fetchone()
            
            if not card:
                return jsonify({
                    'status': 'FAILED',
                    'message': 'Card not found'
                }), 404
                
            if str(card['customer_id']) != customer_id:
                return jsonify({
                    'status': 'FAILED',
                    'message': 'Card does not belong to this customer'
                }), 403
                
            if card['status'] not in ['ACTIVE', 'PIN_CHANGE_REQUIRED']:
                return jsonify({
                    'status': 'FAILED',
                    'message': f"Card is not in a valid state for PIN setting. Current status: {card['status']}"
                }), 400
                
            # Generate salt and hash PIN
            pin_salt = uuid.uuid4().hex
            pin_hash = hash_password(data['pin'], pin_salt)
            
            # Store PIN hash and salt
            cursor.execute(
                """
                UPDATE cards
                SET pin_hash = %s, 
                    pin_salt = %s, 
                    pin_set_at = NOW(),
                    status = 'ACTIVE'
                WHERE id = %s
                """,
                (pin_hash, pin_salt, card['id'])
            )
            
            conn.commit()
            
            # Send notification
            notification_service.send_security_alert(
                customer_id=customer_id,
                data={
                    'alert_type': 'PIN_CHANGE',
                    'pin_type': 'Card PIN',
                    'masked_card': masked_card,
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
            
            return jsonify({
                'status': 'SUCCESS',
                'message': 'Card PIN set successfully',
                'data': {
                    'masked_card_number': masked_card,
                    'updated_at': datetime.datetime.now().isoformat()
                }
            }), 200
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error during card PIN setting: {str(e)}")
            raise
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error in card PIN setting: {str(e)}")
        raise APIException(f"Failed to set card PIN: {str(e)}", 500)


@card_api.route('/pin/change', methods=['POST'])
@token_required
@validate_request_schema(CardPINChangeSchema)
@rate_limit(limit=3, period=300)  # Restrictive rate limit for security operations
def change_card_pin():
    """
    Change PIN for a card
    
    Request body:
        {
            "card_number": "1234567890123456",
            "current_pin": "1234",
            "new_pin": "5678",
            "confirm_pin": "5678"
        }
        
    Returns:
        200 - PIN changed successfully
        400 - Invalid request data
        401 - Unauthorized
        403 - Current PIN verification failed
        500 - Server error
    """
    try:
        data = request.get_json()
        customer_id = request.user.get('customer_id')
        
        # Mask card number for logging
        masked_card = f"{'*' * 12}{data['card_number'][-4:]}"
        logger.info(f"Card PIN change request for {masked_card}")
        
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Validate card ownership and get current PIN data
            cursor.execute(
                """
                SELECT id, card_number, status, customer_id, pin_hash, pin_salt
                FROM cards
                WHERE card_number = %s
                """,
                (data['card_number'],)
            )
            
            card = cursor.fetchone()
            
            if not card:
                return jsonify({
                    'status': 'FAILED',
                    'message': 'Card not found'
                }), 404
                
            if str(card['customer_id']) != customer_id:
                return jsonify({
                    'status': 'FAILED',
                    'message': 'Card does not belong to this customer'
                }), 403
                
            if card['status'] != 'ACTIVE':
                return jsonify({
                    'status': 'FAILED',
                    'message': f"Card is not active. Current status: {card['status']}"
                }), 400
            
            # Verify current PIN
            if not verify_password(data['current_pin'], card['pin_hash'], card['pin_salt']):
                logger.warning(f"Failed PIN verification attempt for card {masked_card}")
                return jsonify({
                    'status': 'FAILED',
                    'message': 'Current PIN is incorrect'
                }), 403
                
            # Generate new salt and hash for new PIN
            pin_salt = uuid.uuid4().hex
            pin_hash = hash_password(data['new_pin'], pin_salt)
            
            # Update PIN hash and salt
            cursor.execute(
                """
                UPDATE cards
                SET pin_hash = %s, 
                    pin_salt = %s, 
                    pin_set_at = NOW()
                WHERE id = %s
                """,
                (pin_hash, pin_salt, card['id'])
            )
            
            conn.commit()
            
            # Send security alert
            notification_service.send_security_alert(
                customer_id=customer_id,
                data={
                    'alert_type': 'PIN_CHANGE',
                    'pin_type': 'Card PIN',
                    'masked_card': masked_card,
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
            
            return jsonify({
                'status': 'SUCCESS',
                'message': 'Card PIN changed successfully',
                'data': {
                    'masked_card_number': masked_card,
                    'updated_at': datetime.datetime.now().isoformat()
                }
            }), 200
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error during card PIN change: {str(e)}")
            raise
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error in card PIN change: {str(e)}")
        raise APIException(f"Failed to change card PIN: {str(e)}", 500)


@card_api.route('/block', methods=['POST'])
@token_required
@validate_request_schema(CardBlockSchema)
@rate_limit(limit=5, period=300)  # Restrictive rate limit for security operations
def block_card():
    """
    Block a card
    
    Request body:
        {
            "card_number": "1234567890123456",
            "reason": "LOST",
            "additional_info": "Lost while traveling"
        }
        
    Returns:
        200 - Card blocked successfully
        400 - Invalid request data
        401 - Unauthorized
        500 - Server error
    """
    try:
        data = request.get_json()
        customer_id = request.user.get('customer_id')
        
        # Mask card number for logging
        masked_card = f"{'*' * 12}{data['card_number'][-4:]}"
        logger.info(f"Card block request for {masked_card}, reason: {data['reason']}")
        
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Validate card ownership
            cursor.execute(
                """
                SELECT id, card_number, status, customer_id
                FROM cards
                WHERE card_number = %s
                """,
                (data['card_number'],)
            )
            
            card = cursor.fetchone()
            
            if not card:
                return jsonify({
                    'status': 'FAILED',
                    'message': 'Card not found'
                }), 404
                
            if str(card['customer_id']) != customer_id:
                return jsonify({
                    'status': 'FAILED',
                    'message': 'Card does not belong to this customer'
                }), 403
                
            if card['status'] in ['BLOCKED', 'EXPIRED']:
                return jsonify({
                    'status': 'FAILED',
                    'message': f"Card is already in {card['status']} state"
                }), 400
                
            # Block the card
            cursor.execute(
                """
                UPDATE cards
                SET status = 'BLOCKED', 
                    block_reason = %s,
                    blocked_at = NOW(),
                    additional_info = %s
                WHERE id = %s
                """,
                (data['reason'], data.get('additional_info'), card['id'])
            )
            
            conn.commit()
            
            # Send security alert (high priority)
            notification_service.send_security_alert(
                customer_id=customer_id,
                data={
                    'alert_type': 'CARD_BLOCKED',
                    'reason': data['reason'],
                    'masked_card': masked_card,
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
            
            # Also send SMS notification for immediate awareness
            notification_service.send_notification(
                customer_id=customer_id,
                notification_type="CARD_BLOCKED",
                message=f"Your card ending with {masked_card[-4:]} has been blocked. Reason: {data['reason']}",
                channel="SMS"
            )
            
            return jsonify({
                'status': 'SUCCESS',
                'message': 'Card blocked successfully',
                'data': {
                    'masked_card_number': masked_card,
                    'status': 'BLOCKED',
                    'reason': data['reason'],
                    'blocked_at': datetime.datetime.now().isoformat()
                }
            }), 200
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error during card blocking: {str(e)}")
            raise
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error in card blocking: {str(e)}")
        raise APIException(f"Failed to block card: {str(e)}", 500)


@card_api.route('/limits/update', methods=['POST'])
@token_required
@validate_request_schema(CardLimitUpdateSchema)
@rate_limit(limit=10, period=60)
def update_card_limits():
    """
    Update card usage limits
    
    Request body:
        {
            "card_number": "1234567890123456",
            "daily_atm_limit": 25000,
            "daily_pos_limit": 50000,
            "daily_online_limit": 30000,
            "domestic_usage": true,
            "international_usage": false,
            "contactless_enabled": true
        }
        
    Returns:
        200 - Limits updated successfully
        400 - Invalid request data
        401 - Unauthorized
        500 - Server error
    """
    try:
        data = request.get_json()
        customer_id = request.user.get('customer_id')
        
        # Mask card number for logging
        masked_card = f"{'*' * 12}{data['card_number'][-4:]}"
        logger.info(f"Card limits update request for {masked_card}")
        
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Validate card ownership
            cursor.execute(
                """
                SELECT id, card_number, status, customer_id
                FROM cards
                WHERE card_number = %s
                """,
                (data['card_number'],)
            )
            
            card = cursor.fetchone()
            
            if not card:
                return jsonify({
                    'status': 'FAILED',
                    'message': 'Card not found'
                }), 404
                
            if str(card['customer_id']) != customer_id:
                return jsonify({
                    'status': 'FAILED',
                    'message': 'Card does not belong to this customer'
                }), 403
                
            if card['status'] != 'ACTIVE':
                return jsonify({
                    'status': 'FAILED',
                    'message': f"Card is not active. Current status: {card['status']}"
                }), 400
                
            # Update card limits
            update_fields = []
            update_values = []
            
            # Build dynamic update query based on provided fields
            for field in ['daily_atm_limit', 'daily_pos_limit', 'daily_online_limit']:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    update_values.append(data[field])
                    
            for field in ['domestic_usage', 'international_usage', 'contactless_enabled']:
                if field in data:
                    update_fields.append(f"{field} = %s")
                    update_values.append(1 if data[field] else 0)
            
            if not update_fields:
                return jsonify({
                    'status': 'FAILED',
                    'message': 'No fields to update'
                }), 400
                
            # Add card ID to update values
            update_values.append(card['id'])
            
            # Execute update
            cursor.execute(
                f"""
                UPDATE card_limits
                SET {', '.join(update_fields)},
                    updated_at = NOW()
                WHERE card_id = %s
                """,
                tuple(update_values)
            )
            
            conn.commit()
            
            # Send notification
            notification_service.send_notification(
                customer_id=customer_id,
                notification_type="CARD_LIMIT_UPDATE",
                message=f"Your card ending with {masked_card[-4:]} limits have been updated.",
                channel="EMAIL",
                data={
                    'masked_card': masked_card,
                    'updated_limits': {k: v for k, v in data.items() if k not in ['card_number']}
                }
            )
            
            return jsonify({
                'status': 'SUCCESS',
                'message': 'Card limits updated successfully',
                'data': {
                    'masked_card_number': masked_card,
                    'updated_at': datetime.datetime.now().isoformat()
                }
            }), 200
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error during card limits update: {str(e)}")
            raise
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error in card limits update: {str(e)}")
        raise APIException(f"Failed to update card limits: {str(e)}", 500)
