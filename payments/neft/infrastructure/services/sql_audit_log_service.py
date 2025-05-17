"""
SQL NEFT Audit Log Service.
Implementation of the NEFTAuditLogServiceInterface using SQL database.
"""
import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from ...application.interfaces.neft_audit_log_service_interface import NEFTAuditLogServiceInterface
from ...domain.entities.neft_transaction import NEFTTransaction
from ...domain.entities.neft_batch import NEFTBatch


class SQLNEFTAuditLogService(NEFTAuditLogServiceInterface):
    """SQL implementation of NEFT audit log service."""
    
    def __init__(self, db_connection):
        """
        Initialize the service.
        
        Args:
            db_connection: Database connection
        """
        self.db = db_connection
        self.logger = logging.getLogger(__name__)
    
    def log_transaction_created(
        self, 
        transaction: NEFTTransaction, 
        user_id: Optional[str] = None
    ) -> bool:
        """
        Log transaction creation.
        
        Args:
            transaction: The created transaction
            user_id: Optional user ID for tracking who performed the action
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        return self._log_event(
            entity_type="TRANSACTION",
            entity_id=str(transaction.id),
            action="CREATED",
            previous_state=None,
            current_state=transaction.status.value,
            details={
                "transaction_reference": transaction.transaction_reference,
                "amount": transaction.payment_details.amount,
                "beneficiary_account": transaction.payment_details.beneficiary_account_number,
                "beneficiary_name": transaction.payment_details.beneficiary_name
            },
            user_id=user_id
        )
    
    def log_transaction_updated(
        self, 
        transaction: NEFTTransaction, 
        previous_status: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Log transaction update.
        
        Args:
            transaction: The updated transaction
            previous_status: Previous transaction status
            user_id: Optional user ID for tracking who performed the action
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        details = {
            "transaction_reference": transaction.transaction_reference,
            "batch_number": transaction.batch_number
        }
        
        if transaction.utr_number:
            details["utr_number"] = transaction.utr_number
            
        if transaction.error_message:
            details["error_message"] = transaction.error_message
        
        return self._log_event(
            entity_type="TRANSACTION",
            entity_id=str(transaction.id),
            action="UPDATED",
            previous_state=previous_status,
            current_state=transaction.status.value,
            details=details,
            user_id=user_id
        )
    
    def log_batch_created(
        self, 
        batch: NEFTBatch, 
        user_id: Optional[str] = None
    ) -> bool:
        """
        Log batch creation.
        
        Args:
            batch: The created batch
            user_id: Optional user ID for tracking who performed the action
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        return self._log_event(
            entity_type="BATCH",
            entity_id=str(batch.id),
            action="CREATED",
            previous_state=None,
            current_state=batch.status.value,
            details={
                "batch_number": batch.batch_number,
                "batch_time": batch.batch_time.isoformat(),
                "total_transactions": batch.total_transactions,
                "total_amount": batch.total_amount
            },
            user_id=user_id
        )
    
    def log_batch_updated(
        self, 
        batch: NEFTBatch, 
        previous_status: str,
        user_id: Optional[str] = None
    ) -> bool:
        """
        Log batch update.
        
        Args:
            batch: The updated batch
            previous_status: Previous batch status
            user_id: Optional user ID for tracking who performed the action
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        return self._log_event(
            entity_type="BATCH",
            entity_id=str(batch.id),
            action="UPDATED",
            previous_state=previous_status,
            current_state=batch.status.value,
            details={
                "batch_number": batch.batch_number,
                "total_transactions": batch.total_transactions,
                "completed_transactions": batch.completed_transactions,
                "failed_transactions": batch.failed_transactions
            },
            user_id=user_id
        )
    
    def get_transaction_audit_logs(
        self, 
        transaction_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get audit logs for a transaction.
        
        Args:
            transaction_id: Transaction ID to get logs for
            
        Returns:
            List[Dict[str, Any]]: List of audit log entries
        """
        return self._get_events("TRANSACTION", str(transaction_id))
    
    def get_batch_audit_logs(
        self, 
        batch_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get audit logs for a batch.
        
        Args:
            batch_id: Batch ID to get logs for
            
        Returns:
            List[Dict[str, Any]]: List of audit log entries
        """
        return self._get_events("BATCH", str(batch_id))
    
    def _log_event(
        self,
        entity_type: str,
        entity_id: str,
        action: str,
        previous_state: Optional[str],
        current_state: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> bool:
        """
        Log an event to the audit log.
        
        Args:
            entity_type: Type of entity (TRANSACTION, BATCH)
            entity_id: ID of the entity
            action: Action performed (CREATED, UPDATED)
            previous_state: Previous state (if any)
            current_state: Current state
            details: Additional details
            user_id: Optional user ID for tracking who performed the action
            
        Returns:
            bool: True if logged successfully, False otherwise
        """
        try:
            cursor = self.db.cursor()
            
            # Serialize details to JSON
            details_json = json.dumps(details)
            
            # Get timestamp
            timestamp = datetime.utcnow()
            
            # Insert audit log entry
            cursor.execute(
                """
                INSERT INTO neft_audit_logs (
                    entity_type, entity_id, action, 
                    previous_state, current_state, 
                    details, timestamp, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity_type,
                    entity_id,
                    action,
                    previous_state,
                    current_state,
                    details_json,
                    timestamp.isoformat(),
                    user_id
                )
            )
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Error logging audit event: {str(e)}")
            return False
    
    def _get_events(
        self,
        entity_type: str,
        entity_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get events from the audit log.
        
        Args:
            entity_type: Type of entity (TRANSACTION, BATCH)
            entity_id: ID of the entity
            
        Returns:
            List[Dict[str, Any]]: List of audit log entries
        """
        try:
            cursor = self.db.cursor()
            
            # Query audit log entries
            cursor.execute(
                """
                SELECT
                    id, entity_type, entity_id, action,
                    previous_state, current_state,
                    details, timestamp, user_id
                FROM neft_audit_logs
                WHERE entity_type = ? AND entity_id = ?
                ORDER BY timestamp ASC
                """,
                (entity_type, entity_id)
            )
            
            # Process results
            events = []
            for row in cursor.fetchall():
                (
                    id, entity_type, entity_id, action,
                    previous_state, current_state,
                    details_json, timestamp_str, user_id
                ) = row
                
                # Parse JSON
                details = json.loads(details_json) if details_json else {}
                
                # Parse timestamp
                timestamp = datetime.fromisoformat(timestamp_str)
                
                # Create event object
                event = {
                    "id": id,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "action": action,
                    "previous_state": previous_state,
                    "current_state": current_state,
                    "details": details,
                    "timestamp": timestamp,
                    "user_id": user_id
                }
                
                events.append(event)
                
            return events
            
        except Exception as e:
            self.logger.error(f"Error getting audit events: {str(e)}")
            return []
