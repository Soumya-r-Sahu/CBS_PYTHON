"""
Core Banking System - Configuration Package

This package contains configuration modules and settings used by the system.
"""

import os

__version__ = '1.1.0'

# Database configuration
DATABASE_CONFIG = {
    'host': os.environ.get('CBS_DB_HOST', 'localhost'),
    'database': os.environ.get('CBS_DB_NAME', 'CBS_PYTHON'),
    'user': os.environ.get('CBS_DB_USER', 'root'),
    'password': os.environ.get('CBS_DB_PASSWORD', ''),
    'port': int(os.environ.get('CBS_DB_PORT', 3307)),
    'pool_size': int(os.environ.get('CBS_DB_POOL_SIZE', 5)),
    'max_overflow': int(os.environ.get('CBS_DB_MAX_OVERFLOW', 10)),
    'timeout': int(os.environ.get('CBS_DB_TIMEOUT', 30)),
}
