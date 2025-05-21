"""
HR_ERP Data Validation Utilities

This module provides validation utilities for HR_ERP data.
It includes functions to validate employee data, payroll data, and resource data.
"""

import logging
import re
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def validate_employee_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate employee data
    
    Args:
        data: Employee data to validate
        
    Returns:
        Tuple containing (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    required_fields = ["name", "employee_id", "department", "position", "join_date"]
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate employee ID format if provided
    if "employee_id" in data and data["employee_id"]:
        id_pattern = r'^[A-Z0-9]{2,10}$'
        if not re.match(id_pattern, data["employee_id"]):
            errors.append("Invalid employee ID format")
    
    # Validate date format
    if "join_date" in data:
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(date_pattern, data["join_date"]):
            errors.append("Invalid date format. Use YYYY-MM-DD")
            
    # Validate email format if provided
    if "email" in data and data["email"]:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, data["email"]):
            errors.append("Invalid email format")
    
    return len(errors) == 0, errors

def validate_payroll_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate payroll data
    
    Args:
        data: Payroll data to validate
        
    Returns:
        Tuple containing (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    required_fields = ["period", "employee_id", "basic_salary"]
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate period format
    if "period" in data:
        period_pattern = r'^\d{4}-(0[1-9]|1[0-2])$'  # YYYY-MM
        if not re.match(period_pattern, data["period"]):
            errors.append("Invalid period format. Use YYYY-MM")
    
    # Validate salary
    if "basic_salary" in data:
        try:
            salary = float(data["basic_salary"])
            if salary < 0:
                errors.append("Salary cannot be negative")
        except (ValueError, TypeError):
            errors.append("Salary must be a number")
    
    return len(errors) == 0, errors

def validate_leave_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate leave request data
    
    Args:
        data: Leave request data to validate
        
    Returns:
        Tuple containing (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    required_fields = ["employee_id", "leave_type", "start_date", "end_date"]
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate leave type
    valid_types = ["annual", "sick", "unpaid", "parental", "bereavement", "other"]
    if "leave_type" in data and data["leave_type"] not in valid_types:
        errors.append(f"Invalid leave type. Must be one of: {', '.join(valid_types)}")
    
    # Validate date format and range
    if "start_date" in data and "end_date" in data:
        date_pattern = r'^\d{4}-\d{2}-\d{2}$'
        
        if not re.match(date_pattern, data["start_date"]):
            errors.append("Invalid start date format. Use YYYY-MM-DD")
            
        if not re.match(date_pattern, data["end_date"]):
            errors.append("Invalid end date format. Use YYYY-MM-DD")
            
        try:
            start_date = datetime.strptime(data["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(data["end_date"], "%Y-%m-%d")
            
            if end_date < start_date:
                errors.append("End date cannot be before start date")
        except ValueError:
            # Already caught by the regex check
            pass
    
    return len(errors) == 0, errors

def validate_resource_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate resource data
    
    Args:
        data: Resource data to validate
        
    Returns:
        Tuple containing (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required fields
    required_fields = ["resource_id", "resource_type", "name", "status"]
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"Missing required field: {field}")
    
    # Validate resource type
    valid_types = ["hardware", "software", "facility", "vehicle", "equipment", "other"]
    if "resource_type" in data and data["resource_type"] not in valid_types:
        errors.append(f"Invalid resource type. Must be one of: {', '.join(valid_types)}")
    
    # Validate status
    valid_statuses = ["available", "in_use", "maintenance", "reserved", "decommissioned"]
    if "status" in data and data["status"] not in valid_statuses:
        errors.append(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    return len(errors) == 0, errors
