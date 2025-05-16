"""
Accounts CLI Interface

This module provides a command-line interface for the Accounts module.
"""

import argparse
import sys
import logging
from decimal import Decimal
from uuid import UUID
import json
import os

from ..di_container import container


class DecimalEncoder(json.JSONEncoder):
    """JSON Encoder that handles Decimal values"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, UUID):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)


def pretty_print(data):
    """Format and print data in a readable way"""
    if isinstance(data, dict):
        print(json.dumps(data, cls=DecimalEncoder, indent=2))
    else:
        print(data)


def create_account(args):
    """Handle create account command"""
    try:
        # Get account service from container
        account_service = container.account_service()
        
        # Call the service
        result = account_service.create_account(
            customer_id=UUID(args.customer_id),
            account_type=args.account_type,
            initial_deposit=Decimal(args.initial_deposit) if args.initial_deposit else None,
            currency=args.currency
        )
        
        # Print the result
        print("\n✅ Account created successfully!\n")
        pretty_print(result)
        
    except Exception as e:
        print(f"\n❌ Error creating account: {str(e)}")
        sys.exit(1)


def get_account_details(args):
    """Handle get account details command"""
    try:
        # Get account service from container
        account_service = container.account_service()
        
        # Call the service
        result = account_service.get_account_details(
            account_id=UUID(args.account_id)
        )
        
        # Print the result
        print("\n📊 Account Details:\n")
        pretty_print(result)
        
    except Exception as e:
        print(f"\n❌ Error retrieving account details: {str(e)}")
        sys.exit(1)


def deposit_funds(args):
    """Handle deposit funds command"""
    try:
        # Get account service from container
        account_service = container.account_service()
        
        # Call the service
        result = account_service.deposit(
            account_id=UUID(args.account_id),
            amount=Decimal(args.amount),
            description=args.description,
            reference_id=args.reference_id
        )
        
        # Print the result
        print("\n💰 Deposit successful!\n")
        pretty_print(result)
        
    except Exception as e:
        print(f"\n❌ Error depositing funds: {str(e)}")
        sys.exit(1)


def withdraw_funds(args):
    """Handle withdraw funds command"""
    try:
        # Get account service from container
        account_service = container.account_service()
        
        # Call the service
        result = account_service.withdraw(
            account_id=UUID(args.account_id),
            amount=Decimal(args.amount),
            description=args.description,
            reference_id=args.reference_id
        )
        
        # Print the result
        print("\n💸 Withdrawal successful!\n")
        pretty_print(result)
        
    except Exception as e:
        print(f"\n❌ Error withdrawing funds: {str(e)}")
        sys.exit(1)


def transfer_funds(args):
    """Handle transfer funds command"""
    try:
        # Get account service from container
        account_service = container.account_service()
        
        # Call the service
        result = account_service.transfer(
            source_account_id=UUID(args.source_account_id),
            target_account_id=UUID(args.target_account_id),
            amount=Decimal(args.amount),
            description=args.description,
            reference_id=args.reference_id
        )
        
        # Print the result
        print("\n🔄 Transfer successful!\n")
        pretty_print(result)
        
    except Exception as e:
        print(f"\n❌ Error transferring funds: {str(e)}")
        sys.exit(1)


def setup_cli():
    """Set up and return the command line interface parser"""
    parser = argparse.ArgumentParser(
        description="CBS Accounts Module CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,        epilog="Example usages:\n"
               "  python -m core_banking.accounts.cli create-account --customer-id 123e4567-e89b-12d3-a456-426614174000 --account-type SAVINGS --initial-deposit 5000\n"
               "  python -m core_banking.accounts.cli get-account --account-id 123e4567-e89b-12d3-a456-426614174000\n"
               "  python -m core_banking.accounts.cli deposit --account-id 123e4567-e89b-12d3-a456-426614174000 --amount 1000 --description \"Salary deposit\"\n"
               "  python -m core_banking.accounts.cli withdraw --account-id 123e4567-e89b-12d3-a456-426614174000 --amount 500 --description \"ATM withdrawal\"\n"
               "  python -m core_banking.accounts.cli transfer --source-account-id 123e4567-e89b-12d3-a456-426614174000 --target-account-id 876e4567-e89b-12d3-a456-426614174000 --amount 1000 --description \"Rent payment\""
    )
    
    # Add global arguments
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create account command
    create_parser = subparsers.add_parser("create-account", help="Create a new account")
    create_parser.add_argument("--customer-id", required=True, help="Customer ID (UUID)")
    create_parser.add_argument("--account-type", required=True, choices=["SAVINGS", "CURRENT", "FIXED_DEPOSIT", "LOAN"], help="Type of account")
    create_parser.add_argument("--initial-deposit", help="Initial deposit amount (decimal)")
    create_parser.add_argument("--currency", default="INR", help="Currency code (default: INR)")
    create_parser.set_defaults(func=create_account)
    
    # Get account details command
    get_parser = subparsers.add_parser("get-account", help="Get account details")
    get_parser.add_argument("--account-id", required=True, help="Account ID (UUID)")
    get_parser.set_defaults(func=get_account_details)
    
    # Deposit funds command
    deposit_parser = subparsers.add_parser("deposit", help="Deposit funds to an account")
    deposit_parser.add_argument("--account-id", required=True, help="Account ID (UUID)")
    deposit_parser.add_argument("--amount", required=True, help="Amount to deposit (decimal)")
    deposit_parser.add_argument("--description", help="Transaction description")
    deposit_parser.add_argument("--reference-id", help="External reference ID")
    deposit_parser.set_defaults(func=deposit_funds)
    
    # Withdraw funds command
    withdraw_parser = subparsers.add_parser("withdraw", help="Withdraw funds from an account")
    withdraw_parser.add_argument("--account-id", required=True, help="Account ID (UUID)")
    withdraw_parser.add_argument("--amount", required=True, help="Amount to withdraw (decimal)")
    withdraw_parser.add_argument("--description", help="Transaction description")
    withdraw_parser.add_argument("--reference-id", help="External reference ID")
    withdraw_parser.set_defaults(func=withdraw_funds)
    
    # Transfer funds command
    transfer_parser = subparsers.add_parser("transfer", help="Transfer funds between accounts")
    transfer_parser.add_argument("--source-account-id", required=True, help="Source Account ID (UUID)")
    transfer_parser.add_argument("--target-account-id", required=True, help="Target Account ID (UUID)")
    transfer_parser.add_argument("--amount", required=True, help="Amount to transfer (decimal)")
    transfer_parser.add_argument("--description", help="Transaction description")
    transfer_parser.add_argument("--reference-id", help="External reference ID")
    transfer_parser.set_defaults(func=transfer_funds)
    
    return parser


def main():
    """Main entry point for the CLI"""
    # Set up the parser
    parser = setup_cli()
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Execute the command function if specified
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
