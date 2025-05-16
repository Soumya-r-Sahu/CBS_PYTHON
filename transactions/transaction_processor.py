"""
Transaction processing utility for handling inbound and outbound transactions
with thread-safety and proper locking for concurrent operations
"""
import csv
import json
import os
import sys
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Try to import environment module
try:
    # Commented out direct sys.path modification
    # sys.path.insert(0, str(Path(__file__))
    from utils.lib.packages import fix_path
    from app.config.environment import (
        get_environment_name, is_production, is_development, is_test,
        is_debug_enabled, Environment
    )
except ImportError:
    # Fallback environment detection
    env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    def is_production(): return env_str == "production"
    def is_development(): return env_str == "development"
    def is_test(): return env_str == "test"
    def get_environment_name(): return env_str.capitalize()
    def is_debug_enabled(): return os.environ.get("CBS_DEBUG", "false").lower() == "true"

class TransactionProcessor:
    def __init__(self, inbound_dir="transactions/inbound", outbound_dir="transactions/outbound"):
        # Thread locks for concurrent operations
        self.inbound_lock = threading.RLock()
        self.outbound_lock = threading.RLock()
        self.batch_lock = threading.RLock()
        
        # Add environment-specific directories
        env_name = get_environment_name().lower()
        if not is_production():
            # Use environment-specific directories in non-production
            inbound_dir = f"transactions/inbound/{env_name}"
            outbound_dir = f"transactions/outbound/{env_name}"
        
        self.inbound_dir = inbound_dir
        self.outbound_dir = outbound_dir
        os.makedirs(inbound_dir, exist_ok=True)
        os.makedirs(outbound_dir, exist_ok=True)
        
        # Environment-specific settings
        self.env_name = get_environment_name()
        
        # Set environment-specific colors and transaction limits
        if is_production():
            self.env_color = Fore.GREEN
            self.max_transaction_amount = float('inf')  # No limit in production
            self.requires_approval = False  # Real transactions don't need test approval
        elif is_test():
            self.env_color = Fore.YELLOW
            self.max_transaction_amount = 50000  # Test limit
            self.requires_approval = True  # Test transactions need approval
        else:  # development
            self.env_color = Fore.BLUE
            self.max_transaction_amount = 10000  # Dev limit
            self.requires_approval = True  # Dev transactions need approval
        
        # Set logging verbosity based on environment
        self.verbose_logging = not is_production() or is_debug_enabled()
        
        if self.verbose_logging:
            print(f"{self.env_color}[Transaction Processor] Initialized in {self.env_name} environment{Style.RESET_ALL}")
            if not is_production():
                print(f"{self.env_color}Transaction Limit: ₹{self.max_transaction_amount:,.2f} | Approval Required: {self.requires_approval}{Style.RESET_ALL}")
                
    def process_inbound_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """
        Process an inbound transaction and store it
        
        Parameters:
        - transaction_data: Dictionary with transaction details
        
        Returns:
        - transaction_id: Unique identifier for the processed transaction
        """
        if self.verbose_logging:
            print(f"{self.env_color}[Transaction] Processing inbound transaction in {self.env_name} environment{Style.RESET_ALL}")
        
        # Validate transaction amount based on environment limits
        amount = float(transaction_data.get("amount", 0))
        if amount > self.max_transaction_amount:
            error_msg = f"Transaction amount (₹{amount:,.2f}) exceeds limit for {self.env_name} environment (₹{self.max_transaction_amount:,.2f})"
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            raise ValueError(error_msg)
        
        # Add environment-specific metadata
        transaction_data["environment"] = self.env_name.lower()
        transaction_data["is_test_transaction"] = not is_production()
        transaction_data["processed_timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Generate transaction ID with environment prefix in non-production
        if not is_production():
            prefix = self.env_name[:3].upper()
            transaction_id = transaction_data.get("transaction_id", f"{prefix}_TX_{int(datetime.utcnow().timestamp())}")
        else:
            transaction_id = transaction_data.get("transaction_id", f"TX_{int(datetime.utcnow().timestamp())}")
            
        transaction_data["transaction_id"] = transaction_id
        
        # Add approval requirement for non-production environments
        if self.requires_approval:
            transaction_data["requires_approval"] = True
            transaction_data["approval_status"] = "pending"
        
        # Use thread-safe locks when storing the transaction
        with self.inbound_lock:
            # Store the transaction
            filename = f"{self.inbound_dir}/inbound_tx_{transaction_id}.json"
            with open(filename, "w") as f:
                json.dump(transaction_data, f, indent=2)
            
            # Log summary to batch CSV with proper locking
            batch_file = f"{self.inbound_dir}/inbound_batch_{datetime.utcnow().strftime('%Y%m%d')}.csv"
            file_exists = os.path.exists(batch_file)
            
            with self.batch_lock:
                with open(batch_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    
                    # Write header if new file
                    if not file_exists:
                        writer.writerow(["transaction_id", "amount", "type", "timestamp", "source", "status"])
                    
                    # Write transaction summary
                    writer.writerow([
                        transaction_id,
                        transaction_data.get("amount", 0),
                        transaction_data.get("type", "unknown"),
                        transaction_data.get("processed_timestamp"),
                        transaction_data.get("source", "system"),
                        "received"
                    ])
            
        return transaction_id
        
    def create_outbound_transaction(self, 
                                   transaction_type: str,
                                   amount: float,
                                   source_account: str,
                                   destination_account: str,
                                   details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create an outbound transaction
        
        Returns:
        - Transaction data dictionary
        """
        if self.verbose_logging:
            print(f"{self.env_color}[Transaction] Creating outbound transaction in {self.env_name} environment{Style.RESET_ALL}")
            
        # Environment-specific validation
        if amount > self.max_transaction_amount:
            error_msg = f"Transaction amount (₹{amount:,.2f}) exceeds limit for {self.env_name} environment (₹{self.max_transaction_amount:,.2f})"
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            raise ValueError(error_msg)
            
        # Special protections for certain account patterns in non-production
        if not is_production():
            # Prevent accidental transactions to production accounts
            if destination_account.startswith("PROD_") and not source_account.startswith("PROD_"):
                error_msg = f"Cannot send from non-production account to production account in {self.env_name} environment"
                print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
                raise ValueError(error_msg)
                
        # Generate transaction ID with environment prefix
        if not is_production():
            prefix = self.env_name[:3].upper()
            transaction_id = f"{prefix}_OUT_{int(datetime.utcnow().timestamp())}"
        else:
            transaction_id = f"OUT_{int(datetime.utcnow().timestamp())}"
            
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        transaction = {
            "transaction_id": transaction_id,
            "type": transaction_type,
            "amount": amount,
            "source_account": source_account,
            "destination_account": destination_account,
            "timestamp": timestamp,
            "status": "pending",
            "environment": self.env_name.lower(),
            "is_test_transaction": not is_production()
        }
        
        if details:
            transaction["details"] = details
        
        # Use thread-safe locks when storing the transaction    
        with self.outbound_lock:
            # Save the transaction
            filename = f"{self.outbound_dir}/outbound_tx_{transaction_id}.json"
            with open(filename, "w") as f:
                json.dump(transaction, f, indent=2)
            
            # Log to outbound batch with proper locking
            batch_file = f"{self.outbound_dir}/outbound_batch_{datetime.utcnow().strftime('%Y%m%d')}.csv"
            file_exists = os.path.exists(batch_file)
            
            with self.batch_lock:
                with open(batch_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    
                    # Write header if new file
                    if not file_exists:
                        writer.writerow(["transaction_id", "type", "amount", "source", "destination", "timestamp", "status"])
                    
                    # Write transaction summary
                    writer.writerow([
                        transaction_id,
                        transaction_type,
                        amount,
                        source_account,
                        destination_account,
                        timestamp,
                        "pending"
                    ])
            
        return transaction
        
    def update_transaction_status(self, transaction_id: str, status: str, 
                                 is_outbound: bool = True,
                                 additional_details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update the status of a transaction
        
        Parameters:
        - transaction_id: ID of the transaction to update
        - status: New status value
        - is_outbound: Whether this is an outbound transaction
        - additional_details: Any additional information to add to the transaction
        
        Returns:
        - Success status
        """
        if self.verbose_logging:
            print(f"{self.env_color}[Transaction] Updating transaction status in {self.env_name} environment{Style.RESET_ALL}")
        
        # Environment-specific validation for finalized statuses
        if status.lower() in ["completed", "approved", "finalized"] and not is_production():
            if self.requires_approval:
                approver = additional_details.get("approver", "") if additional_details else ""
                if not approver:
                    print(f"{Fore.YELLOW}⚠️ Warning: Transactions in {self.env_name} environment require an approver{Style.RESET_ALL}")
        
        # Determine the directory and filename
        tx_dir = self.outbound_dir if is_outbound else self.inbound_dir
        prefix = "outbound" if is_outbound else "inbound"
        
        # Acquire the appropriate lock based on transaction type
        lock_to_use = self.outbound_lock if is_outbound else self.inbound_lock
        
        with lock_to_use:
            # Handle environment-specific transaction IDs
            if not is_production() and not transaction_id.startswith((self.env_name[:3].upper() + "_")):
                # Try both with and without environment prefix
                possible_filenames = [
                    f"{tx_dir}/{prefix}_tx_{transaction_id}.json",
                    f"{tx_dir}/{prefix}_tx_{self.env_name[:3].upper()}_{transaction_id}.json"
                ]
                filename = next((f for f in possible_filenames if os.path.exists(f)), None)
                if not filename:
                    if self.verbose_logging:
                        print(f"{Fore.RED}Transaction not found: {transaction_id}{Style.RESET_ALL}")
                    return False
            else:
                filename = f"{tx_dir}/{prefix}_tx_{transaction_id}.json"
                if not os.path.exists(filename):
                    if self.verbose_logging:
                        print(f"{Fore.RED}Transaction not found: {filename}{Style.RESET_ALL}")
                    return False
                
            # Update the transaction
            with open(filename, "r") as f:
                transaction = json.load(f)
            
            # Environment validation - prevent mixing transactions between environments
            if "environment" in transaction and transaction["environment"] != self.env_name.lower():
                error_msg = f"Cannot update transaction from '{transaction['environment']}' environment in '{self.env_name}' environment"
                print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
                return False
                
            # Update status and details
            transaction["status"] = status
            transaction["updated_timestamp"] = datetime.utcnow().isoformat() + "Z"
            transaction["updated_environment"] = self.env_name.lower()  # Track which environment made the update
            
            if additional_details:
                transaction.update(additional_details)
                
            # Save updated transaction
            with open(filename, "w") as f:
                json.dump(transaction, f, indent=2)
                
        return True

if __name__ == "__main__":
    # Example usage
    processor = TransactionProcessor()
    
    # Process an inbound transaction
    inbound_tx = {
        "amount": 1000.00,
        "type": "deposit",
        "source": "ATM",
        "account": "12345678",
        "notes": "Cash deposit"
    }
    
    tx_id = processor.process_inbound_transaction(inbound_tx)
    print(f"Processed inbound transaction with ID: {tx_id}")
    
    # Create an outbound transaction
    outbound_tx = processor.create_outbound_transaction(
        transaction_type="transfer",
        amount=500.00,
        source_account="12345678",
        destination_account="87654321",
        details={
            "description": "Monthly rent payment",
            "reference": "RENT-MAY-2025"
        }
    )
    print(f"Created outbound transaction with ID: {outbound_tx['transaction_id']}")
    
    # Update the transaction status
    updated = processor.update_transaction_status(
        outbound_tx['transaction_id'],
        "completed",
        is_outbound=True,
        additional_details={
            "confirmation_code": "TRF12345",
            "processed_by": "batch_processor"
        }
    )
    print(f"Transaction status update: {'Success' if updated else 'Failed'}")
