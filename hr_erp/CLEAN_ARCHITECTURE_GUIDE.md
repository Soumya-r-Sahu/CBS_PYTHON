# HR-ERP Clean Architecture Guide

Last Updated: May 19, 2025

## Overview

This document provides guidance for implementing and maintaining Clean Architecture in the HR-ERP module of the CBS_PYTHON system.

## Clean Architecture Structure

Each module in HR-ERP follows a clean architecture structure with the following layers:

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

## Testing Strategy

- **Domain Layer**: Unit tests for entities, value objects, and domain services
- **Application Layer**: Unit tests for use cases with mocked dependencies
- **Infrastructure Layer**: Integration tests for repositories and adapters
- **Presentation Layer**: API tests and CLI tests
- **End-to-End**: Full workflow tests

## Module-Specific Guidelines

### Employee Management
- Focus on employee lifecycle management
- Implement value objects for employee identification
- Separate domain logic for different employee operations

### Leave Management
- Implement domain rules for leave entitlement and calculation
- Use rich domain models for leave requests
- Implement approval workflows in application layer

### Performance Management
- Build domain models around performance criteria
- Implement review cycles as domain services
- Use repository pattern for performance history

### Recruitment
- Implement hiring workflow in application layer
- Use value objects for job requirements
- Maintain candidate state using domain entities

### Training
- Track training progress using domain models
- Implement certification validation in domain services
- Use adapters for external learning platforms

### Integration
- Implement adapters for external HR systems
- Use domain events for synchronization
- Keep integration concerns out of domain layer

## Related Resources

- [Clean Architecture Overview](../../Documentation/architecture/CLEAN_ARCHITECTURE.md)
- [System Architecture](../../Documentation/architecture/SYSTEM_ARCHITECTURE.md)
