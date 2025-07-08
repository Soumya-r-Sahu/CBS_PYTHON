"""
Loans Presentation Layer

This package contains presentation layer components for the loans module,
including CLI and API interfaces.
"""

from .cli import loan_cli
from .api import loan_router

__all__ = [
    'loan_cli',
    'loan_router',
]
