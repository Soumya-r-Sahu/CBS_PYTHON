"""
Core Banking System - Security Module

This module provides security-related functionalities for the Core Banking System,
including authentication, authorization, encryption, certificate management,
and security middleware.
"""

from security.auth import authenticate_user, verify_permissions
from security.encryption import encrypt_data, decrypt_data
from security.access_control import check_access, create_token
from security.password_manager import (
    hash_password, verify_password, validate_password_policy,
    generate_secure_password, check_password_expiration
)
from security.mfa import setup_mfa, verify_mfa, disable_mfa, regenerate_backup_codes
from security.config import get_config_value

# Import middleware components
from security.middleware.auth_middleware import AuthMiddleware
from security.middleware.validation_middleware import RequestValidator
from security.middleware.rate_limit import RateLimitMiddleware
from security.middleware.security_headers import SecurityHeadersMiddleware
from security.middleware.cors_middleware import CORSMiddleware, cors_protected
from security.middleware.xss_protection import XSSProtectionMiddleware, xss_protected

# Import certificate management
from security.certificates.certificate_manager import CertificateManager

# Import logging components
from security.logs.audit_logger import AuditLogger
from security.logs.security_monitor import SecurityMonitor

# Version
__version__ = '1.2.0'
