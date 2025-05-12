"""
Transaction processing utility for handling inbound and outbound transactions
"""
import csv
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

class TransactionProcessor:
    def __init__(self, inbound_dir="transactions/inbound", outbound_dir="transactions/outbound"):
        self.inbound_dir = inbound_dir
        self.outbound_dir = outbound_dir
        os.makedirs(inbound_dir, exist_ok=True)
        os.makedirs(outbound_dir, exist_ok=True)
    
    def process_inbound_transaction(self, transaction_data: Dict[str, Any]) -> str:
        """
        Process an inbound transaction and store it
        
        Parameters:
        - transaction_data: Dictionary with transaction details
        
        Returns:
        - transaction_id: Unique identifier for the processed transaction
        """
        # Add processing metadata
        transaction_data["processed_timestamp"] = datetime.utcnow().isoformat() + "Z"
        transaction_id = transaction_data.get("transaction_id", f"tx_{int(datetime.utcnow().timestamp())}")
        transaction_data["transaction_id"] = transaction_id
        
        # Store the transaction
        filename = f"{self.inbound_dir}/inbound_tx_{transaction_id}.json"
        with open(filename, "w") as f:
            json.dump(transaction_data, f, indent=2)
            
        # Log summary to batch CSV
        batch_file = f"{self.inbound_dir}/inbound_batch_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        file_exists = os.path.exists(batch_file)
        
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
        transaction_id = f"tx_{int(datetime.utcnow().timestamp())}"
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        transaction = {
            "transaction_id": transaction_id,
            "type": transaction_type,
            "amount": amount,
            "source_account": source_account,
            "destination_account": destination_account,
            "timestamp": timestamp,
            "status": "pending"
        }
        
        if details:
            transaction["details"] = details
            
        # Save the transaction
        filename = f"{self.outbound_dir}/outbound_tx_{transaction_id}.json"
        with open(filename, "w") as f:
            json.dump(transaction, f, indent=2)
            
        # Log to outbound batch
        batch_file = f"{self.outbound_dir}/outbound_batch_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        file_exists = os.path.exists(batch_file)
        
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
        # Determine the directory and filename
        tx_dir = self.outbound_dir if is_outbound else self.inbound_dir
        prefix = "outbound" if is_outbound else "inbound"
        filename = f"{tx_dir}/{prefix}_tx_{transaction_id}.json"
        
        if not os.path.exists(filename):
            return False
            
        # Update the transaction
        with open(filename, "r") as f:
            transaction = json.load(f)
            
        # Update status and details
        transaction["status"] = status
        transaction["updated_timestamp"] = datetime.utcnow().isoformat() + "Z"
        
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
