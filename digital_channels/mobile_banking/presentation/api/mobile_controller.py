"""
Mobile Banking API Controller.
"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
from flask import Blueprint, request, jsonify, current_app, g

from ...application.use_cases.authentication_use_case import AuthenticationUseCase, LoginResult
from ...application.use_cases.session_management_use_case import SessionManagementUseCase
from ...application.use_cases.transaction_management_use_case import TransactionManagementUseCase
from ...application.use_cases.user_management_use_case import UserManagementUseCase
from ...domain.entities.mobile_transaction import TransactionType


logger = logging.getLogger(__name__)

# Create a blueprint for the mobile banking API
mobile_api = Blueprint('mobile_api', __name__, url_prefix='/api/mobile')


@mobile_api.before_request
def validate_session():
    """Validate session token before processing API requests."""
    # Skip validation for login, register routes
    if request.endpoint in ['mobile_api.login', 'mobile_api.register']:
        return
    
    # Get the token from the header
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid authorization token'}), 401
    
    # Extract the token
    token = token.replace('Bearer ', '')
    
    # Get the session management use case
    session_management_use_case = current_app.container.get_session_management_use_case()
    
    # Validate the session
    validation_result = session_management_use_case.validate_session(
        token=token,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', ''),
        device_id=request.headers.get('X-Device-ID')
    )
    
    if not validation_result.is_valid:
        return jsonify({'error': validation_result.message}), 401
    
    # Store the session in g for use in route handlers
    g.session = validation_result.session
    
    # Extend the session if needed
    if validation_result.needs_extension:
        session_management_use_case.extend_session(token, request.remote_addr)


@mobile_api.route('/login', methods=['POST'])
def login():
    """Log in a user and create a session."""
    # Get request data
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Extract credentials
    username = data.get('username')
    password = data.get('password')
    device_id = data.get('device_id')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    # Get the authentication use case
    auth_use_case = current_app.container.get_authentication_use_case()
    
    # Attempt login
    login_result = auth_use_case.login(
        username=username,
        password=password,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', ''),
        device_id=device_id,
        location={'ip': request.remote_addr}
    )
    
    if not login_result.success:
        return jsonify({
            'success': False,
            'message': login_result.message
        }), 401
    
    # Build response
    response = {
        'success': True,
        'message': login_result.message,
        'token': login_result.token,
        'additional_auth_required': login_result.additional_auth_required,
        'user': {
            'id': str(login_result.user.id),
            'username': login_result.user.username,
            'full_name': login_result.user.full_name,
            'email': login_result.user.email,
            'mobile_number': login_result.user.mobile_number,
            'profile_complete': login_result.user.profile_complete
        }
    }
    
    return jsonify(response), 200


@mobile_api.route('/register', methods=['POST'])
def register():
    """Register a new mobile banking user."""
    # Get request data
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Extract user information
    username = data.get('username')
    password = data.get('password')
    mobile_number = data.get('mobile_number')
    email = data.get('email')
    full_name = data.get('full_name')
    customer_id = data.get('customer_id')
    device_id = data.get('device_id')
    device_info = data.get('device_info')
    
    # Basic validation
    required_fields = ['username', 'password', 'mobile_number', 'email', 'full_name', 'customer_id']
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        return jsonify({
            'error': f"Missing required fields: {', '.join(missing_fields)}"
        }), 400
    
    # Get the user management use case
    user_use_case = current_app.container.get_user_management_use_case()
    
    # Attempt registration
    registration_result = user_use_case.register_user(
        username=username,
        password=password,
        mobile_number=mobile_number,
        email=email,
        full_name=full_name,
        customer_id=customer_id,
        ip_address=request.remote_addr,
        device_id=device_id,
        device_info=device_info
    )
    
    if not registration_result.success:
        return jsonify({
            'success': False,
            'message': registration_result.message
        }), 400
    
    # Build response
    response = {
        'success': True,
        'message': registration_result.message,
        'user': {
            'id': str(registration_result.user.id),
            'username': registration_result.user.username,
            'full_name': registration_result.user.full_name,
            'email': registration_result.user.email,
            'mobile_number': registration_result.user.mobile_number
        }
    }
    
    return jsonify(response), 201


@mobile_api.route('/logout', methods=['POST'])
def logout():
    """Log out a user by invalidating their session."""
    # Get the token from the header
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid authorization token'}), 401
    
    # Extract the token
    token = token.replace('Bearer ', '')
    
    # Get the authentication use case
    auth_use_case = current_app.container.get_authentication_use_case()
    
    # Attempt logout
    success = auth_use_case.logout(token, request.remote_addr)
    
    if not success:
        return jsonify({
            'success': False,
            'message': 'Failed to log out'
        }), 400
    
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200


@mobile_api.route('/profile', methods=['GET'])
def get_profile():
    """Get the user's profile."""
    # The session is already validated in the before_request handler
    session = g.session
    
    # Get the user management use case
    user_use_case = current_app.container.get_user_management_use_case()
    
    # Get the user
    user = user_use_case.get_user_by_id(session.user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Build response
    response = {
        'id': str(user.id),
        'username': user.username,
        'full_name': user.full_name,
        'email': user.email,
        'mobile_number': user.mobile_number,
        'status': user.status,
        'profile_complete': user.profile_complete,
        'registration_date': user.registration_date.isoformat() if user.registration_date else None,
        'last_login_date': user.last_login_date.isoformat() if user.last_login_date else None,
        'preferences': user.preferences,
        'registered_devices': [
            {
                'device_id': device.device_id,
                'device_name': device.device_name,
                'last_used_date': device.last_used_date.isoformat() if device.last_used_date else None
            }
            for device in user.registered_devices
        ]
    }
    
    return jsonify(response), 200


@mobile_api.route('/profile', methods=['PUT'])
def update_profile():
    """Update the user's profile."""
    # The session is already validated in the before_request handler
    session = g.session
    
    # Get request data
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Extract profile information
    email = data.get('email')
    full_name = data.get('full_name')
    preferences = data.get('preferences')
    
    # Get the user management use case
    user_use_case = current_app.container.get_user_management_use_case()
    
    # Attempt profile update
    update_result = user_use_case.update_profile(
        user_id=session.user_id,
        email=email,
        full_name=full_name,
        preferences=preferences,
        ip_address=request.remote_addr
    )
    
    if not update_result.success:
        return jsonify({
            'success': False,
            'message': update_result.message
        }), 400
    
    # Build response
    response = {
        'success': True,
        'message': update_result.message,
        'user': {
            'id': str(update_result.user.id),
            'username': update_result.user.username,
            'full_name': update_result.user.full_name,
            'email': update_result.user.email,
            'mobile_number': update_result.user.mobile_number,
            'preferences': update_result.user.preferences
        }
    }
    
    return jsonify(response), 200


@mobile_api.route('/transactions', methods=['GET'])
def get_transactions():
    """Get the user's transactions."""
    # The session is already validated in the before_request handler
    session = g.session
    
    # Get query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Parse dates if provided
    start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
    end_date = datetime.fromisoformat(end_date_str) if end_date_str else None
    
    # Get the transaction management use case
    transaction_use_case = current_app.container.get_transaction_management_use_case()
    
    # Get transactions
    transactions = transaction_use_case.get_user_transactions(
        user_id=session.user_id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Build response
    response = [
        {
            'id': str(txn.id),
            'transaction_type': txn.transaction_type.value,
            'amount': txn.amount,
            'from_account': txn.from_account,
            'to_account': txn.to_account,
            'reference_number': txn.reference_number,
            'remarks': txn.remarks,
            'status': txn.status.value,
            'initiation_time': txn.initiation_time.isoformat() if txn.initiation_time else None,
            'completion_time': txn.completion_time.isoformat() if txn.completion_time else None
        }
        for txn in transactions
    ]
    
    return jsonify(response), 200


@mobile_api.route('/transactions', methods=['POST'])
def create_transaction():
    """Create a new transaction."""
    # The session is already validated in the before_request handler
    session = g.session
    
    # Get request data
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Extract transaction information
    transaction_type_str = data.get('transaction_type')
    amount = data.get('amount')
    from_account = data.get('from_account')
    to_account = data.get('to_account')
    remarks = data.get('remarks')
    
    # Basic validation
    if not transaction_type_str or not amount or not from_account or not to_account:
        return jsonify({
            'error': 'Missing required fields: transaction_type, amount, from_account, to_account'
        }), 400
    
    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({'error': 'Amount must be a number'}), 400
    
    # Parse transaction type
    try:
        transaction_type = TransactionType(transaction_type_str)
    except ValueError:
        return jsonify({
            'error': f"Invalid transaction type. Must be one of: {', '.join([t.value for t in TransactionType])}"
        }), 400
    
    # Get the transaction management use case
    transaction_use_case = current_app.container.get_transaction_management_use_case()
    
    # Initiate transaction
    transaction_result = transaction_use_case.initiate_transaction(
        user_id=session.user_id,
        transaction_type=transaction_type,
        amount=amount,
        from_account=from_account,
        to_account=to_account,
        remarks=remarks,
        ip_address=request.remote_addr,
        device_id=session.device_id,
        location={'ip': request.remote_addr}
    )
    
    if not transaction_result.success:
        return jsonify({
            'success': False,
            'message': transaction_result.message
        }), 400
    
    # Build response
    response = {
        'success': True,
        'message': transaction_result.message,
        'reference_number': transaction_result.reference_number,
        'needs_approval': transaction_result.needs_approval,
        'needs_verification': transaction_result.needs_verification,
        'transaction': {
            'id': str(transaction_result.transaction.id),
            'transaction_type': transaction_result.transaction.transaction_type.value,
            'amount': transaction_result.transaction.amount,
            'from_account': transaction_result.transaction.from_account,
            'to_account': transaction_result.transaction.to_account,
            'status': transaction_result.transaction.status.value,
            'initiation_time': transaction_result.transaction.initiation_time.isoformat() 
                if transaction_result.transaction.initiation_time else None
        }
    }
    
    return jsonify(response), 201


@mobile_api.route('/transactions/<transaction_id>/verify', methods=['POST'])
def verify_transaction(transaction_id):
    """Verify a transaction with a verification code."""
    # The session is already validated in the before_request handler
    session = g.session
    
    # Get request data
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Extract verification code
    verification_code = data.get('verification_code')
    
    if not verification_code:
        return jsonify({'error': 'Verification code is required'}), 400
    
    # Get the transaction management use case
    transaction_use_case = current_app.container.get_transaction_management_use_case()
    
    # Verify transaction
    try:
        transaction_id_uuid = UUID(transaction_id)
    except ValueError:
        return jsonify({'error': 'Invalid transaction ID'}), 400
    
    verification_result = transaction_use_case.verify_transaction(
        user_id=session.user_id,
        transaction_id=transaction_id_uuid,
        verification_code=verification_code,
        ip_address=request.remote_addr
    )
    
    if not verification_result.success:
        return jsonify({
            'success': False,
            'message': verification_result.message
        }), 400
    
    # Build response
    response = {
        'success': True,
        'message': verification_result.message,
        'reference_number': verification_result.reference_number,
        'transaction': {
            'id': str(verification_result.transaction.id),
            'status': verification_result.transaction.status.value
        }
    }
    
    return jsonify(response), 200


@mobile_api.route('/change-password', methods=['POST'])
def change_password():
    """Change a user's password."""
    # The session is already validated in the before_request handler
    session = g.session
    
    # Get request data
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Extract password information
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current password and new password are required'}), 400
    
    # Get the authentication use case
    auth_use_case = current_app.container.get_authentication_use_case()
    
    # Attempt password change
    password_change_result = auth_use_case.change_password(
        user_id=session.user_id,
        current_password=current_password,
        new_password=new_password,
        ip_address=request.remote_addr
    )
    
    if not password_change_result.success:
        return jsonify({
            'success': False,
            'message': password_change_result.message
        }), 400
    
    return jsonify({
        'success': True,
        'message': password_change_result.message
    }), 200


@mobile_api.route('/register-device', methods=['POST'])
def register_device():
    """Register a device for the user."""
    # The session is already validated in the before_request handler
    session = g.session
    
    # Get request data
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Extract device information
    device_id = data.get('device_id')
    device_name = data.get('device_name')
    device_model = data.get('device_model')
    os_version = data.get('os_version')
    app_version = data.get('app_version')
    
    if not device_id or not device_name or not device_model:
        return jsonify({
            'error': 'device_id, device_name, and device_model are required'
        }), 400
    
    # Get the authentication use case
    auth_use_case = current_app.container.get_authentication_use_case()
    
    # Attempt device registration
    registration_result = auth_use_case.register_device(
        user_id=session.user_id,
        device_id=device_id,
        device_name=device_name,
        device_model=device_model,
        os_version=os_version or 'Unknown',
        app_version=app_version or 'Unknown',
        ip_address=request.remote_addr
    )
    
    if not registration_result.success:
        return jsonify({
            'success': False,
            'message': registration_result.message
        }), 400
    
    return jsonify({
        'success': True,
        'message': registration_result.message,
        'device_id': registration_result.device_id
    }), 200


def register_blueprint(app):
    """Register the blueprint with the app."""
    app.register_blueprint(mobile_api)
