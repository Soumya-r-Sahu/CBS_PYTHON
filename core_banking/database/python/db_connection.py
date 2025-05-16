"""
Database Connection Utilities for Core Banking

This module provides database connection utilities for the Core Banking modules.
"""

def get_database_connection(connection_string=None):
    """
    Get a database connection.
    
    Args:
        connection_string: Optional connection string for the database
        
    Returns:
        Database connection object
    """
    # For testing purposes, this returns a simple dictionary that simulates a connection
    return {
        "connection_string": connection_string,
        "is_connected": True,
        "type": "mock"
    }
