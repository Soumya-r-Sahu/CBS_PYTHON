# Core Banking System - Mobile Banking API Documentation

## Overview

The Mobile Banking API provides secure access to core banking services, enabling mobile applications to perform banking transactions, account management, card operations, UPI transactions, and more. The API follows RESTful principles with JSON request/response format and JWT-based authentication.

## API Structure

- `/api/v1/auth` - Authentication endpoints
- `/api/v1/accounts` - Account management endpoints
- `/api/v1/cards` - Card management endpoints
- `/api/v1/transactions` - Transaction endpoints
- `/api/v1/upi` - UPI transaction endpoints
- `/api/v1/customers` - Customer profile management endpoints

## Authentication

All API requests (except login) require a valid JWT token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

### Authentication Endpoints

- `POST /api/v1/auth/login` - User login with password
- `POST /api/v1/auth/login/mpin` - User login with MPIN
- `POST /api/v1/auth/mpin/setup` - Set up MPIN
- `POST /api/v1/auth/mpin/validate` - Validate MPIN
- `POST /api/v1/auth/password/change` - Change password
- `POST /api/v1/auth/password/forgot` - Initiate forgot password flow
- `POST /api/v1/auth/otp/verify` - Verify OTP

## Account Management

### Account Endpoints

- `GET /api/v1/accounts` - List customer accounts
- `GET /api/v1/accounts/{account_number}` - Get account details
- `GET /api/v1/accounts/{account_number}/balance` - Get account balance
- `POST /api/v1/accounts/{account_number}/statement` - Request account statement
- `POST /api/v1/accounts/link` - Link multiple accounts
- `PUT /api/v1/accounts/{account_number}/limits` - Update account limits

## Card Management

### Card Endpoints

- `POST /api/v1/cards/activate` - Activate a new card
- `POST /api/v1/cards/pin/set` - Set card PIN
- `POST /api/v1/cards/pin/change` - Change card PIN
- `POST /api/v1/cards/block` - Block a card
- `PUT /api/v1/cards/limits/update` - Update card usage limits
- `GET /api/v1/cards` - List customer cards

## Transaction Management

### Transaction Endpoints

- `POST /api/v1/transactions/transfer` - Fund transfer
- `GET /api/v1/transactions/history/{account_number}` - Get transaction history
- `GET /api/v1/transactions/{transaction_id}` - Get transaction details
- `POST /api/v1/transactions/recurring` - Set up recurring transfers
- `POST /api/v1/transactions/cheque/stop` - Request stop cheque

## UPI Transactions

### UPI Endpoints

- `POST /api/v1/upi/register` - Register UPI ID
- `POST /api/v1/upi/transaction` - Make UPI payment
- `POST /api/v1/upi/balance` - Check UPI account balance
- `POST /api/v1/upi/pin/change` - Change UPI PIN
- `POST /api/v1/upi/qr/generate` - Generate QR code for payment
- `GET /api/v1/upi/transactions/history` - Get UPI transaction history

## Customer Profile Management

### Customer Endpoints

- `GET /api/v1/customers/profile` - Get customer profile
- `PUT /api/v1/customers/profile/update` - Update customer profile
- `PUT /api/v1/customers/contact/update` - Update contact details
- `PUT /api/v1/customers/notifications/preferences` - Update notification preferences

## Security Features

1. **JWT-based Authentication**: Secure token-based authentication with configurable expiration
2. **Rate Limiting**: Prevents brute force and DoS attacks
3. **PIN Encryption**: Secure PIN storage using salted hashing
4. **Input Validation**: All request data validated using schemas
5. **Error Handling**: Standardized error responses without revealing system details
6. **Audit Logging**: Comprehensive logging of all security events

## Response Format

All API responses follow a consistent format:

### Success Response (200 OK)

```json
{
    "status": "SUCCESS",
    "message": "Operation completed successfully",
    "data": {
        // Response data specific to each endpoint
    }
}
```

### Error Response (4XX, 5XX)

```json
{
    "status": "FAILED",
    "message": "Error description",
    "errors": {
        // Detailed error information (optional)
    },
    "error_code": "ERROR_CODE" // Optional error code
}
```

## API Versioning

The API uses URI versioning (e.g., `/api/v1/`) to support backward compatibility as the API evolves.

## Rate Limiting

To protect the API from abuse, rate limiting is applied to all endpoints. The specific limits vary by endpoint based on sensitivity and resource requirements. Rate limit information is provided in response headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1589458415
```

## Dependencies

- Flask 2.2.3
- Flask-Cors 3.0.10
- PyJWT 2.6.0
- Marshmallow 3.19.0
- MySQL Connector Python 8.0.32

## Setup Instructions

1. Install dependencies: `pip install -r requirements-api.txt`
2. Set environment variables in `.env`
3. Initialize database with proper schema
4. Run the API server: `python -m app.api.app`
