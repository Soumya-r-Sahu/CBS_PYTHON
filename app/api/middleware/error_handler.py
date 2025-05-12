"""
Error handling middleware for Mobile Banking API

Standardized error handling for API endpoints
"""

from flask import Flask, jsonify

def setup_error_handlers(app: Flask):
    """
    Set up global error handlers for the API
    
    Args:
        app: Flask application instance
    """
    # Handle 404 Not Found errors
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'status': 'error',
            'message': 'Resource not found',
            'code': 'RESOURCE_NOT_FOUND'
        }), 404
    
    # Handle 405 Method Not Allowed errors
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'status': 'error',
            'message': 'Method not allowed',
            'code': 'METHOD_NOT_ALLOWED'
        }), 405
    
    # Handle 400 Bad Request errors
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'status': 'error',
            'message': 'Bad request',
            'code': 'BAD_REQUEST',
            'details': str(error) if hasattr(error, 'description') else None
        }), 400
    
    # Handle 500 Internal Server Error
    @app.errorhandler(500)
    def server_error(error):
        # In production, we would log the error here
        return jsonify({
            'status': 'error',
            'message': 'Internal server error',
            'code': 'INTERNAL_SERVER_ERROR'
        }), 500
    
    # Handle custom APIException
    @app.errorhandler(APIException)
    def handle_api_exception(error):
        return jsonify({
            'status': 'error',
            'message': error.message,
            'code': error.code,
            'details': error.details
        }), error.status_code

# Custom exception class for API errors
class APIException(Exception):
    """Custom exception for API errors with standardized format"""
    
    def __init__(self, message, code, status_code=400, details=None):
        """
        Initialize API exception
        
        Args:
            message (str): Human-readable error message
            code (str): Error code for client-side error handling
            status_code (int): HTTP status code
            details (dict, optional): Additional error details
        """
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)
