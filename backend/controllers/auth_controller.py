"""
Authentication Controller for Core Banking System Backend

Handles user authentication, session management, and security operations.
All sensitive operations are encrypted using the encryption service.
"""

import logging
from flask import request, jsonify, session
from datetime import datetime, timedelta
import jwt
import hashlib
import secrets

logger = logging.getLogger(__name__)

class AuthController:
    """Controller for authentication operations."""
    
    def __init__(self, encryption_service):
        """Initialize the authentication controller."""
        self.encryption_service = encryption_service
        self.secret_key = secrets.token_hex(32)  # In production, use environment variable
    
    def login(self):
        """Handle user login."""
        try:
            data = request.get_json()
            
            if not data or 'username' not in data or 'password' not in data:
                return jsonify({'error': 'Username and password required'}), 400
            
            username = data['username']
            password = data['password']
            
            # Encrypt credentials before processing
            encrypted_username = self.encryption_service.encrypt_data(username)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Validate credentials (in production, check against database)
            if self._validate_credentials(username, password_hash):
                # Generate JWT token
                token_payload = {
                    'user_id': self._get_user_id(username),
                    'username': encrypted_username,
                    'exp': datetime.utcnow() + timedelta(hours=24),
                    'iat': datetime.utcnow()
                }
                
                token = jwt.encode(token_payload, self.secret_key, algorithm='HS256')
                
                # Store session data
                session['user_id'] = token_payload['user_id']
                session['username'] = username
                session['token'] = token
                
                logger.info(f"User {username} logged in successfully")
                
                return jsonify({
                    'success': True,
                    'token': token,
                    'user_id': token_payload['user_id'],
                    'expires_at': token_payload['exp'].isoformat()
                })
            
            else:
                logger.warning(f"Failed login attempt for user: {username}")
                return jsonify({'error': 'Invalid credentials'}), 401
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({'error': 'Authentication failed'}), 500
    
    def logout(self):
        """Handle user logout."""
        try:
            # Clear session
            user_id = session.get('user_id')
            session.clear()
            
            logger.info(f"User {user_id} logged out successfully")
            
            return jsonify({
                'success': True,
                'message': 'Logged out successfully'
            })
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return jsonify({'error': 'Logout failed'}), 500
    
    def refresh_token(self):
        """Refresh authentication token."""
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({'error': 'No token provided'}), 401
            
            token = auth_header.split(' ')[1]
            
            try:
                payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
                
                # Generate new token
                new_payload = {
                    'user_id': payload['user_id'],
                    'username': payload['username'],
                    'exp': datetime.utcnow() + timedelta(hours=24),
                    'iat': datetime.utcnow()
                }
                
                new_token = jwt.encode(new_payload, self.secret_key, algorithm='HS256')
                
                return jsonify({
                    'success': True,
                    'token': new_token,
                    'expires_at': new_payload['exp'].isoformat()
                })
                
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Token expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401
                
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return jsonify({'error': 'Token refresh failed'}), 500
    
    def validate_token(self, token):
        """Validate JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def _validate_credentials(self, username, password_hash):
        """Validate user credentials (mock implementation)."""
        # In production, this would check against a database
        # For demo purposes, accept any username with password "password"
        expected_hash = hashlib.sha256("password".encode()).hexdigest()
        return password_hash == expected_hash
    
    def _get_user_id(self, username):
        """Get user ID for username (mock implementation)."""
        # In production, this would query the database
        return f"user_{hashlib.md5(username.encode()).hexdigest()[:8]}"
