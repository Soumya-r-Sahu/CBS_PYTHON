"""
Central Audit Trail System for Core Banking System

This module provides comprehensive audit logging capabilities for tracking all
significant actions within the system for compliance, security, and traceability.
"""

import os
import time
import logging
import datetime
import json
from typing import Dict, Any, Optional, List
import uuid

# Try to import pymongo for database storage
try:
    import pymongo
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

# Initialize logger
logger = logging.getLogger(__name__)

# Import configuration
import os

# Try to use local config if available
try:

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed

    from config import get_config, get_environment
except ImportError:
    # Fallback to system config
    try:
        from config import get_config, get_environment
    except ImportError:
        # Use stub functions if all else fails
        def get_environment():
            return os.environ.get("CBS_ENVIRONMENT", "DEVELOPMENT").upper()
            
        def get_config(module_name):
            return {
                "storage_type": "file",
                "log_directory": "logs/audit"
            }


class AuditTrailManager:
    """Manager for comprehensive audit trail across the CBS system"""
    
    def __init__(self):
        """Initialize the Audit Trail Manager"""
        self.environment = get_environment()
        self.config = get_config("audit_trail")
        
        # Configure storage based on environment
        self._setup_storage()
        
        logger.info(f"Audit Trail Manager initialized in {self.environment} environment")
        
    def _setup_storage(self):
        """Set up storage backend based on environment and configuration"""
        storage_type = self.config.get("storage_type", "file")
        
        if storage_type == "mongodb" and MONGODB_AVAILABLE:
            self._setup_mongodb_storage()
        else:
            self._setup_file_storage()
    
    def _setup_mongodb_storage(self):
        """Set up MongoDB as storage backend"""
        try:
            connection_string = self.config.get("mongodb_uri", "mongodb://localhost:27017/")
            self.db_client = pymongo.MongoClient(connection_string)
            self.db = self.db_client.audit_trail
            self.audit_collection = self.db.audit_events
            
            # Create indices for faster querying
            self.audit_collection.create_index([("timestamp", pymongo.DESCENDING)])
            self.audit_collection.create_index([("event_type", pymongo.ASCENDING)])
            self.audit_collection.create_index([("user_id", pymongo.ASCENDING)])
            self.audit_collection.create_index([("entity_id", pymongo.ASCENDING)])
            
            logger.info("MongoDB audit trail storage initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB audit storage: {str(e)}")
            self._setup_file_storage()
    
    def _setup_file_storage(self):
        """Set up file-based storage as backup or default"""
        self.log_dir = self.config.get("log_directory", "logs/audit")
        
        # Create directory if it doesn't exist
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create file handler based on environment
        env_prefix = self.environment.lower()
        self.log_file = f"{self.log_dir}/{env_prefix}_audit_trail.log"
        
        # Set up file handler for audit logs
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Create separate logger for audit events
        self.file_logger = logging.getLogger("audit_trail")
        self.file_logger.setLevel(logging.INFO)
        self.file_logger.addHandler(file_handler)
        
        logger.info(f"File-based audit trail storage initialized at {self.log_file}")
    
    def log_event(self, event_type: str, user_id: str = None, description: str = None, 
                entity_type: str = None, entity_id: str = None,
                status: str = "SUCCESS", metadata: Dict[str, Any] = None) -> str:
        """
        Log an audit event to the audit trail
        
        Args:
            event_type (str): Type of event (e.g., "login", "transaction", "account_create")
            user_id (str, optional): ID of the user performing the action
            description (str, optional): Human-readable description of the event
            entity_type (str, optional): Type of entity being acted upon (e.g., "account", "customer")
            entity_id (str, optional): ID of the entity being acted upon
            status (str, optional): Outcome status ("SUCCESS", "FAILED", "PENDING")
            metadata (Dict, optional): Additional structured data about the event
            
        Returns:
            str: Unique ID of the audit event
        """
        # Generate an event ID
        event_id = str(uuid.uuid4())
        
        # Create basic event structure
        event = {
            "event_id": event_id,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event_type": event_type,
            "environment": self.environment,
            "status": status
        }
        
        # Add optional fields if provided
        if user_id:
            event["user_id"] = user_id
        
        if description:
            event["description"] = description
            
        if entity_type:
            event["entity_type"] = entity_type
            
        if entity_id:
            event["entity_id"] = entity_id
        
        # Add metadata if provided
        if metadata:
            event["metadata"] = metadata
        
        # Store the event based on configured storage
        try:
            if hasattr(self, 'audit_collection'):
                # Store in MongoDB
                self.audit_collection.insert_one(event)
            
            # Always log to file as backup
            if hasattr(self, 'file_logger'):
                self.file_logger.info(json.dumps(event))
                
            return event_id
        except Exception as e:
            logger.error(f"Failed to store audit event: {str(e)}")
            # Emergency fallback - log to application log
            logger.info(f"AUDIT: {json.dumps(event)}")
            return event_id
    
    def query_events(self, filters: Dict[str, Any] = None, 
                   start_time: datetime.datetime = None, 
                   end_time: datetime.datetime = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query audit events based on filters
        
        Args:
            filters (Dict, optional): Filters to apply (e.g., {"event_type": "login"})
            start_time (datetime, optional): Start time for query range
            end_time (datetime, optional): End time for query range
            limit (int, optional): Maximum number of events to return
            
        Returns:
            List[Dict]: List of matching audit events
        """
        query = filters or {}
        
        # Add time range if provided
        if start_time or end_time:
            query["timestamp"] = {}
            
            if start_time:
                query["timestamp"]["$gte"] = start_time.isoformat()
                
            if end_time:
                query["timestamp"]["$lte"] = end_time.isoformat()
        
        # If MongoDB is available, query from database
        if hasattr(self, 'audit_collection'):
            try:
                results = list(self.audit_collection.find(
                    query, 
                    sort=[("timestamp", pymongo.DESCENDING)],
                    limit=limit
                ))
                
                # Convert ObjectId to string for JSON serialization
                for result in results:
                    if "_id" in result:
                        result["_id"] = str(result["_id"])
                        
                return results
            except Exception as e:
                logger.error(f"Failed to query MongoDB audit trail: {str(e)}")
                # Fall back to file-based query
        
        # If MongoDB unavailable or query failed, try to parse from file
        if hasattr(self, 'log_file'):
            try:
                results = []
                with open(self.log_file, 'r') as f:
                    for line in f:
                        # Parse JSON from log line (skipping timestamp prefix)
                        try:
                            json_start = line.find('{')
                            if json_start != -1:
                                event = json.loads(line[json_start:])
                                
                                # Apply filters
                                matches = True
                                for key, value in query.items():
                                    if key == "timestamp":
                                        # Handle time range separately
                                        continue
                                    
                                    if key not in event or event[key] != value:
                                        matches = False
                                        break
                                
                                # Apply time range if provided
                                if matches and "timestamp" in query:
                                    timestamp = event.get("timestamp")
                                    if timestamp:
                                        if "$gte" in query["timestamp"] and timestamp < query["timestamp"]["$gte"]:
                                            matches = False
                                        if "$lte" in query["timestamp"] and timestamp > query["timestamp"]["$lte"]:
                                            matches = False
                                
                                if matches:
                                    results.append(event)
                                    if len(results) >= limit:
                                        break
                        except json.JSONDecodeError:
                            continue
                
                return results
            except Exception as e:
                logger.error(f"Failed to query file-based audit trail: {str(e)}")
        
        # Return empty list if all queries fail
        return []
    
    def generate_report(self, report_type: str, filters: Dict[str, Any] = None,
                       start_time: datetime.datetime = None,
                       end_time: datetime.datetime = None) -> Dict[str, Any]:
        """
        Generate an audit report based on events
        
        Args:
            report_type (str): Type of report to generate
            filters (Dict, optional): Filters to apply
            start_time (datetime, optional): Start time for report range
            end_time (datetime, optional): End time for report range
            
        Returns:
            Dict: Report results
        """
        # Default to last 24 hours if no time range specified
        if not end_time:
            end_time = datetime.datetime.utcnow()
        
        if not start_time:
            start_time = end_time - datetime.timedelta(days=1)
            
        # Get events for the report
        events = self.query_events(
            filters=filters,
            start_time=start_time,
            end_time=end_time,
            limit=10000  # Higher limit for reports
        )
        
        # Process based on report type
        if report_type == "activity_summary":
            return self._generate_activity_summary(events, start_time, end_time)
        elif report_type == "security_events":
            return self._generate_security_events_report(events, start_time, end_time)
        elif report_type == "user_activity":
            return self._generate_user_activity_report(events, start_time, end_time)
        else:
            return {
                "error": "Unsupported report type",
                "available_types": ["activity_summary", "security_events", "user_activity"]
            }
    
    def _generate_activity_summary(self, events, start_time, end_time):
        """Generate a summary of activities in the system"""
        # Count events by type
        event_counts = {}
        for event in events:
            event_type = event.get("event_type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Count events by status
        status_counts = {}
        for event in events:
            status = event.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count events per hour
        hourly_counts = {}
        for event in events:
            timestamp = event.get("timestamp")
            if timestamp:
                try:
                    dt = datetime.datetime.fromisoformat(timestamp)
                    hour = dt.strftime("%Y-%m-%d %H:00:00")
                    hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
                except (ValueError, TypeError):
                    pass
        
        return {
            "report_type": "activity_summary",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_events": len(events),
            "event_type_distribution": event_counts,
            "status_distribution": status_counts,
            "hourly_distribution": hourly_counts
        }
    
    def _generate_security_events_report(self, events, start_time, end_time):
        """Generate a report focused on security-related events"""
        # Filter security events
        security_events = []
        security_event_types = [
            "login", "login_failed", "password_change", "pin_change",
            "permission_change", "user_blocked", "mfa_enabled",
            "mfa_disabled", "api_key_generated", "api_key_revoked"
        ]
        
        for event in events:
            event_type = event.get("event_type", "")
            if event_type in security_events or event.get("status") == "FAILED":
                security_events.append(event)
        
        # Group by user
        user_events = {}
        for event in security_events:
            user_id = event.get("user_id", "unknown")
            if user_id not in user_events:
                user_events[user_id] = []
            user_events[user_id].append(event)
        
        # Find users with failed login attempts
        suspicious_users = {}
        for user_id, events in user_events.items():
            failed_logins = [e for e in events if e.get("event_type") == "login" and e.get("status") == "FAILED"]
            if len(failed_logins) >= 3:
                suspicious_users[user_id] = len(failed_logins)
        
        return {
            "report_type": "security_events",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_security_events": len(security_events),
            "suspicious_users": suspicious_users,
            "failed_login_count": len([e for e in security_events 
                                   if e.get("event_type") == "login" and e.get("status") == "FAILED"]),
            "password_changes": len([e for e in security_events if e.get("event_type") == "password_change"]),
            "permission_changes": len([e for e in security_events if e.get("event_type") == "permission_change"])
        }
    
    def _generate_user_activity_report(self, events, start_time, end_time):
        """Generate a report of user activities"""
        # Group by user
        user_activities = {}
        for event in events:
            user_id = event.get("user_id", "unknown")
            if user_id not in user_activities:
                user_activities[user_id] = {
                    "total_events": 0,
                    "first_activity": None,
                    "last_activity": None,
                    "event_types": {}
                }
            
            # Update user activity record
            record = user_activities[user_id]
            record["total_events"] += 1
            
            # Track event types
            event_type = event.get("event_type", "unknown")
            record["event_types"][event_type] = record["event_types"].get(event_type, 0) + 1
            
            # Track activity times
            timestamp = event.get("timestamp")
            if timestamp:
                try:
                    dt = datetime.datetime.fromisoformat(timestamp)
                    if record["first_activity"] is None or dt < record["first_activity"]:
                        record["first_activity"] = dt
                    if record["last_activity"] is None or dt > record["last_activity"]:
                        record["last_activity"] = dt
                except (ValueError, TypeError):
                    pass
        
        # Convert datetime objects to strings
        for user_id, record in user_activities.items():
            if record["first_activity"]:
                record["first_activity"] = record["first_activity"].isoformat()
            if record["last_activity"]:
                record["last_activity"] = record["last_activity"].isoformat()
        
        return {
            "report_type": "user_activity",
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_users": len(user_activities),
            "user_activities": user_activities
        }


# Create a singleton instance
audit_trail = AuditTrailManager()

# Export main functions for easy access
log_event = audit_trail.log_event
query_events = audit_trail.query_events
generate_report = audit_trail.generate_report