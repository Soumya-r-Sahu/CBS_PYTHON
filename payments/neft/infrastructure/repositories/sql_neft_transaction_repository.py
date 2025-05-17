"""
SQL NEFT Transaction Repository.
Implementation of the NEFTTransactionRepositoryInterface using SQL database.
"""
import logging
from typing import Optional, List
from uuid import UUID
import json
from datetime import datetime

from ...domain.entities.neft_transaction import NEFTTransaction, NEFTPaymentDetails, NEFTStatus, NEFTReturnReason
from ...application.interfaces.neft_transaction_repository_interface import NEFTTransactionRepositoryInterface


class SQLNEFTTransactionRepository(NEFTTransactionRepositoryInterface):
    """SQL implementation of NEFT transaction repository."""
    
    def __init__(self, db_connection):
        """
        Initialize the repository.
        
        Args:
            db_connection: Database connection
        """
        self.db = db_connection
        self.logger = logging.getLogger(__name__)
    
    def get_by_id(self, transaction_id: UUID) -> Optional[NEFTTransaction]:
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: The transaction ID
            
        Returns:
            Optional[NEFTTransaction]: The transaction if found, None otherwise
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT
                    id, transaction_reference, utr_number, status, 
                    created_at, updated_at, processed_at, completed_at,
                    batch_number, return_reason, error_message, customer_id,
                    metadata, payment_details
                FROM neft_transactions
                WHERE id = ?
                """,
                (str(transaction_id),)
            )
            
            row = cursor.fetchone()
            if not row:
                return None
                
            # Extract data
            (
                id_str, transaction_reference, utr_number, status_str,
                created_at_str, updated_at_str, processed_at_str, completed_at_str,
                batch_number, return_reason_str, error_message, customer_id,
                metadata_json, payment_details_json
            ) = row
            
            # Convert strings to appropriate types
            id = UUID(id_str)
            status = NEFTStatus(status_str)
            created_at = datetime.fromisoformat(created_at_str)
            updated_at = datetime.fromisoformat(updated_at_str)
            processed_at = datetime.fromisoformat(processed_at_str) if processed_at_str else None
            completed_at = datetime.fromisoformat(completed_at_str) if completed_at_str else None
            return_reason = NEFTReturnReason(return_reason_str) if return_reason_str else None
            metadata = json.loads(metadata_json) if metadata_json else {}
            
            # Deserialize payment details
            payment_data = json.loads(payment_details_json)
            payment_details = NEFTPaymentDetails(
                sender_account_number=payment_data.get("sender_account_number", ""),
                sender_ifsc_code=payment_data.get("sender_ifsc_code", ""),
                sender_account_type=payment_data.get("sender_account_type", ""),
                sender_name=payment_data.get("sender_name", ""),
                beneficiary_account_number=payment_data.get("beneficiary_account_number", ""),
                beneficiary_ifsc_code=payment_data.get("beneficiary_ifsc_code", ""),
                beneficiary_account_type=payment_data.get("beneficiary_account_type", ""),
                beneficiary_name=payment_data.get("beneficiary_name", ""),
                amount=float(payment_data.get("amount", 0)),
                payment_reference=payment_data.get("payment_reference", ""),
                remarks=payment_data.get("remarks", "")
            )
            
            # Create transaction object
            transaction = NEFTTransaction(
                id=id,
                payment_details=payment_details,
                transaction_reference=transaction_reference,
                utr_number=utr_number,
                status=status,
                created_at=created_at,
                updated_at=updated_at,
                processed_at=processed_at,
                completed_at=completed_at,
                batch_number=batch_number,
                return_reason=return_reason,
                error_message=error_message,
                customer_id=customer_id,
                metadata=metadata
            )
            
            return transaction
            
        except Exception as e:
            self.logger.error(f"Error getting NEFT transaction by ID: {e}")
            return None
    
    def save(self, transaction: NEFTTransaction) -> NEFTTransaction:
        """
        Save a transaction.
        
        Args:
            transaction: The transaction to save
            
        Returns:
            NEFTTransaction: The saved transaction
        """
        try:
            cursor = self.db.cursor()
            
            # Serialize payment details
            payment_details_json = json.dumps({
                "sender_account_number": transaction.payment_details.sender_account_number,
                "sender_ifsc_code": transaction.payment_details.sender_ifsc_code,
                "sender_account_type": transaction.payment_details.sender_account_type,
                "sender_name": transaction.payment_details.sender_name,
                "beneficiary_account_number": transaction.payment_details.beneficiary_account_number,
                "beneficiary_ifsc_code": transaction.payment_details.beneficiary_ifsc_code,
                "beneficiary_account_type": transaction.payment_details.beneficiary_account_type,
                "beneficiary_name": transaction.payment_details.beneficiary_name,
                "amount": transaction.payment_details.amount,
                "payment_reference": transaction.payment_details.payment_reference,
                "remarks": transaction.payment_details.remarks
            })
            
            # Serialize metadata
            metadata_json = json.dumps(transaction.metadata) if transaction.metadata else None
            
            # Insert the transaction
            cursor.execute(
                """
                INSERT INTO neft_transactions (
                    id, transaction_reference, utr_number, status,
                    created_at, updated_at, processed_at, completed_at,
                    batch_number, return_reason, error_message, customer_id,
                    metadata, payment_details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(transaction.id),
                    transaction.transaction_reference,
                    transaction.utr_number,
                    transaction.status.value,
                    transaction.created_at.isoformat(),
                    transaction.updated_at.isoformat(),
                    transaction.processed_at.isoformat() if transaction.processed_at else None,
                    transaction.completed_at.isoformat() if transaction.completed_at else None,
                    transaction.batch_number,
                    transaction.return_reason.value if transaction.return_reason else None,
                    transaction.error_message,
                    transaction.customer_id,
                    metadata_json,
                    payment_details_json
                )
            )
            
            self.db.commit()
            return transaction
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error saving NEFT transaction: {e}")
            raise
    
    def update(self, transaction: NEFTTransaction) -> NEFTTransaction:
        """
        Update a transaction.
        
        Args:
            transaction: The transaction to update
            
        Returns:
            NEFTTransaction: The updated transaction
        """
        try:
            cursor = self.db.cursor()
            
            # Serialize payment details
            payment_details_json = json.dumps({
                "sender_account_number": transaction.payment_details.sender_account_number,
                "sender_ifsc_code": transaction.payment_details.sender_ifsc_code,
                "sender_account_type": transaction.payment_details.sender_account_type,
                "sender_name": transaction.payment_details.sender_name,
                "beneficiary_account_number": transaction.payment_details.beneficiary_account_number,
                "beneficiary_ifsc_code": transaction.payment_details.beneficiary_ifsc_code,
                "beneficiary_account_type": transaction.payment_details.beneficiary_account_type,
                "beneficiary_name": transaction.payment_details.beneficiary_name,
                "amount": transaction.payment_details.amount,
                "payment_reference": transaction.payment_details.payment_reference,
                "remarks": transaction.payment_details.remarks
            })
            
            # Serialize metadata
            metadata_json = json.dumps(transaction.metadata) if transaction.metadata else None
            
            # Update the transaction
            cursor.execute(
                """
                UPDATE neft_transactions SET
                    transaction_reference = ?,
                    utr_number = ?,
                    status = ?,
                    updated_at = ?,
                    processed_at = ?,
                    completed_at = ?,
                    batch_number = ?,
                    return_reason = ?,
                    error_message = ?,
                    customer_id = ?,
                    metadata = ?,
                    payment_details = ?
                WHERE id = ?
                """,
                (
                    transaction.transaction_reference,
                    transaction.utr_number,
                    transaction.status.value,
                    transaction.updated_at.isoformat(),
                    transaction.processed_at.isoformat() if transaction.processed_at else None,
                    transaction.completed_at.isoformat() if transaction.completed_at else None,
                    transaction.batch_number,
                    transaction.return_reason.value if transaction.return_reason else None,
                    transaction.error_message,
                    transaction.customer_id,
                    metadata_json,
                    payment_details_json,
                    str(transaction.id)
                )
            )
            
            self.db.commit()
            return transaction
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error updating NEFT transaction: {e}")
            raise
    
    def get_by_customer_id(self, customer_id: str, limit: int = 10) -> List[NEFTTransaction]:
        """
        Get transactions by customer ID.
        
        Args:
            customer_id: The customer ID
            limit: Maximum number of transactions to return
            
        Returns:
            List[NEFTTransaction]: List of transactions
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT
                    id, transaction_reference, utr_number, status, 
                    created_at, updated_at, processed_at, completed_at,
                    batch_number, return_reason, error_message, customer_id,
                    metadata, payment_details
                FROM neft_transactions
                WHERE customer_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (customer_id, limit)
            )
            
            transactions = []
            for row in cursor.fetchall():
                (
                    id_str, transaction_reference, utr_number, status_str,
                    created_at_str, updated_at_str, processed_at_str, completed_at_str,
                    batch_number, return_reason_str, error_message, customer_id,
                    metadata_json, payment_details_json
                ) = row

                id = UUID(id_str)
                status = NEFTStatus(status_str)
                created_at = datetime.fromisoformat(created_at_str)
                updated_at = datetime.fromisoformat(updated_at_str)
                processed_at = datetime.fromisoformat(processed_at_str) if processed_at_str else None
                completed_at = datetime.fromisoformat(completed_at_str) if completed_at_str else None
                return_reason = NEFTReturnReason(return_reason_str) if return_reason_str else None
                metadata = json.loads(metadata_json) if metadata_json else {}

                payment_data = json.loads(payment_details_json)
                payment_details = NEFTPaymentDetails(
                    sender_account_number=payment_data.get("sender_account_number", ""),
                    sender_ifsc_code=payment_data.get("sender_ifsc_code", ""),
                    sender_account_type=payment_data.get("sender_account_type", ""),
                    sender_name=payment_data.get("sender_name", ""),
                    beneficiary_account_number=payment_data.get("beneficiary_account_number", ""),
                    beneficiary_ifsc_code=payment_data.get("beneficiary_ifsc_code", ""),
                    beneficiary_account_type=payment_data.get("beneficiary_account_type", ""),
                    beneficiary_name=payment_data.get("beneficiary_name", ""),
                    amount=float(payment_data.get("amount", 0)),
                    payment_reference=payment_data.get("payment_reference", ""),
                    remarks=payment_data.get("remarks", "")
                )

                transaction = NEFTTransaction(
                    id=id,
                    payment_details=payment_details,
                    transaction_reference=transaction_reference,
                    utr_number=utr_number,
                    status=status,
                    created_at=created_at,
                    updated_at=updated_at,
                    processed_at=processed_at,
                    completed_at=completed_at,
                    batch_number=batch_number,
                    return_reason=return_reason,
                    error_message=error_message,
                    customer_id=customer_id,
                    metadata=metadata
                )

                transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error getting NEFT transactions by customer ID: {e}")
            return []
    
    def get_by_status(self, status: str, limit: int = 100) -> List[NEFTTransaction]:
        """
        Get transactions by status.
        
        Args:
            status: The transaction status
            limit: Maximum number of transactions to return
            
        Returns:
            List[NEFTTransaction]: List of transactions
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT
                    id, transaction_reference, utr_number, status, 
                    created_at, updated_at, processed_at, completed_at,
                    batch_number, return_reason, error_message, customer_id,
                    metadata, payment_details
                FROM neft_transactions
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (status, limit)
            )
            
            transactions = []
            for row in cursor.fetchall():
                (
                    id_str, transaction_reference, utr_number, status_str,
                    created_at_str, updated_at_str, processed_at_str, completed_at_str,
                    batch_number, return_reason_str, error_message, customer_id,
                    metadata_json, payment_details_json
                ) = row

                id = UUID(id_str)
                status = NEFTStatus(status_str)
                created_at = datetime.fromisoformat(created_at_str)
                updated_at = datetime.fromisoformat(updated_at_str)
                processed_at = datetime.fromisoformat(processed_at_str) if processed_at_str else None
                completed_at = datetime.fromisoformat(completed_at_str) if completed_at_str else None
                return_reason = NEFTReturnReason(return_reason_str) if return_reason_str else None
                metadata = json.loads(metadata_json) if metadata_json else {}

                payment_data = json.loads(payment_details_json)
                payment_details = NEFTPaymentDetails(
                    sender_account_number=payment_data.get("sender_account_number", ""),
                    sender_ifsc_code=payment_data.get("sender_ifsc_code", ""),
                    sender_account_type=payment_data.get("sender_account_type", ""),
                    sender_name=payment_data.get("sender_name", ""),
                    beneficiary_account_number=payment_data.get("beneficiary_account_number", ""),
                    beneficiary_ifsc_code=payment_data.get("beneficiary_ifsc_code", ""),
                    beneficiary_account_type=payment_data.get("beneficiary_account_type", ""),
                    beneficiary_name=payment_data.get("beneficiary_name", ""),
                    amount=float(payment_data.get("amount", 0)),
                    payment_reference=payment_data.get("payment_reference", ""),
                    remarks=payment_data.get("remarks", "")
                )

                transaction = NEFTTransaction(
                    id=id,
                    payment_details=payment_details,
                    transaction_reference=transaction_reference,
                    utr_number=utr_number,
                    status=status,
                    created_at=created_at,
                    updated_at=updated_at,
                    processed_at=processed_at,
                    completed_at=completed_at,
                    batch_number=batch_number,
                    return_reason=return_reason,
                    error_message=error_message,
                    customer_id=customer_id,
                    metadata=metadata
                )
                
                transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error getting NEFT transactions by status: {e}")
            return []
    
    def get_by_batch_number(self, batch_number: str) -> List[NEFTTransaction]:
        """
        Get transactions by batch number.
        
        Args:
            batch_number: The batch number
            
        Returns:
            List[NEFTTransaction]: List of transactions
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """
                SELECT
                    id, transaction_reference, utr_number, status, 
                    created_at, updated_at, processed_at, completed_at,
                    batch_number, return_reason, error_message, customer_id,
                    metadata, payment_details
                FROM neft_transactions
                WHERE batch_number = ?
                ORDER BY created_at ASC
                """,
                (batch_number,)
            )
            
            transactions = []
            for row in cursor.fetchall():
                (
                    id_str, transaction_reference, utr_number, status_str,
                    created_at_str, updated_at_str, processed_at_str, completed_at_str,
                    batch_number, return_reason_str, error_message, customer_id,
                    metadata_json, payment_details_json
                ) = row

                id = UUID(id_str)
                status = NEFTStatus(status_str)
                created_at = datetime.fromisoformat(created_at_str)
                updated_at = datetime.fromisoformat(updated_at_str)
                processed_at = datetime.fromisoformat(processed_at_str) if processed_at_str else None
                completed_at = datetime.fromisoformat(completed_at_str) if completed_at_str else None
                return_reason = NEFTReturnReason(return_reason_str) if return_reason_str else None
                metadata = json.loads(metadata_json) if metadata_json else {}

                payment_data = json.loads(payment_details_json)
                payment_details = NEFTPaymentDetails(
                    sender_account_number=payment_data.get("sender_account_number", ""),
                    sender_ifsc_code=payment_data.get("sender_ifsc_code", ""),
                    sender_account_type=payment_data.get("sender_account_type", ""),
                    sender_name=payment_data.get("sender_name", ""),
                    beneficiary_account_number=payment_data.get("beneficiary_account_number", ""),
                    beneficiary_ifsc_code=payment_data.get("beneficiary_ifsc_code", ""),
                    beneficiary_account_type=payment_data.get("beneficiary_account_type", ""),
                    beneficiary_name=payment_data.get("beneficiary_name", ""),
                    amount=float(payment_data.get("amount", 0)),
                    payment_reference=payment_data.get("payment_reference", ""),
                    remarks=payment_data.get("remarks", "")
                )

                transaction = NEFTTransaction(
                    id=id,
                    payment_details=payment_details,
                    transaction_reference=transaction_reference,
                    utr_number=utr_number,
                    status=status,
                    created_at=created_at,
                    updated_at=updated_at,
                    processed_at=processed_at,
                    completed_at=completed_at,
                    batch_number=batch_number,
                    return_reason=return_reason,
                    error_message=error_message,
                    customer_id=customer_id,
                    metadata=metadata
                )
                
                transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error getting NEFT transactions by batch number: {e}")
            return []
