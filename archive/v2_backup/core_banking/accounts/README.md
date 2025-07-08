# Core Banking System - Accounts Module

This module provides account management functionality for the Core Banking System using Clean Architecture principles.

## Overview

The Accounts module is designed following the Clean Architecture pattern, which ensures separation of concerns and testability. The architecture is divided into four layers:

1. **Domain Layer** - Contains business entities and business rules
2. **Application Layer** - Contains use cases that orchestrate the flow of data
3. **Infrastructure Layer** - Contains implementations of interfaces defined in the application layer
4. **Presentation Layer** - Contains UI components that present information to users

## Directory Structure

```
accounts/
├── domain/                # Core business logic and entities
├── application/           # Use cases and service interfaces
├── infrastructure/        # External concerns implementation
├── presentation/          # UI layers (API, CLI, GUI)
├── di_container.py        # Dependency injection container
├── integration.py         # Integration with main application
├── CLEAN_ARCHITECTURE_IMPLEMENTATION.md  # Implementation details
└── README.md              # This file
```

## Features

- Account creation and management
- Deposit and withdrawal transactions
- Account balance inquiries
- Transaction history
- Support for different account types
- Notification system for account activities
- Available via API, CLI, and GUI interfaces

## Clean Architecture Benefits

- **Independence of frameworks** - The core business logic does not depend on external frameworks
- **Testability** - Each layer can be tested independently
- **Independence of UI** - The UI can be changed without affecting the business rules
- **Independence of database** - The database can be changed without affecting the business logic
- **Independence of external agencies** - The business rules don't know anything about the outside world

## Usage

### API Usage

```python
from flask import Flask
from core_banking.accounts.integration import register_with_flask, initialize_accounts_module

# Initialize the module
initialize_accounts_module()

# Create a Flask app
app = Flask(__name__)

# Register the accounts API
register_with_flask(app)

# Run the app
app.run()
```

### CLI Usage

```bash
# Run the CLI directly
python -m core_banking.accounts.presentation.cli.accounts_cli create-account --customer-id 123e4567-e89b-12d3-a456-426614174000 --account-type SAVINGS --initial-deposit 5000

# Or use the integration script
python -m core_banking.accounts.integration --mode cli
```

### GUI Usage

```bash
# Run the GUI directly
python -m core_banking.accounts.presentation.gui.accounts_gui

# Or use the integration script
python -m core_banking.accounts.integration --mode gui
```

### Programmatic Usage

```python
from core_banking.accounts.integration import get_account_service, initialize_accounts_module
from decimal import Decimal
from uuid import UUID

# Initialize the module
initialize_accounts_module()

# Get the account service
account_service = get_account_service()

# Create an account
result = account_service.create_account(
    customer_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
    account_type="SAVINGS",
    initial_deposit=Decimal("5000.00"),
    currency="INR"
)
print(f"Created account: {result['account_number']}")

# Deposit funds
deposit_result = account_service.deposit(
    account_id=UUID(result['account_id']),
    amount=Decimal("1000.00"),
    description="Salary deposit"
)
print(f"New balance: {deposit_result['balance']}")
```

## Configuration

The module can be configured through the dependency injection container:

```python
from core_banking.accounts.integration import initialize_accounts_module

# Configure the module
config = {
    "interest": {
        "base_rate": "3.5",
        "premium_rate": "4.5"
    },
    "account": {
        "min_balance": "1000.0",
        "withdrawal_limit": "50000.0"
    },
    "notifications": {
        "default_channel": "email"  # or "sms"
    }
}

# Initialize with custom configuration
initialize_accounts_module(config=config)
```

## Testing

Each layer has its own testing strategy:

### Domain Layer Tests

```bash
pytest core_banking/accounts/tests/domain/
```

### Application Layer Tests

```bash
pytest core_banking/accounts/tests/application/
```

### Infrastructure Layer Tests

```bash
pytest core_banking/accounts/tests/infrastructure/
```

### Presentation Layer Tests

```bash
pytest core_banking/accounts/tests/presentation/
```

## Implementation Details

For more information about the Clean Architecture implementation, see [CLEAN_ARCHITECTURE_IMPLEMENTATION.md](CLEAN_ARCHITECTURE_IMPLEMENTATION.md).
