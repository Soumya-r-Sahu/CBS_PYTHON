"""
Accounts Controller for Core Banking System Backend

Handles account management operations with encryption for sensitive data.
"""

import logging
from flask import request, jsonify, session
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class AccountsController:
    """Controller for account operations."""
    
    def __init__(self, encryption_service):
        """Initialize the accounts controller."""
        self.encryption_service = encryption_service
    
    def get_accounts(self):
        """Get user accounts."""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Mock account data (in production, fetch from database)
            accounts = [
                {
                    'account_id': 'ACC001',
                    'account_number': self.encryption_service.encrypt_data('1234567890'),
                    'account_type': 'savings',
                    'balance': 15000.50,
                    'currency': 'USD',
                    'status': 'active',
                    'created_at': '2023-01-15T10:30:00Z'
                },
                {
                    'account_id': 'ACC002',
                    'account_number': self.encryption_service.encrypt_data('0987654321'),
                    'account_type': 'checking',
                    'balance': 2500.00,
                    'currency': 'USD',
                    'status': 'active',
                    'created_at': '2023-02-20T14:15:00Z'
                }
            ]
            
            logger.info(f"Retrieved {len(accounts)} accounts for user {user_id}")
            
            return jsonify({
                'success': True,
                'accounts': accounts,
                'total_count': len(accounts)
            })
            
        except Exception as e:
            logger.error(f"Get accounts error: {e}")
            return jsonify({'error': 'Failed to retrieve accounts'}), 500
    
    def get_account(self, account_id):
        """Get specific account details."""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Mock account data (in production, fetch from database with account_id)
            account = {
                'account_id': account_id,
                'account_number': self.encryption_service.encrypt_data('1234567890'),
                'account_type': 'savings',
                'balance': 15000.50,
                'available_balance': 14800.50,
                'currency': 'USD',
                'status': 'active',
                'interest_rate': 2.5,
                'created_at': '2023-01-15T10:30:00Z',
                'last_activity': '2024-01-15T09:45:00Z',
                'branch_code': 'BR001',
                'branch_name': 'Main Branch'
            }
            
            logger.info(f"Retrieved account {account_id} for user {user_id}")
            
            return jsonify({
                'success': True,
                'account': account
            })
            
        except Exception as e:
            logger.error(f"Get account error: {e}")
            return jsonify({'error': 'Failed to retrieve account'}), 500
    
    def get_account_balance(self, account_id):
        """Get account balance."""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Mock balance data (in production, fetch from database)
            balance_info = {
                'account_id': account_id,
                'current_balance': 15000.50,
                'available_balance': 14800.50,
                'pending_transactions': 200.00,
                'currency': 'USD',
                'last_updated': datetime.utcnow().isoformat(),
                'daily_limit': 5000.00,
                'daily_spent': 150.00
            }
            
            # Encrypt sensitive balance information
            encrypted_balance = self.encryption_service.encrypt_data(
                json.dumps({
                    'current_balance': balance_info['current_balance'],
                    'available_balance': balance_info['available_balance']
                })
            )
            
            logger.info(f"Retrieved balance for account {account_id}")
            
            return jsonify({
                'success': True,
                'balance_info': balance_info,
                'encrypted_balance': encrypted_balance
            })
            
        except Exception as e:
            logger.error(f"Get account balance error: {e}")
            return jsonify({'error': 'Failed to retrieve balance'}), 500
    
    def create_account(self):
        """Create a new account."""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            data = request.get_json()
            if not data or 'account_type' not in data:
                return jsonify({'error': 'Account type required'}), 400
            
            account_type = data['account_type']
            initial_deposit = data.get('initial_deposit', 0.0)
            
            # Generate new account ID and number
            import uuid
            account_id = f"ACC{uuid.uuid4().hex[:8].upper()}"
            account_number = f"{uuid.uuid4().int % 10000000000:010d}"
            
            # Encrypt account number
            encrypted_account_number = self.encryption_service.encrypt_data(account_number)
            
            new_account = {
                'account_id': account_id,
                'account_number': encrypted_account_number,
                'account_type': account_type,
                'balance': initial_deposit,
                'currency': 'USD',
                'status': 'active',
                'created_at': datetime.utcnow().isoformat(),
                'user_id': user_id
            }
            
            logger.info(f"Created new account {account_id} for user {user_id}")
            
            return jsonify({
                'success': True,
                'account': new_account,
                'message': 'Account created successfully'
            }), 201
            
        except Exception as e:
            logger.error(f"Create account error: {e}")
            return jsonify({'error': 'Failed to create account'}), 500
    
    def update_account(self, account_id):
        """Update account information."""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Update data required'}), 400
            
            # Mock update operation (in production, update database)
            updated_fields = {}
            allowed_fields = ['account_type', 'status']
            
            for field in allowed_fields:
                if field in data:
                    updated_fields[field] = data[field]
            
            if not updated_fields:
                return jsonify({'error': 'No valid fields to update'}), 400
            
            logger.info(f"Updated account {account_id} for user {user_id}")
            
            return jsonify({
                'success': True,
                'updated_fields': updated_fields,
                'message': 'Account updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Update account error: {e}")
            return jsonify({'error': 'Failed to update account'}), 500
