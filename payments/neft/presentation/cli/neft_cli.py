"""
NEFT CLI Controller.
This module provides command-line interface for NEFT payment operations.
"""
import logging
import cmd
import json
from typing import Dict, Any, Optional
from uuid import UUID

from ...application.use_cases.transaction_creation_use_case import NEFTTransactionCreationUseCase
from ...application.use_cases.transaction_processing_use_case import NEFTTransactionProcessingUseCase
from ...application.use_cases.batch_processing_use_case import NEFTBatchProcessingUseCase
from ...application.use_cases.transaction_query_use_case import NEFTTransactionQueryUseCase
from ...application.use_cases.batch_query_use_case import NEFTBatchQueryUseCase


class NEFTCli(cmd.Cmd):
    """Command-line interface for NEFT payment operations."""
    
    prompt = "NEFT> "
    intro = "Welcome to NEFT CLI. Type 'help' for available commands."
    
    def __init__(
        self,
        transaction_creation_use_case: NEFTTransactionCreationUseCase,
        transaction_processing_use_case: NEFTTransactionProcessingUseCase,
        batch_processing_use_case: NEFTBatchProcessingUseCase,
        transaction_query_use_case: NEFTTransactionQueryUseCase,
        batch_query_use_case: NEFTBatchQueryUseCase
    ):
        """
        Initialize the CLI.
        
        Args:
            transaction_creation_use_case: Use case for creating transactions
            transaction_processing_use_case: Use case for processing transactions
            batch_processing_use_case: Use case for processing batches
            transaction_query_use_case: Use case for querying transactions
            batch_query_use_case: Use case for querying batches
        """
        super().__init__()
        self.transaction_creation_use_case = transaction_creation_use_case
        self.transaction_processing_use_case = transaction_processing_use_case
        self.batch_processing_use_case = batch_processing_use_case
        self.transaction_query_use_case = transaction_query_use_case
        self.batch_query_use_case = batch_query_use_case
        
        self.logger = logging.getLogger(__name__)
    
    def do_create_transaction(self, arg):
        """
        Create a new NEFT transaction.
        Usage: create_transaction <payment_data_json>
        Example: create_transaction {"sender_account_number": "12345", "sender_ifsc_code": "ABCD0123456", "sender_name": "John Doe", "beneficiary_account_number": "67890", "beneficiary_ifsc_code": "EFGH0123456", "beneficiary_name": "Jane Smith", "amount": 1000, "reference": "Invoice #123", "remarks": "Payment for services"}
        """
        try:
            # Parse JSON input
            payment_data = json.loads(arg)
            
            # Execute use case
            result = self.transaction_creation_use_case.execute(
                payment_data=payment_data,
                customer_id=payment_data.get("customer_id"),
                user_id="cli_user"
            )
            
            # Pretty print result
            print(json.dumps(result, indent=2))
            
        except json.JSONDecodeError:
            print("Error: Invalid JSON input")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_process_transaction(self, arg):
        """
        Process a NEFT transaction.
        Usage: process_transaction <transaction_id>
        Example: process_transaction 123e4567-e89b-12d3-a456-426614174000
        """
        try:
            # Execute use case
            result = self.transaction_processing_use_case.process_transaction(
                transaction_id=UUID(arg),
                user_id="cli_user"
            )
            
            # Pretty print result
            print(json.dumps(result, indent=2))
            
        except ValueError:
            print("Error: Invalid transaction ID format")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_get_transaction(self, arg):
        """
        Get details of a NEFT transaction.
        Usage: get_transaction <transaction_id>
        Example: get_transaction 123e4567-e89b-12d3-a456-426614174000
        """
        try:
            # Execute use case
            result = self.transaction_query_use_case.get_transaction(
                transaction_id=UUID(arg),
                user_id="cli_user"
            )
            
            # Pretty print result
            print(json.dumps(result, indent=2))
            
        except ValueError:
            print("Error: Invalid transaction ID format")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_process_batch(self, arg):
        """
        Process a NEFT batch.
        Usage: process_batch <batch_id>
        Example: process_batch 123e4567-e89b-12d3-a456-426614174000
        """
        try:
            # Execute use case
            result = self.batch_processing_use_case.process_batch(
                batch_id=UUID(arg),
                user_id="cli_user"
            )
            
            # Pretty print result
            print(json.dumps(result, indent=2))
            
        except ValueError:
            print("Error: Invalid batch ID format")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_get_batch(self, arg):
        """
        Get details of a NEFT batch.
        Usage: get_batch <batch_id>
        Example: get_batch 123e4567-e89b-12d3-a456-426614174000
        """
        try:
            # Execute use case
            result = self.batch_query_use_case.get_batch(
                batch_id=UUID(arg),
                user_id="cli_user"
            )
            
            # Pretty print result
            print(json.dumps(result, indent=2))
            
        except ValueError:
            print("Error: Invalid batch ID format")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_get_pending_batches(self, arg):
        """
        Get all pending NEFT batches.
        Usage: get_pending_batches
        """
        try:
            # Execute use case
            result = self.batch_query_use_case.get_pending_batches(user_id="cli_user")
            
            # Pretty print result
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_get_batches_by_date(self, arg):
        """
        Get NEFT batches by date.
        Usage: get_batches_by_date <date_str>
        Example: get_batches_by_date 2025-05-17
        """
        try:
            # Execute use case
            result = self.batch_query_use_case.get_batches_by_date(
                date_str=arg,
                user_id="cli_user"
            )
            
            # Pretty print result
            print(json.dumps(result, indent=2))
            
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_get_customer_transactions(self, arg):
        """
        Get NEFT transactions for a customer.
        Usage: get_customer_transactions <customer_id> [limit]
        Example: get_customer_transactions CUST12345 10
        """
        try:
            # Parse arguments
            args = arg.split()
            customer_id = args[0]
            limit = int(args[1]) if len(args) > 1 else 10
            
            # Execute use case
            result = self.transaction_query_use_case.get_customer_transactions(
                customer_id=customer_id,
                limit=limit,
                user_id="cli_user"
            )
            
            # Pretty print result
            print(json.dumps(result, indent=2))
            
        except IndexError:
            print("Error: Missing customer ID")
        except ValueError:
            print("Error: Invalid limit format")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    def do_exit(self, arg):
        """Exit the CLI."""
        print("Exiting NEFT CLI...")
        return True
    
    def do_quit(self, arg):
        """Exit the CLI."""
        return self.do_exit(arg)
