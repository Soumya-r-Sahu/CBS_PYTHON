"""
Transaction Validation Service

Domain service for validating transaction data.
"""
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List, Optional
from uuid import UUID

class ValidationService:
    """Validates transaction data against domain rules"""
    
    @staticmethod
    def validate_transaction_data(data: Dict[str, Any]) -> List[str]:
        """
        Validate transaction data from external sources
        
        Args:
            data: Transaction data dictionary
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Required fields
        required_fields = ["account_id", "amount", "transaction_type"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # If missing required fields, no need to validate further
        if errors:
            return errors
        
        # Validate account_id
        try:
            if not isinstance(data["account_id"], UUID):
                UUID(data["account_id"])
        except (ValueError, TypeError):
            errors.append("Invalid account_id format")
        
        # Validate amount
        try:
            amount = Decimal(str(data["amount"]))
            if amount <= Decimal("0"):
                errors.append("Amount must be positive")
        except (InvalidOperation, ValueError):
            errors.append("Invalid amount format")
        
        # Validate transaction type
        valid_types = ["deposit", "withdrawal", "transfer", "reversal", "payment", "refund", "charge", "interest"]
        if data["transaction_type"].lower() not in valid_types:
            errors.append(f"Invalid transaction type: {data['transaction_type']}")
        
        # Validate to_account_id for transfers
        if data["transaction_type"].lower() == "transfer":
            if "to_account_id" not in data:
                errors.append("Missing to_account_id for transfer transaction")
            else:
                try:
                    if not isinstance(data["to_account_id"], UUID):
                        UUID(data["to_account_id"])
                except (ValueError, TypeError):
                    errors.append("Invalid to_account_id format")
        
        return errors
