"""
API Logging Service - Core Banking System

This module provides services for logging and retrieving API logs.
"""
from datetime import datetime
import json
import os
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import logging
import mysql.connector
from mysql.connector import pooling

from ..config.log_config import api_log_config
from ..models.log_models import ApiLogEntry, ApiLogSummary, ApiErrorGroup

# Configure logger
logger = logging.getLogger(__name__)


class ApiLoggerService:
    """Service for managing API logs"""
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one service instance exists"""
        if cls._instance is None:
            cls._instance = super(ApiLoggerService, cls).__new__(cls)
            cls._instance._setup()
        return cls._instance
    
    def _setup(self):
        """Set up service with configuration"""
        self.config = api_log_config
        self.log_dir = self.config.get("log_dir")
        self.max_file_size_mb = self.config.get("max_file_size_mb")
        self.sensitive_fields = self.config.get("sensitive_fields", [])
        self.lock = threading.Lock()
        
        # Create log directory if it doesn't exist
        Path(self.log_dir).mkdir(parents=True, exist_ok=True)
        
        # Set up database connection if enabled
        self.db_pool = None
        if self.config.get("enable_db_logging", False):
            try:
                self.db_pool = pooling.MySQLConnectionPool(
                    pool_name="api_log_pool",
                    pool_size=5,
                    **self._parse_db_connection_string()
                )
                logger.info("API Log DB connection pool created successfully")
            except Exception as e:
                logger.error(f"Failed to create API Log DB connection pool: {str(e)}")
    
    def _parse_db_connection_string(self) -> Dict[str, Any]:
        """Parse the database connection string into connection parameters"""
        connection_string = self.config.get("db_connection_string", "")
        
        # Simple parsing logic - in production, would use a more robust method
        params = {}
        if connection_string:
            parts = connection_string.split(';')
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    params[key.strip()] = value.strip()
                    
        # Apply defaults if needed
        params.setdefault('host', 'localhost')
        params.setdefault('user', 'root')
        params.setdefault('database', 'api_logs')
        
        return params
    
    def log_api_call(self, endpoint: str, request_data: Dict[str, Any], 
                   response_data: Dict[str, Any], status: str,
                   duration_ms: Optional[int] = None,
                   error: Optional[str] = None,
                   request_id: Optional[str] = None,
                   user_id: Optional[str] = None,
                   ip_address: Optional[str] = None) -> None:
        """Log an API call
        
        Args:
            endpoint: API endpoint that was called
            request_data: Request data (will be sanitized)
            response_data: Response data (will be sanitized)
            status: Status of the API call (success/error)
            duration_ms: Duration of the call in milliseconds
            error: Error message if status is error
            request_id: Unique identifier for the request
            user_id: ID of the user making the request
            ip_address: IP address of the requester
        """
        timestamp = datetime.utcnow().isoformat()
        
        # Sanitize sensitive data
        sanitized_request = self._sanitize_data(request_data)
        sanitized_response = self._sanitize_data(response_data)
        
        # Truncate bodies if they're too large
        max_size = self.config.get("max_body_size_kb", 1024) * 1024
        if not self.config.get("enable_request_body_logging", True):
            sanitized_request = {"logging_disabled": True}
        if not self.config.get("enable_response_body_logging", True):
            sanitized_response = {"logging_disabled": True}
            
        # Create log entry
        log_entry = ApiLogEntry(
            timestamp=timestamp,
            endpoint=endpoint,
            request=sanitized_request,
            response=sanitized_response,
            status=status,
            duration_ms=duration_ms,
            error=error,
            request_id=request_id,
            user_id=user_id,
            ip_address=ip_address
        )
        
        # Log to file and/or database
        self._log_to_file(log_entry)
        if self.config.get("enable_db_logging", False):
            self._log_to_database(log_entry)
    
    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize sensitive data in requests/responses"""
        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    sanitized[key] = self._sanitize_data(value)
                elif any(field in key.lower() for field in self.sensitive_fields):
                    sanitized[key] = "***REDACTED***"
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(data, list):
            return [self._sanitize_data(item) if isinstance(item, (dict, list)) else item for item in data]
        return data
    
    def _log_to_file(self, log_entry: ApiLogEntry) -> None:
        """Write log entry to file with rotation"""
        # Generate log filename based on date
        current_date = datetime.utcnow().strftime("%Y-%m-%d")
        log_file = os.path.join(self.log_dir, f"api_log_{current_date}.json")
        
        # Lock to prevent race conditions when multiple processes write logs
        with self.lock:
            # Rotate log file if it exceeds the maximum size
            if os.path.exists(log_file) and os.path.getsize(log_file) > self.max_file_size_mb * 1024 * 1024:
                self._rotate_log_file(log_file)
            
            # Append log entry to file
            try:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry.to_dict()) + '\n')
            except Exception as e:
                logger.error(f"Failed to write API log to file: {str(e)}")
    
    def _rotate_log_file(self, log_file: str) -> None:
        """Rotate log file when it gets too large"""
        rotation_count = self.config.get("rotation_count", 5)
        
        # Remove oldest rotation if it exists
        oldest_rotation = f"{log_file}.{rotation_count}"
        if os.path.exists(oldest_rotation):
            try:
                os.remove(oldest_rotation)
            except Exception as e:
                logger.error(f"Failed to remove old log rotation: {str(e)}")
        
        # Shift existing rotations
        for i in range(rotation_count - 1, 0, -1):
            current = f"{log_file}.{i}"
            next_rotation = f"{log_file}.{i + 1}"
            if os.path.exists(current):
                try:
                    os.rename(current, next_rotation)
                except Exception as e:
                    logger.error(f"Failed to rotate log file: {str(e)}")
        
        # Rename current log file to first rotation
        try:
            os.rename(log_file, f"{log_file}.1")
        except Exception as e:
            logger.error(f"Failed to rotate current log file: {str(e)}")
    
    def _log_to_database(self, log_entry: ApiLogEntry) -> None:
        """Store log entry in database"""
        if not self.db_pool:
            logger.warning("Database logging enabled but no connection pool available")
            return
            
        try:
            # Get connection from pool
            conn = self.db_pool.get_connection()
            cursor = conn.cursor()
            
            # SQL to insert log entry
            sql = """
            INSERT INTO api_logs (
                timestamp, endpoint, request_data, response_data, 
                status, duration_ms, error, request_id, user_id, ip_address
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """
            
            # Convert request and response to JSON strings
            request_json = json.dumps(log_entry.request)
            response_json = json.dumps(log_entry.response)
            
            # Execute query
            cursor.execute(sql, (
                log_entry.timestamp,
                log_entry.endpoint,
                request_json,
                response_json,
                log_entry.status,
                log_entry.duration_ms,
                log_entry.error,
                log_entry.request_id,
                log_entry.user_id,
                log_entry.ip_address
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log API call to database: {str(e)}")
    
    def get_logs(self, start_date: Optional[str] = None, 
               end_date: Optional[str] = None,
               status: Optional[str] = None,
               endpoint: Optional[str] = None,
               limit: int = 100) -> List[ApiLogEntry]:
        """Retrieve API logs with optional filtering
        
        Args:
            start_date: Filter logs starting from this date (ISO format)
            end_date: Filter logs up to this date (ISO format)
            status: Filter by status (success/error)
            endpoint: Filter by endpoint
            limit: Maximum number of logs to return
            
        Returns:
            List of ApiLogEntry objects
        """
        logs = []
        
        # If database logging is enabled, query from there
        if self.config.get("enable_db_logging", False) and self.db_pool:
            return self._get_logs_from_database(
                start_date, end_date, status, endpoint, limit
            )
        
        # Otherwise, read from log files
        log_files = self._get_log_files(start_date, end_date)
        
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            log_data = json.loads(line.strip())
                            
                            # Apply filters
                            if status and log_data.get("status") != status:
                                continue
                                
                            if endpoint and log_data.get("endpoint") != endpoint:
                                continue
                            
                            logs.append(ApiLogEntry(
                                timestamp=log_data.get("timestamp", ""),
                                endpoint=log_data.get("endpoint", ""),
                                request=log_data.get("request", {}),
                                response=log_data.get("response", {}),
                                status=log_data.get("status", ""),
                                duration_ms=log_data.get("duration_ms"),
                                error=log_data.get("error"),
                                request_id=log_data.get("request_id"),
                                user_id=log_data.get("user_id"),
                                ip_address=log_data.get("ip_address")
                            ))
                            
                            # Apply limit
                            if len(logs) >= limit:
                                return logs[:limit]
            except Exception as e:
                logger.error(f"Error reading log file {log_file}: {str(e)}")
        
        return logs[:limit]
    
    def _get_log_files(self, start_date: Optional[str], end_date: Optional[str]) -> List[str]:
        """Get list of log files within date range"""
        log_files = []
        
        try:
            # Get all log files in directory
            all_files = os.listdir(self.log_dir)
            
            for filename in all_files:
                if filename.startswith("api_log_") and filename.endswith(".json"):
                    # Extract date from filename
                    try:
                        date_str = filename.replace("api_log_", "").replace(".json", "").split('.')[0]
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")
                        
                        # Apply date filters
                        if start_date:
                            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                            if file_date < start:
                                continue
                                
                        if end_date:
                            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                            if file_date > end:
                                continue
                        
                        log_files.append(os.path.join(self.log_dir, filename))
                    except Exception:
                        # Skip files that don't match the expected format
                        continue
        except Exception as e:
            logger.error(f"Error listing log directory: {str(e)}")
        
        return sorted(log_files)
    
    def _get_logs_from_database(self, start_date: Optional[str], 
                              end_date: Optional[str],
                              status: Optional[str],
                              endpoint: Optional[str],
                              limit: int) -> List[ApiLogEntry]:
        """Query logs from database"""
        logs = []
        
        if not self.db_pool:
            return logs
            
        try:
            # Build query
            sql = "SELECT * FROM api_logs WHERE 1=1"
            params = []
            
            if start_date:
                sql += " AND timestamp >= %s"
                params.append(start_date)
                
            if end_date:
                sql += " AND timestamp <= %s"
                params.append(end_date)
                
            if status:
                sql += " AND status = %s"
                params.append(status)
                
            if endpoint:
                sql += " AND endpoint = %s"
                params.append(endpoint)
                
            sql += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            # Execute query
            conn = self.db_pool.get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql, params)
            
            for row in cursor:
                logs.append(ApiLogEntry(
                    timestamp=row["timestamp"],
                    endpoint=row["endpoint"],
                    request=json.loads(row["request_data"]),
                    response=json.loads(row["response_data"]),
                    status=row["status"],
                    duration_ms=row["duration_ms"],
                    error=row["error"],
                    request_id=row["request_id"],
                    user_id=row["user_id"],
                    ip_address=row["ip_address"]
                ))
                
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Database query error: {str(e)}")
            
        return logs
    
    def get_log_summary(self, start_date: Optional[str] = None, 
                      end_date: Optional[str] = None) -> ApiLogSummary:
        """Get summary statistics for API logs
        
        Args:
            start_date: Filter logs starting from this date (ISO format)
            end_date: Filter logs up to this date (ISO format)
            
        Returns:
            ApiLogSummary object with statistics
        """
        # Get logs within date range
        logs = self.get_logs(start_date, end_date, limit=10000)
        
        if not logs:
            # Return empty summary if no logs
            start = datetime.fromisoformat(start_date) if start_date else datetime.utcnow()
            end = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
            return ApiLogSummary(
                total_requests=0,
                success_count=0,
                error_count=0,
                avg_duration_ms=0,
                min_duration_ms=0,
                max_duration_ms=0,
                period_start=start,
                period_end=end
            )
            
        # Calculate statistics
        total = len(logs)
        success_count = sum(1 for log in logs if log.status == "success")
        error_count = total - success_count
        
        # Duration statistics - skip logs with no duration
        durations = [log.duration_ms for log in logs if log.duration_ms is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        
        # Group by endpoints
        endpoints = {}
        for log in logs:
            if log.endpoint not in endpoints:
                endpoints[log.endpoint] = {
                    "endpoint": log.endpoint,
                    "count": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "avg_duration_ms": 0,
                    "durations": []
                }
                
            ep_data = endpoints[log.endpoint]
            ep_data["count"] += 1
            
            if log.status == "success":
                ep_data["success_count"] += 1
            else:
                ep_data["error_count"] += 1
                
            if log.duration_ms is not None:
                ep_data["durations"].append(log.duration_ms)
        
        # Calculate per-endpoint statistics
        endpoint_stats = []
        for endpoint, data in endpoints.items():
            if data["durations"]:
                data["avg_duration_ms"] = sum(data["durations"]) / len(data["durations"])
            del data["durations"]
            endpoint_stats.append(data)
            
        # Sort endpoints by count
        endpoint_stats.sort(key=lambda x: x["count"], reverse=True)
        
        # Determine time range
        if logs:
            try:
                start_timestamp = min(datetime.fromisoformat(log.timestamp.replace('Z', '+00:00')) for log in logs)
                end_timestamp = max(datetime.fromisoformat(log.timestamp.replace('Z', '+00:00')) for log in logs)
            except ValueError:
                # Fallback if timestamp parsing fails
                start_timestamp = datetime.utcnow()
                end_timestamp = datetime.utcnow()
        else:
            start_timestamp = datetime.utcnow()
            end_timestamp = datetime.utcnow()
            
        return ApiLogSummary(
            total_requests=total,
            success_count=success_count,
            error_count=error_count,
            avg_duration_ms=avg_duration,
            min_duration_ms=min_duration,
            max_duration_ms=max_duration,
            period_start=start_timestamp,
            period_end=end_timestamp,
            endpoints=endpoint_stats
        )


# Create a service instance for import

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
api_logger_service = ApiLoggerService()
