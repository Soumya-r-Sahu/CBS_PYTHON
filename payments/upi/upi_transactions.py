"""
UPI Transaction Handler for Core Banking System
Implements SBI Bank standard formats for UPI IDs and transactions
"""

import re
import uuid
import datetime
import logging
import time
import random
import string
import io
import base64
from typing import Dict, Any, Optional, List, Tuple

try:
    from app.lib.id_generator import generate_transaction_id, generate_reference_number, validate_upi_id
except ImportError:
    # Fallback functions if module is not available
    def generate_transaction_id(channel=None):
        return f"TXN-{int(time.time())}-{str(uuid.uuid4())[:8]}"
    
    def generate_reference_number():
        return f"REF-{int(time.time())}-{str(uuid.uuid4())[:6]}"
    
    def validate_upi_id(upi_id):
        return '@' in upi_id and len(upi_id) > 3

# Import encryption module
try:
    from app.lib.encryption import verify_password
except ImportError:
    # Fallback function if module is not available
    def verify_password(password, password_hash, salt):
        # Simple verification for development only (not secure)
        return True

# Import other required modules
try:
    import qrcode
    HAS_QR_MODULE = True
except ImportError:
    HAS_QR_MODULE = False

# Import colorama for terminal output styling
try:
    from colorama import init, Fore, Style
    # Initialize colorama for colored terminal output
    init(autoreset=True)
except ImportError:
    # Define mock classes if colorama is not available
    class ForeStub:
        def __getattr__(self, name):
            return ''
    
    class StyleStub:
        def __getattr__(self, name):
            return ''
    
    Fore = ForeStub()
    Style = StyleStub()
    
    def init(**kwargs):
        pass

# Set up logging
logger = logging.getLogger(__name__)

class UpiTransactions:
    def __init__(self, database_connection):
        self.database_connection = database_connection
        
    def initiate_transaction(self, sender_upi_id: str, receiver_upi_id: str, 
                           amount: float, purpose: str = "PAYMENT") -> Dict[str, Any]:
        """
        Initiate a UPI transaction with SBI formatted IDs
        
        Args:
            sender_upi_id (str): Sender's SBI format UPI ID (username@sbi)
            receiver_upi_id (str): Receiver's UPI ID
            amount (float): Transaction amount
            purpose (str): Transaction purpose
            
        Returns:
            Dict containing transaction details
        """
        transaction_id = None
        reference_number = None
        conn = None
        cursor = None
        
        # Validate input parameters before proceeding
        if not sender_upi_id or not receiver_upi_id or not amount:
            logger.warning("Missing required parameters for UPI transaction")
            return {"status": "FAILED", "error": "Missing required parameters", "error_code": "UPI000"}
        
        try:
            # Validate UPI IDs
            if not validate_upi_id(sender_upi_id):
                logger.warning(f"Invalid sender UPI ID format: {sender_upi_id}")
                return {"status": "FAILED", "error": "Invalid sender UPI ID format", "error_code": "UPI001"}
                
            if not validate_upi_id(receiver_upi_id):
                logger.warning(f"Invalid receiver UPI ID format: {receiver_upi_id}")
                return {"status": "FAILED", "error": "Invalid receiver UPI ID format", "error_code": "UPI002"}
            
            # Validate amount
            try:
                amount = float(amount)
                if amount <= 0:
                    return {"status": "FAILED", "error": "Amount must be greater than zero", "error_code": "UPI003"}
            except (ValueError, TypeError):
                logger.warning(f"Invalid amount value: {amount}")
                return {"status": "FAILED", "error": "Amount must be a valid number", "error_code": "UPI004"}
            
            # Generate SBI format transaction ID
            try:
                transaction_id = generate_transaction_id(channel="UPI")
                
                # Generate SBI format reference number
                reference_number = generate_reference_number()
            except Exception as gen_error:
                logger.error(f"Failed to generate transaction identifiers: {gen_error}", exc_info=True)
                return {"status": "FAILED", "error": "System error: Failed to generate transaction ID", "error_code": "SYS002"}
            
            try:
                # Handle potential database connection errors properly
                try:
                    conn = self.database_connection.get_connection()
                    if not conn:
                        logger.error("Failed to establish database connection")
                        return {"status": "FAILED", "error": "Database connection error", "error_code": "DB000", "transaction_id": transaction_id}
                        
                    cursor = conn.cursor(dictionary=True)
                    if not cursor:
                        logger.error("Failed to create database cursor")
                        return {"status": "FAILED", "error": "Database cursor error", "error_code": "DB001", "transaction_id": transaction_id}
                except Exception as conn_error:
                    logger.error(f"Critical database connection error: {conn_error}", exc_info=True)
                    return {"status": "FAILED", "error": "Database connection failed", "error_code": "DB002", "transaction_id": transaction_id}
                
                # Get sender's UPI account with proper error handling
                try:
                    cursor.execute(
                        """
                        SELECT u.*, a.account_number, a.balance 
                        FROM upi_accounts u
                        JOIN accounts a ON u.account_id = a.id
                        WHERE u.upi_id = %s AND u.is_active = TRUE
                        """,
                        (sender_upi_id,)
                    )
                    
                    sender = cursor.fetchone()
                    
                    if not sender:
                        return {"status": "FAILED", "error": "Sender UPI ID not found or inactive", "error_code": "UPI005"}
                except Exception as query_error:
                    logger.error(f"Database error while fetching sender UPI account: {query_error}")
                    return {"status": "FAILED", "error": "Error fetching sender account", "error_code": "DB001"}
                    
                # Get receiver's UPI account with proper error handling
                try:
                    cursor.execute(
                        """
                        SELECT u.*, a.account_number
                        FROM upi_accounts u
                        JOIN accounts a ON u.account_id = a.id
                        WHERE u.upi_id = %s AND u.is_active = TRUE
                        """,
                        (receiver_upi_id,)
                    )
                    
                    receiver = cursor.fetchone()
                    
                    if not receiver:
                        return {"status": "FAILED", "error": "Receiver UPI ID not found or inactive", "error_code": "UPI006"}
                except Exception as query_error:
                    logger.error(f"Database error while fetching receiver UPI account: {query_error}")
                    return {"status": "FAILED", "error": "Error fetching receiver account", "error_code": "DB002"}
                    
                # Check for sufficient balance with proper error handling
                try:
                    if not sender or not isinstance(sender, dict) or 'balance' not in sender:
                        return {"status": "FAILED", "error": "Invalid sender account data", "error_code": "DB003"}
                        
                    if sender['balance'] < amount:
                        return {"status": "FAILED", "error": "Insufficient balance", "error_code": "UPI007"}
                except Exception as balance_error:
                    logger.error(f"Error checking balance: {balance_error}")
                    return {"status": "FAILED", "error": "Error checking balance", "error_code": "APP001"}
                    
                # Create transaction record
                transaction_details = {
                    "transaction_id": transaction_id,
                    "reference_number": reference_number,
                    "sender_upi_id": sender_upi_id,
                    "receiver_upi_id": receiver_upi_id,
                    "sender_account": sender['account_number'],
                    "receiver_account": receiver['account_number'],
                    "amount": amount,
                    "purpose": purpose,
                    "status": "SUCCESS",
                    "timestamp": datetime.datetime.now().isoformat()
                }
                
                # Log successful transaction initiation
                logger.info(f"UPI transaction initiated: {transaction_id} from {sender_upi_id} to {receiver_upi_id} for amount {amount}")
                
                return transaction_details
                
            except Exception as db_error:
                error_message = f"Database error in UPI transaction: {db_error}"
                logger.error(error_message)
                return {
                    "status": "FAILED", 
                    "error": "Database error occurred", 
                    "error_code": "DB999",
                    "transaction_id": transaction_id
                }
            finally:
                # Safely close resources, handling potential errors during close operations
                try:
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()
                except Exception as close_error:
                    logger.error(f"Error closing database resources: {close_error}")
        except Exception as e:
            # Comprehensive error handling for any unexpected exceptions
            error_message = f"Unexpected error in UPI transaction: {e}"
            logger.error(error_message, exc_info=True)
            return {
                "status": "FAILED", 
                "error": "An unexpected error occurred", 
                "error_code": "SYS001",
                "transaction_id": transaction_id
            }

    def get_transaction_history(self, upi_id: str, from_date: str = None, to_date: str = None, 
                               limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        Retrieve transaction history for a UPI ID
        
        Args:
            upi_id (str): UPI ID
            from_date (str): Optional start date (YYYY-MM-DD)
            to_date (str): Optional end date (YYYY-MM-DD)
            limit (int): Number of transactions to return
            offset (int): Offset for pagination
            
        Returns:
            Dict with transaction history
        """
        if not validate_upi_id(upi_id):
            return {"status": "FAILED", "error": "Invalid UPI ID format"}
            
        try:
            conn = self.database_connection.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Build query with optional date filters
            query = """
                SELECT t.transaction_id, t.amount, t.transaction_date, t.status,
                       ut.upi_transaction_id, ut.sender_upi_id, ut.receiver_upi_id,
                       ut.purpose, ut.status as upi_status, ut.reference_number
                FROM upi_transactions ut
                JOIN transactions t ON ut.transaction_id = t.transaction_id
                WHERE (ut.sender_upi_id = %s OR ut.receiver_upi_id = %s)
            """
            
            params = [upi_id, upi_id]
            
            # Add date filters if provided
            if from_date:
                query += " AND t.transaction_date >= %s"
                params.append(from_date)
            
            if to_date:
                query += " AND t.transaction_date <= %s"
                params.append(to_date)
                
            # Count total matching transactions first (for pagination)
            count_query = f"SELECT COUNT(*) as total FROM ({query}) as count_query"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()['total']
            
            # Add order and limit
            query += " ORDER BY t.transaction_date DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            
            transactions = cursor.fetchall()
            
            # Convert datetime objects to strings for JSON serialization
            for tx in transactions:
                if 'transaction_date' in tx and isinstance(tx['transaction_date'], datetime.datetime):
                    tx['transaction_date'] = tx['transaction_date'].isoformat()
                    
                # Add transaction type (credit/debit) based on UPI ID
                tx['is_credit'] = tx['receiver_upi_id'] == upi_id
                tx['is_debit'] = tx['sender_upi_id'] == upi_id
                tx['transaction_type'] = "CREDIT" if tx['is_credit'] else "DEBIT"
            
            # Check if there are more transactions
            has_more = total_count > (offset + len(transactions))
            
            return {
                "status": "SUCCESS",
                "transactions": transactions,
                "total_count": total_count,
                "has_more": has_more
            }
            
        except Exception as e:
            logger.error(f"Error fetching UPI transaction history: {e}")
            return {
                "status": "FAILED",
                "error": f"Failed to retrieve transaction history: {str(e)}",
                "transactions": [],
                "total_count": 0,
                "has_more": False
            }
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

    def cancel_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Cancel a UPI transaction if possible
        
        Args:
            transaction_id (str): SBI format transaction ID
            
        Returns:
            Dict with cancellation status
        """
        # Validation for SBI transaction ID format
        if not re.match(r'^[ABIMUNRS][a-f0-9]{17}$', transaction_id):
            return {"status": "FAILED", "error": "Invalid transaction ID format"}
            
        try:
            conn = self.database_connection.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Check if transaction exists and can be cancelled
            cursor.execute(
                """
                SELECT t.*, ut.sender_upi_id, ut.receiver_upi_id, 
                       ut.sender_account, ut.receiver_account
                FROM transactions t
                JOIN upi_transactions ut ON t.transaction_id = ut.transaction_id
                WHERE t.transaction_id = %s AND t.status = 'SUCCESS'
                AND t.transaction_date > DATE_SUB(NOW(), INTERVAL 30 MINUTE)
                """,
                (transaction_id,)
            )
            
            transaction = cursor.fetchone()
            
            if not transaction:
                return {"status": "FAILED", "error": "Transaction not found or cannot be cancelled"}
                
            # Mark transaction as cancelled/reversed
            cursor.execute(
                """
                UPDATE transactions
                SET status = 'REVERSED'
                WHERE transaction_id = %s
                """,
                (transaction_id,)
            )
            
            # Reverse the amounts in accounts
            cursor.execute(
                """
                UPDATE accounts
                SET balance = balance + %s
                WHERE account_number = %s
                """,
                (transaction['amount'], transaction['sender_account'])
            )
            
            cursor.execute(
                """
                UPDATE accounts
                SET balance = balance - %s
                WHERE account_number = %s
                """,
                (transaction['amount'], transaction['receiver_account'])
            )
            
            # Update UPI transaction status
            cursor.execute(
                """
                UPDATE upi_transactions
                SET status = 'REVERSED'
                WHERE transaction_id = %s
                """,
                (transaction_id,)
            )
            
            conn.commit()
            
            # Create cancellation record
            cancellation_result = {
                "status": "CANCELLED",
                "transaction_id": transaction_id,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            return cancellation_result
            
        except Exception as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Error cancelling UPI transaction: {e}")
            return {"status": "FAILED", "error": str(e)}
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

    def validate_upi_id(self, upi_id: str) -> bool:
        """
        Validate UPI ID according to SBI format
        
        Args:
            upi_id (str): UPI ID to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Use the imported validation function
        return validate_upi_id(upi_id)

    def send_notification(self, upi_id: str, message: str) -> bool:
        """
        Send transaction notification to UPI user
        
        Args:
            upi_id (str): SBI format UPI ID
            message (str): Notification message
            
        Returns:
            bool: Success status
        """
        if not validate_upi_id(upi_id):
            return False
            
        try:
            conn = self.database_connection.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get user's mobile number
            cursor.execute(
                """
                SELECT customer_id, mobile_number
                FROM upi_accounts
                WHERE upi_id = %s
                """,
                (upi_id,)
            )
            
            user = cursor.fetchone()
            
            if not user:
                return False
                
            # Log notification
            cursor.execute(
                """
                INSERT INTO notifications
                (customer_id, notification_type, message, channel, status, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                """,
                (
                    user['customer_id'],
                    'UPI_TRANSACTION',
                    message,
                    'SMS',
                    'SENT'
                )
            )
            
            conn.commit()
            
            # In a real implementation, we would send an actual SMS or push notification here
            logger.info(f"Notification sent to UPI ID {upi_id}: {message}")
            
            return True
            
        except Exception as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Error sending notification: {e}")
            return False
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
        
    def generate_upi_qr(self, upi_id: str, amount: float = None, 
                       purpose: str = None) -> Dict[str, Any]:
        """
        Generate UPI QR code details for SBI format UPI ID
        
        Args:
            upi_id (str): SBI format UPI ID
            amount (float, optional): Pre-filled amount
            purpose (str, optional): Pre-filled purpose
            
        Returns:
            Dict with QR code details
        """
        if not validate_upi_id(upi_id):
            return {"status": "FAILED", "error": "Invalid UPI ID format"}
            
        qr_data = f"upi://pay?pa={upi_id}"
        
        if amount:
            qr_data += f"&am={amount}"
            
        if purpose:
            qr_data += f"&pn={purpose}"
            
        # Add other UPI QR parameters
        qr_data += f"&cu=INR&tr={uuid.uuid4().hex[:16]}"
        
        return {
            "status": "SUCCESS",
            "upi_id": upi_id,
            "qr_data": qr_data,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    def register_upi_id(self, account_number: str, mobile_number: str, 
                       username: str = None) -> Dict[str, Any]:
        """
        Register a new UPI ID for a customer with SBI format
        
        Args:
            account_number (str): SBI format account number
            mobile_number (str): Customer's mobile number
            username (str, optional): Preferred username
            
        Returns:
            Dict with registration status and UPI ID
        """
        # Generate UPI ID based on username or mobile
        try:
            # Import id_generator function or use fallback
            try:
                from app.lib.id_generator import generate_upi_id
            except ImportError:
                # Fallback function if module is not available
                def generate_upi_id(name=None, mobile=None, **kwargs):
                    if name:
                        name_part = ''.join(e for e in name if e.isalnum()).lower()[:8]
                    else:
                        name_part = ''.join(random.choices(string.ascii_lowercase, k=5))
                    
                    if mobile:
                        mobile_part = mobile[-4:] if len(mobile) >= 4 else mobile
                    else:
                        mobile_part = ''.join(random.choices(string.digits, k=4))
                        
                    random_part = ''.join(random.choices(string.ascii_lowercase, k=4))
                    return f"{name_part}{mobile_part}@cbs"
            
            conn = self.database_connection.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Check if account exists
            cursor.execute(
                """
                SELECT a.id, a.customer_id
                FROM accounts a
                WHERE a.account_number = %s AND a.is_active = TRUE
                """,
                (account_number,)
            )
            
            account = cursor.fetchone()
            
            if not account:
                return {"status": "FAILED", "error": "Account not found or inactive"}
                
            # Check if UPI ID already exists for this account
            cursor.execute(
                """
                SELECT upi_id
                FROM upi_accounts
                WHERE account_id = %s AND is_active = TRUE
                """,
                (account['id'],)
            )
            
            existing_upi = cursor.fetchone()
            
            if existing_upi:
                return {
                    "status": "EXISTS",
                    "upi_id": existing_upi['upi_id'],
                    "account_number": account_number,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            
            # Generate UPI ID
            if username:
                upi_id = generate_upi_id(username=username)
            else:
                upi_id = generate_upi_id(mobile_number=mobile_number)
                
            return {
                "status": "SUCCESS",
                "upi_id": upi_id,
                "account_number": account_number,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error registering UPI ID: {e}")
            return {"status": "FAILED", "error": str(e)}
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

    def verify_upi_pin(self, upi_id: str, pin: str) -> bool:
        """
        Verify UPI PIN
        
        Args:
            upi_id (str): UPI ID
            pin (str): PIN to verify
            
        Returns:
            bool: True if PIN is valid, False otherwise
        """
        try:
            conn = self.database_connection.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT pin_hash, pin_salt
                FROM upi_accounts
                WHERE upi_id = %s AND is_active = TRUE
                """,
                (upi_id,)
            )
            
            result = cursor.fetchone()
            
            if not result:
                return False
                
            return verify_password(pin, result['pin_hash'], result['pin_salt'])
            
        except Exception as e:
            logger.error(f"Error verifying UPI PIN: {e}")
            return False
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

    def update_upi_pin(self, upi_id: str, pin_hash: str, pin_salt: str) -> Dict[str, Any]:
        """
        Update UPI PIN
        
        Args:
            upi_id (str): UPI ID
            pin_hash (str): New PIN hash
            pin_salt (str): New PIN salt
            
        Returns:
            Dict: Status of operation
        """
        try:
            conn = self.database_connection.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Verify UPI ID exists
            cursor.execute(
                """
                SELECT id, customer_id
                FROM upi_accounts
                WHERE upi_id = %s AND is_active = TRUE
                """,
                (upi_id,)
            )
            
            upi_account = cursor.fetchone()
            
            if not upi_account:
                return {
                    "status": "FAILED",
                    "error": f"UPI ID {upi_id} not found or not active"
                }
                
            # Update PIN hash and salt
            cursor.execute(
                """
                UPDATE upi_accounts
                SET pin_hash = %s, pin_salt = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (pin_hash, pin_salt, upi_account['id'])
            )
            
            conn.commit()
            
            # Log PIN change
            cursor.execute(
                """
                INSERT INTO security_events
                (customer_id, event_type, event_description, ip_address, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                """,
                (
                    upi_account['customer_id'],
                    'UPI_PIN_CHANGE',
                    f"UPI PIN changed for UPI ID {upi_id}",
                    "127.0.0.1"  # In a real implementation, you would pass the actual IP
                )
            )
            
            conn.commit()
            
            return {
                "status": "SUCCESS",
                "message": "UPI PIN updated successfully"
            }
            
        except Exception as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Error updating UPI PIN: {e}")
            return {
                "status": "FAILED",
                "error": f"Failed to update UPI PIN: {str(e)}"
            }
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

    def process_collect_request(self, requester_upi_id: str, payer_upi_id: str,
                              amount: float, purpose: str = "PAYMENT") -> Dict[str, Any]:
        """
        Process a UPI collect request (pull payment)
        
        Args:
            requester_upi_id (str): The UPI ID requesting the payment
            payer_upi_id (str): The UPI ID that will pay
            amount (float): Amount requested
            purpose (str): Purpose of payment
            
        Returns:
            Dict: Status and details of the collect request
        """
        try:
            conn = self.database_connection.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Validate UPI IDs
            cursor.execute(
                """
                SELECT u.id, u.customer_id, u.account_id, a.account_number, a.balance
                FROM upi_accounts u
                JOIN accounts a ON u.account_id = a.id
                WHERE u.upi_id = %s AND u.is_active = TRUE
                """,
                (requester_upi_id,)
            )
            
            requester = cursor.fetchone()
            
            if not requester:
                return {
                    "status": "FAILED",
                    "error": f"Requester UPI ID {requester_upi_id} not found or not active"
                }
                
            cursor.execute(
                """
                SELECT u.id, u.customer_id, u.account_id, a.account_number, a.balance
                FROM upi_accounts u
                JOIN accounts a ON u.account_id = a.id
                WHERE u.upi_id = %s AND u.is_active = TRUE
                """,
                (payer_upi_id,)
            )
            
            payer = cursor.fetchone()
            
            if not payer:
                return {
                    "status": "FAILED",
                    "error": f"Payer UPI ID {payer_upi_id} not found or not active"
                }
                
            # Generate reference numbers
            collect_id = f"COLLECT{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{requester['id']:04d}"
            reference_number = generate_reference_number()
            
            # Create collect request record
            cursor.execute(
                """
                INSERT INTO upi_collect_requests
                (collect_id, requester_upi_id, payer_upi_id, amount, purpose, 
                 reference_number, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """,
                (
                    collect_id,
                    requester_upi_id,
                    payer_upi_id,
                    amount,
                    purpose,
                    reference_number,
                    "PENDING"
                )
            )
            
            conn.commit()
            
            # Return the collect request details
            return {
                "status": "SUCCESS",
                "message": f"Collect request sent to {payer_upi_id}",
                "collect_id": collect_id,
                "reference_number": reference_number,
                "amount": amount,
                "purpose": purpose,
                "requester_upi_id": requester_upi_id,
                "payer_upi_id": payer_upi_id,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Error processing UPI collect request: {e}")
            return {
                "status": "FAILED",
                "error": f"Failed to process collect request: {str(e)}"
            }
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

    def generate_qr_code(self, upi_id: str, amount: float = None, purpose: str = None, qr_type: str = 'STATIC') -> Dict[str, Any]:
        """
        Generate QR code for UPI payments
        
        Args:
            upi_id (str): UPI ID
            amount (float): Optional amount for the transaction
            purpose (str): Optional purpose of payment
            qr_type (str): Type of QR code - STATIC or DYNAMIC
            
        Returns:
            Dict: QR code data
        """
        try:
            # Verify UPI ID exists
            conn = self.database_connection.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT id, customer_id
                FROM upi_accounts
                WHERE upi_id = %s AND is_active = TRUE
                """,
                (upi_id,)
            )
            
            upi_account = cursor.fetchone()
            
            if not upi_account:
                return {
                    "status": "FAILED",
                    "error": f"UPI ID {upi_id} not found or not active"
                }
                
            # Create QR payload according to UPI specifications
            # This is a simplified version - real implementation would follow
            # the complete UPI QR code specification
            qr_payload = f"upi://{upi_id}"
            
            if amount:
                qr_payload += f"?am={amount}"
                
            if purpose:
                qr_payload += f"&pn={purpose}"
                
            # Add transaction reference for dynamic QR codes
            if qr_type == 'DYNAMIC':
                ref_id = f"QR{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{upi_account['id']:04d}"
                qr_payload += f"&tr={ref_id}"
                expiry = datetime.datetime.now() + datetime.timedelta(minutes=15)
            else:
                expiry = None
                
            # In a real implementation, we would use a QR code generation library
            # like 'qrcode' to generate an actual QR code image
            qr_code = self._encode_base64_qr(qr_payload)
            
            # For dynamic QR codes, store the reference in database
            if qr_type == 'DYNAMIC':
                cursor.execute(
                    """
                    INSERT INTO upi_qr_codes
                    (upi_account_id, reference_id, qr_payload, amount, purpose, expiry, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """,
                    (
                        upi_account['id'],
                        ref_id,
                        qr_payload,
                        amount if amount else 0,
                        purpose,
                        expiry
                    )
                )
                
                conn.commit()
            
            return {
                "status": "SUCCESS",
                "message": "QR code generated successfully",
                "qr_code": qr_code,
                "payload": qr_payload,
                "expiry": expiry.isoformat() if expiry else None,
                "qr_type": qr_type
            }
            
        except Exception as e:
            logger.error(f"Error generating QR code: {e}")
            return {
                "status": "FAILED",
                "error": f"Failed to generate QR code: {str(e)}"
            }
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()
            
    def _encode_base64_qr(self, payload: str) -> str:
        """
        Generate a base64 encoded QR code
        
        Args:
            payload (str): QR code payload
            
        Returns:
            str: Base64 encoded QR code image
        """
        try:
            # In a real implementation, you would use a library like 'qrcode'
            # to generate an actual QR code image
            if not HAS_QR_MODULE:
                # If qrcode library is not available, return a placeholder
                logger.warning("QR code generation library not available")
                return "QR_CODE_PLACEHOLDER"
                
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(payload)
            qr.make(fit=True)
            
            # Create an image from the QR code
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert the image to bytes
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            
            # Convert bytes to base64 string
            qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return f"data:image/png;base64,{qr_base64}"
            
        except Exception as e:
            logger.error(f"Error generating QR code image: {e}")
            return "ERROR_GENERATING_QR"

    def get_upi_balance(self, upi_id: str) -> Dict[str, Any]:
        """
        Get balance for UPI account
        
        Args:
            upi_id (str): UPI ID
            
        Returns:
            Dict: Balance information
        """
        try:
            conn = self.database_connection.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT u.id, u.account_id, a.account_number, a.balance, a.currency
                FROM upi_accounts u
                JOIN accounts a ON u.account_id = a.id
                WHERE u.upi_id = %s AND u.is_active = TRUE
                """,
                (upi_id,)
            )
            
            result = cursor.fetchone()
            
            if not result:
                return {
                    "status": "FAILED",
                    "error": f"UPI ID {upi_id} not found or not active"
                }
                
            return {
                "status": "SUCCESS",
                "balance": result['balance'],
                "currency": result['currency'],
                "account_number": result['account_number']
            }
            
        except Exception as e:
            logger.error(f"Error getting UPI balance: {e}")
            return {
                "status": "FAILED",
                "error": f"Failed to get UPI balance: {str(e)}"
            }
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

    def respond_to_collect_request(self, collect_id: str, action: str, upi_pin: str = None) -> Dict[str, Any]:
        """
        Respond to a UPI collect request
        
        Args:
            collect_id (str): The ID of the collect request
            action (str): 'ACCEPT' or 'REJECT'
            upi_pin (str): UPI PIN required for accepting a request
            
        Returns:
            Dict: Status and details of the action
        """
        try:
            conn = self.database_connection.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get collect request details
            cursor.execute(
                """
                SELECT * FROM upi_collect_requests
                WHERE collect_id = %s AND status = 'PENDING'
                """,
                (collect_id,)
            )
            
            collect_request = cursor.fetchone()
            
            if not collect_request:
                return {
                    "status": "FAILED",
                    "error": f"Collect request {collect_id} not found or already processed"
                }
                
            # If rejecting, simply update status
            if action.upper() == "REJECT":
                cursor.execute(
                    """
                    UPDATE upi_collect_requests
                    SET status = 'REJECTED', updated_at = NOW()
                    WHERE collect_id = %s
                    """,
                    (collect_id,)
                )
                conn.commit()
                
                return {
                    "status": "SUCCESS",
                    "message": "Collect request rejected successfully",
                    "collect_id": collect_id
                }
                
            # If accepting, verify PIN and process payment
            elif action.upper() == "ACCEPT":
                if not upi_pin:
                    return {
                        "status": "FAILED",
                        "error": "UPI PIN required to accept collect request"
                    }
                    
                # Verify UPI PIN
                pin_verified = self.verify_upi_pin(collect_request['payer_upi_id'], upi_pin)
                
                if not pin_verified:
                    return {
                        "status": "FAILED",
                        "error": "Invalid UPI PIN"
                    }
                    
                # Process the payment using the transaction logic
                transaction_result = self.initiate_transaction(
                    sender_upi_id=collect_request['payer_upi_id'],
                    receiver_upi_id=collect_request['requester_upi_id'],
                    amount=collect_request['amount'],
                    purpose=collect_request['purpose']
                )
                
                if transaction_result.get("status") == "SUCCESS":
                    # Update collect request status
                    cursor.execute(
                        """
                        UPDATE upi_collect_requests
                        SET status = 'ACCEPTED', transaction_id = %s, updated_at = NOW()
                        WHERE collect_id = %s
                        """,
                        (transaction_result.get("transaction_id"), collect_id)
                    )
                    conn.commit()
                    
                    return {
                        "status": "SUCCESS",
                        "message": "Collect request accepted and payment processed",
                        "collect_id": collect_id,
                        "transaction_id": transaction_result.get("transaction_id"),
                        "reference_number": transaction_result.get("reference_number")
                    }
                else:
                    # Handle failed transaction
                    cursor.execute(
                        """
                        UPDATE upi_collect_requests
                        SET status = 'FAILED', failure_reason = %s, updated_at = NOW()
                        WHERE collect_id = %s
                        """,
                        (transaction_result.get("error", "Unknown error"), collect_id)
                    )
                    conn.commit()
                    
                    return {
                        "status": "FAILED",
                        "error": transaction_result.get("error", "Failed to process payment"),
                        "collect_id": collect_id
                    }
            else:
                return {
                    "status": "FAILED",
                    "error": f"Invalid action: {action}. Must be 'ACCEPT' or 'REJECT'."
                }
                
        except Exception as e:
            if 'conn' in locals() and conn:
                conn.rollback()
            logger.error(f"Error responding to UPI collect request: {e}")
            return {
                "status": "FAILED",
                "error": f"Failed to process request response: {str(e)}"
            }
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

    def get_pending_collect_requests(self, upi_id: str) -> Dict[str, Any]:
        """
        Get pending collect requests for a UPI ID
        
        Args:
            upi_id (str): UPI ID to check for pending requests
            
        Returns:
            Dict: List of pending collect requests
        """
        try:
            conn = self.database_connection.get_connection()
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute(
                """
                SELECT collect_id, requester_upi_id, payer_upi_id, amount, 
                       purpose, reference_number, created_at
                FROM upi_collect_requests
                WHERE payer_upi_id = %s AND status = 'PENDING'
                ORDER BY created_at DESC
                """,
                (upi_id,)
            )
            
            pending_requests = cursor.fetchall()
            
            # Convert datetime objects to strings for JSON serialization
            for request in pending_requests:
                if 'created_at' in request and isinstance(request['created_at'], datetime.datetime):
                    request['created_at'] = request['created_at'].isoformat()
            
            return {
                "status": "SUCCESS",
                "pending_requests": pending_requests,
                "count": len(pending_requests)
            }
            
        except Exception as e:
            logger.error(f"Error getting pending collect requests: {e}")
            return {
                "status": "FAILED",
                "error": f"Failed to retrieve collect requests: {str(e)}",
                "pending_requests": [],
                "count": 0
            }
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()


def main():
    from colorama import init, Fore, Style
    init(autoreset=True)  # Initialize colorama
    print(f"{Fore.CYAN}💸 UPI Transactions App Running...{Style.RESET_ALL}")
    # TODO: Add CLI or GUI logic for UPI transactions


if __name__ == "__main__":
    main()
