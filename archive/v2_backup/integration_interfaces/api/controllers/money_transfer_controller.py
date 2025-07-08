"""
Money Transfer & Payments API

This module handles all money movement operations in the banking system, including:

• Sending money to other accounts
• Paying bills and utilities
• Setting up recurring transfers
• Checking payment status and history
• International remittances
• Instant payments via UPI/IMPS

All operations include security validations and transaction limits.
"""

from flask import Blueprint, request, jsonify
from app.api.middleware.authentication import token_required
from app.api.middleware.validation import validate_schema
from app.api.middleware.error_handler import APIException
from app.api.middleware.rate_limiter import rate_limit
from database.python.connection import DatabaseConnection

# Import with fallback for backward compatibility
try:
    from utils.lib.id_generator import generate_transaction_id, generate_reference_number
except ImportError:
    # Fallback to old import path
    from app.lib.id_generator import generate_transaction_id, generate_reference_number

import datetime
import uuid
import re
import html
import json


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
# Create blueprint
transaction_api = Blueprint('transaction_api', __name__)

# Initialize database connection
db_connection = DatabaseConnection()

@transaction_api.route('/transfer', methods=['POST'])
@token_required
@rate_limit(max_requests=10, time_window=60)  # 10 transfers per minute
def fund_transfer(current_user):
    """
    Transfer funds between accounts
    
    Request body:
    {
        "from_account": "string",
        "to_account": "string",
        "amount": number,
        "purpose": "string",
        "remarks": "string"
    }
    """
    conn = None
    cursor = None
    try:
        # Validate and sanitize incoming JSON data
        try:
            data = request.get_json()
            if not data:
                raise APIException(
                    "Missing request body", 
                    "MISSING_DATA", 
                    400
                )
        except json.JSONDecodeError:
            raise APIException(
                "Invalid JSON format in request body",
                "INVALID_JSON",
                400
            )
            
        # Validate required fields
        required_fields = ['from_account', 'to_account', 'amount']
        for field in required_fields:
            if field not in data:
                raise APIException(
                    f"Missing required field: {field}", 
                    "MISSING_FIELD", 
                    400
                )
        
        # Sanitize and validate account numbers (prevent SQL injection)
        account_pattern = r'^[A-Z0-9]{8,16}$'
        if not re.match(account_pattern, str(data['from_account'])):
            raise APIException(
                "Invalid source account format", 
                "INVALID_SOURCE_ACCOUNT_FORMAT", 
                400
            )
            
        if not re.match(account_pattern, str(data['to_account'])):
            raise APIException(
                "Invalid destination account format", 
                "INVALID_DESTINATION_ACCOUNT_FORMAT", 
                400
            )
            
        # Validate and sanitize amount
        try:
            amount = float(data['amount'])
            if amount <= 0:
                raise APIException(
                    "Amount must be greater than zero",
                    "INVALID_AMOUNT",
                    400
                )
        except ValueError:
            raise APIException(
                "Invalid amount format",
                "INVALID_AMOUNT_FORMAT",
                400
            )
            
        # Sanitize purpose and remarks fields to prevent XSS
        purpose = data.get('purpose', 'Fund Transfer')
        if purpose:
            # Remove any potentially dangerous HTML/script content
            purpose = html.escape(purpose)
            # Limit length to prevent buffer issues
            purpose = purpose[:100] if len(purpose) > 100 else purpose
            
        remarks = data.get('remarks', '')
        if remarks:
            # Remove any potentially dangerous HTML/script content
            remarks = html.escape(remarks)
            # Limit length to prevent buffer issues
            remarks = remarks[:255] if len(remarks) > 255 else remarks
            
        # Initialize database connection with proper error handling
        try:
            conn = db_connection.get_connection()
            cursor = conn.cursor(dictionary=True)
        except Exception as db_error:
            raise APIException(
                "Database connection error",
                "DB_CONNECTION_ERROR",
                500
            )
            
        # Start a database transaction
        try:
            conn.start_transaction()
        except Exception as tx_error:
            raise APIException(
                "Failed to start transaction",
                "TRANSACTION_START_ERROR",
                500
            )
            
        try:
            # Check if source account exists and belongs to the current user
            cursor.execute(
                """
                SELECT a.* FROM accounts a
                JOIN customers c ON a.customer_id = c.id
                WHERE a.account_number = %s AND c.user_id = %s
                """,
                (data['from_account'], current_user['id'])
            )
            
            source_account = cursor.fetchone()
            
            if not source_account:
                conn.rollback()
                raise APIException(
                    "Source account not found or unauthorized", 
                    "ACCOUNT_NOT_FOUND", 
                    404
                )
                
            # Check for sufficient balance
            if source_account['balance'] < amount:
                conn.rollback()
                raise APIException(
                    "Insufficient balance", 
                    "INSUFFICIENT_BALANCE", 
                    400
                )
                
            # Check if destination account exists
            cursor.execute(
                "SELECT * FROM accounts WHERE account_number = %s",
                (data['to_account'],)
            )
            
            destination_account = cursor.fetchone()
            
            if not destination_account:
                conn.rollback()
                raise APIException(
                    "Destination account not found", 
                    "ACCOUNT_NOT_FOUND", 
                    404
                )
                
            # Generate transaction IDs using secure methods
            transaction_id = generate_transaction_id(channel="MOBILE")
            reference_number = generate_reference_number()
            
            # Create debit transaction with parameterized queries
            cursor.execute(
                """
                INSERT INTO transactions
                (transaction_id, account_id, transaction_type, channel, amount, 
                 balance_before, balance_after, currency, description, 
                 transaction_date, value_date, reference_number, remarks, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s, %s)
                """,
                (
                    transaction_id,
                    source_account['id'],
                    'TRANSFER_DEBIT',
                    'MOBILE',
                    amount,
                    source_account['balance'],
                    source_account['balance'] - amount,
                    'INR',
                    f"Transfer to {html.escape(str(data['to_account']))}",
                    reference_number,
                    remarks,
                    'SUCCESS'
                )
            )
            
            # Update source account balance
            cursor.execute(
                """
                UPDATE accounts
                SET balance = balance - %s,
                    last_updated = NOW()
                WHERE id = %s
                """,
                (amount, source_account['id'])
            )
            
            # Create credit transaction
            cursor.execute(
                """
                INSERT INTO transactions
                (transaction_id, account_id, transaction_type, channel, amount, 
                 balance_before, balance_after, currency, description, 
                 transaction_date, value_date, reference_number, remarks, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s, %s)
                """,
                (
                    transaction_id,
                    destination_account['id'],
                    'TRANSFER_CREDIT',
                    'MOBILE',
                    amount,
                    destination_account['balance'],
                    destination_account['balance'] + amount,
                    'INR',
                    f"Transfer from {html.escape(str(data['from_account']))}",
                    reference_number,
                    remarks,
                    'SUCCESS'
                )
            )
            
            # Update destination account balance
            cursor.execute(
                """
                UPDATE accounts
                SET balance = balance + %s,
                    last_updated = NOW()
                WHERE id = %s
                """,
                (amount, destination_account['id'])
            )
            
            # Commit the transaction
            conn.commit()
            
            # Prepare response
            response = {
                "status": "SUCCESS",
                "message": "Fund transfer completed successfully",
                "transaction_id": transaction_id,
                "reference_number": reference_number,
                "date": datetime.datetime.now().isoformat(),
                "from_account": data['from_account'],
                "to_account": data['to_account'],
                "amount": amount,
                "purpose": purpose,
                "remarks": remarks
            }
            
            return jsonify(response), 200
            
        except Exception as e:
            # Roll back transaction on any error
            try:
                conn.rollback()
            except Exception as rollback_error:
                pass  # Already in error state
                
            raise APIException(
                "Transaction failed", 
                "TRANSACTION_FAILED", 
                500
            )
    except APIException as api_error:
        # API exceptions are already formatted
        return jsonify({
            "status": "FAILED",
            "error": api_error.message,
            "error_code": api_error.error_code
        }), api_error.status_code
    except Exception as e:
        # Catch any other exceptions
        return jsonify({
            "status": "FAILED",
            "error": "An unexpected error occurred",
            "error_code": "SYSTEM_ERROR"
        }), 500
    finally:
        # Safely close database resources
        try:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        except Exception:
            pass  # Already in error state

@transaction_api.route('/transaction/<transaction_id>', methods=['GET'])
@token_required
def get_transaction_details(current_user, transaction_id):
    """
    Get details of a specific transaction
    """
    conn = None
    cursor = None
    try:
        # Validate transaction_id format to prevent SQL injection
        if not re.match(r'^[A-Za-z0-9\-]{10,36}$', transaction_id):
            raise APIException(
                "Invalid transaction ID format", 
                "INVALID_TRANSACTION_ID", 
                400
            )
            
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query using parameterized query to prevent SQL injection
        cursor.execute(
            """
            SELECT t.*, a.account_number
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            JOIN customers c ON a.customer_id = c.id
            WHERE t.transaction_id = %s AND c.user_id = %s
            """,
            (transaction_id, current_user['id'])
        )
        
        transaction = cursor.fetchone()
        
        if not transaction:
            raise APIException(
                "Transaction not found or unauthorized", 
                "TRANSACTION_NOT_FOUND", 
                404
            )
            
        return jsonify(transaction), 200
        
    except APIException as api_error:
        return jsonify({
            "status": "FAILED",
            "error": api_error.message,
            "error_code": api_error.error_code
        }), api_error.status_code
    except Exception as e:
        return jsonify({
            "status": "FAILED",
            "error": "An unexpected error occurred",
            "error_code": "SYSTEM_ERROR"
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
