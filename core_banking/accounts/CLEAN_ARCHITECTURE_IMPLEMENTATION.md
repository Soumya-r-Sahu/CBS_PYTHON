# Core Banking - Accounts Module Clean Architecture Implementation

## Overview

This document outlines the implementation of Clean Architecture in the Core Banking Accounts Module. The architecture is structured into four distinct layers:

1. **Domain Layer** - Contains business entities and business rules independent of external concerns
2. **Application Layer** - Contains use cases that orchestrate the flow of data to and from entities
3. **Infrastructure Layer** - Contains implementations of interfaces defined in the application layer
4. **Presentation Layer** - Contains UI components that present information to users

## Directory Structure

```
accounts/
├── domain/                # Domain Layer
│   ├── entities/          # Business entities and value objects 
│   │   ├── account.py
│   │   ├── transaction.py
│   │   ├── customer.py
│   │   └── value_objects/
│   │       ├── money.py
│   │       ├── account_number.py
│   │       └── account_status.py
│   ├── validators/        # Domain validation rules
│   │   ├── account_validator.py
│   │   └── transaction_validator.py
│   └── services/          # Pure domain business logic
│       ├── interest_calculator.py
│       └── account_rules.py
├── application/           # Application Layer
│   ├── use_cases/         # Application use cases
│   │   ├── create_account.py
│   │   ├── close_account.py 
│   │   ├── deposit_funds.py
│   │   ├── withdraw_funds.py
│   │   ├── transfer_funds.py
│   │   ├── get_account_details.py
│   │   └── get_statement.py
│   ├── services/          # Orchestration services
│   │   └── account_service.py
│   └── interfaces/        # Interfaces that infrastructure must implement
│       ├── account_repository.py
│       ├── customer_repository.py
│       └── notification_service.py
├── infrastructure/        # Infrastructure Layer
│   ├── repositories/      # Data access implementation
│   │   ├── sql_account_repository.py
│   │   └── sql_customer_repository.py
│   ├── apis/              # External API integration
│   │   └── customer_kyc_api.py
│   └── services/          # External services implementation
│       ├── email_notification_service.py
│       └── sms_notification_service.py
├── presentation/          # Presentation Layer
│   ├── api/               # API controllers/views
│   │   ├── account_controller.py
│   │   └── transaction_controller.py
│   ├── cli/               # CLI interfaces
│   │   └── account_cli.py
│   └── gui/               # GUI implementations
│       └── account_management_ui.py
├── di_container.py        # Dependency injection container
└── __init__.py            # Module initialization
```

## Implementation Status

### 1. Domain Layer ✅ (Complete)

1. **Create domain entities** ✅:
   - `Account` entity defined with proper encapsulation and business rules
   - `Transaction` entity with transaction types, status tracking, and validation
   - Value objects created for `Money`, `AccountNumber`, and `AccountStatus`

2. **Implement domain services** ✅:
   - Interest calculation service implemented
   - Account rule enforcement implemented with business rule validations

### 2. Application Layer ✅ (Complete)

1. **Define interfaces** ✅:
   - Repository interfaces created for `AccountRepository` and `TransactionRepository`
   - External service interfaces defined for `NotificationService`

2. **Implement use cases** ✅:
   - `CreateAccountUseCase` - Create new customer accounts
   - `DepositFundsUseCase` - Handle deposits to accounts
   - `WithdrawFundsUseCase` - Process withdrawals with validation
   - `GetAccountDetailsUseCase` - Retrieve account information

3. **Create orchestration services** ✅:
   - `AccountService` orchestrates all account-related use cases

### 3. Infrastructure Layer ✅ (Complete)

1. **Implement repositories** ✅:
   - `SqlAccountRepository` - SQL implementation for account persistence
   - `SqlTransactionRepository` - SQL implementation for transaction history

2. **Integrate external services** ✅:
   - `EmailNotificationService` - Email notifications for account activities
   - `SmsNotificationService` - SMS notifications for transactions

### 4. Presentation Layer ✅ (Complete)

1. **Build API controllers** ✅:
   - RESTful endpoints implemented in `accounts_controller.py`
   - Support for account creation, deposits, withdrawals, and balance inquiries

2. **Create CLI interface** ✅:
   - Command-line tools implemented in `accounts_cli.py`
   - Commands for creating accounts, deposits, withdrawals, and queries

3. **Develop GUI** ✅:
   - User interface developed in `accounts_gui.py` using PyQt5
   - Forms for all account operations with feedback and validation

### 5. Dependency Injection ✅ (Complete)

1. **Configure DI container** ✅:
   - Components wired up in `di_container.py`
   - Configuration management with environment variable support
   - Support for switching between different notification services

## Key Principles to Follow

1. **Dependency Rule**:
   - Dependencies always point inward, toward the domain layer
   - Domain and application layers have no dependency on infrastructure or presentation

2. **Interface Segregation**:
   - External dependencies are defined as interfaces in the application layer
   - Infrastructure implements these interfaces

3. **Separation of Concerns**:
   - Each layer has a specific responsibility
   - No layer should do work that belongs to another layer

4. **Testability**:
   - Each layer can be tested independently
   - Domain and application layers can be unit tested without infrastructure

## Testing Strategy

1. **Domain Layer Tests**:
   - Unit tests for entities, value objects, and validators
   - Unit tests for domain services

2. **Application Layer Tests**:
   - Unit tests for use cases with mock repositories and services
   - Integration tests for service orchestration

3. **Infrastructure Layer Tests**:
   - Integration tests for repositories with test database
   - Integration tests for external service adapters

4. **Presentation Layer Tests**:
   - Unit tests for controllers/presenters
   - End-to-end tests for UI workflows
