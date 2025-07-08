"""
Transaction processing utility for handling inbound and outbound transactions
"""
import csv
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Use centralized import system
from utils.lib.packages import fix_path, is_production, is_development, is_test, is_debug_enabled
fix_path()  # Ensures the project root is in sys.path

try:
    from core_banking.utils.config import get_environment_name
except ImportError:
    # Fallback function if the config module is not available
    def get_environment_name():
        env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
        return env_str.capitalize()

# Import database models
try:
    from core_banking.database.models import Transaction, Account
    from core_banking.database import SessionLocal
except ImportError:
    print(f"{Fore.YELLOW}Warning: Could not import database models. Running in demo mode.")
    # Define demo classes
    class Transaction:
        id: str = ""
        account_id: str = ""
        amount: float = 0.0
        transaction_type: str = ""
        status: str = ""
        timestamp: datetime = datetime.now()
        
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class Account:
        id: str = ""
        account_number: str = ""
        customer_id: str = ""
        balance: float = 0.0
        
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    def SessionLocal():
        return None

# Import utility functions
try:
    from core_banking.utils.notification_service import send_transaction_notification
    from core_banking.utils.id_generator import generate_transaction_id
except ImportError:
    print(f"{Fore.YELLOW}Warning: Could not import utility functions. Using fallback implementations.")
    
    def generate_transaction_id():
        """Fallback implementation for transaction ID generation"""
        import uuid
        return f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    
    def send_transaction_notification(transaction, account):
        """Fallback implementation for transaction notification"""
        print(f"{Fore.CYAN}[NOTIFICATION] Transaction {transaction.id} processed for account {account.account_number}")

class TransactionProcessor:
    """Process transactions for Core Banking System"""
    
    def __init__(self):
        self.environment = get_environment_name()
        self._print_environment_banner()
    
    def _print_environment_banner(self):
        """Display the current environment as a colored banner"""
        env = self.environment.upper()
        if is_production():
            color = Fore.GREEN
        elif is_test():
            color = Fore.YELLOW
        else:
            color = Fore.BLUE
        
        print(f"{color}{'=' * 80}")
        print(f"{color}{'=' * 30} {env} ENVIRONMENT {'=' * 30}")
        print(f"{color}{'=' * 80}")
    
    def process_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single transaction
        
        Args:
            transaction_data: Dictionary containing transaction details
            
        Returns:
            Dictionary with transaction result and status
        """
        # Validate transaction data
        if not self._validate_transaction(transaction_data):
            return {"status": "failed", "error": "Invalid transaction data"}
        
        # Generate transaction ID if not provided
        if "transaction_id" not in transaction_data:
            transaction_data["transaction_id"] = generate_transaction_id()
        
        # Apply environment-specific rules
        self._apply_environment_rules(transaction_data)
        
        # Process based on transaction type
        transaction_type = transaction_data.get("type", "").lower()
        if transaction_type == "deposit":
            result = self._process_deposit(transaction_data)
        elif transaction_type == "withdrawal":
            result = self._process_withdrawal(transaction_data)
        elif transaction_type == "transfer":
            result = self._process_transfer(transaction_data)
        else:
            result = {"status": "failed", "error": f"Unsupported transaction type: {transaction_type}"}
        
        # Log transaction
        self._log_transaction(transaction_data, result)
        
        return result
    
    def _validate_transaction(self, transaction_data: Dict[str, Any]) -> bool:
        """
        Validate transaction data
        
        Args:
            transaction_data: Dictionary containing transaction details
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["account_number", "amount", "type"]
        
        # Check required fields
        for field in required_fields:
            if field not in transaction_data:
                print(f"{Fore.RED}Error: Missing required field: {field}")
                return False
        
        # Validate amount
        try:
            amount = float(transaction_data["amount"])
            if amount <= 0:
                print(f"{Fore.RED}Error: Transaction amount must be positive")
                return False
        except ValueError:
            print(f"{Fore.RED}Error: Invalid amount format")
            return False
        
        return True
    
    def _apply_environment_rules(self, transaction_data: Dict[str, Any]) -> None:
        """
        Apply environment-specific rules to transaction
        
        Args:
            transaction_data: Dictionary containing transaction details
        """
        # Get transaction amount
        amount = float(transaction_data["amount"])
        
        # Apply environment-specific limits
        if is_production():
            # Production has the highest limits
            max_amount = 1000000.00
        elif is_test():
            # Test environment has medium limits
            max_amount = 100000.00
        else:  # Development
            # Development has the lowest limits
            max_amount = 10000.00
        
        # Cap the transaction amount if it exceeds the limit
        if amount > max_amount:
            print(f"{Fore.YELLOW}Warning: Transaction amount {amount} exceeds the limit for {self.environment} environment.")
            print(f"{Fore.YELLOW}Amount will be capped at {max_amount}.")
            transaction_data["amount"] = max_amount
            transaction_data["original_amount"] = amount
    
    def _process_deposit(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process deposit transaction"""
        try:
            account_number = transaction_data["account_number"]
            amount = float(transaction_data["amount"])
            
            # Demo implementation - in real code, this would update the database
            print(f"{Fore.GREEN}Processing deposit of {amount} to account {account_number}")
            
            # Create transaction record
            transaction = Transaction(
                id=transaction_data["transaction_id"],
                account_id=account_number,
                amount=amount,
                transaction_type="deposit",
                status="completed",
                timestamp=datetime.now()
            )
            
            # Get account (simplified)
            account = Account(
                id="ACC-ID",
                account_number=account_number,
                balance=1000 + amount  # Demo balance update
            )
            
            # Send notification
            send_transaction_notification(transaction, account)
            
            return {
                "status": "success",
                "transaction_id": transaction_data["transaction_id"],
                "account_number": account_number,
                "amount": amount,
                "new_balance": account.balance,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"{Fore.RED}Error processing deposit: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def _process_withdrawal(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process withdrawal transaction"""
        try:
            account_number = transaction_data["account_number"]
            amount = float(transaction_data["amount"])
            
            # Demo implementation - in real code, this would update the database
            print(f"{Fore.GREEN}Processing withdrawal of {amount} from account {account_number}")
            
            # Demo account balance (would come from database in real implementation)
            initial_balance = 1000.00
            
            if initial_balance < amount:
                return {
                    "status": "failed",
                    "error": "Insufficient funds",
                    "account_number": account_number,
                    "requested_amount": amount,
                    "available_balance": initial_balance
                }
            
            # Create transaction record
            transaction = Transaction(
                id=transaction_data["transaction_id"],
                account_id=account_number,
                amount=amount,
                transaction_type="withdrawal",
                status="completed",
                timestamp=datetime.now()
            )
            
            # Get account (simplified)
            account = Account(
                id="ACC-ID",
                account_number=account_number,
                balance=initial_balance - amount  # Demo balance update
            )
            
            # Send notification
            send_transaction_notification(transaction, account)
            
            return {
                "status": "success",
                "transaction_id": transaction_data["transaction_id"],
                "account_number": account_number,
                "amount": amount,
                "new_balance": account.balance,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"{Fore.RED}Error processing withdrawal: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def _process_transfer(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process transfer transaction"""
        try:
            from_account = transaction_data["account_number"]
            to_account = transaction_data.get("to_account")
            
            if not to_account:
                return {"status": "failed", "error": "Destination account is required for transfers"}
            
            amount = float(transaction_data["amount"])
            
            # Demo implementation - in real code, this would update the database
            print(f"{Fore.GREEN}Processing transfer of {amount} from account {from_account} to {to_account}")
            
            # Demo account balance (would come from database in real implementation)
            initial_balance = 1000.00
            
            if initial_balance < amount:
                return {
                    "status": "failed",
                    "error": "Insufficient funds",
                    "account_number": from_account,
                    "requested_amount": amount,
                    "available_balance": initial_balance
                }
            
            # Create transaction record
            transaction = Transaction(
                id=transaction_data["transaction_id"],
                account_id=from_account,
                amount=amount,
                transaction_type="transfer",
                status="completed",
                timestamp=datetime.now()
            )
            
            # Get source account (simplified)
            source_account = Account(
                id="SRC-ACC-ID",
                account_number=from_account,
                balance=initial_balance - amount  # Demo balance update
            )
            
            # Get destination account (simplified)
            dest_account = Account(
                id="DEST-ACC-ID",
                account_number=to_account,
                balance=initial_balance + amount  # Demo balance update
            )
            
            # Send notification
            send_transaction_notification(transaction, source_account)
            
            return {
                "status": "success",
                "transaction_id": transaction_data["transaction_id"],
                "from_account": from_account,
                "to_account": to_account,
                "amount": amount,
                "source_balance": source_account.balance,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"{Fore.RED}Error processing transfer: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    def _log_transaction(self, transaction_data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """
        Log transaction details
        
        Args:
            transaction_data: Dictionary containing transaction details
            result: Dictionary containing transaction result
        """
        log_dir = Path(__file__).parent.parent.parent / "logs" / "transactions"
        log_dir.mkdir(exist_ok=True, parents=True)
        
        log_file = log_dir / f"{self.environment.lower()}_transactions.log"
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment,
            "transaction_data": transaction_data,
            "result": result
        }
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

# Function to export transactions to CSV
def export_transactions_to_csv(transactions: List[Dict[str, Any]], output_file: str) -> None:
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

# Command line interface
if __name__ == "__main__":
    processor = TransactionProcessor()
    
    # Demo transaction
    demo_transaction = {
        "account_number": "1234567890",
        "amount": 100.50,
        "type": "deposit",
        "description": "Demo transaction"
    }
    
    result = processor.process_transaction(demo_transaction)
    
    print(f"\n{Fore.CYAN}Transaction Result:")
    for key, value in result.items():
        print(f"{Fore.CYAN}{key}: {Style.RESET_ALL}{value}")
