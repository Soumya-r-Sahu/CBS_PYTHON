# Risk & Compliance Domain

This directory contains modules for risk management, fraud detection, regulatory reporting, and compliance.

## Clean Architecture Checklist for Risk & Compliance

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
