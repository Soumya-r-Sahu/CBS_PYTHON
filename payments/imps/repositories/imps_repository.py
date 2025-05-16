"""
IMPS Payment Repository - Core Banking System

This module provides data access for IMPS payments.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from ..models.imps_model import IMPSTransaction, IMPSStatus
from ..exceptions.imps_exceptions import IMPSTransactionNotFound
from ..config.imps_config import imps_config

# Configure logger
logger = logging.getLogger(__name__)


class IMPSRepository:
    """Repository for IMPS transactions."""
    _instance = None
    
    def __new__(cls):
        """Ensure only one instance of IMPSRepository exists."""
        if cls._instance is None:
            cls._instance = super(IMPSRepository, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the repository."""
        # In-memory storage for development/testing
        self.transactions = {}
        
        # Get configuration
        self.db_collection = imps_config.get("db_collection", "imps_transactions")
        self.history_collection = imps_config.get("history_collection", "imps_history")
        
        # Initialize database connection (mock for now)
        self._init_db_connection()
        
        logger.info("IMPS repository initialized")
    
    def _init_db_connection(self):
        """Initialize database connection."""
        # TODO: Implement actual database connection
        self.db_connected = True
        logger.debug("Mock database connection established")
    
    def create_transaction_id(self) -> str:
        """
        Generate a unique transaction ID.
        
        Returns:
            str: Unique transaction ID
        """
        # Format: IMPS-YYYYMMDD-XXXXXXXX
        date_part = datetime.utcnow().strftime("%Y%m%d")
        unique_part = uuid.uuid4().hex[:8].upper()
        transaction_id = f"IMPS-{date_part}-{unique_part}"
        
        return transaction_id
    
    def save_transaction(self, transaction: IMPSTransaction) -> IMPSTransaction:
        """
        Save a transaction to the database.
        
        Args:
            transaction: Transaction to save
            
        Returns:
            IMPSTransaction: Saved transaction
        """
        # Update timestamp
        transaction.updated_at = datetime.utcnow()
        
        # For development/testing, save in memory
        self.transactions[transaction.transaction_id] = transaction
        
        # TODO: Implement actual database save
        logger.debug(f"Saved IMPS transaction: {transaction.transaction_id}")
        
        return transaction
    
    def get_transaction(self, transaction_id: str) -> Optional[IMPSTransaction]:
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: Transaction ID to retrieve
            
        Returns:
            Optional[IMPSTransaction]: Transaction if found
            
        Raises:
            IMPSTransactionNotFound: If transaction not found
        """
        # For development/testing, retrieve from memory
        transaction = self.transactions.get(transaction_id)
        
        if not transaction:
            # TODO: Try to get from actual database
            logger.debug(f"IMPS transaction not found: {transaction_id}")
            raise IMPSTransactionNotFound(transaction_id)
        
        logger.debug(f"Retrieved IMPS transaction: {transaction_id}")
        return transaction
    
    def get_transaction_by_rrn(self, rrn: str) -> Optional[IMPSTransaction]:
        """
        Get a transaction by RRN.
        
        Args:
            rrn: Reference Retrieval Number assigned by NPCI
            
        Returns:
            Optional[IMPSTransaction]: Transaction if found
        """
        # For development/testing, search in memory
        for transaction in self.transactions.values():
            if transaction.rrn == rrn:
                return transaction
        
        # TODO: Implement actual database search
        return None
    
    def update_transaction_status(self, transaction_id: str, status: IMPSStatus, 
                               error_message: str = None) -> IMPSTransaction:
        """
        Update transaction status.
        
        Args:
            transaction_id: Transaction ID
            status: New status
            error_message: Error message (if applicable)
            
        Returns:
            IMPSTransaction: Updated transaction
            
        Raises:
            IMPSTransactionNotFound: If transaction not found
        """
        transaction = self.get_transaction(transaction_id)
        transaction.update_status(status)
        
        if error_message:
            transaction.error_message = error_message
        
        return self.save_transaction(transaction)
    
    def get_transaction_history(self, transaction_id: str) -> List[Dict[str, Any]]:
        """
        Get transaction history for auditing.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            List[Dict[str, Any]]: List of history records
        """
        # TODO: Implement actual history retrieval
        return []
    
    def get_transactions_by_status(self, status: IMPSStatus) -> List[IMPSTransaction]:
        """
        Get transactions by status.
        
        Args:
            status: Status to filter by
            
        Returns:
            List[IMPSTransaction]: List of transactions with the given status
        """
        # For development/testing, filter in memory
        filtered_transactions = [
            t for t in self.transactions.values() if t.status == status
        ]
        
        # TODO: Implement actual database query
        
        return filtered_transactions
    
    def get_transactions_by_mobile(self, mobile_number: str) -> List[IMPSTransaction]:
        """
        Get transactions by mobile number.
        
        Args:
            mobile_number: Mobile number to search for (sender or beneficiary)
            
        Returns:
            List[IMPSTransaction]: List of transactions with the given mobile number
        """
        # For development/testing, filter in memory
        filtered_transactions = [
            t for t in self.transactions.values() 
            if (t.payment_details.sender_mobile_number == mobile_number or 
                t.payment_details.beneficiary_mobile_number == mobile_number)
        ]
        
        # TODO: Implement actual database query
        
        return filtered_transactions
    
    def get_transactions_by_account(self, account_number: str) -> List[IMPSTransaction]:
        """
        Get transactions by account number.
        
        Args:
            account_number: Account number to search for
            
        Returns:
            List[IMPSTransaction]: List of transactions with the given account number
        """
        # For development/testing, filter in memory
        filtered_transactions = [
            t for t in self.transactions.values() 
            if (t.payment_details.sender_account_number == account_number or 
                t.payment_details.beneficiary_account_number == account_number)
        ]
        
        # TODO: Implement actual database query
        
        return filtered_transactions
    
    def is_duplicate_transaction(self, reference_number: str, 
                              sender_account: str, 
                              beneficiary_account: str,
                              amount: float,
                              time_window_minutes: int = 15) -> bool:
        """
        Check if a transaction is a duplicate.
        
        Args:
            reference_number: Transaction reference number
            sender_account: Sender account number
            beneficiary_account: Beneficiary account number
            amount: Transaction amount
            time_window_minutes: Time window to check for duplicates (in minutes)
            
        Returns:
            bool: True if duplicate found, False otherwise
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)
        
        # For development/testing, check in memory
        for transaction in self.transactions.values():
            if (transaction.payment_details.reference_number == reference_number or
                (transaction.payment_details.sender_account_number == sender_account and
                 transaction.payment_details.beneficiary_account_number == beneficiary_account and
                 transaction.payment_details.amount == amount and
                 transaction.created_at >= cutoff_time)):
                return True
        
        # TODO: Implement actual database check
        
        return False


# Create singleton instance
imps_repository = IMPSRepository()
