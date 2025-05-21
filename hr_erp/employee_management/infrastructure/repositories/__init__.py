"""
Employee Management Infrastructure Repository Package

This package contains repository implementations for the
employee management domain in the HR-ERP system.
"""

from .sql_employee_repository import SqlEmployeeRepository

__all__ = ['SqlEmployeeRepository']