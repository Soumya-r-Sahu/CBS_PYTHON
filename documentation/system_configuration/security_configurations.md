# Security Configurations

This document provides comprehensive information about security configurations in the CBS_PYTHON system.

## Security Architecture Overview

The CBS_PYTHON system implements a defense-in-depth security architecture with multiple layers of protection:

1. **Authentication**: Identity verification
2. **Authorization**: Access control
3. **Data Protection**: Encryption and data security
4. **Input Validation**: Preventing injection attacks
5. **Auditing**: Logging security events
6. **Rate Limiting**: Preventing abuse

## Authentication Configuration

### JWT Authentication

```yaml
security:
  jwt:
    secret: ${CBS_JWT_SECRET}  # Environment variable for secret key
    algorithm: HS256  # Signing algorithm
    expiry_minutes: 60  # Token expiry time
    refresh_expiry_days: 7  # Refresh token expiry
    token_location: 
      - cookies
      - headers
    refresh_token_cookie_name: refresh_token
    csrf_protection: true
```

### Password Security

```yaml
security:
  password:
    min_length: 12  # Minimum password length
    require_uppercase: true  # Require uppercase characters
    require_lowercase: true  # Require lowercase characters
    require_digits: true  # Require numeric digits
    require_special: true  # Require special characters
    max_age_days: 90  # Password expiry
    prevent_common_passwords: true  # Check against common password list
    prevent_password_reuse: 10  # Number of previous passwords that can't be reused
    bcrypt_rounds: 12  # Work factor for bcrypt
```

### Multi-Factor Authentication

```yaml
security:
  mfa:
    enabled: true
    methods:
      - totp  # Time-based One-Time Password
      - sms   # SMS-based verification
    totp:
      issuer: "CBS Banking"
      digits: 6
      period: 30
    sms:
      message_template: "Your verification code is: {code}"
      expiry_minutes: 5
      rate_limit: 3  # Max attempts per hour
```

## Authorization Configuration

### Role-Based Access Control

```yaml
security:
  rbac:
    enabled: true
    default_role: user
    roles:
      - user
      - teller
      - branch_manager
      - admin
      - system_admin
    role_permissions_file: config/role_permissions.yaml
```

### API Scope Configuration

```yaml
security:
  api_scopes:
    account:read: "Access to read account information"
    account:write: "Access to modify account information"
    transaction:read: "Access to read transaction information"
    transaction:execute: "Access to execute transactions"
    customer:read: "Access to read customer information"
    customer:write: "Access to modify customer information"
    admin: "Administrative access"
```

## Data Protection Configuration

### Encryption

```yaml
security:
  encryption:
    key_management: 
      provider: ${CBS_ENCRYPTION_PROVIDER}  # vault, aws-kms, etc.
      key_rotation_days: 90
    data_at_rest:
      enabled: true
      algorithm: AES-256-GCM
      sensitive_fields:
        - customer.tax_id
        - customer.id_document
        - payment.card_number
    data_in_transit:
      enforce_https: true
      min_tls_version: "1.2"
      hsts_enabled: true
      hsts_max_age: 63072000  # 2 years
```

### Data Masking

```yaml
security:
  data_masking:
    enabled: true
    patterns:
      credit_card: "XXXX-XXXX-XXXX-{last4}"
      email: "{first3}****@{domain}"
      phone: "+{country_code} XXX-XXX-{last4}"
      account_number: "XXXXX{last4}"
      name: "{first_initial}. {last_name}"
```

## Network Security Configuration

### CORS Configuration

```yaml
security:
  cors:
    enabled: true
    allowed_origins: ${CBS_ALLOWED_ORIGINS}  # Comma-separated list
    allowed_methods: 
      - GET
      - POST
      - PUT
      - DELETE
    allowed_headers:
      - Content-Type
      - Authorization
    expose_headers:
      - X-Request-ID
    max_age: 86400  # 1 day
    allow_credentials: true
```

### IP Filtering

```yaml
security:
  ip_filtering:
    enabled: true
    mode: "allowlist"  # or "blocklist"
    allowlist:
      - "10.0.0.0/8"      # Internal network
      - "192.168.0.0/16"  # VPN network
    blocklist:
      - "known_malicious_ips.txt"  # File with IPs to block
    admin_panel:
      allowlist_only: true
      allowlist:
        - "10.10.0.0/16"  # Admin network
```

## API Security Configuration

### Rate Limiting

```yaml
security:
  rate_limiting:
    enabled: true
    default:
      rate: 60  # Requests per minute
      burst: 10  # Additional requests allowed in bursts
    routes:
      "/api/v1/auth/login":
        rate: 10  # Stricter limit for login endpoint
        burst: 3
      "/api/v1/accounts":
        rate: 30
        burst: 5
    by_role:
      user: 
        rate: 60
      admin:
        rate: 200
    storage: "redis"  # Where to store rate limit counters
```

### API Keys

```yaml
security:
  api_keys:
    enabled: true
    header_name: "X-API-Key"
    key_rotation_days: 90
    key_length: 32
    daily_quota: 10000  # Requests per day
```

## Audit and Logging

### Security Audit Logging

```yaml
security:
  audit:
    enabled: true
    log_login_attempts: true
    log_authorization_failures: true
    log_sensitive_operations: true
    log_admin_actions: true
    log_data_exports: true
    sensitive_operations:
      - account_creation
      - large_transfers
      - customer_data_change
      - permission_change
```

### Logging Configuration

```yaml
logging:
  security:
    level: INFO
    format: json
    include_context: true
    sensitive_data_in_logs: false
    mask_patterns:
      - "card_number": "regex:(?:\\d{4}-){3}\\d{4}|\\d{16}"
      - "password": "regex:password.*"
      - "token": "regex:Bearer\\s+[\\w-]+\\.[\\w-]+\\.[\\w-]+"
```

## Content Security

### CSP Configuration

```yaml
security:
  content_security_policy:
    enabled: true
    default_src: "'self'"
    script_src: "'self' 'unsafe-inline'"
    style_src: "'self' 'unsafe-inline'"
    img_src: "'self' data:"
    connect_src: "'self'"
    frame_src: "'none'"
    report_uri: "/api/v1/security/csp-report"
    report_only: false
```

## Environment-Specific Security Settings

### Development

```yaml
# development.yaml security section
security:
  jwt:
    expiry_minutes: 1440  # 24 hours for development
  password:
    min_length: 8  # Relaxed for development
  mfa:
    enabled: false  # Disabled for easier development
  rate_limiting:
    enabled: false  # Disabled for development
```

### Production

```yaml
# production.yaml security section
security:
  jwt:
    expiry_minutes: 30  # Shorter time for production
  password:
    min_length: 12  # Stricter for production
  mfa:
    enabled: true  # Enforced for production
  rate_limiting:
    enabled: true  # Enforced for production
  audit:
    enabled: true  # Full audit trail in production
```

## Security Features Configuration

### CAPTCHA

```yaml
security:
  captcha:
    enabled: true
    provider: "recaptcha"  # recaptcha, hcaptcha, etc.
    site_key: ${CBS_CAPTCHA_SITE_KEY}
    secret_key: ${CBS_CAPTCHA_SECRET_KEY}
    threshold: 0.5
    trigger_on:
      - login_failure
      - registration
      - password_reset
```

### Account Lockout

```yaml
security:
  account_lockout:
    enabled: true
    max_attempts: 5  # Number of failed attempts before lockout
    lockout_period_minutes: 30  # How long the account remains locked
    reset_counter_after_minutes: 15  # Reset failed attempts counter
    notify_user: true  # Send notification to user
```

## Security Compliance Settings

```yaml
security:
  compliance:
    pci_dss:
      enabled: true
      log_retention_days: 365
      scan_frequency_days: 30
    gdpr:
      enabled: true
      data_retention_policy: "config/data_retention_policy.yaml"
      right_to_be_forgotten: true
    regulatory_reporting:
      aml_checks: true
      suspicious_transaction_threshold: 10000
```

## Mobile Security Settings

```yaml
security:
  mobile:
    certificate_pinning: true
    jailbreak_detection: true
    root_detection: true
    app_tamper_protection: true
    biometric_authentication: true
    device_binding: true
```

## Implementing Security Configurations

### Loading Security Configuration

```python
from config import ConfigManager

# Get configuration instance
config = ConfigManager.get_instance()

# Access security configuration
jwt_secret = config.get("security.jwt.secret")
jwt_expiry = config.get_int("security.jwt.expiry_minutes")
password_min_length = config.get_int("security.password.min_length")
```

### Security Middlewares

The security configurations are automatically applied through various middlewares:

```python
# Example of how authentication middleware is configured
def configure_auth_middleware(app):
    jwt_config = config.get_section("security.jwt")
    app.add_middleware(
        JWTAuthenticationMiddleware,
        secret=jwt_config.get("secret"),
        algorithm=jwt_config.get("algorithm"),
        expiry_minutes=jwt_config.get_int("expiry_minutes")
    )
```

## Best Practices

1. **Never hardcode secrets**: Always use environment variables or secure vaults
2. **Defense in depth**: Apply multiple security controls
3. **Principle of least privilege**: Restrict access to the minimum required
4. **Regularly rotate keys and credentials**: Implement automatic key rotation
5. **Validate all inputs**: Prevent injection attacks
6. **Encrypt sensitive data**: Both at rest and in transit
7. **Comprehensive logging**: Log security events for audit purposes
8. **Regular security testing**: Conduct penetration testing and vulnerability scanning

## Related Documentation

- [Environment-Specific Configurations](environment_configs.md)
- [Configuration System](configuration_system.md)
- [API Configuration](api_configuration.md)