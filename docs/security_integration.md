# Core Banking System Security Module Documentation

## Overview

The Security Module provides comprehensive security features for the Core Banking System including:

- Authentication and Authorization
- Encryption and Data Protection
- Password Management
- Multi-Factor Authentication (MFA)
- Certificate Management
- Security Middleware
- Audit Logging and Monitoring

This document outlines how to integrate and use the security features in your application code.

## Getting Started

### Installation

Ensure the required dependencies are installed:

```bash
pip install -r requirements.txt
```

For MFA support, install additional dependencies:

```bash
pip install pyotp qrcode pillow
```

### Basic Configuration

The security module uses settings from `security/config.py`. For production environments, configure these settings using environment variables:

```bash
# Set environment
export CBS_ENVIRONMENT=production

# Set secure JWT key
export JWT_SECRET_KEY=your-secure-secret-key

# Set storage URI for rate limiting
export RATE_LIMIT_STORAGE=redis://localhost:6379/0
```

## Authentication and Authorization

### User Authentication

```python
from security import authenticate_user, verify_permissions
from security.password_manager import hash_password, verify_password

# Create a new user with hashed password
def create_user(username, password, roles=None):
    hashed_password, salt = hash_password(password)
    # Store in database: username, hashed_password, salt, roles
    
    # Example of storing in a database
    user_data = {
        "username": username,
        "password_hash": hashed_password,
        "password_salt": salt,
        "roles": roles or ["user"],
        "created_at": time.time()
    }
    db.users.insert_one(user_data)
    
    return user_data

# Authenticate a user
def login_user(username, password):
    # Retrieve user from database
    user = db.users.find_one({"username": username})
    
    if not user:
        return {"success": False, "message": "User not found"}
    
    # Verify password
    if verify_password(password, user["password_hash"], user["password_salt"]):
        # Generate token
        from security.access_control import create_token
        token = create_token(user["username"], user["roles"])
        
        return {"success": True, "token": token}
    else:
        return {"success": False, "message": "Invalid password"}
```

### Authorization and Access Control

```python
from security import check_access, verify_permissions

# Example of protecting an API endpoint
def transfer_funds(user_id, from_account, to_account, amount):
    # Verify user has permission to transfer funds from this account
    if not check_access(user_id, f"account:{from_account}", "transfer"):
        return {"success": False, "message": "Permission denied"}
    
    # Process the transfer
    # ...
    
    return {"success": True}
    
# Example for a Flask route with permission check
@app.route("/api/admin/reports", methods=["GET"])
@verify_permissions(["admin", "reports_viewer"])
def get_reports():
    # This endpoint is only accessible to users with admin or reports_viewer role
    return jsonify({"reports": get_all_reports()})
```

## Encryption

```python
from security import encrypt_data, decrypt_data

# Encrypt sensitive data
def store_payment_details(user_id, card_number, cvv):
    # Encrypt sensitive data
    encrypted_card = encrypt_data(card_number)
    encrypted_cvv = encrypt_data(cvv)
    
    # Store in database
    payment_data = {
        "user_id": user_id,
        "encrypted_card": encrypted_card,
        "encrypted_cvv": encrypted_cvv
    }
    db.payment_details.insert_one(payment_data)
    
    return {"success": True}

# Decrypt data when needed
def process_payment(user_id, amount):
    # Get encrypted details
    payment_details = db.payment_details.find_one({"user_id": user_id})
    
    # Decrypt only when needed
    card_number = decrypt_data(payment_details["encrypted_card"])
    cvv = decrypt_data(payment_details["encrypted_cvv"])
    
    # Process payment with external service
    # ...
    
    # Don't return the decrypted values
    return {"success": True, "amount": amount}
```

## Password Management

```python
from security.password_manager import (
    validate_password_policy,
    generate_secure_password,
    check_password_expiration,
    is_password_reused
)

# Validate a new password against policy
def change_user_password(user_id, new_password):
    # Validate password policy
    validation = validate_password_policy(new_password)
    
    if not validation["valid"]:
        return {"success": False, "errors": validation["errors"]}
    
    # Get user's password history
    user = db.users.find_one({"_id": user_id})
    password_history = user.get("password_history", [])
    
    # Check if password was used before
    if is_password_reused(new_password, password_history):
        return {"success": False, "message": "Password was used previously"}
    
    # Hash the new password
    from security.password_manager import hash_password
    hashed, salt = hash_password(new_password)
    
    # Update the password and add to history
    new_history_entry = {"hash": hashed, "salt": salt, "created_at": time.time()}
    
    # Keep only the last N entries in history
    from security.config import PASSWORD_POLICY
    if len(password_history) >= PASSWORD_POLICY["history_size"]:
        password_history = password_history[-(PASSWORD_POLICY["history_size"]-1):]
    
    password_history.append(new_history_entry)
    
    # Update in database
    db.users.update_one(
        {"_id": user_id},
        {"$set": {
            "password_hash": hashed,
            "password_salt": salt,
            "password_history": password_history,
            "password_last_changed": time.time()
        }}
    )
    
    return {"success": True}

# Check if a user's password has expired
def check_user_password_expired(user_id):
    user = db.users.find_one({"_id": user_id})
    
    # Check password expiration
    last_changed = user.get("password_last_changed", 0)
    expiration_info = check_password_expiration(last_changed)
    
    if expiration_info["expired"]:
        # Password has expired, require change
        return {"expired": True, "days_since_change": expiration_info["days_since_change"]}
    else:
        # Password still valid
        return {"expired": False, "days_left": expiration_info["days_left"]}
```

## Multi-Factor Authentication (MFA)

```python
from security.mfa import setup_mfa, verify_mfa, disable_mfa, regenerate_backup_codes

# Set up MFA for a user
def setup_user_mfa(user_id):
    # Get user data
    user = db.users.find_one({"_id": user_id})
    
    # Set up MFA
    setup_info = setup_mfa(user["username"])
    
    # Save MFA data in database
    db.users.update_one(
        {"_id": user_id},
        {"$set": {"mfa_data": setup_info["mfa_data"]}}
    )
    
    # Return setup information to display to the user
    return {
        "qr_code": setup_info["qr_code"],  # Base64-encoded QR code image
        "backup_codes": setup_info["backup_codes"],
        "setup_instructions": setup_info["setup_instructions"]
    }

# Verify MFA during login
def verify_user_mfa(user_id, token):
    # Get user data
    user = db.users.find_one({"_id": user_id})
    
    if not user.get("mfa_data", {}).get("enabled", False):
        # MFA not enabled for this user
        return {"success": False, "message": "MFA not enabled"}
    
    # Verify the token
    is_valid, updated_mfa_data = verify_mfa(token, user["mfa_data"])
    
    if is_valid:
        # Update MFA data if changed (e.g., backup code was used)
        db.users.update_one(
            {"_id": user_id},
            {"$set": {"mfa_data": updated_mfa_data}}
        )
        
        return {"success": True}
    else:
        return {"success": False, "message": "Invalid MFA token or backup code"}
```

## Security Middleware

### Adding Security Middleware to a Flask Application

```python
from flask import Flask
from security.middleware.auth_middleware import AuthMiddleware
from security.middleware.validation_middleware import RequestValidator
from security.middleware.rate_limit import RateLimitMiddleware
from security.middleware.security_headers import SecurityHeadersMiddleware

app = Flask(__name__)

# Apply middleware
AuthMiddleware(app)
RequestValidator(app)
RateLimitMiddleware(app)
SecurityHeadersMiddleware(app)

# Define routes
@app.route("/")
def index():
    return "Secured application"
```

## Certificate Management

```python
from security.certificates.certificate_manager import CertificateManager

# Initialize certificate manager
cert_manager = CertificateManager()

# Generate self-signed certificate
def generate_self_signed_cert(domain_name):
    cert_path, key_path = cert_manager.generate_self_signed_cert(
        common_name=domain_name,
        days_valid=365
    )
    
    return {"cert_path": cert_path, "key_path": key_path}

# Check certificate expiry
def check_cert_expiry(cert_path):
    days_left = cert_manager.check_certificate_expiry(cert_path)
    
    if days_left < 30:
        # Certificate expiring soon, notify admin
        send_notification(f"Certificate expiring in {days_left} days")
    
    return {"days_left": days_left}
```

## Audit Logging

```python
from security.logs.audit_logger import AuditLogger

# Initialize audit logger
audit_logger = AuditLogger()

# Log security events
def process_transaction(user_id, transaction_type, amount):
    # Process transaction
    # ...
    
    # Log the security-sensitive event
    audit_logger.log_event(
        event_type="transaction",
        user_id=user_id,
        description=f"{transaction_type} transaction for ${amount}",
        metadata={
            "transaction_type": transaction_type,
            "amount": amount,
            "ip_address": request.remote_addr
        }
    )
    
    return {"success": True}
```

## Security Monitoring

```python
from security.logs.security_monitor import SecurityMonitor

# Initialize security monitor
security_monitor = SecurityMonitor()

# Register a login event for anomaly detection
def register_login_event(user_id, success, ip_address):
    security_monitor.register_event(
        event_type="login",
        user_id=user_id,
        success=success,
        metadata={
            "ip_address": ip_address,
            "timestamp": time.time(),
            "user_agent": request.user_agent.string
        }
    )
    
    # Check for unusual activity
    anomalies = security_monitor.check_anomalies(user_id)
    
    if anomalies:
        # Handle potential security issue
        alert_security_team(user_id, anomalies)
```

## Best Practices

1. **Environment Variables**: Always use environment variables for sensitive configuration values.

2. **Defense in Depth**: Apply multiple security controls (authentication, authorization, encryption).

3. **Principle of Least Privilege**: Grant minimum necessary access to users and processes.

4. **Secure Defaults**: Security features should be enabled by default, requiring explicit opt-out.

5. **Input Validation**: Validate all user input to prevent injection attacks.

6. **Error Handling**: Use secure error handling that doesn't reveal sensitive information.

7. **Logging**: Log security-relevant events for audit and anomaly detection.

8. **Regular Updates**: Keep security dependencies updated.

## Testing

Run the security module tests:

```bash
python -m pytest tests/unit/test_password_manager.py
python -m pytest tests/unit/test_mfa.py
python -m pytest tests/unit/test_security_config.py
```
