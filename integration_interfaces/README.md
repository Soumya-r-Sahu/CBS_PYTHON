# Integration Interfaces

This directory contains all external system integration points for the Core Banking System.

## REST APIs
Modern RESTful APIs for integration with web and mobile applications.

## SOAP APIs
Legacy SOAP web services support for existing enterprise integrations.

## MQ Interfaces
Message queue-based interfaces for asynchronous communication.

## File-Based Interfaces
File upload/download interfaces for batch processing and data exchange.

## API Logging
Comprehensive logging and monitoring for all API calls and integrations.

## Implementation Guidelines

Each integration interface should:

1. Follow the relevant API standards (REST, SOAP, etc.)
2. Include proper authentication mechanisms
3. Implement request validation
4. Include comprehensive error handling
5. Support monitoring and logging
6. Include proper documentation
7. Provide client examples where appropriate

## Clean Architecture Checklist for Integration Interfaces

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
