"""
SQLite implementation of the audit log service interface.
"""
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import sqlite3

from ...application.interfaces.audit_log_service_interface import AuditLogServiceInterface, AuditEventType

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class SQLAuditLogService(AuditLogServiceInterface):
    """SQLite implementation of the audit log service."""
    
    def __init__(self, db_connection):
        """
        Initialize the service.
        
        Args:
            db_connection: SQLite database connection
        """
        self._connection = db_connection
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure the required tables exist in the database."""
        cursor = self._connection.cursor()
        
        # Create audit_logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mobile_banking_audit_logs (
            id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            user_id TEXT,
            ip_address TEXT,
            details TEXT,
            status TEXT NOT NULL,
            device_info TEXT,
            location TEXT,
            timestamp TEXT NOT NULL
        )
        ''')
        
        # Create index on user_id
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS mobile_banking_audit_logs_user_id
        ON mobile_banking_audit_logs (user_id)
        ''')
        
        # Create index on timestamp
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS mobile_banking_audit_logs_timestamp
        ON mobile_banking_audit_logs (timestamp)
        ''')
        
        # Create index on event_type
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS mobile_banking_audit_logs_event_type
        ON mobile_banking_audit_logs (event_type)
        ''')
        
        self._connection.commit()
    
    def log_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[UUID],
        ip_address: str,
        details: Dict[str, Any],
        status: str,
        device_info: Optional[Dict[str, Any]] = None,
        location: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> bool:
        """
        Log an audit event.
        
        Args:
            event_type: The type of event to log
            user_id: The ID of the user involved
            ip_address: The IP address from which the event originated
            details: Details about the event
            status: Status of the event (success, failure, etc.)
            device_info: Information about the device used
            location: Location information
            timestamp: The time of the event (defaults to now)
            
        Returns:
            True if event was logged, False otherwise
        """
        # Use current time if timestamp not provided
        if timestamp is None:
            timestamp = datetime.now()
        
        cursor = self._connection.cursor()
        
        # Generate ID for the log entry
        log_id = str(uuid4())
        
        # Convert dictionaries to JSON
        details_json = json.dumps(details)
        device_info_json = json.dumps(device_info) if device_info else None
        location_json = json.dumps(location) if location else None
        
        # Insert the log entry
        cursor.execute('''
        INSERT INTO mobile_banking_audit_logs 
        (id, event_type, user_id, ip_address, details, status, device_info, location, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_id,
            event_type.value,
            str(user_id) if user_id else None,
            ip_address,
            details_json,
            status,
            device_info_json,
            location_json,
            timestamp.isoformat()
        ))
        
        self._connection.commit()
        return True
    
    def get_user_events(
        self,
        user_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[list[AuditEventType]] = None
    ) -> list[Dict[str, Any]]:
        """
        Get audit events for a user.
        
        Args:
            user_id: The ID of the user
            start_time: The start time of the range
            end_time: The end time of the range
            event_types: Only include these event types
            
        Returns:
            List of audit events as dictionaries
        """
        cursor = self._connection.cursor()
        
        # Build the query
        query = "SELECT * FROM mobile_banking_audit_logs WHERE user_id = ?"
        params = [str(user_id)]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        if event_types:
            placeholders = ", ".join("?" for _ in event_types)
            query += f" AND event_type IN ({placeholders})"
            params.extend(event_type.value for event_type in event_types)
        
        query += " ORDER BY timestamp DESC"
        
        # Execute the query
        cursor.execute(query, params)
        log_rows = cursor.fetchall()
        
        # Convert rows to dictionaries
        return [self._log_entry_to_dict(row) for row in log_rows]
    
    def get_system_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[list[AuditEventType]] = None,
        status: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """
        Get audit events for the system.
        
        Args:
            start_time: The start time of the range
            end_time: The end time of the range
            event_types: Only include these event types
            status: Only include events with this status
            
        Returns:
            List of audit events as dictionaries
        """
        cursor = self._connection.cursor()
        
        # Build the query
        query = "SELECT * FROM mobile_banking_audit_logs WHERE 1=1"
        params = []
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())
        
        if event_types:
            placeholders = ", ".join("?" for _ in event_types)
            query += f" AND event_type IN ({placeholders})"
            params.extend(event_type.value for event_type in event_types)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY timestamp DESC"
        
        # Execute the query
        cursor.execute(query, params)
        log_rows = cursor.fetchall()
        
        # Convert rows to dictionaries
        return [self._log_entry_to_dict(row) for row in log_rows]
    
    def _log_entry_to_dict(self, row: tuple) -> Dict[str, Any]:
        """
        Convert a database row to a dictionary.
        
        Args:
            row: Database row
            
        Returns:
            Dictionary representation of the log entry
        """
        # Extract columns based on order
        (id_str, event_type_str, user_id_str, ip_address, details_json, 
         status, device_info_json, location_json, timestamp_str) = row
        
        # Parse JSON fields
        details = json.loads(details_json)
        device_info = json.loads(device_info_json) if device_info_json else None
        location = json.loads(location_json) if location_json else None
        
        # Create and return dictionary
        return {
            "id": id_str,
            "event_type": event_type_str,
            "user_id": user_id_str,
            "ip_address": ip_address,
            "details": details,
            "status": status,
            "device_info": device_info,
            "location": location,
            "timestamp": timestamp_str
        }
