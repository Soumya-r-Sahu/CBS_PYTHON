# CBS_PYTHON Clean Architecture Central Guide

Last Updated: May 23, 2025

## Overview

This document provides a comprehensive guide for implementing and maintaining Clean Architecture across all modules of the CBS_PYTHON system. Each module maintains its own implementation guide that extends and references this central document.

## Clean Architecture Structure

Every module in the CBS_PYTHON system follows a standardized clean architecture structure with the following layers:

### 1. Domain Layer
- **Purpose**: Core business rules, entities, and logic
- **Components**:
  - Entities: Core business objects
  - Value Objects: Immutable objects representing domain concepts
  - Domain Services: Business logic that doesn't fit in entities
  - Repository Interfaces: Abstractions for data access

### 2. Application Layer
- **Purpose**: Orchestration of business logic, use cases
- **Components**:
  - Use Cases: Application-specific business rules
  - Interfaces: Ports for external services
  - Services: Orchestration of domain entities

### 3. Infrastructure Layer
- **Purpose**: Technical implementation details
- **Components**: 
  - Repositories: Data access implementations
  - Adapters: Implementations of external service interfaces
  - Persistence: Database models and connection code

### 4. Presentation Layer
- **Purpose**: User interface and API
- **Components**:
  - API: REST endpoints
  - CLI: Command-line interfaces
  - DTOs: Data Transfer Objects for external communication

## Dependency Rule

The fundamental rule is that dependencies can only point inward:
- Domain layer has no dependencies on other layers
- Application layer depends only on Domain layer
- Infrastructure layer depends on Application and Domain layers
- Presentation layer depends on Application and Domain layers

## Central Version Control Guidelines

### 1. Branching Strategy

We follow a Git Flow branching model:

- **main**: Production-ready code
- **develop**: Integration branch for feature development
- **feature/[module]-[feature-name]**: Feature branches
- **release/v[X.Y.Z]**: Release preparation branches
- **hotfix/[issue-description]**: Emergency fixes for production

### 2. Versioning Scheme

We use Semantic Versioning (SemVer) for all modules:
- **Major version**: Incompatible API changes
- **Minor version**: New features in a backward-compatible manner
- **Patch version**: Backward-compatible bug fixes

### 3. Commit Guidelines

- Use conventional commit messages:
  - `feat:` for new features
  - `fix:` for bug fixes
  - `refactor:` for code changes that neither fix bugs nor add features
  - `docs:` for documentation changes
  - `test:` for test additions or modifications
  - `chore:` for maintenance tasks

- Include the module name in the commit message: `[module] feat: add new payment gateway`

### 4. Code Reviews

- All changes require at least one code review
- Module maintainers must approve changes to their modules
- Architecture team must approve changes to interfaces between modules

### 5. Documentation Requirements

- Each architectural change must include updates to relevant documentation
- CLEAN_ARCHITECTURE_PROGRESS.md must be updated with implementation status
- Version history must be maintained in module documentation

## Implementation Guidelines

### Creating a New Feature

1. Start with Domain layer:
   - Define entities with behavior and validation
   - Create value objects for domain concepts
   - Define repository interfaces

2. Define Use Cases in Application layer:
   - Create specific use case classes for each business operation
   - Define needed interfaces for external services

3. Implement Infrastructure layer:
   - Create repository implementations
   - Implement external service adapters

4. Create Presentation components:
   - Define DTOs for external communication
   - Implement API endpoints or CLI commands

### Dependency Injection

Use dependency injection to maintain the dependency rule:
- Each module has a `di_container.py` file
- Configure constructor injection of dependencies
- Use interfaces for dependencies to maintain abstraction

## Best Practices

1. **Keep Domain Clean**:
   - Domain entities should have behavior, not just data
   - No infrastructure imports in domain layer
   - Use value objects for immutable concepts

2. **Use Case Focused**:
   - One use case class per business operation
   - Follow command/query separation
   - Return DTOs, not domain entities

3. **Repository Pattern**:
   - Use repository interfaces in domain layer
   - Implement repositories in infrastructure layer
   - Hide data access details from business logic

4. **DTO Pattern**:
   - Use DTOs for communication between layers
   - Convert between domain entities and DTOs
   - Keep presentation models separate from domain models

5. **Version Control**:
   - Keep commits focused on single concerns
   - Update documentation with code changes
   - Follow the branching strategy

## Testing Strategy

- **Domain Layer**: Unit tests for entities, value objects, and domain services
- **Application Layer**: Unit tests for use cases with mocked dependencies
- **Infrastructure Layer**: Integration tests for repositories and adapters
- **Presentation Layer**: API tests and CLI tests
- **End-to-End**: Full workflow tests covering complete features

## Cross-Module Integration

- Use well-defined interfaces for cross-module communication
- Define contracts for service interactions
- Use the service registry pattern for dynamic module discovery
- Maintain backward compatibility when updating interfaces

## Monitoring and Performance

Each module should implement:
- Health checks exposing the status of each layer
- Performance metrics for critical operations
- Logging standards for operations, errors, and warnings
- Circuit breakers for external dependencies

## Migration Path

For legacy code:
1. Identify bounded contexts
2. Create abstraction layers around legacy code
3. Implement new features using clean architecture
4. Gradually refactor legacy code to fit clean architecture principles

## Related Resources

- [System Architecture Overview](./SYSTEM_ARCHITECTURE.md)
- [API Standards](../technical/API_STANDARDS.md)
- [Testing Strategy](../technical/TESTING_STRATEGY.md)
