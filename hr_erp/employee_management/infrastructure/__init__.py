"""
Employee Management Infrastructure Package

This package contains infrastructure implementations for the
employee management domain in the HR-ERP system.
"""

from .di_container import get_container
from .repositories.sql_employee_repository import SqlEmployeeRepository
from .database.database_connection import DatabaseConnection

__all__ = [
    'get_container',
    'SqlEmployeeRepository',
    'DatabaseConnection'
]