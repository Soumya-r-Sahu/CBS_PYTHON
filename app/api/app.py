"""
Main application module for CBS-python

Initializes the Flask application and sets up routes
"""

from flask import Flask
from app.api.routes import setup_routes
import os

def create_app():
    """
    Create and configure the Flask application
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Configure app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Setup API routes
    setup_routes(app)
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
