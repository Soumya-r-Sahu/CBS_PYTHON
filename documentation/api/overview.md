# API Overview 🌐

This document provides an overview of the APIs available in CBS_PYTHON.

## Available APIs 📋

| API Name       | Description                     |
|----------------|---------------------------------|
| **Core Banking** | Handles accounts and transactions |
| **Digital Channels** | Provides internet and mobile banking |
| **Admin Module** | Centralized control and monitoring |

_Last updated: May 23, 2025_

## API Overview

The CBS_PYTHON system offers RESTful APIs for various banking operations, implementing Clean Architecture principles. The APIs are organized by banking modules:

- Accounts API
- Customer Management API
- Loans API
- Transactions API
- Payments API
- UPI API

## General API Information

- **Base URL**: `/api/v1`
- **Content-Type**: `application/json`
- **Authentication**: JWT Bearer token
- **Versioning**: URL-based versioning (e.g., `/api/v1`, `/api/v2`)

## Authentication

All API endpoints (except for public endpoints) require authentication using a JWT Bearer token:

```
Authorization: Bearer <token>
```

Tokens can be obtained through the authentication endpoint:

```
POST /api/v1/auth/login
```

## Error Handling

All APIs follow a standard error response format:

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { /* Additional error details */ }
  }
}
```

### Common Error Codes

| Code                  | Description                                    |
|-----------------------|------------------------------------------------|
| `VALIDATION_ERROR`    | Invalid input parameters                       |
| `AUTHENTICATION_ERROR`| Authentication failed                          |
| `AUTHORIZATION_ERROR` | Permission denied                              |
| `RESOURCE_NOT_FOUND`  | Requested resource not found                   |
| `INTERNAL_ERROR`      | Server-side error                              |
| `BUSINESS_RULE_ERROR` | Operation violates business rules              |

## Rate Limiting

API calls are subject to rate limiting:

- 100 requests per minute per API key for standard operations
- 1000 requests per minute per API key for read-only operations
- Rate limit headers are included in responses

## Endpoints

### Accounts API

| Endpoint                     | Method | Description                           |
|------------------------------|--------|---------------------------------------|
| `/api/v1/accounts`           | GET    | List all accounts (with pagination)   |
| `/api/v1/accounts`           | POST   | Create a new account                  |
| `/api/v1/accounts/{id}`      | GET    | Get account details                   |
| `/api/v1/accounts/{id}`      | PUT    | Update account                        |
| `/api/v1/accounts/{id}`      | DELETE | Close account                         |
| `/api/v1/accounts/{id}/deposit` | POST | Deposit funds to account            |
| `/api/v1/accounts/{id}/withdraw` | POST | Withdraw funds from account        |
| `/api/v1/accounts/{id}/transfer` | POST | Transfer funds between accounts    |
| `/api/v1/accounts/{id}/statement` | GET | Get account statement              |

### Customer Management API

| Endpoint                     | Method | Description                           |
|------------------------------|--------|---------------------------------------|
| `/api/v1/customers`          | GET    | List all customers (with pagination)  |
| `/api/v1/customers`          | POST   | Create a new customer                 |
| `/api/v1/customers/{id}`     | GET    | Get customer details                  |
| `/api/v1/customers/{id}`     | PUT    | Update customer                       |
| `/api/v1/customers/{id}`     | DELETE | Delete customer                       |
| `/api/v1/customers/{id}/accounts` | GET | Get customer's accounts            |
| `/api/v1/customers/{id}/kyc`  | GET   | Get customer KYC details             |
| `/api/v1/customers/{id}/kyc`  | POST  | Submit customer KYC documents        |

### Loans API

| Endpoint                     | Method | Description                           |
|------------------------------|--------|---------------------------------------|
| `/api/v1/loans`              | GET    | List all loans (with pagination)      |
| `/api/v1/loans`              | POST   | Create a new loan application         |
| `/api/v1/loans/{id}`         | GET    | Get loan details                      |
| `/api/v1/loans/{id}`         | PUT    | Update loan                           |
| `/api/v1/loans/{id}/repayment` | POST | Make loan repayment                  |
| `/api/v1/loans/{id}/schedule` | GET   | Get loan repayment schedule          |
| `/api/v1/loans/calculator`   | POST   | Calculate loan EMI                    |

## Sample API Calls

### Create Account

**Request:**
```http
POST /api/v1/accounts HTTP/1.1
Content-Type: application/json
Authorization: Bearer <token>

{
  "customer_id": "123e4567-e89b-12d3-a456-426614174000",
  "account_type": "SAVINGS",
  "initial_deposit": 5000.00,
  "currency": "INR"
}
```

**Response:**
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "status": "success",
  "data": {
    "account_id": "456e4567-e89b-12d3-a456-426614174000",
    "account_number": "SAVAC1234567890",
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "account_type": "SAVINGS",
    "balance": 5000.00,
    "currency": "INR",
    "status": "ACTIVE",
    "created_at": "2025-05-17T08:30:00Z"
  }
}
```

### Get Account Details

**Request:**
```http
GET /api/v1/accounts/456e4567-e89b-12d3-a456-426614174000 HTTP/1.1
Authorization: Bearer <token>
```

**Response:**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "data": {
    "account_id": "456e4567-e89b-12d3-a456-426614174000",
    "account_number": "SAVAC1234567890",
    "customer_id": "123e4567-e89b-12d3-a456-426614174000",
    "account_type": "SAVINGS",
    "balance": 5000.00,
    "currency": "INR",
    "status": "ACTIVE",
    "created_at": "2025-05-17T08:30:00Z",
    "last_updated_at": "2025-05-17T08:30:00Z"
  }
}
```

## API Documentation Tools

Full API documentation with detailed request/response schemas is available using:

1. **OpenAPI/Swagger**: Available at `/api/v1/docs` when running the system
2. **Postman Collection**: Available in the `documentation/api/postman` directory

## API Versioning Policy

1. **URL Path Versioning**: `/api/v1/`, `/api/v2/`
2. **Backward Compatibility**: New versions maintain backward compatibility when possible
3. **Deprecation Notices**: APIs are marked as deprecated at least 6 months before removal
4. **Version Lifespan**: Each API version is supported for at least 18 months

## Related Documentation

- [API Security Guide](api_security.md)
- [API Best Practices](api_best_practices.md)
- [API Integration Examples](api_integration_examples.md)
