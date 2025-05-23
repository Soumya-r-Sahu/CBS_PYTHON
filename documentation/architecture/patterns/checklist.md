# Clean Architecture Checklist ✅

Use this checklist to ensure your module follows Clean Architecture principles:

- [x] Domain entities are defined.
- [x] Use cases are implemented.
- [x] Interfaces are defined in the application layer.
- [x] Infrastructure components implement application interfaces.
- [x] Presentation layer exposes use cases.

_Last updated: May 23, 2025_

## Domain Layer

### Domain Entities
- [ ] Entities encapsulate business data and logic
- [ ] Entities have proper validation logic
- [ ] Entities use value objects for immutable concepts
- [ ] No dependencies on infrastructure or application layer

### Domain Services
- [ ] Business rules that don't naturally fit in entities are in domain services
- [ ] Domain services receive dependencies via constructor parameters
- [ ] No dependencies on infrastructure or application layer

## Application Layer

### Use Cases
- [ ] Each use case focuses on a single business operation
- [ ] Use cases access domain entities and services, not infrastructure
- [ ] Use cases implement business workflows
- [ ] Use cases handle coordination between multiple domain entities/services

### Interfaces
- [ ] Clear interfaces define what repositories and services must implement
- [ ] Interfaces are in the application layer, not infrastructure
- [ ] Interface methods have clear contracts (parameters and return types)
- [ ] No concrete implementations in the application layer

## Infrastructure Layer

### Repositories
- [ ] Repository implementations satisfy their interfaces
- [ ] Repositories handle translation between domain entities and data models
- [ ] Database-specific code is isolated to the infrastructure layer
- [ ] Repositories encapsulate query logic
- [ ] Repositories implement proper error handling

### External Services
- [ ] Service implementations satisfy their interfaces
- [ ] Third-party integrations are isolated to the infrastructure layer
- [ ] Services implement proper error handling and retry logic
- [ ] Configuration parameters are injectable

## Presentation Layer

### Controllers/Handlers
- [ ] Presentation components use application use cases, not domain directly
- [ ] Input validation is performed before calling use cases
- [ ] Proper error handling and status codes
- [ ] Consistent response formats

### Views/Templates
- [ ] View logic is isolated from business logic
- [ ] Views transform domain entities to presentation formats
- [ ] No business logic in templates

## Dependency Management

### Dependency Injection
- [ ] Container is configured with all dependencies
- [ ] Dependencies are resolved at application startup
- [ ] Testing can replace dependencies with mocks
- [ ] Dependencies follow the Dependency Rule (point inward)

### Module Structure
- [ ] Clear separation between layers (folder structure)
- [ ] No circular dependencies between modules
- [ ] Public API of the module is clearly defined
- [ ] Imports follow the Dependency Rule (domain doesn't import application, etc.)

## Testing

### Unit Tests
- [ ] Domain entities and services have unit tests
- [ ] Use cases have unit tests (with mocked dependencies)
- [ ] Domain logic is tested independently of infrastructure

### Integration Tests
- [ ] Repository implementations have integration tests
- [ ] External service integrations have integration tests
- [ ] End-to-end workflows have integration tests

## Documentation

### Architecture Documentation
- [ ] Module has a README explaining its architecture
- [ ] Clean Architecture layers are clearly documented
- [ ] Domain model is documented (entities, relationships, business rules)
- [ ] Public interfaces are documented

### Comments and Code Documentation
- [ ] Complex business rules have comments explaining the "why"
- [ ] Interface methods have docstrings explaining the contract
- [ ] Domain entities have docstrings explaining the business concepts
- [ ] Use cases have docstrings explaining the business workflow

## Red Flags to Look For

1. **Domain layer importing from infrastructure layer**: This violates the Dependency Rule
2. **Business logic in repositories**: Business logic should be in the domain layer
3. **Direct database access in controllers**: Controllers should use use cases
4. **Anemic domain model**: Business logic should be in entities, not just services
5. **Fat repositories**: Repositories should focus on data access, not business logic
6. **Missing interfaces**: Infrastructure components should implement interfaces
7. **No dependency injection**: Dependencies should be injectable for testing
8. **Business rules spread across layers**: Business rules should be in the domain layer
9. **UI logic mixed with business logic**: UI logic should be in the presentation layer
10. **Direct use of third-party libraries in domain/application**: Use abstractions

## Action Items When Violations Are Found

1. **Move business logic to domain layer**
2. **Create interfaces for external dependencies**
3. **Inject dependencies instead of creating them directly**
4. **Fix dependency direction violations**
5. **Extract use cases from controllers**
6. **Document the domain model**
7. **Add missing tests**
8. **Refactor anemic domain models to include behavior**
9. **Create a dependency injection container**
10. **Validate module against this checklist regularly**
