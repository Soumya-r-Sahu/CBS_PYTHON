"""
Accounts Module Integration Script

This script demonstrates how to integrate the Accounts module with Clean Architecture
into the main CBS_PYTHON application. It shows how to initialize the module,
configure dependencies, and expose its functionality.
"""

import os
import sys
import logging
from uuid import UUID

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the accounts container
from core_banking.accounts.di_container import container

# Import presentation layers for exposure
from core_banking.accounts.presentation.api.accounts_controller import register_accounts_api
from core_banking.accounts.presentation.cli.accounts_cli import main as run_accounts_cli
from core_banking.accounts.presentation.gui.accounts_gui import run_gui as run_accounts_gui

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



def initialize_accounts_module(config=None):
    """
    Initialize the accounts module with configuration
    
    Args:
        config: Optional configuration dictionary to override defaults
    
    Returns:
        The configured container
    """
    # Configure the container
    if config:
        container.config.from_dict(config)
    
    # Initialize any required resources
    logging.info("Initializing accounts module...")
    
    return container


def register_with_flask(app):
    """
    Register the accounts API with a Flask application
    
    Args:
        app: Flask application to register with
    """
    register_accounts_api(app)
    logging.info("Registered accounts API endpoints")


def run_cli():
    """Run the accounts CLI"""
    run_accounts_cli()


def run_gui():
    """Run the accounts GUI"""
    run_accounts_gui()


def get_account_service():
    """
    Get the account service for programmatic usage
    
    Returns:
        AccountService instance
    """
    return container.account_service()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Parse arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="CBS Accounts Module Integration")
    parser.add_argument("--mode", choices=["api", "cli", "gui"], required=True, help="Mode to run")
    args = parser.parse_args()
    
    # Initialize the module
    initialize_accounts_module()
    
    # Run in the specified mode
    if args.mode == "api":
        # Start a simple Flask server to demonstrate the API
        from flask import Flask
        
        app = Flask(__name__)
        register_with_flask(app)
        
        logging.info("Starting accounts API server on http://localhost:5000")
        app.run(debug=True, port=5000)
    
    elif args.mode == "cli":
        logging.info("Starting accounts CLI")
        run_cli()
    
    elif args.mode == "gui":
        logging.info("Starting accounts GUI")
        run_gui()
