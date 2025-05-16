# Core Banking System - Payments Domain

This directory contains implementations of various payment systems following a domain-oriented structure.

## Implemented Payment Modules

### 1. NEFT (National Electronic Funds Transfer)
- **Path**: `/payments/neft`
- **Description**: Batch-based electronic funds transfer system
- **Features**:
  - Transaction validation
  - Batch processing
  - Status tracking
  - Error handling
  - Mock processing for development/testing

### 2. RTGS (Real-Time Gross Settlement)
- **Path**: `/payments/rtgs`
- **Description**: Real-time large value fund transfers
- **Features**:
  - High-value transaction support
  - Real-time processing
  - Purpose code validation
  - Mock processing for development/testing

### 3. IMPS (Immediate Payment Service)
- **Path**: `/payments/imps`
- **Description**: 24x7 instant payment service
- **Features**:
  - P2P transfers with mobile number + MMID
  - Account-to-account transfers
  - Immediate settlement
  - Mobile number validation
  - Mock processing for development/testing

## Pending Implementations

### 1. UPI (Unified Payments Interface)
- Unified Payments Interface integration for instant mobile payments

### 2. NACH (National Automated Clearing House)
- For bulk payment needs like direct debit, salary processing, etc.

### 3. Bill Payments
- Integration with bill payment aggregators and billers

## Module Structure

Each payment module follows a consistent domain-oriented structure:

```
payment_type/
├── __init__.py             # Module initialization
├── models/                 # Data models
├── services/               # Business logic
├── repositories/           # Data access
├── validators/             # Input validation
├── controllers/            # API endpoints
├── config/                 # Configuration
├── exceptions/             # Module-specific exceptions
├── utils/                  # Helper functions
└── tests/                  # Unit tests
```

## Common Features

- **Singleton Services**: Single instance of service and repository classes
- **Comprehensive Validation**: Validates all inputs before processing
- **Exception Handling**: Specific exceptions for different error scenarios
- **Transaction Tracking**: Complete lifecycle tracking with timestamps
- **Mock Processing**: Simulated processing for development environments
- **Configuration Management**: Environment-based config with sensible defaults

## Clean Architecture Checklist for Payments Domain

- [ ] README explains module architecture
- [ ] Clean Architecture layers are clearly documented
- [ ] Domain model is documented (entities, relationships, business rules)
- [ ] Public interfaces are documented
- [ ] Complex business rules have comments explaining the "why"
- [ ] Interface methods have docstrings explaining the contract
- [ ] Domain entities have docstrings explaining the business concepts
- [ ] Use cases have docstrings explaining the business workflow

See the main [Clean Architecture Validation Checklist](../documentation/implementation_guides/CLEAN_ARCHITECTURE_CHECKLIST.md) for full details and validation steps.

## Documentation Guidance
- Document the domain model in `domain/` (entities, value objects, business rules)
- Document interfaces in `application/interfaces/`
- Document use cases in `application/use_cases/`
- Document infrastructure implementations in `infrastructure/`
- Document presentation logic in `presentation/`

## Red Flags
- Domain layer importing from infrastructure layer
- Business logic in repositories
- Direct database access in controllers
- Anemic domain model (no business logic in entities)
- Fat repositories (business logic in repositories)
- Missing interfaces for infrastructure
- No dependency injection
- Business rules spread across layers
- UI logic mixed with business logic
- Direct use of third-party libraries in domain/application
