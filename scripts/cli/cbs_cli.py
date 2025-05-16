#!/usr/bin/env python
"""
CBS Core Banking System CLI

A unified command-line interface for the CBS Core Banking System.
This CLI provides access to all banking modules through a single entry point.

Usage:
    python -m scripts.cli.cbs_cli [options] <command> [<args>...]

Example:
    python -m scripts.cli.cbs_cli accounts create-account --customer-id 123e4567-e89b-12d3-a456-426614174000 --account-type SAVINGS
"""

import argparse
import sys
import logging
import os
import importlib
from typing import Dict, List, Optional, Any


def setup_logging(debug: bool = False):
    """Set up logging configuration"""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(os.path.join("logs", "cbs_cli.log"))
        ]
    )


def create_root_parser() -> argparse.ArgumentParser:
    """
    Create the root argument parser for the CBS CLI.
    
    Returns:
        argparse.ArgumentParser: Configured parser
    """
    parser = argparse.ArgumentParser(
        description="CBS Core Banking System CLI",
        usage="python -m scripts.cli.cbs_cli [options] <module> <command> [<args>...]"
    )
    
    # Global options
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--config", help="Path to a custom configuration file")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    
    # Module argument
    parser.add_argument(
        "module",
        help="Banking module to use",
        choices=["accounts", "customers", "loans", "transactions", "payments", "upi"],
        nargs="?"
    )
    
    return parser


def load_cli_module(module_name: str) -> Any:
    """
    Dynamically load a CLI module based on the module name.
    
    Args:
        module_name (str): Name of the module (e.g., 'accounts', 'customers')
        
    Returns:
        Any: The imported CLI module
    
    Raises:
        ImportError: If the CLI module cannot be loaded
    """
    module_mapping = {
        "accounts": "core_banking.accounts.presentation.cli.accounts_cli",
        "customers": "core_banking.customer_management.presentation.cli.customers_cli",
        "loans": "core_banking.loans.presentation.cli.loans_cli", 
        "transactions": "core_banking.transactions.presentation.cli.transactions_cli",
        "payments": "payments.presentation.cli.payments_cli",
        "upi": "payments.upi.presentation.cli.upi_cli"
    }
    
    if module_name not in module_mapping:
        raise ImportError(f"CLI module for '{module_name}' is not available")
    
    module_path = module_mapping[module_name]
    try:
        return importlib.import_module(module_path)
    except ImportError as e:
        logging.error(f"Failed to import {module_path}: {e}")
        raise ImportError(f"CLI module for '{module_name}' is not implemented or cannot be loaded: {e}")


def show_version():
    """Show the current version of the CBS system"""
    from importlib.metadata import version, PackageNotFoundError
    
    try:
        cbs_version = version("cbs_python")
    except PackageNotFoundError:
        cbs_version = "development"
    
    print(f"CBS Core Banking System CLI version {cbs_version}")
    print("Modules available:")
    
    # Try to import each module and show its version/status
    modules = {
        "Accounts": "core_banking.accounts",
        "Customer Management": "core_banking.customer_management",
        "Loans": "core_banking.loans",
        "Transactions": "core_banking.transactions",
        "UPI Payments": "payments.upi"
    }
    
    for name, module_path in modules.items():
        try:
            module = importlib.import_module(module_path)
            module_version = getattr(module, "__version__", "available")
            print(f"  ✅ {name}: {module_version}")
        except ImportError:
            print(f"  ❌ {name}: not available")


def main():
    """Main entry point for the CBS CLI"""
    # Create the root parser
    parser = create_root_parser()
    
    # Parse the initial arguments (just to get the module and global options)
    args, remaining_args = parser.parse_known_args()
    
    # Configure logging
    setup_logging(args.debug)
    
    # Show version if requested
    if args.version:
        show_version()
        return
    
    # If no module is specified, show help
    if not args.module:
        parser.print_help()
        return
    
    try:
        # Load the appropriate CLI module
        cli_module = load_cli_module(args.module)
        
        # Get the module parser
        module_parser = cli_module.setup_cli()
        
        # Parse the remaining arguments with the module's parser
        module_args = module_parser.parse_args(remaining_args)
        
        # Execute the command function if specified
        if hasattr(module_args, "func"):
            module_args.func(module_args)
        else:
            module_parser.print_help()
    
    except ImportError as e:
        logging.error(f"Module '{args.module}' CLI is not available: {e}")
        print(f"\n❌ Error: {str(e)}")
        print(f"\nThe CLI for the '{args.module}' module is not available or fully implemented.")
        print("Please check the available modules with --version or check the documentation.")
    
    except Exception as e:
        logging.exception(f"Error executing {args.module} command: {e}")
        print(f"\n❌ Error executing command: {str(e)}")


if __name__ == "__main__":
    main()