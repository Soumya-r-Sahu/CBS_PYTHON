"""
UPI Payment Repository Module.

Data access layer for UPI payment operations.
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import uuid

from ..models.upi_model import UpiRegistration, UpiTransaction, TransactionStatus
from ..exceptions.upi_exceptions import UpiNotFoundError, UpiBaseException
from ..config.upi_config import upi_config

# Set up logging
logger = logging.getLogger(__name__)


class UpiRepository:
    """Repository for UPI data operations"""
    
    def __init__(self):
        """Initialize the UPI repository"""
        self.data_dir = upi_config.get('DATA_DIR', 'upi/transactions')
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        logger.info(f"UPI Repository initialized with data directory: {self.data_dir}")
    
    def _get_registration_file_path(self, upi_id: str) -> str:
        """Get file path for registration data"""
        return os.path.join(self.data_dir, f"registration_{upi_id}.json")
    
    def _get_transaction_file_path(self, transaction_id: str) -> str:
        """Get file path for transaction data"""
        return os.path.join(self.data_dir, f"transaction_{transaction_id}.json")
    
    def save_registration(self, registration: Union[UpiRegistration, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Save UPI registration data.
        
        Args:
            registration: Registration data object or dictionary
            
        Returns:
            Dict: Saved registration data
        """
        # Convert to dictionary if object
        if isinstance(registration, UpiRegistration):
            reg_data = registration.to_dict()
        else:
            reg_data = dict(registration)
        
        # Ensure registration has an ID
        if 'registration_id' not in reg_data:
            reg_data['registration_id'] = str(uuid.uuid4())
        
        # Ensure registration has a timestamp
        if 'registration_date' not in reg_data:
            reg_data['registration_date'] = datetime.utcnow().isoformat() + "Z"
        
        # Save to file
        file_path = self._get_registration_file_path(reg_data['upi_id'])
        try:
            with open(file_path, 'w') as f:
                json.dump(reg_data, f, indent=2)
            
            logger.info(f"Saved registration for UPI ID: {reg_data['upi_id']}")
            return reg_data
            
        except Exception as e:
            logger.error(f"Error saving registration for UPI ID: {reg_data['upi_id']}, Error: {str(e)}")
            raise UpiBaseException(f"Failed to save UPI registration: {str(e)}")
    
    def get_registration(self, upi_id: str) -> Dict[str, Any]:
        """
        Get UPI registration data by UPI ID.
        
        Args:
            upi_id: UPI ID to retrieve
            
        Returns:
            Dict: Registration data
            
        Raises:
            UpiNotFoundError: If registration not found
        """
        file_path = self._get_registration_file_path(upi_id)
        
        try:
            if not os.path.exists(file_path):
                raise UpiNotFoundError(upi_id, resource_type="registration")
            
            with open(file_path, 'r') as f:
                reg_data = json.load(f)
            
            logger.debug(f"Retrieved registration for UPI ID: {upi_id}")
            return reg_data
            
        except UpiNotFoundError:
            logger.warning(f"Registration not found for UPI ID: {upi_id}")
            raise
            
        except Exception as e:
            logger.error(f"Error retrieving registration for UPI ID: {upi_id}, Error: {str(e)}")
            raise UpiBaseException(f"Failed to retrieve UPI registration: {str(e)}")
    
    def save_transaction(self, transaction: Union[UpiTransaction, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Save UPI transaction data.
        
        Args:
            transaction: Transaction data object or dictionary
            
        Returns:
            Dict: Saved transaction data
        """
        # Convert to dictionary if object
        if isinstance(transaction, UpiTransaction):
            txn_data = transaction.to_dict()
        else:
            txn_data = dict(transaction)
        
        # Ensure transaction has an ID
        if 'transaction_id' not in txn_data:
            txn_data['transaction_id'] = f"UPI{int(datetime.utcnow().timestamp())}{str(uuid.uuid4())[:8]}"
        
        # Ensure transaction has a timestamp
        if 'timestamp' not in txn_data:
            txn_data['timestamp'] = datetime.utcnow().isoformat() + "Z"
        
        # Save to file
        file_path = self._get_transaction_file_path(txn_data['transaction_id'])
        try:
            with open(file_path, 'w') as f:
                json.dump(txn_data, f, indent=2)
            
            logger.info(f"Saved transaction with ID: {txn_data['transaction_id']}")
            return txn_data
            
        except Exception as e:
            logger.error(f"Error saving transaction with ID: {txn_data['transaction_id']}, Error: {str(e)}")
            raise UpiBaseException(f"Failed to save UPI transaction: {str(e)}")
    
    def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get UPI transaction data by transaction ID.
        
        Args:
            transaction_id: Transaction ID to retrieve
            
        Returns:
            Dict: Transaction data
            
        Raises:
            UpiNotFoundError: If transaction not found
        """
        file_path = self._get_transaction_file_path(transaction_id)
        
        try:
            if not os.path.exists(file_path):
                raise UpiNotFoundError(transaction_id)
            
            with open(file_path, 'r') as f:
                txn_data = json.load(f)
            
            logger.debug(f"Retrieved transaction with ID: {transaction_id}")
            return txn_data
            
        except UpiNotFoundError:
            logger.warning(f"Transaction not found with ID: {transaction_id}")
            raise
            
        except Exception as e:
            logger.error(f"Error retrieving transaction with ID: {transaction_id}, Error: {str(e)}")
            raise UpiBaseException(f"Failed to retrieve UPI transaction: {str(e)}")
    
    def update_transaction_status(self, transaction_id: str, status: Union[TransactionStatus, str], 
                               gateway_response: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Update transaction status.
        
        Args:
            transaction_id: Transaction ID to update
            status: New transaction status
            gateway_response: Gateway response data
            
        Returns:
            Dict: Updated transaction data
            
        Raises:
            UpiNotFoundError: If transaction not found
        """
        try:
            # Get existing transaction
            transaction = self.get_transaction(transaction_id)
            
            # Update status
            if isinstance(status, TransactionStatus):
                transaction['status'] = status.value
            else:
                transaction['status'] = status
            
            # Update gateway response if provided
            if gateway_response:
                transaction['gateway_response'] = gateway_response
            
            # Update timestamp
            transaction['updated_at'] = datetime.utcnow().isoformat() + "Z"
            
            # Save updated transaction
            return self.save_transaction(transaction)
            
        except UpiNotFoundError:
            logger.warning(f"Cannot update status: Transaction not found with ID: {transaction_id}")
            raise
            
        except Exception as e:
            logger.error(f"Error updating transaction status for ID: {transaction_id}, Error: {str(e)}")
            raise UpiBaseException(f"Failed to update UPI transaction status: {str(e)}")
    
    def get_transactions_by_upi_id(self, upi_id: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get transactions by UPI ID.
        
        Args:
            upi_id: UPI ID to search for
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List: List of transaction data dictionaries
        """
        transactions = []
        
        try:
            # Get all transaction files
            transaction_files = [f for f in os.listdir(self.data_dir) if f.startswith("transaction_")]
            
            # Process each transaction file
            for file_name in transaction_files:
                try:
                    with open(os.path.join(self.data_dir, file_name), 'r') as f:
                        txn = json.load(f)
                        
                        # Filter by UPI ID
                        if txn.get('payer_upi_id') == upi_id or txn.get('payee_upi_id') == upi_id:
                            transactions.append(txn)
                except Exception as e:
                    logger.warning(f"Error reading transaction file {file_name}: {str(e)}")
            
            # Sort by timestamp (descending)
            transactions.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            # Apply pagination
            paginated = transactions[offset:offset+limit]
            
            logger.info(f"Retrieved {len(paginated)} transactions for UPI ID: {upi_id}")
            return paginated
            
        except Exception as e:
            logger.error(f"Error retrieving transactions for UPI ID: {upi_id}, Error: {str(e)}")
            raise UpiBaseException(f"Failed to retrieve UPI transactions: {str(e)}")


# Create singleton instance
upi_repository = UpiRepository()
