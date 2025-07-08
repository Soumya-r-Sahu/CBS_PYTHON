"""
Django Client for CBS Banking System API

This package provides Django-specific utilities for interacting with 
the Core Banking System API.
"""

from .django_api_client import BankingAPIClient, APIError

__all__ = ['BankingAPIClient', 'APIError']
