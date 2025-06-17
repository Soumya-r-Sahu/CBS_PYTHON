# CBS_PYTHON V2.0 API Documentation

## Overview
The CBS_PYTHON V2.0 platform provides a comprehensive RESTful API for core banking operations. This document outlines all available endpoints across the 8 microservices.

## Architecture
- **API Gateway**: Central entry point routing requests to microservices
- **Authentication**: JWT-based with role-based access control
- **Rate Limiting**: Configurable limits per endpoint and user
- **Monitoring**: Prometheus metrics and health checks

## Base URLs
- **Production**: `https://api.cbs-platform.com`
- **Development**: `http://localhost:8000`

## Authentication
All API requests require authentication via JWT tokens:

```bash
curl -H "Authorization: Bearer <jwt_token>" https://api.cbs-platform.com/api/v2/customers
```

### Get Authentication Token
```bash
POST /api/v2/auth/login
Content-Type: application/json

{
  "username": "user@bank.com",
  "password": "password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Services Overview

| Service | Port | Base Path | Description |
|---------|------|-----------|-------------|
| Gateway | 8000 | `/api/v2/` | Main API entry point |
| Customer | 8001 | `/api/v2/customers` | Customer management |
| Account | 8002 | `/api/v2/accounts` | Account operations |
| Transaction | 8003 | `/api/v2/transactions` | Transaction processing |
| Payment | 8004 | `/api/v2/payments` | Payment services |
| Loan | 8005 | `/api/v2/loans` | Loan management |
| Notification | 8006 | `/api/v2/notifications` | Messaging services |
| Audit | 8007 | `/api/v2/audit` | Audit and compliance |

---

## 1. Customer Service API

### Create Customer
```bash
POST /api/v2/customers
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@email.com",
  "phone": "+1234567890",
  "date_of_birth": "1990-01-01",
  "address": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "USA"
  },
  "identity_documents": [
    {
      "type": "passport",
      "number": "A12345678",
      "expiry_date": "2030-12-31"
    }
  ]
}
```

### Get Customer
```bash
GET /api/v2/customers/{customer_id}
```

### List Customers
```bash
GET /api/v2/customers?skip=0&limit=100&status=active
```

---

## 2. Account Service API

### Create Account
```bash
POST /api/v2/accounts
Content-Type: application/json

{
  "customer_id": "customer_123",
  "account_type": "savings",
  "currency": "USD",
  "initial_deposit": 1000.00,
  "branch_code": "NYC001"
}
```

### Get Account Balance
```bash
GET /api/v2/accounts/{account_id}/balance
```

### Account Statement
```bash
GET /api/v2/accounts/{account_id}/statement?start_date=2024-01-01&end_date=2024-12-31
```

---

## 3. Transaction Service API

### Create Transaction
```bash
POST /api/v2/transactions
Content-Type: application/json

{
  "from_account_id": "acc_123",
  "to_account_id": "acc_456", 
  "amount": 500.00,
  "currency": "USD",
  "transaction_type": "transfer",
  "description": "Monthly transfer",
  "reference_number": "TXN001"
}
```

### Get Transaction
```bash
GET /api/v2/transactions/{transaction_id}
```

### Transaction History
```bash
GET /api/v2/transactions?account_id=acc_123&start_date=2024-01-01&limit=50
```

---

## 4. Payment Service API

### Process Payment
```bash
POST /api/v2/payments
Content-Type: application/json

{
  "payer_account_id": "acc_123",
  "payee_account_id": "acc_456",
  "amount": 1000.00,
  "currency": "USD",
  "payment_method": "bank_transfer",
  "description": "Invoice payment",
  "scheduled_date": "2024-06-20"
}
```

### Payment Status
```bash
GET /api/v2/payments/{payment_id}/status
```

---

## 5. Loan Service API

### Apply for Loan
```bash
POST /api/v2/loans/applications
Content-Type: application/json

{
  "customer_id": "customer_123",
  "loan_type": "personal",
  "loan_purpose": "Home renovation",
  "requested_amount": 50000.00,
  "tenure_months": 24,
  "primary_account_id": "acc_123",
  "monthly_income": 5000.00,
  "employment_type": "salaried"
}
```

### Approve Loan
```bash
POST /api/v2/loans/applications/{application_id}/approve
Content-Type: application/json

{
  "approved_amount": 45000.00,
  "approved_tenure_months": 24,
  "interest_rate": 12.5,
  "approver_id": "officer_123"
}
```

### EMI Calculator
```bash
POST /api/v2/loans/calculate/emi
Content-Type: application/json

{
  "principal_amount": 50000.00,
  "interest_rate": 12.5,
  "tenure_months": 24,
  "loan_type": "personal"
}
```

### EMI Schedule
```bash
GET /api/v2/loans/{loan_id}/schedule
```

---

## 6. Notification Service API

### Send Notification
```bash
POST /api/v2/notifications
Content-Type: application/json

{
  "recipient_id": "customer_123",
  "notification_type": "transaction_alert",
  "channels": ["email", "sms"],
  "priority": "high",
  "content": {
    "subject": "Transaction Alert",
    "message": "Your account has been debited with $500",
    "data": {
      "transaction_id": "txn_123",
      "amount": 500.00
    }
  }
}
```

### Notification History
```bash
GET /api/v2/notifications?recipient_id=customer_123&limit=50
```

---

## 7. Audit Service API

### Query Audit Logs
```bash
GET /api/v2/audit/logs?service=customer-service&start_date=2024-01-01&limit=100
```

### Security Events
```bash
GET /api/v2/audit/security-events?severity=high&limit=50
```

### Compliance Report
```bash
GET /api/v2/audit/compliance/reports?report_type=transaction_monitoring&date=2024-06-01
```

---

## Error Handling

### Standard Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": [
      {
        "field": "email",
        "message": "Invalid email format"
      }
    ],
    "timestamp": "2024-06-17T10:30:00Z",
    "request_id": "req_123456"
  }
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

---

## Rate Limits
- **Default**: 1000 requests per hour per user
- **Burst**: 100 requests per minute
- **Admin**: 5000 requests per hour

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1624810800
```

---

## Webhooks

### Register Webhook
```bash
POST /api/v2/webhooks
Content-Type: application/json

{
  "url": "https://your-app.com/webhook",
  "events": ["transaction.created", "payment.completed"],
  "secret": "webhook_secret_key"
}
```

### Webhook Payload Example
```json
{
  "id": "evt_123",
  "event": "transaction.created",
  "data": {
    "transaction_id": "txn_123",
    "amount": 500.00,
    "status": "completed"
  },
  "timestamp": "2024-06-17T10:30:00Z"
}
```

---

## SDK Examples

### Python SDK
```python
from cbs_platform import CBSClient

client = CBSClient(
    base_url="https://api.cbs-platform.com",
    api_key="your_api_key"
)

# Create customer
customer = client.customers.create({
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@email.com"
})

# Create account
account = client.accounts.create({
    "customer_id": customer.id,
    "account_type": "savings"
})
```

### JavaScript SDK
```javascript
import { CBSClient } from '@cbs-platform/sdk';

const client = new CBSClient({
    baseUrl: 'https://api.cbs-platform.com',
    apiKey: 'your_api_key'
});

// Process payment
const payment = await client.payments.create({
    amount: 1000.00,
    currency: 'USD',
    payerAccountId: 'acc_123'
});
```

---

## Testing

### Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "customer-service": "healthy",
    "account-service": "healthy", 
    "transaction-service": "healthy",
    "payment-service": "healthy",
    "loan-service": "healthy",
    "notification-service": "healthy",
    "audit-service": "healthy"
  },
  "timestamp": "2024-06-17T10:30:00Z"
}
```

### API Versions
```bash
GET /api/versions
```

---

## Support

- **Documentation**: https://docs.cbs-platform.com
- **API Reference**: https://api.cbs-platform.com/docs
- **Support**: support@cbs-platform.com
- **Status Page**: https://status.cbs-platform.com

## Changelog

### v2.0.0 (Latest)
- Complete microservices architecture
- Enhanced security and monitoring
- Comprehensive loan management
- Advanced notification system
- Real-time audit and compliance

---

*Last Updated: June 17, 2025*
