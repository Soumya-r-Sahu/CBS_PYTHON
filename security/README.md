# Core Banking System - Security Module

This directory contains the security module for the Core Banking System, which provides comprehensive security features for protecting banking data and operations.

## Module Structure

### Core Security Components

- `__init__.py`: Module initialization and exports
- `auth.py`: Authentication functionality including JWT token management
- `access_control.py`: Role-based access control and permission management
- `encryption.py`: Data encryption utilities using AES-256-CBC
- `password_manager.py`: Secure password handling and policy enforcement
- `mfa.py`: Multi-factor authentication with TOTP and backup codes
- `config.py`: Centralized security configuration

### Subdirectories

- `certificates/`: SSL/TLS certificate management
  - `certificate_manager.py`: Certificate operations and lifecycle management
  - `tls_config.py`: TLS security settings and cipher configurations

- `logs/`: Security logging and monitoring
  - `audit_logger.py`: Security event audit logging
  - `security_monitor.py`: Security incident detection and monitoring

- `middleware/`: Security middleware components
  - `auth_middleware.py`: Authentication middleware for Flask
  - `validation_middleware.py`: Request validation and sanitization
  - `rate_limit.py`: API rate limiting for abuse prevention
  - `security_headers.py`: Security HTTP headers
  - `cors_middleware.py`: Cross-Origin Resource Sharing protection
  - `xss_protection.py`: Cross-Site Scripting protection

## Usage

See the `docs/security_integration.md` file for detailed integration instructions and examples.

## Best Practices

1. Always use environment variables for sensitive configuration values
2. Follow the principle of least privilege for access control
3. Use strong encryption and secure password hashing algorithms
4. Implement defense in depth with multiple security layers
5. Log security-relevant events for audit and monitoring
6. Regularly update security dependencies and certificates

## Testing

Security unit tests are available in:
- `tests/unit/test_password_manager.py`
- `tests/unit/test_mfa.py`
- `tests/unit/test_security_config.py`
