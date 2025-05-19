# API Standards

This document outlines the API standards used in the Core Banking System.

## RESTful API Design

All APIs in the Core Banking System follow RESTful design principles:

1. **Resource-Oriented**: APIs are organized around resources
2. **HTTP Methods**: Use standard HTTP methods (GET, POST, PUT, DELETE)
3. **URL Structure**: Use clear, hierarchical URL structures
4. **Status Codes**: Use appropriate HTTP status codes

## Authentication & Authorization

- All APIs require authentication using OAuth 2.0
- JWT tokens are used for session management
- Role-based access control (RBAC) determines permissions

## Request & Response Format

All APIs use JSON for request and response formats:

```json
{
  "status": "success",
  "data": {
    "accountId": "12345-0101-829173-42",
    "balance": 5000.75,
    "currency": "USD"
  }
}
```

Error responses follow a consistent format:

```json
{
  "status": "error",
  "errorCode": "ACCOUNT_NOT_FOUND",
  "message": "The specified account could not be found",
  "requestId": "1234-5678-90ab-cdef"
}
```

## Versioning

API versioning is handled through the URL path:

```
/api/v1/accounts
/api/v2/accounts
```

Last updated: May 19, 2025
