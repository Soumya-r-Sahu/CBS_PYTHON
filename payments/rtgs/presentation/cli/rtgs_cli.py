"""
RTGS CLI interface.
"""
import argparse
import logging
import json
import sys
from datetime import datetime
from uuid import UUID
from typing import Dict, Any

logger = logging.getLogger(__name__)


class RTGSCLI:
    """Command Line Interface for RTGS operations."""
    
    def __init__(self, container):
        """
        Initialize the CLI.
        
        Args:
            container: Dependency injection container
        """
        self.container = container
        
    def setup_parser(self):
        """Set up the argument parser."""
        parser = argparse.ArgumentParser(description='RTGS Command Line Interface')
        subparsers = parser.add_subparsers(dest='command', help='Command to execute')
        
        # Create transaction command
        create_parser = subparsers.add_parser('create-transaction', help='Create a new RTGS transaction')
        create_parser.add_argument('--sender-account', required=True, help='Sender account number')
        create_parser.add_argument('--sender-ifsc', required=True, help='Sender IFSC code')
        create_parser.add_argument('--sender-name', required=True, help='Sender name')
        create_parser.add_argument('--beneficiary-account', required=True, help='Beneficiary account number')
        create_parser.add_argument('--beneficiary-ifsc', required=True, help='Beneficiary IFSC code')
        create_parser.add_argument('--beneficiary-name', required=True, help='Beneficiary name')
        create_parser.add_argument('--amount', required=True, type=float, help='Transaction amount')
        create_parser.add_argument('--reference', required=True, help='Payment reference')
        create_parser.add_argument('--remarks', help='Optional remarks')
        create_parser.add_argument('--priority', choices=['NORMAL', 'HIGH', 'URGENT'], default='NORMAL', help='Transaction priority')
        create_parser.add_argument('--customer-id', help='Customer ID for tracking')
        
        # Get transaction command
        get_parser = subparsers.add_parser('get-transaction', help='Get a transaction by ID')
        get_parser.add_argument('transaction_id', help='Transaction ID')
        
        # Get customer transactions command
        customer_parser = subparsers.add_parser('get-customer-transactions', help='Get transactions for a customer')
        customer_parser.add_argument('customer_id', help='Customer ID')
        customer_parser.add_argument('--limit', type=int, default=10, help='Maximum number of transactions to return')
        
        # Process transactions command
        process_parser = subparsers.add_parser('process-transactions', help='Process pending transactions')
        process_parser.add_argument('--limit', type=int, default=100, help='Maximum number of transactions to process')
        
        # Get batches command
        batches_parser = subparsers.add_parser('get-batches', help='Get RTGS batches')
        batches_parser.add_argument('--status', help='Filter by status')
        batches_parser.add_argument('--limit', type=int, default=10, help='Maximum number of batches to return')
        
        # Get batch command
        batch_parser = subparsers.add_parser('get-batch', help='Get a batch by number')
        batch_parser.add_argument('batch_number', help='Batch number')
        
        # Process batches command
        process_batches_parser = subparsers.add_parser('process-batches', help='Process pending batches')
        
        return parser
    
    def run(self, args=None):
        """
        Run the CLI.
        
        Args:
            args: Command line arguments (defaults to sys.argv[1:])
        
        Returns:
            Dict[str, Any]: Command result
        """
        parser = self.setup_parser()
        args = parser.parse_args(args)
        
        if not args.command:
            parser.print_help()
            return {"status": "error", "message": "No command specified"}
        
        try:
            # Dispatch to the appropriate command handler
            if args.command == 'create-transaction':
                return self._create_transaction(args)
            elif args.command == 'get-transaction':
                return self._get_transaction(args)
            elif args.command == 'get-customer-transactions':
                return self._get_customer_transactions(args)
            elif args.command == 'process-transactions':
                return self._process_transactions(args)
            elif args.command == 'get-batches':
                return self._get_batches(args)
            elif args.command == 'get-batch':
                return self._get_batch(args)
            elif args.command == 'process-batches':
                return self._process_batches(args)
            else:
                return {"status": "error", "message": f"Unknown command: {args.command}"}
        except Exception as e:
            logger.error(f"Error executing command {args.command}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def _create_transaction(self, args):
        """Create a new RTGS transaction."""
        # Prepare payment data
        payment_data = {
            "sender_account_number": args.sender_account,
            "sender_ifsc_code": args.sender_ifsc,
            "sender_name": args.sender_name,
            "beneficiary_account_number": args.beneficiary_account,
            "beneficiary_ifsc_code": args.beneficiary_ifsc,
            "beneficiary_name": args.beneficiary_name,
            "amount": args.amount,
            "reference": args.reference,
            "remarks": args.remarks,
            "priority": args.priority
        }
        
        # Get the use case from container
        transaction_creation_use_case = self.container.get_transaction_creation_use_case()
        
        # Execute the use case
        result = transaction_creation_use_case.execute(
            payment_data=payment_data,
            customer_id=args.customer_id
        )
        
        return result
    
    def _get_transaction(self, args):
        """Get a transaction by ID."""
        # Parse transaction ID
        try:
            transaction_id = UUID(args.transaction_id)
        except ValueError:
            return {"status": "error", "message": "Invalid transaction ID"}
        
        # Get the use case from container
        transaction_query_use_case = self.container.get_transaction_query_use_case()
        
        # Execute the use case
        result = transaction_query_use_case.get_by_id(transaction_id)
        
        if not result:
            return {"status": "error", "message": "Transaction not found"}
        
        return {"status": "success", "data": result}
    
    def _get_customer_transactions(self, args):
        """Get transactions for a customer."""
        # Get the use case from container
        transaction_query_use_case = self.container.get_transaction_query_use_case()
        
        # Execute the use case
        result = transaction_query_use_case.get_by_customer_id(args.customer_id, args.limit)
        
        return {"status": "success", "data": result}
    
    def _process_transactions(self, args):
        """Process pending transactions."""
        # Get the use case from container
        transaction_processing_use_case = self.container.get_transaction_processing_use_case()
        
        # Execute the use case
        result = transaction_processing_use_case.process_pending_transactions(args.limit)
        
        return {"status": "success", "data": result}
    
    def _get_batches(self, args):
        """Get RTGS batches."""
        # Get the use case from container
        batch_query_use_case = self.container.get_batch_query_use_case()
        
        # Execute the use case
        if args.status:
            result = batch_query_use_case.get_by_status(args.status, args.limit)
        else:
            result = batch_query_use_case.get_recent_batches(args.limit)
        
        return {"status": "success", "data": result}
    
    def _get_batch(self, args):
        """Get a batch by number."""
        # Get the use case from container
        batch_query_use_case = self.container.get_batch_query_use_case()
        
        # Execute the use case
        result = batch_query_use_case.get_by_batch_number(args.batch_number)
        
        if not result:
            return {"status": "error", "message": "Batch not found"}
        
        return {"status": "success", "data": result}
    
    def _process_batches(self, args):
        """Process pending batches."""
        # Get the use case from container
        batch_processing_use_case = self.container.get_batch_processing_use_case()
        
        # Execute the use case
        result = batch_processing_use_case.process_pending_batches()
        
        return {"status": "success", "data": result}


def main():
    """Main entry point for the CLI."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Import container for CLI use
    from rtgs.di_container import RTGSDiContainer
    
    # Get configuration
    from rtgs.main_clean_architecture import get_config
    config = get_config()
    
    # Create container
    container = RTGSDiContainer(config)
    
    # Create and run CLI
    cli = RTGSCLI(container)
    result = cli.run()
    
    # Print result as JSON
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
