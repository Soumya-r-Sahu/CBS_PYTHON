# HR-ERP Employee Management: Clean Architecture Example

This directory contains a sample implementation of Clean Architecture principles for the HR-ERP module, focusing on the employee onboarding process. It serves as a reference implementation that can be used as a template for implementing Clean Architecture in other modules of the CBS_PYTHON system.

## Directory Structure

The implementation follows a strict layered approach, with clear boundaries between layers:

```
employee_management/
│
├── domain/                  # Domain layer - business entities and rules
│   ├── entities/            # Business entities
│   ├── value_objects/       # Value objects
│   ├── repositories/        # Repository interfaces
│   └── exceptions/          # Domain-specific exceptions
│
├── application/             # Application layer - use cases and business workflows
│   ├── use_cases/           # Application use cases
│   └── interfaces/          # Service interfaces
│
├── infrastructure/          # Infrastructure layer - external dependencies
│   ├── repositories/        # Repository implementations
│   ├── notification/        # External service adapters for notifications
│   └── document/            # External service adapters for documents
│
├── presentation/            # Presentation layer - UI and API controllers
│   └── controllers/         # REST API controllers
│
├── di_container.py          # Dependency injection container
└── tests/                   # Tests for all layers
    ├── domain/
    ├── application/
    ├── infrastructure/
    └── presentation/
```

## Key Components

### Domain Layer

- **Entities**: `Employee` entity represents the core business concept with its attributes and behavior
- **Value Objects**: Immutable objects like `EmployeeId`, `Address`, and `ContactInfo`
- **Repository Interfaces**: Define data access contracts like `EmployeeRepository`

### Application Layer

- **Use Cases**: `OnboardEmployeeUseCase` implements the business workflow for onboarding employees
- **Service Interfaces**: Define contracts for external services like `NotificationService` and `DocumentService`

### Infrastructure Layer

- **Repository Implementations**: `SqlEmployeeRepository` implements data access using an SQL database
- **Service Adapters**: Implementations of services like `EmailNotificationService` and `FileSystemDocumentService`

### Presentation Layer

- **API Controllers**: REST API implementation in `employee_controller.py`

## Clean Architecture Principles Demonstrated

1. **Dependency Rule**: All dependencies point inward, with domain at the center
2. **Independence from Frameworks**: Domain and application layers have no dependencies on external frameworks
3. **Testability**: Business logic is easily testable without external dependencies
4. **Separation of Concerns**: Each layer has a clear responsibility
5. **Entity-centric Design**: Domain entities are at the core of the system
6. **Use Case-driven**: Application layer organized around business use cases

## How to Use This Template

To implement Clean Architecture in another module:

1. **Create the Domain Layer First**:
   - Define your core business entities, value objects, and repository interfaces
   - Ensure domain layer has no dependencies on outer layers or frameworks

2. **Develop Use Cases in Application Layer**:
   - Create input/output DTOs for your use cases
   - Implement business workflows using domain entities and repositories
   - Define service interfaces needed by your use cases

3. **Implement Infrastructure Adapters**:
   - Create concrete implementations of repository interfaces
   - Implement service adapters for external dependencies

4. **Build Presentation Layer**:
   - Create controllers that use your application use cases
   - Map between API requests/responses and use case DTOs

5. **Wire Everything with Dependency Injection**:
   - Create a container that injects dependencies while respecting the dependency rule

## Example Use Case: Employee Onboarding

This implementation demonstrates the employee onboarding process:

1. User submits employee information via API
2. Controller converts request to DTO and passes to use case
3. Use case performs business logic:
   - Creates employee entity with value objects
   - Validates data and business rules
   - Persists employee via repository
   - Creates onboarding tasks and document requirements
   - Sends notifications
4. Controller returns response with result information

## Testing Strategy

The sample includes tests that demonstrate proper testing strategy for Clean Architecture:

- **Unit Tests**: Focus on testing domain entities, value objects, and use cases in isolation
- **Integration Tests**: Test repository implementations and external services
- **Mock Dependencies**: Use mocks to isolate the component under test

## Further Resources

For more information about Clean Architecture:

1. Robert C. Martin's "Clean Architecture: A Craftsman's Guide to Software Structure and Design"
2. The system-wide Clean Architecture Guide at `../../Documentation/architecture/CLEAN_ARCHITECTURE_CENTRAL_GUIDE.md`
