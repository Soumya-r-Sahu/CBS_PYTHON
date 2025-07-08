"""
Alert utilities for the Core Banking System monitoring subsystem.

This module provides functions to create and manage system alerts.
"""
import json
from datetime import datetime

def create_alert(alert_type, severity, description, resolved=False):
    """Create a new alert as a dictionary."""
    return {
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "alert_type": alert_type,
        "severity": severity,
        "description": description,
        "resolved": resolved
    }

def save_alert(alert, path):
    """Save an alert to a JSON file."""
    with open(path, 'a') as f:
        f.write(json.dumps(alert) + '\n')
