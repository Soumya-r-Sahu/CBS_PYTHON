"""
UPI Payment Service - Core functionality for UPI transactions
"""
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

class UpiPaymentService:
    def __init__(self, data_dir="upi/transactions"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
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
        registration = {
            "upi_id": upi_id,
            "account_number": account_number,
            "mobile_number": mobile_number,
            "name": name,
            "registration_date": datetime.utcnow().isoformat() + "Z",
            "status": "active",
            "registration_id": str(uuid.uuid4())
        }
        
        # Save registration
        reg_file = f"{self.data_dir}/registration_{upi_id}.json"
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
            "reference": reference
        }
        
        # Save transaction
        tx_file = f"{self.data_dir}/transaction_{transaction_id}.json"
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
            daily_file = f"{self.data_dir}/daily_transactions_{datetime.utcnow().strftime('%Y%m%d')}.json"
            
            daily_transactions = []
            if os.path.exists(daily_file):
                with open(daily_file, "r") as f:
                    try:
                        daily_transactions = json.load(f)
                    except json.JSONDecodeError:
                        daily_transactions = []
            
            daily_transactions.append(transaction)
            
            with open(daily_file, "w") as f:
                json.dump(daily_transactions, f, indent=2)
                
        return transaction
    
    def get_transaction(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific transaction"""
        tx_file = f"{self.data_dir}/transaction_{transaction_id}.json"
        
        if not os.path.exists(tx_file):
            return None
            
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
                    with open(filepath, "r") as f:
                        transaction = json.load(f)
                        
                    # Check if this transaction involves the specified UPI ID
                    if (transaction.get("payer_upi_id") == upi_id or 
                        transaction.get("payee_upi_id") == upi_id):
                        transactions.append(transaction)
                        
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
    print(f"Registered user with UPI ID: {user['upi_id']}")
    
    # Create a transaction
    transaction = upi_service.initiate_transaction(
        payer_upi_id="user@upi",
        payee_upi_id="merchant@upi",
        amount=500.00,
        note="Payment for services"
    )
    print(f"Initiated transaction with ID: {transaction['transaction_id']}")
    
    # Verify transaction (simulating PIN verification)
    verified_tx = upi_service.verify_transaction(transaction['transaction_id'], True)
    print(f"Transaction verified, status: {verified_tx['status']}")
    
    # Complete transaction
    completed_tx = upi_service.complete_transaction(
        transaction['transaction_id'], 
        "success",
        response_code="00",
        response_message="Transaction successful"
    )
    print(f"Transaction completed with status: {completed_tx['status']}")
