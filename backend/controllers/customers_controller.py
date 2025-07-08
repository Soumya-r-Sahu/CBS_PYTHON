"""
Customers Controller for Core Banking System Backend

Handles customer management operations with encryption for sensitive data.
"""

import logging
from flask import request, jsonify, session
from datetime import datetime
import json
import uuid

logger = logging.getLogger(__name__)

class CustomersController:
    """Controller for customer operations."""
    
    def __init__(self, encryption_service):
        """Initialize the customers controller."""
        self.encryption_service = encryption_service
    
    def get_customers(self):
        """Get customers (admin operation)."""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check if user has admin privileges (mock implementation)
            if not self._is_admin(user_id):
                return jsonify({'error': 'Admin privileges required'}), 403
            
            # Get query parameters
            limit = int(request.args.get('limit', 50))
            offset = int(request.args.get('offset', 0))
            search = request.args.get('search', '')
            
            # Mock customer data (in production, fetch from database)
            customers = [
                {
                    'customer_id': 'CUST001',
                    'full_name': 'John Doe',
                    'email': self.encryption_service.encrypt_data('john.doe@email.com'),
                    'phone': self.encryption_service.encrypt_data('+1234567890'),
                    'status': 'active',
                    'kyc_status': 'verified',
                    'created_at': '2023-01-15T10:30:00Z',
                    'last_login': '2024-01-15T09:45:00Z',
                    'account_count': 2,
                    'total_balance': 17500.50
                },
                {
                    'customer_id': 'CUST002',
                    'full_name': 'Jane Smith',
                    'email': self.encryption_service.encrypt_data('jane.smith@email.com'),
                    'phone': self.encryption_service.encrypt_data('+1234567891'),
                    'status': 'active',
                    'kyc_status': 'pending',
                    'created_at': '2023-02-20T14:15:00Z',
                    'last_login': '2024-01-14T16:20:00Z',
                    'account_count': 1,
                    'total_balance': 5000.00
                }
            ]
            
            # Apply search filter if provided
            if search:
                customers = [c for c in customers if search.lower() in c['full_name'].lower()]
            
            # Apply pagination
            total_count = len(customers)
            customers = customers[offset:offset + limit]
            
            logger.info(f"Retrieved {len(customers)} customers for admin {user_id}")
            
            return jsonify({
                'success': True,
                'customers': customers,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            })
            
        except Exception as e:
            logger.error(f"Get customers error: {e}")
            return jsonify({'error': 'Failed to retrieve customers'}), 500
    
    def get_customer(self, customer_id):
        """Get specific customer details."""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check if user has access to customer data
            if not (self._is_admin(user_id) or self._is_own_customer(user_id, customer_id)):
                return jsonify({'error': 'Access denied'}), 403
            
            # Mock customer data (in production, fetch from database)
            customer = {
                'customer_id': customer_id,
                'full_name': 'John Doe',
                'email': self.encryption_service.encrypt_data('john.doe@email.com'),
                'phone': self.encryption_service.encrypt_data('+1234567890'),
                'date_of_birth': self.encryption_service.encrypt_data('1985-05-15'),
                'address': {
                    'street': self.encryption_service.encrypt_data('123 Main St'),
                    'city': 'New York',
                    'state': 'NY',
                    'zip_code': self.encryption_service.encrypt_data('10001'),
                    'country': 'USA'
                },
                'status': 'active',
                'kyc_status': 'verified',
                'created_at': '2023-01-15T10:30:00Z',
                'last_login': '2024-01-15T09:45:00Z',
                'account_count': 2,
                'total_balance': 17500.50,
                'preferred_language': 'en',
                'notification_preferences': {
                    'email': True,
                    'sms': True,
                    'push': False
                }
            }
            
            logger.info(f"Retrieved customer {customer_id} details")
            
            return jsonify({
                'success': True,
                'customer': customer
            })
            
        except Exception as e:
            logger.error(f"Get customer error: {e}")
            return jsonify({'error': 'Failed to retrieve customer'}), 500
    
    def create_customer(self):
        """Create a new customer."""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check admin privileges for customer creation
            if not self._is_admin(user_id):
                return jsonify({'error': 'Admin privileges required'}), 403
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Customer data required'}), 400
            
            required_fields = ['full_name', 'email', 'phone', 'date_of_birth']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return jsonify({'error': f'Missing required fields: {missing_fields}'}), 400
            
            # Generate customer ID
            customer_id = f"CUST{uuid.uuid4().hex[:8].upper()}"
            
            # Encrypt sensitive data
            encrypted_email = self.encryption_service.encrypt_data(data['email'])
            encrypted_phone = self.encryption_service.encrypt_data(data['phone'])
            encrypted_dob = self.encryption_service.encrypt_data(data['date_of_birth'])
            
            # Create customer record
            customer = {
                'customer_id': customer_id,
                'full_name': data['full_name'],
                'email': encrypted_email,
                'phone': encrypted_phone,
                'date_of_birth': encrypted_dob,
                'status': 'active',
                'kyc_status': 'pending',
                'created_at': datetime.utcnow().isoformat(),
                'created_by': user_id,
                'account_count': 0,
                'total_balance': 0.0
            }
            
            # Add optional address if provided
            if 'address' in data:
                address = data['address']
                customer['address'] = {
                    'street': self.encryption_service.encrypt_data(address.get('street', '')),
                    'city': address.get('city', ''),
                    'state': address.get('state', ''),
                    'zip_code': self.encryption_service.encrypt_data(address.get('zip_code', '')),
                    'country': address.get('country', 'USA')
                }
            
            logger.info(f"Created customer {customer_id} by admin {user_id}")
            
            return jsonify({
                'success': True,
                'customer': customer,
                'message': 'Customer created successfully'
            }), 201
            
        except Exception as e:
            logger.error(f"Create customer error: {e}")
            return jsonify({'error': 'Failed to create customer'}), 500
    
    def update_customer(self, customer_id):
        """Update customer information."""
        try:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check if user has access to update customer data
            if not (self._is_admin(user_id) or self._is_own_customer(user_id, customer_id)):
                return jsonify({'error': 'Access denied'}), 403
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Update data required'}), 400
            
            # Define allowed fields for update
            allowed_fields = ['full_name', 'email', 'phone', 'address', 'notification_preferences']
            updated_fields = {}
            
            for field in allowed_fields:
                if field in data:
                    value = data[field]
                    # Encrypt sensitive fields
                    if field in ['email', 'phone']:
                        value = self.encryption_service.encrypt_data(value)
                    elif field == 'address' and isinstance(value, dict):
                        # Encrypt sensitive address fields
                        if 'street' in value:
                            value['street'] = self.encryption_service.encrypt_data(value['street'])
                        if 'zip_code' in value:
                            value['zip_code'] = self.encryption_service.encrypt_data(value['zip_code'])
                    
                    updated_fields[field] = value
            
            if not updated_fields:
                return jsonify({'error': 'No valid fields to update'}), 400
            
            # Add update metadata
            updated_fields['updated_at'] = datetime.utcnow().isoformat()
            updated_fields['updated_by'] = user_id
            
            logger.info(f"Updated customer {customer_id} by user {user_id}")
            
            return jsonify({
                'success': True,
                'updated_fields': updated_fields,
                'message': 'Customer updated successfully'
            })
            
        except Exception as e:
            logger.error(f"Update customer error: {e}")
            return jsonify({'error': 'Failed to update customer'}), 500
    
    def _is_admin(self, user_id):
        """Check if user has admin privileges (mock implementation)."""
        # In production, check against user roles in database
        admin_users = ['user_admin123', 'user_superadmin']
        return user_id in admin_users
    
    def _is_own_customer(self, user_id, customer_id):
        """Check if user is accessing their own customer record (mock implementation)."""
        # In production, check against database relations
        return user_id == f"user_{customer_id.lower()}"
