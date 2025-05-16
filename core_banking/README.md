# Core Banking

This directory contains the core banking functionality of the Core Banking System, organized using domain-driven design and Clean Architecture principles.

## Clean Architecture Implementation

The Core Banking System is gradually being refactored to follow Clean Architecture principles. This architecture ensures:

- Clear separation of concerns
- Independence from frameworks and UI
- Testability of each component
- Business rules that are independent of external concerns

### Clean Architecture Layers

1. **Domain Layer** - Contains business entities and rules
2. **Application Layer** - Contains use cases
3. **Infrastructure Layer** - Contains frameworks and adapters
4. **Presentation Layer** - Contains UI components

## Implemented Modules

### Accounts Module (Clean Architecture)

The Accounts module is fully implemented using Clean Architecture and includes:

- Account creation and management
- Transaction processing (deposits, withdrawals)
- Balance inquiries and statements
- Multiple interfaces (API, CLI, GUI)

See [accounts/README.md](accounts/README.md) for more information.

## Customer Management
- Customer Information Files (CIF)
- Know Your Customer (KYC) processes
- Anti-Money Laundering (AML) checks

## Accounts
- Savings accounts
- Current accounts
- Fixed-deposit accounts

## Loans
- Loan origination
- EMI calculation
- Non-performing assets management

## Transactions
- Fund transfers
- Cash deposits
- Withdrawals
- Transaction reversals

## Implementation Guide
Each module should implement the following:
1. Data access layer for respective entities
2. Business logic for all operations
3. Validation rules
4. Process flows
5. Unit tests

## Clean Architecture Checklist for Core Banking

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
