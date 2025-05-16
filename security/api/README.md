# API Security

This directory contains components for securing API endpoints and handling API security concerns.

## Components

- `api_gateway.py` - Security gateway for API endpoints
- `middleware/` - API security middleware components
  - `auth_middleware.py` - Authentication middleware for API requests
  - `validation_middleware.py` - Request validation and sanitization
  - `rate_limit.py` - API rate limiting for abuse prevention
  - `security_headers.py` - Security HTTP headers implementation
  - `cors_middleware.py` - Cross-Origin Resource Sharing protection
  - `xss_protection.py` - Cross-Site Scripting protection
  - `csp_manager.py` - Content Security Policy management
  - `api_security.py` - API-specific security measures

## Usage

```python
# Using the API gateway
from security.api.api_gateway import secure_api_endpoint

@secure_api_endpoint(requires_auth=True, rate_limit="10/minute")
def sensitive_api_function():
    # Function implementation
    pass

# Using middleware (Flask example)
from security.api.middleware.auth_middleware import jwt_required
from security.api.middleware.rate_limit import rate_limited

@app.route('/api/sensitive-data')
@jwt_required
@rate_limited(limit=10, period=60)  # 10 requests per 60 seconds
def get_sensitive_data():
    # Endpoint implementation
    return jsonify({"data": "sensitive information"})
```

## Security Features

1. Authentication and authorization for API endpoints
2. Input validation and sanitization
3. Rate limiting to prevent abuse
4. Security headers for browser security
5. CORS protection
6. XSS protection
7. Content Security Policy implementation
