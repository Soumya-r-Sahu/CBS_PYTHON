"""
Authentication Controller for Mobile Banking API

Handles user authentication and session management
"""

import datetime
import uuid
from flask import Blueprint, request, jsonify

# Use centralized import system 
from utils.lib.packages import fix_path, import_module
fix_path()  # Ensures project root is in sys.path

# Import middleware with fallback mechanisms
try:
    from integration_interfaces.api.middleware.authentication import generate_token, token_required
except ImportError:
    try:
        from app.api.middleware.authentication import generate_token, token_required
    except ImportError:
        # Fallback implementations
        def generate_token(user_id, role="user"):
            return f"mock_token_{user_id}_{role}_{uuid.uuid4().hex}"
        
        def token_required(f):
            def decorator(*args, **kwargs):
                return f(*args, **kwargs)
            return decorator

try:
    from integration_interfaces.api.middleware.validation import validate_schema
except ImportError:
    try:
        from app.api.middleware.validation import validate_schema
    except ImportError:
        # Fallback implementation
        def validate_schema(schema):
            def decorator(f):
                def wrapper(*args, **kwargs):
                    return f(*args, **kwargs)
                return wrapper
            return decorator

try:
    from integration_interfaces.api.middleware.error_handler import APIException
except ImportError:
    try:
        from app.api.middleware.error_handler import APIException
    except ImportError:
        # Fallback implementation
        class APIException(Exception):
            def __init__(self, message="API Error", status_code=400):
                self.message = message
                self.status_code = status_code

try:
    from integration_interfaces.api.middleware.rate_limiter import rate_limit
except ImportError:
    try:
        from app.api.middleware.rate_limiter import rate_limit
    except ImportError:
        # Fallback implementation
        def rate_limit(max_requests=10, time_window=60):
            def decorator(f):
                def wrapper(*args, **kwargs):
                    return f(*args, **kwargs)
                return wrapper
            return decorator

try:
    from integration_interfaces.api.schemas.auth_schemas import login_schema, mpin_schema
except ImportError:
    try:
        from app.api.schemas.auth_schemas import login_schema, mpin_schema
    except ImportError:
        # Fallback schemas
        login_schema = {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "password": {"type": "string"},
                "device_id": {"type": "string"},
            },
            "required": ["customer_id", "password"]
        }
        mpin_schema = {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "mpin": {"type": "string"}
            },
            "required": ["customer_id", "mpin"]
        }

# Import encryption utilities
try:
    from integration_interfaces.utils.lib.encryption import verify_password, hash_password
except ImportError:
    try:
        from app.utils.lib.encryption import verify_password, hash_password
    except ImportError:
        import hashlib
        def hash_password(password, salt=None):
            # Simple hash for fallback; real implementation should use salt
            return hashlib.sha256(password.encode()).hexdigest(), 'fallback_salt'
        def verify_password(password, hashed, salt=None):
            return hashed == hash_password(password, salt)[0]

# Import database connection
try:
    from core_banking.database.connection import DatabaseConnection
except ImportError:
    try:
        from database.python.common.database_operations import DatabaseConnection
    except ImportError:
        # Simple mock database connection
        class DatabaseConnection:
            def get_connection(self):
                return None
            def close_connection(self, conn):
                pass

# Create blueprint
auth_api = Blueprint('auth_api', __name__)

# Initialize database connection
db_connection = DatabaseConnection()

@auth_api.route('/login', methods=['POST'])
@validate_schema(login_schema)
@rate_limit(max_requests=10, time_window=300)  # Limit to 10 login attempts per 5 minutes
def login():
    """
    Authenticate user and generate JWT token
    
    Request body:
    {
        "customer_id": "string",
        "password": "string",
        "device_id": "string",
        "device_info": {
            "device_model": "string",
            "os_version": "string",
            "app_version": "string"
        }
    }
    """
    try:
        data = request.get_json()
        
        # Connect to database
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists
        cursor.execute(
            """
            SELECT c.customer_id, c.first_name, c.last_name, c.password_hash, 
                   c.password_salt, c.is_active, c.customer_segment, c.kyc_status
            FROM customers c
            WHERE c.customer_id = %s
            """,
            (data['customer_id'],)
        )
        
        user = cursor.fetchone()
        
        if not user:
            raise APIException(
                "Invalid credentials", 
                "INVALID_CREDENTIALS", 
                401
            )
            
        # Verify password
        if not verify_password(data['password'], user['password_hash'], user['password_salt']):
            raise APIException(
                "Invalid credentials", 
                "INVALID_CREDENTIALS", 
                401
            )
            
        # Check if user is active
        if not user['is_active']:
            raise APIException(
                "Account is inactive", 
                "ACCOUNT_INACTIVE", 
                403
            )
            
        # Log device info
        device_id = data['device_id']
        
        cursor.execute(
            """
            INSERT INTO mobile_devices 
            (device_id, customer_id, device_model, os_version, app_version, last_login, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
            last_login = NOW(), login_count = login_count + 1,
            device_model = %s, os_version = %s, app_version = %s
            """,
            (
                device_id, 
                data['customer_id'],
                data['device_info']['device_model'],
                data['device_info']['os_version'],
                data['device_info']['app_version'],
                data['device_info']['device_model'],
                data['device_info']['os_version'],
                data['device_info']['app_version']
            )
        )
        
        conn.commit()
        
        # Generate JWT token
        token = generate_token(
            customer_id=data['customer_id'],
            device_id=device_id,
            role='customer'  # Default role
        )
        
        # Return user info and token
        return jsonify({
            'status': 'success',
            'message': 'Login successful',
            'data': {
                'token': token,
                'customer': {
                    'customer_id': user['customer_id'],
                    'name': f"{user['first_name']} {user['last_name']}",
                    'segment': user['customer_segment'],
                    'kyc_status': user['kyc_status']
                }
            }
        }), 200
        
    except APIException as e:
        raise e
    except Exception as e:
        # Log the error
        print(f"Login Error: {str(e)}")
        raise APIException(
            "Failed to authenticate", 
            "AUTHENTICATION_FAILED", 
            500
        )
    finally:
        cursor.close()
        conn.close()


@auth_api.route('/set-mpin', methods=['POST'])
@token_required
@validate_schema(mpin_schema)
@rate_limit(max_requests=3, time_window=300)  # 3 attempts per 5 minutes
def set_mpin(current_user):
    """
    Set or update mobile banking PIN (MPIN)
    
    Request body:
    {
        "mpin": "string" (6 digits),
        "password": "string" (required for verification)
    }
    """
    try:
        data = request.get_json()
        
        # Connect to database
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verify user's password first
        cursor.execute(
            """
            SELECT c.password_hash, c.password_salt
            FROM customers c
            WHERE c.customer_id = %s
            """,
            (current_user['customer_id'],)
        )
        
        user = cursor.fetchone()
        
        if not user or not verify_password(data['password'], user['password_hash'], user['password_salt']):
            raise APIException(
                "Invalid password", 
                "INVALID_PASSWORD", 
                401
            )
            
        # Validate MPIN
        mpin = data.get('mpin')
        
        if not mpin or len(mpin) != 6 or not mpin.isdigit():
            raise APIException(
                "MPIN must be 6 digits", 
                "INVALID_MPIN", 
                400
            )
            
        # Check MPIN strength
        if _is_weak_pin(mpin):
            raise APIException(
                "MPIN is too weak. Avoid sequential or repetitive numbers.", 
                "WEAK_MPIN", 
                400
            )
            
        # Hash MPIN
        mpin_hash, mpin_salt = hash_password(mpin)
        
        # Update or insert MPIN
        cursor.execute(
            """
            INSERT INTO mobile_banking_settings
            (customer_id, mpin_hash, mpin_salt, created_at, updated_at)
            VALUES (%s, %s, %s, NOW(), NOW())
            ON DUPLICATE KEY UPDATE
            mpin_hash = %s, mpin_salt = %s, updated_at = NOW(), 
            failed_attempts = 0, locked_until = NULL
            """,
            (
                current_user['customer_id'],
                mpin_hash,
                mpin_salt,
                mpin_hash,
                mpin_salt
            )
        )
        
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'MPIN set successfully'
        }), 200
        
    except APIException as e:
        conn.rollback()
        raise e
    except Exception as e:
        conn.rollback()
        # Log the error
        print(f"MPIN Set Error: {str(e)}")
        raise APIException(
            "Failed to set MPIN", 
            "MPIN_SET_FAILED", 
            500
        )
    finally:
        cursor.close()
        conn.close()


@auth_api.route('/verify-mpin', methods=['POST'])
@token_required
@rate_limit(max_requests=5, time_window=60)  # 5 attempts per minute
def verify_mpin(current_user):
    """
    Verify mobile banking PIN (MPIN)
    
    Request body:
    {
        "mpin": "string" (6 digits)
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'mpin' not in data:
            raise APIException(
                "MPIN is required", 
                "MISSING_MPIN", 
                400
            )
            
        # Connect to database
        conn = db_connection.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get user's MPIN settings
        cursor.execute(
            """
            SELECT mpin_hash, mpin_salt, failed_attempts, locked_until
            FROM mobile_banking_settings
            WHERE customer_id = %s
            """,
            (current_user['customer_id'],)
        )
        
        mpin_settings = cursor.fetchone()
        
        if not mpin_settings:
            raise APIException(
                "MPIN not set", 
                "MPIN_NOT_SET", 
                400
            )
            
        # Check if account is locked
        if mpin_settings['locked_until'] and mpin_settings['locked_until'] > datetime.datetime.now():
            lock_minutes = (mpin_settings['locked_until'] - datetime.datetime.now()).seconds // 60
            raise APIException(
                f"Account is temporarily locked due to multiple failed attempts. Try again in {lock_minutes} minutes.", 
                "ACCOUNT_LOCKED", 
                403
            )
            
        # Verify MPIN
        if not verify_password(data['mpin'], mpin_settings['mpin_hash'], mpin_settings['mpin_salt']):
            # Increment failed attempts
            failed_attempts = mpin_settings['failed_attempts'] + 1
            locked_until = None
            
            # Lock account after 5 failed attempts
            if failed_attempts >= 5:
                # Lock for 30 minutes
                locked_until = datetime.datetime.now() + datetime.timedelta(minutes=30)
                
            cursor.execute(
                """
                UPDATE mobile_banking_settings
                SET failed_attempts = %s, locked_until = %s
                WHERE customer_id = %s
                """,
                (failed_attempts, locked_until, current_user['customer_id'])
            )
            
            conn.commit()
            
            raise APIException(
                "Invalid MPIN", 
                "INVALID_MPIN", 
                401
            )
            
        # Reset failed attempts on successful verification
        cursor.execute(
            """
            UPDATE mobile_banking_settings
            SET failed_attempts = 0, locked_until = NULL
            WHERE customer_id = %s
            """,
            (current_user['customer_id'],)
        )
        
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'MPIN verification successful'
        }), 200
        
    except APIException as e:
        raise e
    except Exception as e:
        # Log the error
        print(f"MPIN Verification Error: {str(e)}")
        raise APIException(
            "Failed to verify MPIN", 
            "MPIN_VERIFICATION_FAILED", 
            500
        )
    finally:
        cursor.close()
        conn.close()


# Helper functions
def _is_weak_pin(pin):
    """
    Check if PIN is weak
    
    Args:
        pin: 6-digit PIN to validate
        
    Returns:
        bool: True if PIN is weak, False otherwise
    """
    # Check for sequential numbers (e.g., 123456, 654321)
    sequential_patterns = ['123456', '234567', '345678', '456789', 
                         '987654', '876543', '765432', '654321']
    if pin in sequential_patterns:
        return True
        
    # Check for repetitive digits (e.g., 111111, 222222)
    if len(set(pin)) == 1:
        return True
        
    # Check for common PINs
    common_pins = ['000000', '111111', '222222', '333333', '444444', 
                  '555555', '666666', '777777', '888888', '999999', 
                  '123123', '456456', '789789', '159159', '147147']
    if pin in common_pins:
        return True
        
    return False
