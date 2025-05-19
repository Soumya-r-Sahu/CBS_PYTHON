"""
System Configuration for Core Banking System

This file defines which implementations to use for different components
of the system.
"""

# Import configurations
IMPLEMENTATION_CONFIG = {
    # Set to True to use the new Admin Portal implementation or False for the standalone admin dashboard
    "USE_DJANGO_ADMIN_PORTAL": True,
    
    # Set to True to use Clean Architecture implementation or False for legacy implementation
    "USE_CLEAN_ARCHITECTURE": True,
    
    # Set which database implementation to use: 'mysql', 'sqlite', or 'postgres'
    "DATABASE_IMPLEMENTATION": "mysql",
    
    # Set to True to enable API server
    "ENABLE_API_SERVER": True,
    
    # Set to True to enable transaction logging
    "ENABLE_TRANSACTION_LOGGING": True,
    
    # Set to True to enable performance monitoring
    "ENABLE_PERFORMANCE_MONITORING": True
}

# API Server configuration
API_SERVER_CONFIG = {
    "port": 8000,
    "host": "0.0.0.0",
    "debug": False,
    "use_ssl": False,
    "ssl_cert": "",
    "ssl_key": ""
}

# Django Admin Portal configuration
DJANGO_ADMIN_PORTAL_CONFIG = {
    "port": 8001,
    "host": "0.0.0.0",
    "static_root": "app/Portals/Admin/static",
    "media_root": "app/Portals/Admin/media",
    "database": {
        "engine": "django.db.backends.sqlite3",
        "name": "app/Portals/Admin/db.sqlite3"
    }
}

# Feature flags
FEATURE_FLAGS = {
    "ENABLE_MULTI_CURRENCY": True,
    "ENABLE_SCHEDULED_PAYMENTS": True,
    "ENABLE_MOBILE_NOTIFICATIONS": True,
    "ENABLE_TWO_FACTOR_AUTH": True,
    "ENABLE_BIOMETRIC_AUTH": False,
    "ENABLE_AI_FRAUD_DETECTION": False
}
