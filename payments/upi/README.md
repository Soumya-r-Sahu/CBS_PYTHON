# UPI Payment Module

This module implements the UPI (Unified Payments Interface) payment processing system within the CBS_PYTHON banking system using Clean Architecture principles.

## Overview

The UPI module allows for real-time payment processing using the NPCI (National Payments Corporation of India) UPI interface. It supports:

- UPI Transaction Processing
- VPA (Virtual Payment Address) Management
- QR Code Generation and Scanning
- Transaction Reconciliation
- Fraud Detection and Analysis
- Real-time Notifications

## Clean Architecture Implementation

This module follows the Clean Architecture pattern with four distinct layers:

### 1. Domain Layer ✅ Complete

The core business logic, rules, and entities.

- **Entities**:
  - `UpiTransaction`: Represents a UPI payment transaction
  - `VirtualPaymentAddress`: Value object for UPI addresses

- **Domain Services**:
  - `TransactionRulesService`: Implements business rules for transactions
  - `VpaValidationService`: Validates virtual payment addresses

- **Exceptions**:
  - Gateway-related exceptions for error handling

### 2. Application Layer ✅ Complete

Orchestrates the flow of data and coordinates domain operations.

- **Use Cases**:
  - `SendMoneyUseCase`: Handles money transfer between accounts
  - `CompleteTransactionUseCase`: Processes transaction completion

- **Interfaces**:
  - `UpiTransactionRepositoryInterface`: For data persistence
  - `NotificationServiceInterface`: For alerting users
  - `ExternalPaymentGatewayInterface`: For NPCI gateway integration

### 3. Infrastructure Layer ✅ Complete

External services, data access, and technical implementations.

- **Repositories**:
  - `SqlUpiTransactionRepository`: SQLite implementation for transaction data

- **Services**:
  - `SmsNotificationService`: Sends SMS notifications
  - `EmailNotificationService`: Sends email notifications
  - `NpciGatewayService`: Integrates with NPCI payment gateway
  - `TransactionReconciliationService`: Reconciles pending transactions
  - `FraudDetectionService`: Detects potentially fraudulent transactions

### 4. Presentation Layer ✅ Complete

Handles user interactions through various interfaces.

- **API**:
  - `UpiController`: REST API endpoints for UPI operations
  - Supports transaction processing, status checking, reconciliation, and fraud analysis

- **CLI**:
  - `UpiCli`: Command-line interface for UPI operations

## Key Files

- `main.py`: Entry point that supports both legacy and Clean Architecture implementations
- `main_clean_architecture.py`: Clean Architecture specific implementation
- `di_container.py`: Dependency Injection container for wiring components
- `changelog.txt`: Detailed record of implementation changes

## Usage

### API Endpoints

```
POST /api/upi/send-money
    - Send money using UPI

POST /api/upi/complete-transaction
    - Complete a pending UPI transaction

GET /api/upi/transaction/{transaction_id}
    - Get transaction details

POST /api/upi/reconcile
    - Reconcile pending transactions

GET /api/upi/fraud-analysis/{transaction_id}
    - Get fraud analysis for a transaction
```

### CLI Commands

```
send-money --from <vpa> --to <vpa> --amount <amount>
    - Send money from one VPA to another

check-status --transaction-id <transaction_id>
    - Check transaction status

register-vpa --vpa <vpa> --account <account_number>
    - Register a new VPA
```

### Code Examples

```python
# Using the UPI module in Clean Architecture mode
from payments.upi.main_clean_architecture import create_app, initialize_module

# Initialize the module
init_status = initialize_module()
print(f"UPI module initialization: {init_status}")

# Create the Flask app
app = create_app()
```

## Configuration

Configuration is managed through the `get_config()` function in `main_clean_architecture.py` or through the `UpiConfig` class in the legacy implementation.

Key configuration parameters:

- `daily_transaction_limit`: Maximum allowed transaction amount per day
- `per_transaction_limit`: Maximum amount per transaction
- `db_path`: Path to the SQLite database
- `notification_type`: Type of notification (SMS or email)
- `ENVIRONMENT`: Deployment environment (development, testing, production)
- `USE_MOCK`: Whether to use mock services for testing

## Testing

Run the tests using:

```bash
pytest payments/upi/tests/
```

## Transition to Clean Architecture

This module supports both legacy and Clean Architecture implementations. To use the Clean Architecture version, set the environment variable:

```bash
$env:USE_CLEAN_ARCHITECTURE = "true"
```

To use the legacy implementation:

```bash
$env:USE_CLEAN_ARCHITECTURE = "false"
```

## Recent Updates

- Fixed undefined variables in main.py
- Added missing controller imports
- Implemented proper UpiConfig initialization
- Enhanced error handling and logging
- Integrated with Clean Architecture framework

## Advanced Features

The UPI module includes several powerful features that extend beyond basic transaction processing:

### Fraud Detection System

The module includes a comprehensive fraud detection system that:
- Analyzes transaction patterns for suspicious activity using rule-based logic
- Applies risk scoring based on multiple factors (transaction amount, velocity, receiver VPA)
- Identifies unusual transaction amounts compared to user history
- Detects suspicious patterns like test-then-large transactions
- Generates daily fraud reports with suspicious transaction details
- Provides risk levels (Low, Medium, High) with recommended actions

### Transaction Reconciliation

Automatic reconciliation of transactions ensures consistency between systems:
- Reconciles pending transactions with NPCI gateway status
- Resolves inconsistencies between local and gateway transaction states
- Generates daily summary reports with transaction statistics
- Detects and flags suspicious activities in the reconciliation process
- Automatically resolves long-pending transactions based on configurable rules

### NPCI Gateway Integration

Robust integration with the National Payments Corporation of India (NPCI) gateway:
- Handles transaction processing through standardized NPCI UPI API
- Manages connection timeouts, errors, and retries
- Provides detailed error handling with specific exception types
- Supports transaction verification with gateway
- Includes mock mode for development and testing

### Notification Services

Flexible notification system for transaction alerts:
- Configurable SMS and email notifications
- Contextual messages based on transaction status
- Recipient address mapping from VPA to phone/email
- Template-based message formatting

## Next Steps

- Complete Infrastructure layer implementation
- Finalize Presentation layer controllers
- Implement transaction reconciliation
- Add advanced fraud detection
- Integrate with UPI 2.0 features

## Dependencies

- Core Banking - Accounts module
- Integration Interfaces - API module
- Security module for authentication
