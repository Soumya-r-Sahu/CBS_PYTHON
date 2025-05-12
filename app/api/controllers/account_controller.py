"""
Account Controller for Mobile Banking API

Handles account-related operations including fetching account details,
statements, and transfers
"""

from flask import Blueprint, request, jsonify
from app.api.middleware.authentication import token_required
from app.api.middleware.error_handler import APIException
from database.connection import DatabaseConnection
import datetime

# Create blueprint
account_api = Blueprint('account_api', __name__)

# Initialize database connection
db_connection = DatabaseConnection()

@account_api.route('/', methods=['GET'])
@token_required
def get_user_accounts(current_user):
    """
    Get all accounts associated with the customer
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            """
            SELECT a.account_number, a.account_type, a.balance, a.currency,
                   a.branch_code, a.ifsc_code, a.account_status, a.minimum_balance,
                   a.opening_date, a.is_active
            FROM accounts a
            JOIN customers c ON a.customer_id = c.id
            WHERE c.customer_id = %s
            """,
            (current_user['customer_id'],)
        )
        
        accounts = cursor.fetchall()
        
        # Format dates for display
        for account in accounts:
            if 'opening_date' in account and account['opening_date']:
                account['opening_date'] = account['opening_date'].strftime('%Y-%m-%d')
        
        return jsonify({
            'status': 'success',
            'data': {
                'accounts': accounts
            }
        }), 200
        
    except Exception as e:
        # Log the error
        print(f"Get Accounts Error: {str(e)}")
        raise APIException(
            "Failed to fetch accounts", 
            "FETCH_ACCOUNTS_FAILED", 
            500
        )
    finally:
        cursor.close()
        conn.close()


@account_api.route('/<account_number>', methods=['GET'])
@token_required
def get_account_details(current_user, account_number):
    """
    Get detailed information about a specific account
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if account belongs to user
        cursor.execute(
            """
            SELECT a.*, c.name as branch_name
            FROM accounts a
            JOIN customers cu ON a.customer_id = cu.id
            LEFT JOIN branches c ON a.branch_code = c.branch_code
            WHERE a.account_number = %s AND cu.customer_id = %s
            """,
            (account_number, current_user['customer_id'])
        )
        
        account = cursor.fetchone()
        
        if not account:
            raise APIException(
                "Account not found or does not belong to authenticated user", 
                "ACCOUNT_NOT_FOUND", 
                404
            )
            
        # Format dates for display
        if 'opening_date' in account and account['opening_date']:
            account['opening_date'] = account['opening_date'].strftime('%Y-%m-%d')
        
        # Get linked UPI accounts
        cursor.execute(
            """
            SELECT upi_id, is_active, daily_limit, per_transaction_limit
            FROM upi_accounts
            WHERE account_id = %s
            """,
            (account['id'],)
        )
        
        upi_accounts = cursor.fetchall()
        
        # Get linked cards
        cursor.execute(
            """
            SELECT card_id, card_type, card_network, 
                   CONCAT(SUBSTRING(card_number, 1, 4), '******', 
                          SUBSTRING(card_number, -4)) as masked_card_number,
                   DATE_FORMAT(expiry_date, '%m/%Y') as expiry_date,
                   is_active, status
            FROM cards
            WHERE account_id = %s
            """,
            (account['id'],)
        )
        
        cards = cursor.fetchall()
        
        return jsonify({
            'status': 'success',
            'data': {
                'account': account,
                'upi_accounts': upi_accounts,
                'cards': cards
            }
        }), 200
        
    except APIException as e:
        raise e
    except Exception as e:
        # Log the error
        print(f"Get Account Details Error: {str(e)}")
        raise APIException(
            "Failed to fetch account details", 
            "FETCH_DETAILS_FAILED", 
            500
        )
    finally:
        cursor.close()
        conn.close()


@account_api.route('/<account_number>/statement', methods=['GET'])
@token_required
def get_account_statement(current_user, account_number):
    """
    Get transaction statement for an account
    
    Query parameters:
    - from_date: Start date (YYYY-MM-DD)
    - to_date: End date (YYYY-MM-DD)
    - limit: Maximum number of transactions (default: 50)
    """
    try:
        # Get query parameters
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date', datetime.datetime.now().strftime('%Y-%m-%d'))
        limit = int(request.args.get('limit', 50))
        
        if limit > 100:
            limit = 100  # Cap at 100 for performance
            
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if account belongs to user
        cursor.execute(
            """
            SELECT id FROM accounts a
            JOIN customers c ON a.customer_id = c.id
            WHERE a.account_number = %s AND c.customer_id = %s
            """,
            (account_number, current_user['customer_id'])
        )
        
        account = cursor.fetchone()
        
        if not account:
            raise APIException(
                "Account not found or does not belong to authenticated user", 
                "ACCOUNT_NOT_FOUND", 
                404
            )
            
        # Build query based on date parameters
        query = """
            SELECT transaction_id, transaction_type, channel, amount, 
                   balance_before, balance_after, currency, description, 
                   transaction_date, value_date, reference_number, status
            FROM transactions
            WHERE account_id = %s
        """
        
        params = [account['id']]
        
        if from_date:
            query += " AND transaction_date >= %s"
            params.append(from_date)
            
        query += " AND transaction_date <= %s"
        params.append(to_date)
        
        query += " ORDER BY transaction_date DESC LIMIT %s"
        params.append(limit)
        
        # Execute query
        cursor.execute(query, params)
        
        transactions = cursor.fetchall()
        
        # Format dates
        for tx in transactions:
            if 'transaction_date' in tx and tx['transaction_date']:
                tx['transaction_date'] = tx['transaction_date'].strftime('%Y-%m-%d %H:%M:%S')
            if 'value_date' in tx and tx['value_date']:
                tx['value_date'] = tx['value_date'].strftime('%Y-%m-%d')
        
        return jsonify({
            'status': 'success',
            'data': {
                'account_number': account_number,
                'from_date': from_date,
                'to_date': to_date,
                'transactions': transactions,
                'total_count': len(transactions)
            }
        }), 200
        
    except APIException as e:
        raise e
    except Exception as e:
        # Log the error
        print(f"Get Account Statement Error: {str(e)}")
        raise APIException(
            "Failed to fetch account statement", 
            "FETCH_STATEMENT_FAILED", 
            500
        )
    finally:
        cursor.close()
        conn.close()


@account_api.route('/<account_number>/balance', methods=['GET'])
@token_required
def get_account_balance(current_user, account_number):
    """
    Get current balance of an account
    """
    try:
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if account belongs to user
        cursor.execute(
            """
            SELECT account_number, balance, currency, available_balance, minimum_balance
            FROM accounts a
            JOIN customers c ON a.customer_id = c.id
            WHERE a.account_number = %s AND c.customer_id = %s
            """,
            (account_number, current_user['customer_id'])
        )
        
        account = cursor.fetchone()
        
        if not account:
            raise APIException(
                "Account not found or does not belong to authenticated user", 
                "ACCOUNT_NOT_FOUND", 
                404
            )
            
        # If available_balance is not set, use balance - minimum_balance
        if 'available_balance' not in account or account['available_balance'] is None:
            account['available_balance'] = max(0, account['balance'] - account['minimum_balance'])
        
        return jsonify({
            'status': 'success',
            'data': {
                'account_number': account['account_number'],
                'balance': account['balance'],
                'available_balance': account['available_balance'],
                'currency': account['currency'],
                'as_of': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }), 200
        
    except APIException as e:
        raise e
    except Exception as e:
        # Log the error
        print(f"Get Account Balance Error: {str(e)}")
        raise APIException(
            "Failed to fetch account balance", 
            "FETCH_BALANCE_FAILED", 
            500
        )
    finally:
        cursor.close()
        conn.close()
