# Payments Module API Reference

This document provides a comprehensive reference for the Payments Module API. It details all available services, their inputs, outputs, and usage examples.

## Table of Contents

1. [Payment Processing APIs](#payment-processing-apis)
   - [Process Payment](#process-payment)
   - [Process Refund](#process-refund)
   - [Validate Payment](#validate-payment)
2. [Payment Type-Specific APIs](#payment-type-specific-apis)
   - [Card Payment Processing](#card-payment-processing)
   - [Mobile Payment Processing](#mobile-payment-processing)
3. [Payment Status APIs](#payment-status-apis)
   - [Check Payment Status](#check-payment-status)
   - [Get Transaction History](#get-transaction-history)
4. [Error Handling](#error-handling)
   - [Error Response Format](#error-response-format)
   - [Common Error Codes](#common-error-codes)
5. [Data Types](#data-types)
   - [Payment Data](#payment-data)
   - [Refund Data](#refund-data)
   - [Payment Result](#payment-result)

---

## Payment Processing APIs

### Process Payment

Processes a payment transaction based on the provided payment data.

**Service Name**: `payment.process`

**Input**:
```json
{
  "amount": 100.00,              // Required: Payment amount
  "currency": "USD",             // Required: 3-letter currency code
  "source_account": "ACC123456", // Required: Source account number
  "destination_account": "ACC789012", // Required: Destination account number
  "type": "transfer",            // Optional: Payment type (transfer, card, mobile, cash)
  "description": "Bill payment", // Optional: Payment description
  "reference_id": "PAY12345",    // Optional: Client-generated reference ID
  "timestamp": "2025-05-20T10:15:30Z", // Optional: Client timestamp (ISO format)
  "channel": "web",              // Optional: Payment channel (web, mobile, branch, api)
  "metadata": {                  // Optional: Additional payment data
    "customer_id": "CUST123",
    "invoice_number": "INV456"
  }
}
```

**Output**:
```json
{
  "success": true,                     // Boolean indicating success/failure
  "transaction_id": "TXN987654321",    // Unique transaction identifier
  "confirmation_id": "CNF123456",      // Confirmation ID for user reference
  "status": "completed",               // Status: completed, pending, failed
  "timestamp": "2025-05-20T10:15:35Z", // Server-side timestamp
  "source_account": "ACC123456",       // Source account number
  "destination_account": "ACC789012",  // Destination account number
  "amount": 100.00,                    // Transaction amount
  "currency": "USD",                   // Currency code
  "fees": 0.00,                        // Any transaction fees
  "total": 100.00,                     // Total amount (including fees)
  "metadata": {                        // Additional metadata
    "processing_time_ms": 235
  }
}
```

**Error Responses**:

* Missing required fields:
```json
{
  "success": false,
  "error": {
    "code": "PAYMENT_VALIDATION_ERROR",
    "message": "Missing required field: amount",
    "details": {
      "field": "amount"
    }
  }
}
```

* Insufficient funds:
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_FUNDS",
    "message": "Insufficient funds in source account",
    "details": {
      "account_number": "ACC123456",
      "required_amount": 100.00,
      "available_balance": 75.50,
      "shortfall": 24.50
    }
  }
}
```

**Usage Example**:

```python
from payments.module_interface import get_module_instance

payments = get_module_instance()

payment_data = {
    "amount": 100.00,
    "currency": "USD",
    "source_account": "ACC123456",
    "destination_account": "ACC789012",
    "type": "transfer",
    "description": "Bill payment",
    "reference_id": "PAY12345"
}

result = payments.process_payment(payment_data)

if result.get("success"):
    print(f"Payment successful. Transaction ID: {result.get('transaction_id')}")
else:
    print(f"Payment failed: {result.get('error').get('message')}")
```

### Process Refund

Processes a refund for a previous payment transaction.

**Service Name**: `payment.refund`

**Input**:
```json
{
  "amount": 50.00,                     // Required: Refund amount
  "currency": "USD",                   // Required: 3-letter currency code
  "original_transaction_id": "TXN987654", // Required: Original transaction ID
  "reason": "Customer request",        // Optional: Reason for refund
  "reference_id": "REF12345",          // Optional: Client-generated reference ID
  "timestamp": "2025-05-20T14:30:45Z", // Optional: Client timestamp (ISO format)
  "metadata": {                        // Optional: Additional refund data
    "customer_id": "CUST123",
    "requested_by": "STAFF001"
  }
}
```

**Output**:
```json
{
  "success": true,                     // Boolean indicating success/failure
  "refund_id": "RFD123456789",         // Unique refund identifier
  "original_transaction_id": "TXN987654", // Original transaction ID
  "status": "completed",               // Status: completed, pending, failed
  "timestamp": "2025-05-20T14:30:50Z", // Server-side timestamp
  "amount": 50.00,                     // Refunded amount
  "currency": "USD",                   // Currency code
  "destination_account": "ACC123456",  // Account receiving the refund
  "metadata": {                        // Additional metadata
    "processing_time_ms": 189
  }
}
```

**Error Responses**:

* Original transaction not found:
```json
{
  "success": false,
  "error": {
    "code": "TRANSACTION_NOT_FOUND",
    "message": "Original transaction not found",
    "details": {
      "transaction_id": "TXN987654"
    }
  }
}
```

* Refund amount exceeds original:
```json
{
  "success": false,
  "error": {
    "code": "INVALID_REFUND_AMOUNT",
    "message": "Refund amount exceeds original transaction amount",
    "details": {
      "refund_amount": 150.00,
      "original_amount": 100.00,
      "transaction_id": "TXN987654"
    }
  }
}
```

**Usage Example**:

```python
refund_data = {
    "amount": 50.00,
    "currency": "USD",
    "original_transaction_id": "TXN987654",
    "reason": "Customer request"
}

result = payments.process_refund(refund_data)

if result.get("success"):
    print(f"Refund successful. Refund ID: {result.get('refund_id')}")
else:
    print(f"Refund failed: {result.get('error').get('message')}")
```

### Validate Payment

Validates payment data without processing the actual payment.

**Service Name**: `payment.validate`

**Input**:
Same as [Process Payment](#process-payment)

**Output**:
```json
{
  "valid": true,                    // Boolean indicating validation result
  "validation_id": "VAL123456",     // Validation reference ID
  "timestamp": "2025-05-20T10:14:30Z"
}
```

**Error Response**:
```json
{
  "valid": false,
  "errors": [
    "Missing required field: amount",
    "Invalid account number format"
  ],
  "timestamp": "2025-05-20T10:14:30Z"
}
```

**Usage Example**:

```python
validation_result = payments.validate_payment(payment_data)

if validation_result.get("valid"):
    print("Payment data is valid")
else:
    print(f"Validation errors: {', '.join(validation_result.get('errors'))}")
```

## Payment Type-Specific APIs

### Card Payment Processing

Processes a card payment transaction.

**Service Name**: `payment.card_processor`

**Input**:
```json
{
  "amount": 75.50,                  // Required: Payment amount
  "currency": "USD",                // Required: 3-letter currency code
  "card_number": "4111111111111111", // Required: Card number
  "expiry_month": 12,               // Required: Expiry month (1-12)
  "expiry_year": 2027,              // Required: Expiry year (4-digit)
  "cvv": "123",                     // Required: CVV/security code
  "cardholder_name": "John Doe",    // Required: Cardholder name
  "billing_address": {              // Optional: Billing address
    "street": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "postal_code": "12345",
    "country": "US"
  },
  "description": "Online purchase",  // Optional: Payment description
  "reference_id": "ORDER12345",      // Optional: Client-generated reference
  "metadata": {                      // Optional: Additional payment data
    "customer_id": "CUST123",
    "merchant_id": "MERCH456"
  }
}
```

**Output**:
Same structure as [Process Payment](#process-payment) with additional card-specific fields:
```json
{
  "success": true,
  "transaction_id": "TXN987654321",
  "card_auth_code": "AUTH123456",    // Card authorization code
  "card_type": "visa",               // Card type/brand
  "masked_card_number": "411111******1111", // Masked card number
  "status": "completed",
  "timestamp": "2025-05-20T11:25:35Z",
  "amount": 75.50,
  "currency": "USD",
  "fees": 1.50,                      // Card processing fees
  "total": 77.00
}
```

### Mobile Payment Processing

Processes a mobile payment transaction.

**Service Name**: `payment.mobile_processor`

**Input**:
```json
{
  "amount": 25.00,                   // Required: Payment amount
  "currency": "USD",                 // Required: 3-letter currency code
  "mobile_number": "+15551234567",   // Required: Mobile number
  "payment_method": "mobile_wallet", // Required: mobile_wallet, carrier_billing, etc.
  "wallet_provider": "PayApp",       // Optional: Wallet provider name
  "otp": "123456",                   // Optional: One-time password for verification
  "description": "Mobile purchase",  // Optional: Payment description
  "reference_id": "MOB12345",        // Optional: Client-generated reference
  "metadata": {}                     // Optional: Additional payment data
}
```

**Output**:
Same structure as [Process Payment](#process-payment) with additional mobile-specific fields:
```json
{
  "success": true,
  "transaction_id": "TXN987654321",
  "mobile_confirmation_code": "MOB123456", // Mobile confirmation code
  "wallet_transaction_id": "WALLET987654", // Wallet provider's transaction ID
  "status": "completed",
  "timestamp": "2025-05-20T12:35:35Z",
  "amount": 25.00,
  "currency": "USD"
}
```

## Payment Status APIs

### Check Payment Status

Checks the status of a previously initiated payment.

**Service Name**: `payment.status.check`

**Input**:
```json
{
  "transaction_id": "TXN987654321"   // Required: Transaction ID to check
}
```

**Output**:
```json
{
  "transaction_id": "TXN987654321",
  "status": "completed",              // Status: completed, pending, failed, cancelled
  "timestamp": "2025-05-20T10:15:35Z",
  "last_updated": "2025-05-20T10:15:40Z",
  "amount": 100.00,
  "currency": "USD",
  "source_account": "ACC123456",
  "destination_account": "ACC789012",
  "type": "transfer",
  "description": "Bill payment",
  "additional_info": {                // Optional additional status information
    "clearing_time": "2025-05-20T14:00:00Z",
    "confirmation_id": "CNF123456"
  }
}
```

### Get Transaction History

Retrieves transaction history for a specific account.

**Service Name**: `payment.history.get`

**Input**:
```json
{
  "account_number": "ACC123456",      // Required: Account number
  "start_date": "2025-05-01T00:00:00Z", // Optional: Start date (ISO format)
  "end_date": "2025-05-20T23:59:59Z",   // Optional: End date (ISO format)
  "transaction_type": "all",          // Optional: all, debit, credit, transfer
  "limit": 10,                        // Optional: Maximum number of records
  "offset": 0                         // Optional: Pagination offset
}
```

**Output**:
```json
{
  "account_number": "ACC123456",
  "start_date": "2025-05-01T00:00:00Z",
  "end_date": "2025-05-20T23:59:59Z",
  "transaction_count": 3,             // Total transactions returned
  "total_count": 25,                  // Total available matching the criteria
  "transactions": [
    {
      "transaction_id": "TXN987654321",
      "type": "transfer",
      "amount": 100.00,
      "currency": "USD",
      "direction": "outgoing",
      "counterparty": "ACC789012",
      "description": "Bill payment",
      "timestamp": "2025-05-20T10:15:35Z",
      "status": "completed"
    },
    {
      "transaction_id": "TXN987654320",
      "type": "deposit",
      "amount": 500.00,
      "currency": "USD",
      "direction": "incoming",
      "counterparty": "ATM001",
      "description": "Cash deposit",
      "timestamp": "2025-05-15T14:30:22Z",
      "status": "completed"
    },
    {
      "transaction_id": "TXN987654319",
      "type": "transfer",
      "amount": 75.50,
      "currency": "USD",
      "direction": "outgoing",
      "counterparty": "ACC789013",
      "description": "Rent payment",
      "timestamp": "2025-05-10T09:45:12Z",
      "status": "completed"
    }
  ]
}
```

## Error Handling

### Error Response Format

All error responses follow this standard format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",              // Machine-readable error code
    "message": "Human-readable error message", // User-friendly error message
    "details": {                       // Optional error details
      "field": "field_name",           // Field causing the error (if applicable)
      "value": "invalid_value",        // Invalid value (if applicable)
      "additional_info": "Additional error information"
    },
    "timestamp": "2025-05-20T10:15:35Z" // Error timestamp
  },
  "request_id": "REQ123456789"         // Request identifier for support reference
}
```

### Common Error Codes

| Error Code | Description | HTTP Status |
|------------|-------------|------------|
| `PAYMENT_VALIDATION_ERROR` | Invalid payment data | 400 |
| `INSUFFICIENT_FUNDS` | Insufficient funds in source account | 400 |
| `ACCOUNT_NOT_FOUND` | Account not found | 404 |
| `TRANSACTION_NOT_FOUND` | Transaction not found | 404 |
| `PAYMENT_PROCESSING_ERROR` | Error processing payment | 500 |
| `PROCESSOR_UNAVAILABLE` | Payment processor unavailable | 503 |
| `REFUND_PROCESSING_ERROR` | Error processing refund | 500 |
| `INVALID_REFUND_AMOUNT` | Invalid refund amount | 400 |
| `CARD_PROCESSING_ERROR` | Error processing card payment | 500 |
| `CARD_DECLINED` | Card declined by issuer | 400 |
| `INVALID_CARD` | Invalid card details | 400 |
| `MOBILE_PROCESSING_ERROR` | Error processing mobile payment | 500 |
| `INVALID_MOBILE_NUMBER` | Invalid mobile number | 400 |

## Data Types

### Payment Data

| Field | Type | Required | Description |
|-------|------|----------|------------|
| `amount` | Decimal | Yes | Payment amount |
| `currency` | String | Yes | 3-letter ISO currency code |
| `source_account` | String | Yes | Source account number |
| `destination_account` | String | Yes | Destination account number |
| `type` | String | No | Payment type: transfer, card, mobile, cash |
| `description` | String | No | Payment description |
| `reference_id` | String | No | Client-generated reference ID |
| `timestamp` | String | No | Client timestamp (ISO format) |
| `channel` | String | No | Payment channel: web, mobile, branch, api |
| `metadata` | Object | No | Additional payment data |

### Refund Data

| Field | Type | Required | Description |
|-------|------|----------|------------|
| `amount` | Decimal | Yes | Refund amount |
| `currency` | String | Yes | 3-letter ISO currency code |
| `original_transaction_id` | String | Yes | Original transaction ID |
| `reason` | String | No | Reason for refund |
| `reference_id` | String | No | Client-generated reference ID |
| `timestamp` | String | No | Client timestamp (ISO format) |
| `metadata` | Object | No | Additional refund data |

### Payment Result

| Field | Type | Description |
|-------|------|------------|
| `success` | Boolean | Indicates if operation was successful |
| `transaction_id` | String | Unique transaction identifier |
| `confirmation_id` | String | Confirmation ID for user reference |
| `status` | String | Status: completed, pending, failed |
| `timestamp` | String | Server-side timestamp |
| `source_account` | String | Source account number |
| `destination_account` | String | Destination account number |
| `amount` | Decimal | Transaction amount |
| `currency` | String | Currency code |
| `fees` | Decimal | Any transaction fees |
| `total` | Decimal | Total amount (including fees) |
| `metadata` | Object | Additional metadata |
