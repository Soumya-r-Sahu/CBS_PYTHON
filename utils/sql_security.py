"""
SQL Injection Prevention Utilities

This module provides utilities for preventing SQL injection attacks in the Core Banking System.
It includes functions for safely constructing SQL queries, validating input parameters,
and escaping special characters.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from sqlalchemy.sql import text

# Set up logger
logger = logging.getLogger(__name__)

def sanitize_input(value: str) -> str:
    """
    Sanitize input to prevent SQL injection attacks.
    
    Args:
        value: The input value to sanitize
        
    Returns:
        Sanitized value
    """
    if value is None:
        return None
        
    # Convert to string if not already
    if not isinstance(value, str):
        value = str(value)
        
    # Replace dangerous characters
    sanitized = value.replace("'", "''")
    
    # Remove comments and other SQL injection patterns
    sanitized = re.sub(r'--.*$', '', sanitized)
    sanitized = re.sub(r'/\*.*\*/', '', sanitized)
    
    return sanitized

def create_safe_query(query_template: str, params: Dict[str, Any]) -> text:
    """
    Create a safe SQL query using SQLAlchemy's text() function.
    
    Args:
        query_template: SQL query template with named parameters
        params: Dictionary of parameter values
        
    Returns:
        SQLAlchemy text object with bound parameters
    """
    # Create SQLAlchemy text object with named parameters
    query = text(query_template)
    
    # Log the query for debugging
    logger.debug(f"Creating safe query: {query_template}")
    logger.debug(f"Parameters: {params}")
    
    return query.bindparams(**params)

def validate_column_name(column_name: str) -> bool:
    """
    Validate column name to prevent SQL injection in dynamic queries.
    
    Args:
        column_name: Column name to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Allow only alphanumeric characters, underscores, and dots (for table.column)
    pattern = r'^[a-zA-Z0-9_\.]+$'
    return bool(re.match(pattern, column_name))

def build_dynamic_query(
    table: str, 
    columns: List[str] = None, 
    where_conditions: Dict[str, Any] = None,
    order_by: List[str] = None, 
    limit: int = None
) -> Tuple[text, Dict[str, Any]]:
    """
    Build a dynamic query safely.
    
    Args:
        table: Table name
        columns: List of column names (default: ["*"])
        where_conditions: Dictionary of column-value pairs for WHERE clause
        order_by: List of columns to order by
        limit: Maximum number of results
        
    Returns:
        Tuple of (SQLAlchemy text object, parameters dict)
    """
    # Validate table name
    if not validate_column_name(table):
        raise ValueError(f"Invalid table name: {table}")
    
    # Validate column names
    cols = columns or ["*"]
    for col in cols:
        if col != "*" and not validate_column_name(col):
            raise ValueError(f"Invalid column name: {col}")
    
    # Build SELECT clause
    query = f"SELECT {', '.join(cols)} FROM {table}"
    
    # Build WHERE clause
    params = {}
    if where_conditions:
        where_clauses = []
        for i, (col, val) in enumerate(where_conditions.items()):
            if not validate_column_name(col):
                raise ValueError(f"Invalid column name in WHERE clause: {col}")
            
            param_name = f"param_{i}"
            where_clauses.append(f"{col} = :{param_name}")
            params[param_name] = val
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
    
    # Build ORDER BY clause
    if order_by:
        order_clauses = []
        for col in order_by:
            # Handle DESC and ASC suffixes
            col_parts = col.split()
            base_col = col_parts[0]
            direction = col_parts[1] if len(col_parts) > 1 else ""
            
            if not validate_column_name(base_col):
                raise ValueError(f"Invalid column name in ORDER BY clause: {base_col}")
            
            if direction and direction.upper() not in ["ASC", "DESC"]:
                raise ValueError(f"Invalid sort direction: {direction}")
            
            order_clauses.append(col)
        
        if order_clauses:
            query += " ORDER BY " + ", ".join(order_clauses)
    
    # Add LIMIT
    if limit is not None:
        if not isinstance(limit, int) or limit < 0:
            raise ValueError(f"Invalid limit value: {limit}")
        
        query += f" LIMIT {limit}"
    
    # Create safe query
    return text(query), params
