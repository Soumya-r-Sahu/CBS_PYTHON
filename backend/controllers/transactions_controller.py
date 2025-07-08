"""
Transactions Controller for Core Banking System Backend

Handles transaction operations with encryption for sensitive data.
"""

import logging
from flask import request, jsonify, session
from datetime import datetime, timedelta
import json
import uuid

logger = logging.getLogger(__name__)

class TransactionsController:
    """Controller for transaction operations."""
    
    def __init__(self, encryption_service):
        """Initialize the transactions controller."""
        self.encryption_service = encryption_service
    
    def get_transactions(self):
        """Get user transactions."""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Get query parameters
            account_id = request.args.get('account_id')
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            
            # Mock transaction data (in production, fetch from database)
            transactions = [
                {
                    'transaction_id': 'TXN001',
                    'account_id': 'ACC001',
                    'type': 'debit',
                    'amount': 250.00,
                    'currency': 'USD',
                    'description': 'Online Purchase',
                    'merchant': 'Amazon',
                    'status': 'completed',
                    'created_at': '2024-01-15T10:30:00Z',
                    'reference_number': self.encryption_service.encrypt_data('REF001234567')
                },
                {
                    'transaction_id': 'TXN002',
                    'account_id': 'ACC001',
                    'type': 'credit',
                    'amount': 1500.00,
                    'currency': 'USD',
                    'description': 'Salary Deposit',
                    'merchant': 'Employer Inc',
                    'status': 'completed',
                    'created_at': '2024-01-14T09:15:00Z',
                    'reference_number': self.encryption_service.encrypt_data('REF001234568')
                },
                {
                    'transaction_id': 'TXN003',
                    'account_id': 'ACC001',
                    'type': 'debit',
                    'amount': 85.50,
                    'currency': 'USD',
                    'description': 'Grocery Store',
                    'merchant': 'SuperMart',
                    'status': 'pending',
                    'created_at': '2024-01-15T14:20:00Z',
                    'reference_number': self.encryption_service.encrypt_data('REF001234569')
                }
            ]
            
            # Filter by account_id if specified
            if account_id:
                transactions = [t for t in transactions if t['account_id'] == account_id]
            
            # Apply pagination
            total_count = len(transactions)
            transactions = transactions[offset:offset + limit]
            
            logger.info(f"Retrieved {len(transactions)} transactions for user {user_id}")
            
            return jsonify({
                'success': True,
                'transactions': transactions,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            })
            
        except Exception as e:
            logger.error(f"Get transactions error: {e}")
            return jsonify({'error': 'Failed to retrieve transactions'}), 500
    
    def get_transaction(self, transaction_id):
        """Get specific transaction details."""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Mock transaction data (in production, fetch from database)
            transaction = {
                'transaction_id': transaction_id,
                'account_id': 'ACC001',
                'type': 'debit',
                'amount': 250.00,
                'currency': 'USD',
                'description': 'Online Purchase',
                'merchant': 'Amazon',
                'status': 'completed',
                'created_at': '2024-01-15T10:30:00Z',
                'processed_at': '2024-01-15T10:31:00Z',
                'reference_number': self.encryption_service.encrypt_data('REF001234567'),
                'authorization_code': self.encryption_service.encrypt_data('AUTH123456'),
                'fee': 0.00,
                'exchange_rate': 1.0,
                'category': 'shopping',
                'tags': ['online', 'retail']
            }
            
            logger.info(f"Retrieved transaction {transaction_id} for user {user_id}")
            
            return jsonify({
                'success': True,
                'transaction': transaction
            })
            
        except Exception as e:
            logger.error(f"Get transaction error: {e}")
            return jsonify({'error': 'Failed to retrieve transaction'}), 500
    
    def create_transaction(self):
        """Create a new transaction."""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Transaction data required'}), 400
            
            required_fields = ['from_account', 'to_account', 'amount', 'description']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
            
            # Generate transaction ID and reference number
            transaction_id = f"TXN{uuid.uuid4().hex[:8].upper()}"
            reference_number = f"REF{uuid.uuid4().hex[:10].upper()}"
            
            # Encrypt sensitive data
            encrypted_reference = self.encryption_service.encrypt_data(reference_number)
            encrypted_from_account = self.encryption_service.encrypt_data(data['from_account'])
            encrypted_to_account = self.encryption_service.encrypt_data(data['to_account'])
            
            # Create transaction record
            transaction = {
                'transaction_id': transaction_id,
                'from_account': encrypted_from_account,
                'to_account': encrypted_to_account,
                'amount': float(data['amount']),
                'currency': data.get('currency', 'USD'),
                'description': data['description'],
                'type': 'transfer',
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat(),
                'reference_number': encrypted_reference,
                'user_id': user_id
            }
            
            logger.info(f"Created transaction {transaction_id} for user {user_id}")
            
            return jsonify({
                'success': True,
                'transaction': transaction,
                'message': 'Transaction created successfully'
            }), 201
            
        except Exception as e:
            logger.error(f"Create transaction error: {e}")
            return jsonify({'error': 'Failed to create transaction'}), 500
    
    def get_transaction_history(self):
        """Get detailed transaction history."""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Get query parameters
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            transaction_type = request.args.get('type')
            
            # Mock transaction history data
            history = {
                'account_summary': {
                    'total_credits': 5000.00,
                    'total_debits': 1200.50,
                    'net_change': 3799.50,
                    'transaction_count': 15
                },
                'monthly_summary': [
                    {
                        'month': '2024-01',
                        'credits': 3000.00,
                        'debits': 800.50,
                        'net': 2199.50,
                        'count': 10
                    },
                    {
                        'month': '2023-12',
                        'credits': 2000.00,
                        'debits': 400.00,
                        'net': 1600.00,
                        'count': 5
                    }
                ],
                'categories': [
                    {'category': 'salary', 'amount': 3000.00, 'count': 2},
                    {'category': 'shopping', 'amount': 450.50, 'count': 5},
                    {'category': 'utilities', 'amount': 200.00, 'count': 3}
                ]
            }
            
            logger.info(f"Retrieved transaction history for user {user_id}")
            
            return jsonify({
                'success': True,
                'history': history
            })
            
        except Exception as e:
            logger.error(f"Get transaction history error: {e}")
            return jsonify({'error': 'Failed to retrieve transaction history'}), 500
