"""
API Logging Utilities - Core Banking System

This module provides utility functions for working with API logs.
"""
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from ..models.log_models import ApiLogEntry, ApiErrorGroup
from ..config.log_config import api_log_config


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
# Configure logger
logger = logging.getLogger(__name__)


def group_errors_by_type(logs: List[ApiLogEntry]) -> List[ApiErrorGroup]:
    """Group API logs by error type
    
    Args:
        logs: List of ApiLogEntry objects
        
    Returns:
        List of ApiErrorGroup objects
    """
    error_groups = {}
    
    for log in logs:
        if log.status != "error" or not log.error:
            continue
            
        # Extract error type - either use specific error type or first part of message
        error_parts = log.error.split(':', 1)
        error_type = error_parts[0].strip()
        
        if error_type not in error_groups:
            error_groups[error_type] = {
                "count": 0,
                "first_occurrence": None,
                "last_occurrence": None,
                "endpoints": set(),
                "sample_errors": []
            }
            
        group = error_groups[error_type]
        group["count"] += 1
        group["endpoints"].add(log.endpoint)
        
        timestamp = datetime.fromisoformat(log.timestamp.replace('Z', '+00:00'))
        
        if group["first_occurrence"] is None or timestamp < group["first_occurrence"]:
            group["first_occurrence"] = timestamp
            
        if group["last_occurrence"] is None or timestamp > group["last_occurrence"]:
            group["last_occurrence"] = timestamp
            
        # Add to sample errors if we don't have many yet
        if len(group["sample_errors"]) < 5:
            group["sample_errors"].append({
                "timestamp": log.timestamp,
                "endpoint": log.endpoint,
                "error": log.error,
                "request_id": log.request_id
            })
    
    # Convert to proper ApiErrorGroup objects
    result = []
    for error_type, data in error_groups.items():
        result.append(ApiErrorGroup(
            error_type=error_type,
            count=data["count"],
            first_occurrence=data["first_occurrence"],
            last_occurrence=data["last_occurrence"],
            endpoints=list(data["endpoints"]),
            sample_errors=data["sample_errors"]
        ))
    
    # Sort by count (descending)
    result.sort(key=lambda x: x.count, reverse=True)
    return result


def cleanup_old_logs(days: Optional[int] = None) -> int:
    """Remove log files older than specified days
    
    Args:
        days: Number of days to keep logs (defaults to config value)
        
    Returns:
        Number of files deleted
    """
    if days is None:
        days = api_log_config.get("store_days", 90)
        
    log_dir = api_log_config.get("log_dir")
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    files_deleted = 0
    
    try:
        for filename in os.listdir(log_dir):
            if filename.startswith("api_log_") and filename.endswith(".json"):
                # Extract date from filename
                try:
                    date_str = filename.replace("api_log_", "").replace(".json", "").split('.')[0]
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    if file_date < cutoff_date:
                        os.remove(os.path.join(log_dir, filename))
                        files_deleted += 1
                        logger.info(f"Deleted old log file: {filename}")
                except Exception as e:
                    logger.error(f"Error processing log file {filename}: {str(e)}")
    except Exception as e:
        logger.error(f"Error cleaning up log files: {str(e)}")
        
    return files_deleted


def export_logs_to_json(logs: List[ApiLogEntry], output_file: str) -> bool:
    """Export logs to a JSON file
    
    Args:
        logs: List of ApiLogEntry objects
        output_file: Path to output file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json_data = [log.to_dict() for log in logs]
            json.dump(json_data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error exporting logs to JSON: {str(e)}")
        return False
