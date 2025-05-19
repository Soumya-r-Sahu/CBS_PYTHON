"""
UPI Payment Service Module for Core Banking System

This module provides comprehensive UPI (Unified Payments Interface) payment processing
functionality with thread-safety and cross-process synchronization. It implements the
core services required for UPI transactions including registration, verification, 
processing, and transaction history.

Key Features:
-------------
1. Thread-safe singleton implementation for consistent access
2. File-based locking for cross-process synchronization
3. Environment-specific behavior (production, development, test)
4. Comprehensive transaction lifecycle management
5. Race condition prevention through multiple locking mechanisms
6. Daily transaction aggregation for reporting
7. Fault-tolerant file operations with retry logic

Transaction Flow:
----------------
1. User Registration: Register a user with UPI service
2. Transaction Initiation: Begin a new payment
3. Verification: Confirm PIN and authenticate
4. Processing: Process the payment through backend systems
5. Completion: Finalize the transaction with success/failure status
6. Reporting: Record transaction in daily ledger

Environment Handling:
--------------------
- Production: Strict validation, higher limits, minimal logging
- Development: Mock mode enabled, medium limits, detailed logging
- Test: Mock mode enabled, lower limits, detailed logging

Thread Safety:
-------------
This implementation uses a combination of Python threading locks and
file-based locks to ensure thread safety both within a single process
and across multiple processes.

Usage Examples:
--------------
>>> service = UpiPaymentService()
>>> user = service.register_user("123456789", "9876543210", "user@upi", "Test User")
>>> tx = service.initiate_transaction("user@upi", "merchant@upi", 500.00, "Payment")
>>> verified_tx = service.verify_transaction(tx['transaction_id'], True)
>>> result = service.complete_transaction(tx['transaction_id'], "success")
"""
import json
import os
import sys
import uuid
import threading
import fcntl
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Union, Tuple
from colorama import init, Fore, Style
from pathlib import Path

# Initialize colorama
init(autoreset=True)

# Try to import environment module
try:
    from app.config.environment import (
        get_environment_name, is_production, is_development, is_test,
        is_debug_enabled, get_debug_level
    )
except ImportError:
    # Fallback environment detection
    env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    def is_production(): return env_str == "production"
    def is_development(): return env_str == "development"
    def is_test(): return env_str == "test"
    def get_environment_name(): return env_str.capitalize()
    def is_debug_enabled(): return os.environ.get("CBS_DEBUG", "false").lower() == "true"
    def get_debug_level(): return int(os.environ.get("CBS_DEBUG_LEVEL", "0"))


class FileLock:
    """
    A file-based lock implementation for cross-process synchronization
    """
    def __init__(self, lock_file):
        self.lock_file = lock_file
        self.fd = None
        
    def __enter__(self):
        """Acquire the lock"""
        self.fd = open(self.lock_file, 'w')
        fcntl.flock(self.fd, fcntl.LOCK_EX)
        return self
        
    def __exit__(self, *args):
        """Release the lock"""
        if self.fd:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
            self.fd.close()
            self.fd = None


class UpiPaymentService:
    _instance = None
    _lock = threading.RLock()
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        """
        Thread-safe singleton implementation to prevent race conditions during initialization
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(UpiPaymentService, cls).__new__(cls)
            return cls._instance
    
    def __init__(self, data_dir="upi/transactions"):
        # Ensure initialization happens only once, even with multiple threads
        with self._lock:
            if self._initialized:
                return
                
            # Set environment-specific data directory
            env_name = get_environment_name().lower()
            if not is_production():
                # Use environment-specific directories in non-production
                data_dir = f"upi/transactions/{env_name}"
            
            self.data_dir = data_dir
            self.env_name = get_environment_name()
            os.makedirs(data_dir, exist_ok=True)
            
            # Create locks directory
            self.locks_dir = os.path.join(data_dir, "locks")
            os.makedirs(self.locks_dir, exist_ok=True)
            
            # Initialize the internal locks
            self.registration_lock = threading.RLock()
            self.transaction_lock = threading.RLock()
            self.daily_lock = threading.RLock()
            
            # Set environment-specific colors and settings
            if is_production():
                self.env_color = Fore.GREEN
                self.is_mock_mode = False
                self.validation_strict = True
                self.max_transaction_limit = 100000  # Higher limit in production
            elif is_test():
                self.env_color = Fore.YELLOW
                self.is_mock_mode = True  # Use mock UPI server in test
                self.validation_strict = False
                self.max_transaction_limit = 10000  # Lower limit in test
            else:  # development
                self.env_color = Fore.BLUE
                self.is_mock_mode = True  # Use mock UPI server in development
                self.validation_strict = False
                self.max_transaction_limit = 50000  # Medium limit in development
                
            # Enable detailed logs in non-production
            self.enable_detailed_logs = not is_production() or is_debug_enabled()
            
            if self.enable_detailed_logs:
                print(f"{self.env_color}[UPI Service] {self.env_name} Environment | " 
                      f"Mock Mode: {self.is_mock_mode} | "
                      f"Debug: {is_debug_enabled()}{Style.RESET_ALL}")
                      
            # Mark as initialized
            self._initialized = True
    
    def get_file_lock(self, name):
        """Get a file lock for cross-process synchronization"""
        lock_file = os.path.join(self.locks_dir, f"{name}.lock")
        return FileLock(lock_file)
    
    def register_user(self, account_number: str, mobile_number: str, 
                     upi_id: str, name: str) -> Dict[str, Any]:
        """
        Register a new user for UPI services
        
        Parameters:
        - account_number: Bank account number
        - mobile_number: User's mobile number
        - upi_id: UPI ID chosen by the user
        - name: User's name
        
        Returns:
        - User registration data
        """
        with self.registration_lock:  # Thread-safety for in-process concurrency
            registration = {
                "upi_id": upi_id,
                "account_number": account_number,
                "mobile_number": mobile_number,
                "name": name,
                "registration_date": datetime.utcnow().isoformat() + "Z",
                "status": "active",
                "registration_id": str(uuid.uuid4())
            }
            
            # Save registration with file locking for cross-process concurrency
            reg_file = f"{self.data_dir}/registration_{upi_id}.json"
            
            # Use file lock to prevent race conditions across processes
            with self.get_file_lock(f"reg_{upi_id}"):
                with open(reg_file, "w") as f:
                    json.dump(registration, f, indent=2)
            
            return registration
        
    def initiate_transaction(self, payer_upi_id: str, payee_upi_id: str, 
                           amount: float, note: Optional[str] = None,
                           reference: Optional[str] = None) -> Dict[str, Any]:
        """
        Initiate a new UPI transaction
        
        Parameters:
        - payer_upi_id: UPI ID of the payer
        - payee_upi_id: UPI ID of the payee
        - amount: Transaction amount
        - note: Optional transaction note
        - reference: Optional reference ID
        
        Returns:
        - Transaction details
        """
        # Environment-specific behavior
        if self.enable_detailed_logs:
            print(f"{self.env_color}[UPI] Initiating transaction in {self.env_name} environment{Style.RESET_ALL}")
        
        # Validate transaction amount based on environment
        if amount > self.max_transaction_limit:
            error_msg = f"Transaction amount exceeds limit for {self.env_name} environment (₹{self.max_transaction_limit})"
            print(f"{Fore.RED}❌ {error_msg}{Style.RESET_ALL}")
            raise ValueError(error_msg)
            
        with self.transaction_lock:  # Thread-safety for in-process concurrency
            # Generate transaction ID with environment prefix for non-production
            if not is_production():
                prefix = self.env_name[:3].upper()
                transaction_id = f"{prefix}_UPITX{uuid.uuid4().hex[:16].upper()}"
            else:
                transaction_id = f"UPITX{uuid.uuid4().hex[:16].upper()}"
                
            timestamp = datetime.utcnow().isoformat() + "Z"
            
            transaction = {
                "transaction_id": transaction_id,
                "payer_upi_id": payer_upi_id,
                "payee_upi_id": payee_upi_id,
                "amount": amount,
                "currency": "INR",  # Default to INR for UPI
                "timestamp": timestamp,
                "status": "initiated",
                "note": note,
                "reference": reference,
                "environment": self.env_name,  # Store environment with the transaction
                "is_test": not is_production()  # Flag for test transactions
            }
            
            # Save transaction with file locking
            tx_file = f"{self.data_dir}/transaction_{transaction_id}.json"
            
            with self.get_file_lock(f"tx_{transaction_id}"):
                with open(tx_file, "w") as f:
                    json.dump(transaction, f, indent=2)
                
            return transaction
    
    def verify_transaction(self, transaction_id: str, pin_verified: bool) -> Dict[str, Any]:
        """
        Verify UPI transaction after PIN verification
        
        Parameters:
        - transaction_id: Transaction ID to verify
        - pin_verified: Whether PIN verification was successful
        
        Returns:
        - Updated transaction details
        """
        tx_file = f"{self.data_dir}/transaction_{transaction_id}.json"
        
        with self.get_file_lock(f"tx_{transaction_id}"):
            # Check if transaction exists
            if not os.path.exists(tx_file):
                return {"error": "Transaction not found", "status": "failed"}
                
            # Load transaction
            with open(tx_file, "r") as f:
                transaction = json.load(f)
                
            # Update status based on verification
            if pin_verified:
                transaction["status"] = "processing"
                transaction["verification_timestamp"] = datetime.utcnow().isoformat() + "Z"
            else:
                transaction["status"] = "failed"
                transaction["failure_reason"] = "PIN verification failed"
                transaction["failure_timestamp"] = datetime.utcnow().isoformat() + "Z"
                
            # Save updated transaction
            with open(tx_file, "w") as f:
                json.dump(transaction, f, indent=2)
                
            return transaction
    
    def complete_transaction(self, transaction_id: str, status: str, 
                           response_code: Optional[str] = None,
                           response_message: Optional[str] = None) -> Dict[str, Any]:
        """
        Complete a UPI transaction with final status
        
        Parameters:
        - transaction_id: Transaction ID to complete
        - status: Final status ('success' or 'failed')
        - response_code: Optional bank response code
        - response_message: Optional response message
        
        Returns:
        - Updated transaction details
        """
        tx_file = f"{self.data_dir}/transaction_{transaction_id}.json"
        
        with self.get_file_lock(f"tx_{transaction_id}"):
            # Check if transaction exists
            if not os.path.exists(tx_file):
                return {"error": "Transaction not found", "status": "failed"}
                
            # Load transaction
            with open(tx_file, "r") as f:
                transaction = json.load(f)
                
            # Update status
            transaction["status"] = status
            transaction["completion_timestamp"] = datetime.utcnow().isoformat() + "Z"
            
            if response_code:
                transaction["response_code"] = response_code
                
            if response_message:
                transaction["response_message"] = response_message
                
            # Save updated transaction
            with open(tx_file, "w") as f:
                json.dump(transaction, f, indent=2)
            
        # If successful, append to daily transaction record
        if status == "success":
            self._append_to_daily_transactions(transaction)
                
        return transaction
    
    def _append_to_daily_transactions(self, transaction):
        """
        Thread-safe and race-condition-safe method to append to daily transactions
        """
        daily_file = f"{self.data_dir}/daily_transactions_{datetime.utcnow().strftime('%Y%m%d')}.json"
        
        # First acquire the thread lock
        with self.daily_lock:
            # Then acquire the file lock for cross-process safety
            with self.get_file_lock(f"daily_{datetime.utcnow().strftime('%Y%m%d')}"):
                # Read current daily transactions
                daily_transactions = []
                if os.path.exists(daily_file):
                    retry_count = 0
                    while retry_count < 3:  # Retry up to 3 times
                        try:
                            with open(daily_file, "r") as f:
                                daily_transactions = json.load(f)
                            break  # Success - exit retry loop
                        except json.JSONDecodeError:
                            # Handle corrupted file
                            retry_count += 1
                            if retry_count == 3:
                                # On final retry, just start with an empty list
                                daily_transactions = []
                            else:
                                # Wait briefly before retrying
                                time.sleep(0.1)
                
                # Add the new transaction
                daily_transactions.append(transaction)
                
                # Write back the updated transactions
                with open(daily_file, "w") as f:
                    json.dump(daily_transactions, f, indent=2)
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific transaction"""
        tx_file = f"{self.data_dir}/transaction_{transaction_id}.json"
        
        if not os.path.exists(tx_file):
            return None
            
        with self.get_file_lock(f"tx_{transaction_id}"):
            with open(tx_file, "r") as f:
                return json.load(f)
            
    def get_user_transactions(self, upi_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent transactions for a UPI ID"""
        transactions = []
        
        # List all transaction files
        if os.path.exists(self.data_dir):
            for filename in os.listdir(self.data_dir):
                if filename.startswith("transaction_") and filename.endswith(".json"):
                    filepath = os.path.join(self.data_dir, filename)
                    
                    # Use short-lived file lock just for reading
                    transaction_id = filename.replace("transaction_", "").replace(".json", "")
                    with self.get_file_lock(f"tx_{transaction_id}"):
                        try:
                            with open(filepath, "r") as f:
                                transaction = json.load(f)
                                
                                # Check if this transaction involves the specified UPI ID
                                if (transaction.get("payer_upi_id") == upi_id or 
                                    transaction.get("payee_upi_id") == upi_id):
                                    transactions.append(transaction)
                        except (json.JSONDecodeError, IOError):
                            # Skip corrupted or inaccessible files
                            continue
                        
        # Sort by timestamp (latest first) and limit
        transactions.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return transactions[:limit]


if __name__ == "__main__":
    # Example usage
    upi_service = UpiPaymentService()
    
    # Register a sample user
    user = upi_service.register_user(
        account_number="123456789",
        mobile_number="9876543210",
        upi_id="user@upi",
        name="Test User"
    )
    print(f"{Fore.GREEN}✅ Registered user with UPI ID: {user['upi_id']}{Style.RESET_ALL}")
    
    # Create a transaction
    transaction = upi_service.initiate_transaction(
        payer_upi_id="user@upi",
        payee_upi_id="merchant@upi",
        amount=500.00,
        note="Payment for services"
    )
    print(f"{Fore.CYAN}🔄 Initiated transaction with ID: {transaction['transaction_id']}{Style.RESET_ALL}")
    
    # Verify transaction (simulating PIN verification)
    verified_tx = upi_service.verify_transaction(transaction['transaction_id'], True)
    print(f"{Fore.YELLOW}🔍 Transaction verified, status: {verified_tx['status']}{Style.RESET_ALL}")
    
    # Complete transaction
    completed_tx = upi_service.complete_transaction(
        transaction['transaction_id'], 
        "success",
        response_code="00",
        response_message="Transaction successful"
    )
    print(f"{Fore.GREEN}✅ Transaction completed with status: {completed_tx['status']}{Style.RESET_ALL}")
    
    # Demonstrate thread-safety by creating multiple instances - they should be the same object
    service1 = UpiPaymentService()
    service2 = UpiPaymentService()
    print(f"Singleton works: {service1 is service2}")  # Should print True
