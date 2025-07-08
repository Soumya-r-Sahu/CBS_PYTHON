"""
SQLite implementation of the mobile session repository interface.
"""
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import sqlite3

from ...domain.entities.mobile_session import MobileBankingSession
from ...application.interfaces.mobile_session_repository_interface import MobileSessionRepositoryInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class SQLMobileSessionRepository(MobileSessionRepositoryInterface):
    """SQLite implementation of the mobile session repository."""
    
    def __init__(self, db_connection):
        """
        Initialize the repository.
        
        Args:
            db_connection: SQLite database connection
        """
        self._connection = db_connection
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Ensure the required tables exist in the database."""
        cursor = self._connection.cursor()
        
        # Create sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS mobile_banking_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            device_id TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT,
            last_activity_time TEXT NOT NULL,
            is_active INTEGER NOT NULL,
            location TEXT,
            FOREIGN KEY (user_id) REFERENCES mobile_banking_users (id)
        )
        ''')
        
        self._connection.commit()
    
    def get_by_id(self, session_id: UUID) -> Optional[MobileBankingSession]:
        """
        Get a session by its ID.
        
        Args:
            session_id: The ID of the session to get
            
        Returns:
            MobileBankingSession if found, None otherwise
        """
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM mobile_banking_sessions WHERE id = ?",
            (str(session_id),)
        )
        session_data = cursor.fetchone()
        
        if session_data is None:
            return None
        
        return self._session_from_row(session_data)
    
    def get_by_token(self, token: str) -> Optional[MobileBankingSession]:
        """
        Get a session by its token.
        
        Args:
            token: The token of the session to get
            
        Returns:
            MobileBankingSession if found, None otherwise
        """
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM mobile_banking_sessions WHERE token = ?",
            (token,)
        )
        session_data = cursor.fetchone()
        
        if session_data is None:
            return None
        
        return self._session_from_row(session_data)
    
    def get_active_sessions_by_user_id(self, user_id: UUID) -> List[MobileBankingSession]:
        """
        Get all active sessions for a user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of active MobileBankingSession objects
        """
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM mobile_banking_sessions WHERE user_id = ? AND is_active = 1",
            (str(user_id),)
        )
        session_rows = cursor.fetchall()
        
        return [self._session_from_row(row) for row in session_rows]
    
    def save(self, session: MobileBankingSession) -> MobileBankingSession:
        """
        Save a session to the repository.
        
        Args:
            session: The session to save
            
        Returns:
            The saved session with any updates (e.g., ID assignment)
        """
        # Assign an ID if the session doesn't have one
        if session.id is None:
            session.id = uuid4()
        
        # Ensure last_activity_time is set
        if session.last_activity_time is None:
            session.last_activity_time = session.start_time
        
        cursor = self._connection.cursor()
        
        # Convert location to JSON if present
        location_json = json.dumps(session.location) if session.location else None
        
        # Insert the session
        cursor.execute('''
        INSERT INTO mobile_banking_sessions 
        (id, user_id, token, ip_address, user_agent, device_id, start_time, 
         end_time, last_activity_time, is_active, location)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(session.id),
            str(session.user_id),
            session.token,
            session.ip_address,
            session.user_agent,
            session.device_id,
            session.start_time.isoformat() if session.start_time else None,
            session.end_time.isoformat() if session.end_time else None,
            session.last_activity_time.isoformat() if session.last_activity_time else None,
            1 if session.is_active else 0,
            location_json
        ))
        
        self._connection.commit()
        return session
    
    def update(self, session: MobileBankingSession) -> MobileBankingSession:
        """
        Update an existing session.
        
        Args:
            session: The session to update
            
        Returns:
            The updated session
        """
        cursor = self._connection.cursor()
        
        # Convert location to JSON if present
        location_json = json.dumps(session.location) if session.location else None
        
        # Update the session
        cursor.execute('''
        UPDATE mobile_banking_sessions SET
            user_id = ?,
            token = ?,
            ip_address = ?,
            user_agent = ?,
            device_id = ?,
            start_time = ?,
            end_time = ?,
            last_activity_time = ?,
            is_active = ?,
            location = ?
        WHERE id = ?
        ''', (
            str(session.user_id),
            session.token,
            session.ip_address,
            session.user_agent,
            session.device_id,
            session.start_time.isoformat() if session.start_time else None,
            session.end_time.isoformat() if session.end_time else None,
            session.last_activity_time.isoformat() if session.last_activity_time else None,
            1 if session.is_active else 0,
            location_json,
            str(session.id)
        ))
        
        self._connection.commit()
        return session
    
    def delete(self, session_id: UUID) -> bool:
        """
        Delete a session by its ID.
        
        Args:
            session_id: The ID of the session to delete
            
        Returns:
            True if session was deleted, False otherwise
        """
        cursor = self._connection.cursor()
        cursor.execute(
            "DELETE FROM mobile_banking_sessions WHERE id = ?",
            (str(session_id),)
        )
        
        self._connection.commit()
        return cursor.rowcount > 0
    
    def _session_from_row(self, row: tuple) -> MobileBankingSession:
        """
        Create a MobileBankingSession from a database row.
        
        Args:
            row: Database row
            
        Returns:
            MobileBankingSession object
        """
        # Extract columns based on order
        (id_str, user_id_str, token, ip_address, user_agent, device_id, 
         start_time_str, end_time_str, last_activity_time_str, is_active, location_json) = row
        
        # Parse dates
        start_time = datetime.fromisoformat(start_time_str) if start_time_str else None
        end_time = datetime.fromisoformat(end_time_str) if end_time_str else None
        last_activity_time = datetime.fromisoformat(last_activity_time_str) if last_activity_time_str else None
        
        # Parse location
        location = json.loads(location_json) if location_json else None
        
        # Create and return session
        return MobileBankingSession(
            id=UUID(id_str),
            user_id=UUID(user_id_str),
            token=token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            last_activity_time=last_activity_time,
            is_active=bool(is_active),
            location=location
        )
