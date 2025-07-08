"""
Loans API Module

This package contains REST API endpoints for loan operations.
"""

from .loan_endpoints import router as loan_router

__all__ = [
    'loan_router',
]
