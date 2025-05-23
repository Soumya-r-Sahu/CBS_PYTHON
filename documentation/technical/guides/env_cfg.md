# Environment-Specific Configurations 🛠️

This document provides details on the environment-specific configurations in the CBS_PYTHON system.

## Environment Types 🌍

The CBS_PYTHON system supports three main environment types:

1. **Development**: For local testing and debugging.
2. **Staging**: For pre-production validation.
3. **Production**: For live deployment.

---

## Configuration Details 📋

| Environment  | Key Configurations                     |
|--------------|---------------------------------------|
| Development  | Debug mode enabled, local database    |
| Staging      | Debug mode disabled, staging database |
| Production   | Debug mode disabled, live database    |

_Last updated: May 23, 2025_

## Configuration Files

Each environment has its own configuration file:

- `development.yaml`: Development environment settings
- `test.yaml`: Test environment settings
- `production.yaml`: Production environment settings

## Common Configuration Categories

### 1. Database Configuration

| Parameter | Development | Test | Production |
|-----------|------------|------|------------|
| Database Type | SQLite | PostgreSQL | PostgreSQL |
| Connection Pooling | Basic | Enhanced | Advanced |
| Auto Migrations | Enabled | Disabled | Disabled |
| Query Logging | Verbose | Errors Only | Errors Only |

Example (development.yaml):
```yaml
database:
  type: sqlite
  name: cbs_dev.db
  pool_size: 5
  log_queries: true
  auto_migrate: true
```

Example (production.yaml):
```yaml
database:
  type: postgresql
  host: ${CBS_DB_HOST}
  port: ${CBS_DB_PORT}
  name: ${CBS_DB_NAME}
  user: ${CBS_DB_USER}
  password: ${CBS_DB_PASSWORD}
  pool_size: 20
  max_overflow: 30
  log_queries: false
  auto_migrate: false
```

### 2. Logging Configuration

| Parameter | Development | Test | Production |
|-----------|------------|------|------------|
| Log Level | DEBUG | INFO | WARNING |
| Log Format | Detailed | Standard | Compact |
| Log Destination | File & Console | File | File & Central |
| Rotation Size | 5MB | 50MB | 100MB |

Example (development.yaml):
```yaml
logging:
  level: DEBUG
  format: detailed
  output:
    - file
    - console
  file_path: logs/cbs.log
  rotation_size_mb: 5
  backup_count: 3
```

### 3. Security Configuration

| Parameter | Development | Test | Production |
|-----------|------------|------|------------|
| JWT Expiry | 24h | 12h | 1h |
| Password Complexity | Basic | Standard | Advanced |
| Rate Limiting | Disabled | Basic | Strict |
| IP Restrictions | None | Basic | Comprehensive |

Example (production.yaml):
```yaml
security:
  jwt_expiry_minutes: 60
  password:
    min_length: 14
    require_special: true
    require_numbers: true
    require_uppercase: true
  rate_limiting:
    enabled: true
    requests_per_minute: 60
  ip_allowlist_enabled: true
```

### 4. Feature Flags

| Feature | Development | Test | Production |
|---------|------------|------|------------|
| UPI Payments | Enabled | Enabled | Enabled |
| Loan Processing | Enabled | Enabled | Enabled |
| AI Recommendations | Enabled | Enabled | Disabled |
| Experimental Features | Enabled | Disabled | Disabled |

Example (development.yaml):
```yaml
features:
  upi_payments: true
  loan_processing: true
  ai_recommendations: true
  experimental: true
```

### 5. External Integrations

| Integration | Development | Test | Production |
|-------------|------------|------|------------|
| Payment Gateway | Sandbox | Test | Production |
| KYC Service | Mock | Test | Production |
| SMS Gateway | Simulated | Test | Production |
| Email Service | Internal | Test | Production |

Example (test.yaml):
```yaml
integrations:
  payment_gateway:
    url: https://test-payments.example.com/api
    api_key: ${CBS_TEST_PAYMENT_API_KEY}
  kyc_service:
    url: https://test-kyc.example.com/verify
    api_key: ${CBS_TEST_KYC_API_KEY}
  sms_gateway:
    url: https://test-sms.example.com/send
    username: ${CBS_TEST_SMS_USERNAME}
    password: ${CBS_TEST_SMS_PASSWORD}
```

## Environment Variables

Environment-specific variables should be set according to the deployment environment.
Create a `.env` file in each environment based on the `.env.example` template.

### Development Environment Variables

```
CBS_ENVIRONMENT=development
CBS_DB_TYPE=sqlite
CBS_DB_NAME=cbs_dev.db
CBS_LOG_LEVEL=DEBUG
```

### Test Environment Variables

```
CBS_ENVIRONMENT=test
CBS_DB_TYPE=postgresql
CBS_DB_HOST=test-db.example.com
CBS_DB_PORT=5432
CBS_DB_NAME=cbs_test
CBS_DB_USER=test_user
CBS_DB_PASSWORD=test_password_here
CBS_LOG_LEVEL=INFO
```

### Production Environment Variables

```
CBS_ENVIRONMENT=production
CBS_DB_TYPE=postgresql
CBS_DB_HOST=prod-db.example.com
CBS_DB_PORT=5432
CBS_DB_NAME=cbs_production
CBS_DB_USER=prod_user
CBS_DB_PASSWORD=strong_prod_password_here
CBS_LOG_LEVEL=WARNING
CBS_JWT_SECRET=very_strong_jwt_secret_key_here
```

## Switching Between Environments

To switch between environments:

1. **Using environment variable**:
   ```bash
   export CBS_ENVIRONMENT=development
   python main.py
   ```

2. **Using command-line argument**:
   ```bash
   python main.py --env development
   ```

3. **For CLI operations**:
   ```bash
   python -m scripts.cli.cbs_cli --env development accounts create-account --customer-id <uuid>
   ```

## Adding a New Environment

To add a new environment (e.g., staging):

1. Create a new configuration file `staging.yaml`
2. Add environment-specific settings
3. Create corresponding secret files in `config/secrets/staging/`
4. Update the environment detection logic in `config.py`

## Debugging Configuration

To view the current active configuration:

```bash
python -m scripts.cli.cbs_cli --show-config
```

This will display the merged configuration from all sources for the current environment.

## Common Issues

1. **Missing Environment Variables**: Check that all required environment variables are set
2. **Configuration Override Issues**: Check the configuration loading order
3. **Secret Management**: Ensure secrets are properly configured
4. **Environment Detection**: Verify that the correct environment is detected

## Related Documentation

- [Configuration System](configuration_system.md)
- [Environment Setup Guide](environment_setup.md)
- [Database Configuration](database_configuration.md)
