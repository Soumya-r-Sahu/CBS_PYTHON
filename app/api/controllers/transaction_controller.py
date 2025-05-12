"""
Transaction Controller for Mobile Banking API

Handles transaction-related operations including fund transfers, transaction details,
and status inquiries.
"""

from flask import Blueprint, request, jsonify
from app.api.middleware.authentication import token_required
from app.api.middleware.validation import validate_schema
from app.api.middleware.error_handler import APIException
from app.api.middleware.rate_limiter import rate_limit
from database.connection import DatabaseConnection
from app.lib.id_generator import generate_transaction_id, generate_reference_number
import datetime
import uuid

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
    try:
        data = request.get_json()
        
        if not data:
            raise APIException(
                "Missing request body", 
                "MISSING_DATA", 
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
                
        # Validate amount
        if not isinstance(data['amount'], (int, float)) or data['amount'] <= 0:
            raise APIException(
                "Amount must be a positive number", 
                "INVALID_AMOUNT", 
                400
            )
            
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if source account belongs to user
        cursor.execute(
            """
            SELECT a.id, a.account_number, a.balance, a.minimum_balance, a.is_active
            FROM accounts a
            JOIN customers c ON a.customer_id = c.id
            WHERE a.account_number = %s AND c.customer_id = %s
            """,
            (data['from_account'], current_user['customer_id'])
        )
        
        source_account = cursor.fetchone()
        
        if not source_account:
            raise APIException(
                "Source account not found or does not belong to authenticated user", 
                "SOURCE_ACCOUNT_NOT_FOUND", 
                404
            )
            
        # Check if source account is active
        if not source_account['is_active']:
            raise APIException(
                "Source account is not active", 
                "INACTIVE_ACCOUNT", 
                400
            )
            
        # Check if destination account exists
        cursor.execute(
            """
            SELECT id, account_number, is_active
            FROM accounts
            WHERE account_number = %s
            """,
            (data['to_account'],)
        )
        
        dest_account = cursor.fetchone()
        
        if not dest_account:
            raise APIException(
                "Destination account not found", 
                "DEST_ACCOUNT_NOT_FOUND", 
                404
            )
            
        # Check if destination account is active
        if not dest_account['is_active']:
            raise APIException(
                "Destination account is not active", 
                "INACTIVE_DEST_ACCOUNT", 
                400
            )
            
        # Check sufficient balance
        if source_account['balance'] - data['amount'] < source_account['minimum_balance']:
            raise APIException(
                "Insufficient balance", 
                "INSUFFICIENT_BALANCE", 
                400
            )
            
        # Generate transaction IDs
        transaction_id = generate_transaction_id(channel="MOBILE")
        reference_number = generate_reference_number()
        
        # Create debit transaction
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
                data['amount'],
                source_account['balance'],
                source_account['balance'] - data['amount'],
                'INR',
                f"Transfer to {data['to_account']}",
                reference_number,
                data.get('remarks', ''),
                'SUCCESS'
            )
        )
        
        # Create credit transaction
        credit_transaction_id = generate_transaction_id(channel="MOBILE")
        
        cursor.execute(
            """
            INSERT INTO transactions
            (transaction_id, account_id, transaction_type, channel, amount, 
             balance_before, balance_after, currency, description, 
             transaction_date, value_date, reference_number, remarks, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), %s, %s, %s)
            """,
            (
                credit_transaction_id,
                dest_account['id'],
                'TRANSFER_CREDIT',
                'MOBILE',
                data['amount'],
                0,  # We don't know the destination balance (for security)
                0,  # We don't know the destination balance (for security)
                'INR',
                f"Transfer from {data['from_account']}",
                reference_number,
                data.get('remarks', ''),
                'SUCCESS'
            )
        )
        
        # Update account balances
        cursor.execute(
            """
            UPDATE accounts
            SET balance = balance - %s
            WHERE id = %s
            """,
            (data['amount'], source_account['id'])
        )
        
        cursor.execute(
            """
            UPDATE accounts
            SET balance = balance + %s
            WHERE id = %s
            """,
            (data['amount'], dest_account['id'])
        )
        
        # Create transfer record
        cursor.execute(
            """
            INSERT INTO fund_transfers
            (reference_number, from_account_id, to_account_id, amount, 
             purpose, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                reference_number,
                source_account['id'],
                dest_account['id'],
                data['amount'],
                data.get('purpose', 'Payment'),
                'SUCCESS'
            )
        )
        
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Transfer completed successfully',
            'data': {
                'transaction_id': transaction_id,
                'reference_number': reference_number,
                'amount': data['amount'],
                'from_account': data['from_account'],
                'to_account': data['to_account'],
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 200
        
    except APIException as e:
        conn.rollback()
        raise e
    except Exception as e:
        conn.rollback()
        # Log the error
        print(f"Fund Transfer Error: {str(e)}")
        raise APIException(
            "Failed to process transfer", 
            "TRANSFER_FAILED", 
            500
        )
    finally:
        cursor.close()
        conn.close()


@transaction_api.route('/<transaction_id>', methods=['GET'])
@token_required
def get_transaction_details(current_user, transaction_id):
    """
    Get details of a specific transaction
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if transaction belongs to user
        cursor.execute(
            """
            SELECT t.*, a.account_number
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            JOIN customers c ON a.customer_id = c.id
            WHERE t.transaction_id = %s AND c.customer_id = %s
            """,
            (transaction_id, current_user['customer_id'])
        )
        
        transaction = cursor.fetchone()
        
        if not transaction:
            raise APIException(
                "Transaction not found or does not belong to authenticated user", 
                "TRANSACTION_NOT_FOUND", 
                404
            )
            
        # Format dates
        if 'transaction_date' in transaction and transaction['transaction_date']:
            transaction['transaction_date'] = transaction['transaction_date'].strftime('%Y-%m-%d %H:%M:%S')
        if 'value_date' in transaction and transaction['value_date']:
            transaction['value_date'] = transaction['value_date'].strftime('%Y-%m-%d')
            
        # Get related transactions (e.g., for transfers)
        related_transactions = []
        
        if transaction['reference_number'] and transaction['transaction_type'] in ['TRANSFER_DEBIT', 'TRANSFER_CREDIT']:
            cursor.execute(
                """
                SELECT t.transaction_id, t.transaction_type, t.amount, t.status,
                       a.account_number
                FROM transactions t
                JOIN accounts a ON t.account_id = a.id
                WHERE t.reference_number = %s AND t.transaction_id != %s
                """,
                (transaction['reference_number'], transaction['transaction_id'])
            )
            
            related_transactions = cursor.fetchall()
        
        return jsonify({
            'status': 'success',
            'data': {
                'transaction': transaction,
                'related_transactions': related_transactions
            }
        }), 200
        
    except APIException as e:
        raise e
    except Exception as e:
        # Log the error
        print(f"Get Transaction Details Error: {str(e)}")
        raise APIException(
            "Failed to fetch transaction details", 
            "FETCH_TRANSACTION_FAILED", 
            500
        )
    finally:
        cursor.close()
        conn.close()


@transaction_api.route('/status/<reference_number>', methods=['GET'])
@token_required
def check_transaction_status(current_user, reference_number):
    """
    Check status of a transaction by reference number
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if transaction belongs to user
        cursor.execute(
            """
            SELECT t.transaction_id, t.transaction_type, t.amount, t.status,
                   t.transaction_date, a.account_number
            FROM transactions t
            JOIN accounts a ON t.account_id = a.id
            JOIN customers c ON a.customer_id = c.id
            WHERE t.reference_number = %s AND c.customer_id = %s
            """,
            (reference_number, current_user['customer_id'])
        )
        
        transactions = cursor.fetchall()
        
        if not transactions:
            raise APIException(
                "Transaction not found or does not belong to authenticated user", 
                "TRANSACTION_NOT_FOUND", 
                404
            )
            
        # Format dates
        for tx in transactions:
            if 'transaction_date' in tx and tx['transaction_date']:
                tx['transaction_date'] = tx['transaction_date'].strftime('%Y-%m-%d %H:%M:%S')
        
        # For fund transfers, get additional details
        transfer_info = None
        
        if any(tx['transaction_type'] in ['TRANSFER_DEBIT', 'TRANSFER_CREDIT'] for tx in transactions):
            cursor.execute(
                """
                SELECT ft.*, 
                       a1.account_number as from_account,
                       a2.account_number as to_account
                FROM fund_transfers ft
                JOIN accounts a1 ON ft.from_account_id = a1.id
                JOIN accounts a2 ON ft.to_account_id = a2.id
                WHERE ft.reference_number = %s
                """,
                (reference_number,)
            )
            
            transfer_info = cursor.fetchone()
            
            if transfer_info and 'created_at' in transfer_info and transfer_info['created_at']:
                transfer_info['created_at'] = transfer_info['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'status': 'success',
            'data': {
                'reference_number': reference_number,
                'transactions': transactions,
                'transfer_info': transfer_info
            }
        }), 200
        
    except APIException as e:
        raise e
    except Exception as e:
        # Log the error
        print(f"Check Transaction Status Error: {str(e)}")
        raise APIException(
            "Failed to check transaction status", 
            "CHECK_STATUS_FAILED", 
            500
        )
    finally:
        cursor.close()
        conn.close()
