# Loans Module

This module implements loan management functionality for the Core Banking System using Clean Architecture principles.

## Overview

The Loans module handles all loan-related operations, including:

- Loan application processing
- Loan approval/denial workflows
- Loan disbursement
- EMI calculation and repayment scheduling
- Loan portfolio management

## Architecture

This module follows Clean Architecture principles with four main layers:

1. **Domain Layer**: Core business entities and rules
2. **Application Layer**: Use cases and orchestration
3. **Infrastructure Layer**: External services and persistence
4. **Presentation Layer**: User interfaces (CLI, API)

### Directory Structure

```
core_banking/loans/
├── __init__.py
├── CLEAN_ARCHITECTURE_PROGRESS.md
├── di_container.py              # Dependency injection container
├── domain/                      # Domain layer
│   ├── __init__.py
│   ├── entities/                # Domain entities
│   │   ├── __init__.py
│   │   └── loan.py              # Loan entity and value objects
│   └── services/                # Domain services
│       ├── __init__.py
│       └── loan_rules_service.py # Business rules
├── application/                 # Application layer
│   ├── __init__.py
│   ├── interfaces/              # Repository and service interfaces
│   │   ├── __init__.py
│   │   ├── document_storage_interface.py
│   │   ├── loan_repository_interface.py
│   │   └── notification_service_interface.py
│   ├── services/                # Application services
│   │   ├── __init__.py
│   │   └── loan_calculator_service.py
│   └── use_cases/               # Business use cases
│       ├── __init__.py
│       ├── loan_application_use_case.py
│       ├── loan_approval_use_case.py
│       └── loan_disbursement_use_case.py
├── infrastructure/              # Infrastructure layer
│   ├── __init__.py
│   ├── repositories/            # Repository implementations
│   │   ├── __init__.py
│   │   └── sql_loan_repository.py
│   └── services/                # Service implementations
│       ├── __init__.py
│       ├── email_notification_service.py
│       ├── file_system_document_storage.py
│       └── sms_notification_service.py
└── presentation/                # Presentation layer
    ├── __init__.py
    ├── api/                     # REST API
    │   ├── __init__.py
    │   └── loan_endpoints.py
    └── cli/                     # Command-line interface
        ├── __init__.py
        └── loan_commands.py
```

## Usage

### Using the Command-Line Interface

The module provides a CLI interface with the following commands:

#### Apply for a loan

```bash
python -m core_banking.loans.presentation.cli.loan_commands apply \
  --customer-id "C12345" \
  --loan-type "personal" \
  --amount 10000 \
  --term-months 12 \
  --interest-rate 12.5 \
  --repayment-frequency "monthly" \
  --purpose "Home renovation"
```

#### Approve a loan

```bash
python -m core_banking.loans.presentation.cli.loan_commands approve \
  --loan-id "L789012" \
  --approved-by "E456" \
  --notes "Approved based on good credit score"
```

#### Deny a loan

```bash
python -m core_banking.loans.presentation.cli.loan_commands deny \
  --loan-id "L789012" \
  --denied-by "E456" \
  --reason "Insufficient income" \
  --notes "Monthly expenses too high relative to income"
```

#### Disburse a loan

```bash
python -m core_banking.loans.presentation.cli.loan_commands disburse \
  --loan-id "L789012" \
  --disbursed-by "E456" \
  --account-number "SA1000123456" \
  --reference-number "DISB-123"
```

#### List loans

```bash
python -m core_banking.loans.presentation.cli.loan_commands list \
  --customer-id "C12345" \
  --status "active" \
  --limit 10
```

#### Loan calculator

```bash
python -m core_banking.loans.presentation.cli.loan_commands calculator \
  --amount 10000 \
  --interest-rate 12.5 \
  --term-months 24
```

### Using the REST API

The module provides a REST API with the following endpoints:

- `POST /api/loans/apply` - Submit a new loan application
- `POST /api/loans/{loan_id}/approve` - Approve a loan application
- `POST /api/loans/{loan_id}/deny` - Deny a loan application
- `POST /api/loans/{loan_id}/disburse` - Disburse an approved loan
- `GET /api/loans/{loan_id}` - Get loan details by ID
- `GET /api/loans/` - List loans with optional filtering
- `POST /api/loans/calculator` - Calculate loan EMI and payment details

## Integration

### Programmatic Usage

You can also use the module programmatically by importing the use cases:

```python
from core_banking.loans import (
    LoanApplicationUseCase,
    LoanApprovalUseCase,
    LoanDisbursementUseCase,
    LoanCalculatorService
)
from core_banking.loans.di_container import get_container

# Get container
container = get_container()

# Get use cases from container
loan_application_use_case = container.loan_application_use_case()
loan_approval_use_case = container.loan_approval_use_case()
loan_disbursement_use_case = container.loan_disbursement_use_case()
loan_calculator_service = container.loan_calculator_service()

# Use the loan application use case
loan = loan_application_use_case.execute(
    customer_id="C12345",
    loan_type=LoanType.PERSONAL,
    amount=Decimal("10000"),
    term_months=12,
    interest_rate=Decimal("12.5"),
    repayment_frequency=RepaymentFrequency.MONTHLY,
    purpose="Home renovation"
)
```

## Extension

### Adding New Use Cases

To add a new use case:

1. Create a new class in the `application/use_cases` directory
2. Implement the business logic using domain entities and services
3. Register the use case in the dependency injection container
4. Add CLI and/or API endpoints for the use case

### Adding New Repository/Service Implementations

To add a new implementation of an interface:

1. Create a new class in the appropriate directory
2. Implement the interface methods
3. Update the dependency injection container to use the new implementation

## Testing

Run the tests with pytest:

```bash
pytest core_banking/loans/tests/
```

## Documentation

For more detailed documentation, see:

- [CLEAN_ARCHITECTURE_PROGRESS.md](./CLEAN_ARCHITECTURE_PROGRESS.md) - Implementation progress
- [API Documentation](../documentation/api_guides/loans_api.md) - API documentation
- [Implementation Guide](../documentation/implementation_guides/CLEAN_ARCHITECTURE_IMPLEMENTATION.md) - Clean Architecture implementation guide
