"""
CLI utility to run the Mobile Banking API server
"""

import os
import sys
import argparse
from app.api.app import create_app

def parse_args():
    """
    Parse command line arguments
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description='Run the Mobile Banking API server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    return parser.parse_args()

def main():
    """
    Main entry point
    """
    args = parse_args()
    
    # Create and configure Flask app
    app = create_app()
    
    # Run the app
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )

if __name__ == '__main__':
    main()
