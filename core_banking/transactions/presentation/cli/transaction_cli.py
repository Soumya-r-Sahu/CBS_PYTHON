"""
Transaction CLI Interface

Command-line interface for transaction processing.
"""
import csv
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional
from uuid import UUID

from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Import domain and application components
from ...domain.entities.transaction import Transaction, TransactionStatus, TransactionType
from ...domain.services.transaction_rules_service import TransactionRulesService
from ...domain.services.validation_service import ValidationService
from ...application.use_cases.create_transaction_use_case import CreateTransactionUseCase
from ...infrastructure.repositories.sqlalchemy_transaction_repository import SQLAlchemyTransactionRepository
from ...infrastructure.services.default_notification_service import DefaultNotificationService

# Import from other modules
from core_banking.utils.config import get_environment_name

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path


class TransactionCLI:
    """Command-line interface for transaction processing"""
    
    def __init__(self):
        """Initialize the CLI interface"""
        self.environment = get_environment_name()
        self._print_environment_banner()
        
        # Initialize domain services
        self.transaction_rules_service = TransactionRulesService()
        self.validation_service = ValidationService()
        
        # Initialize infrastructure services
        self.transaction_repository = SQLAlchemyTransactionRepository()
        self.notification_service = DefaultNotificationService(self.environment)
        
        # Import and initialize the account service
        try:
            from core_banking.accounts.infrastructure.services.account_service import AccountService
            self.account_service = AccountService()
        except ImportError:
            # Fallback to mock account service if not available
            from ..mocks.mock_account_service import MockAccountService
            print(f"{Fore.YELLOW}Warning: Could not import AccountService. Using mock implementation.")
            self.account_service = MockAccountService()
        
        # Create use case
        self.create_transaction_use_case = CreateTransactionUseCase(
            transaction_repository=self.transaction_repository,
            account_service=self.account_service,
            notification_service=self.notification_service,
            transaction_rules_service=self.transaction_rules_service,
            validation_service=self.validation_service
        )
    
    def _print_environment_banner(self):
        """Display the current environment as a colored banner"""
        env = self.environment.upper()
        
        if self.environment.lower() == "production":
            color = Fore.GREEN
        elif self.environment.lower() == "test":
            color = Fore.YELLOW
        else:
            color = Fore.BLUE
        
        print(f"{color}{'=' * 80}")
        print(f"{color}{'=' * 30} {env} ENVIRONMENT {'=' * 30}")
        print(f"{color}{'=' * 80}")
    
    def process_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a transaction using the CreateTransactionUseCase
        
        Args:
            transaction_data: Transaction data dictionary
            
        Returns:
            Result dictionary
        """
        # Convert input data format to match use case requirements
        use_case_data = self._prepare_transaction_data(transaction_data)
        
        # Execute the use case
        result = self.create_transaction_use_case.execute(use_case_data)
        
        # Display result
        self._display_transaction_result(result)
        
        return result
    
    def _prepare_transaction_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare transaction data for use case
        
        Args:
            input_data: Input transaction data
            
        Returns:
            Prepared transaction data
        """
        # Convert field names and formats as needed
        prepared_data = {
            "account_id": input_data.get("account_number", input_data.get("account_id")),
            "amount": Decimal(str(input_data["amount"])),
            "transaction_type": input_data["type"].upper(),
            "description": input_data.get("description", "")
        }
        
        # Handle transfer-specific fields
        if input_data["type"].lower() == "transfer":
            prepared_data["to_account_id"] = input_data.get("to_account", input_data.get("to_account_number"))
        
        # Add metadata if available
        if "metadata" in input_data:
            prepared_data["metadata"] = input_data["metadata"]
        else:
            # Create basic metadata
            prepared_data["metadata"] = {
                "channel": input_data.get("channel", "CLI"),
                "location": input_data.get("location"),
                "reference_id": input_data.get("reference_id")
            }
        
        return prepared_data
    
    def _display_transaction_result(self, result: Dict[str, Any]):
        """
        Display transaction result in the console
        
        Args:
            result: Transaction result dictionary
        """
        if result.get("success", False):
            print(f"\n{Fore.GREEN}Transaction successful:")
            print(f"Transaction ID: {result.get('transaction_id')}")
            print(f"Status: {result.get('status')}")
            
            if result.get("requires_verification", False):
                print(f"{Fore.YELLOW}Note: This transaction requires additional verification.")
        else:
            print(f"\n{Fore.RED}Transaction failed:")
            for error in result.get("errors", []):
                print(f"- {error}")
            
            if "details" in result:
                print("\nDetails:")
                for key, value in result["details"].items():
                    print(f"{key}: {value}")
    
    def export_transactions_to_csv(self, transactions: List[Dict[str, Any]], output_file: str) -> None:
        """
        Export transactions to CSV file
        
        Args:
            transactions: List of transaction dictionaries
            output_file: Path to output CSV file
        """
        if not transactions:
            print(f"{Fore.YELLOW}Warning: No transactions to export")
            return
        
        try:
            fields = transactions[0].keys()
            
            with open(output_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fields)
                writer.writeheader()
                writer.writerows(transactions)
                
            print(f"{Fore.GREEN}Successfully exported {len(transactions)} transactions to {output_file}")
        except Exception as e:
            print(f"{Fore.RED}Error exporting transactions: {str(e)}")

# CLI entry point
def main():
    """Main CLI entry point"""
    cli = TransactionCLI()
    
    # Handle command-line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "export":
            # Handle export command
            if len(sys.argv) < 3:
                print(f"{Fore.RED}Error: Missing output file path")
                print("Usage: python -m core_banking.transactions.presentation.cli.transaction_cli export <output_file>")
                return
            
            # Retrieve transactions from repository
            transactions = cli.transaction_repository.search({}, limit=1000)
            
            # Convert to dictionaries
            transaction_dicts = [t.to_dict() for t in transactions]
            
            # Export to CSV
            cli.export_transactions_to_csv(transaction_dicts, sys.argv[2])
            
        elif command == "process":
            # Handle process command (from file or stdin)
            if len(sys.argv) < 3:
                print(f"{Fore.RED}Error: Missing transaction data file or JSON string")
                print("Usage: python -m core_banking.transactions.presentation.cli.transaction_cli process <json_file_or_string>")
                return
            
            # Check if argument is a file or JSON string
            arg = sys.argv[2]
            transaction_data = None
            
            if os.path.isfile(arg):
                # Read from file
                with open(arg, 'r') as f:
                    transaction_data = json.load(f)
            else:
                # Parse as JSON string
                try:
                    transaction_data = json.loads(arg)
                except json.JSONDecodeError:
                    print(f"{Fore.RED}Error: Invalid JSON data")
                    return
            
            # Process transaction
            cli.process_transaction(transaction_data)
            
        else:
            print(f"{Fore.RED}Error: Unknown command: {command}")
            print("Available commands: process, export")
    else:
        # Demo transaction
        print(f"{Fore.CYAN}No command specified. Running demo transaction...")
        
        demo_transaction = {
            "account_number": "1234567890",
            "amount": 100.50,
            "type": "deposit",
            "description": "Demo transaction"
        }
        
        cli.process_transaction(demo_transaction)

if __name__ == "__main__":
    main()
