"""
Database Common Operations Package

This package provides common database operations and utilities that
can be used across all modules of the CBS_PYTHON system.

Available modules:
- database_operations: Core database operations through standardized interfaces
"""

from .database_operations import DatabaseOperations

__all__ = ['DatabaseOperations']
