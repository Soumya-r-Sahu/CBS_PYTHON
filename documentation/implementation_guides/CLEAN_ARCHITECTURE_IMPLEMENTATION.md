# Clean Architecture Implementation Guide

This guide provides step-by-step instructions for implementing Clean Architecture in a new module within the CBS_PYTHON banking system.

## Overview

Clean Architecture organizes code into concentric layers, each with a specific responsibility:

1. **Domain Layer** (innermost): Contains business entities and rules
2. **Application Layer**: Contains use cases and interfaces
3. **Infrastructure Layer** (outermost): Contains implementations of interfaces
4. **Presentation Layer**: Contains UI components

The fundamental rule is that dependencies always point inward: outer layers depend on inner layers, never the reverse.

## Step 1: Plan Your Module Structure

Start by creating the basic directory structure:

```
module_name/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── entities/
│   │   └── __init__.py
│   └── services/
│       └── __init__.py
├── application/
│   ├── __init__.py
│   ├── interfaces/
│   │   └── __init__.py
│   ├── use_cases/
│   │   └── __init__.py
│   └── services/
│       └── __init__.py
├── infrastructure/
│   ├── __init__.py
│   ├── repositories/
│   │   └── __init__.py
│   └── services/
│       └── __init__.py
├── presentation/
│   ├── __init__.py
│   ├── cli/
│   │   └── __init__.py
│   └── api/
│       └── __init__.py
└── di_container.py
```

## Step 2: Define Domain Entities

Domain entities are the core business objects with business logic:

```python
# domain/entities/user.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class User:
    id: str
    username: str
    email: str
    full_name: str
    created_at: datetime
    active: bool = True
    last_login: Optional[datetime] = None
    
    def __post_init__(self):
        """Validate entity after initialization"""
        self._validate()
    
    def _validate(self):
        """Validate the entity"""
        if not self.username:
            raise ValueError("Username cannot be empty")
        if not self.email:
            raise ValueError("Email cannot be empty")
        if '@' not in self.email:
            raise ValueError("Invalid email format")
    
    def deactivate(self):
        """Deactivate user"""
        self.active = False
        
    def activate(self):
        """Activate user"""
        self.active = True
        
    def update_last_login(self):
        """Update the last login time"""
        self.last_login = datetime.now()
        
    def can_login(self) -> bool:
        """Check if user can login"""
        return self.active
```

## Step 3: Implement Domain Services

Domain services contain business logic that doesn't naturally fit within entities:

```python
# domain/services/user_validation_service.py
import re
from ..entities.user import User

class UserValidationService:
    """Service for validating user data"""
    
    def __init__(self, password_min_length: int = 8):
        self.password_min_length = password_min_length
        self.email_pattern = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
    
    def validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < self.password_min_length:
            return False
        
        # Check for at least one uppercase, lowercase, and digit
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        return has_upper and has_lower and has_digit
    
    def validate_email(self, email: str) -> bool:
        """Validate email format"""
        return bool(self.email_pattern.match(email))
    
    def validate_username(self, username: str) -> bool:
        """Validate username format"""
        if len(username) < 3:
            return False
        
        # Check if username has only allowed characters
        return bool(re.match(r'^[a-zA-Z0-9_.-]+$', username))
```

## Step 4: Define Application Interfaces

Application interfaces define contracts for infrastructure implementations:

```python
# application/interfaces/user_repository_interface.py
from abc import ABC, abstractmethod
from typing import List, Optional
from ...domain.entities.user import User

class UserRepositoryInterface(ABC):
    """Interface for user repository implementations"""
    
    @abstractmethod
    def create(self, user: User) -> User:
        """Create a new user"""
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    def update(self, user: User) -> User:
        """Update an existing user"""
        pass
    
    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """Delete a user"""
        pass
    
    @abstractmethod
    def list_all(self) -> List[User]:
        """List all users"""
        pass
```

## Step 5: Implement Use Cases

Use cases implement specific application actions:

```python
# application/use_cases/create_user_use_case.py
from ...domain.entities.user import User
from ...domain.services.user_validation_service import UserValidationService
from ..interfaces.user_repository_interface import UserRepositoryInterface
from datetime import datetime
import uuid

class CreateUserUseCase:
    """Use case for creating a new user"""
    
    def __init__(
        self, 
        user_repository: UserRepositoryInterface,
        user_validation_service: UserValidationService
    ):
        self.user_repository = user_repository
        self.user_validation_service = user_validation_service
    
    def execute(self, username: str, email: str, full_name: str, password: str) -> User:
        """Execute the use case"""
        # Validate input
        if not self.user_validation_service.validate_username(username):
            raise ValueError("Invalid username format")
        
        if not self.user_validation_service.validate_email(email):
            raise ValueError("Invalid email format")
        
        if not self.user_validation_service.validate_password(password):
            raise ValueError("Password does not meet requirements")
        
        # Check if user already exists
        existing_user = self.user_repository.get_by_username(username)
        if existing_user:
            raise ValueError(f"User with username {username} already exists")
        
        existing_email = self.user_repository.get_by_email(email)
        if existing_email:
            raise ValueError(f"User with email {email} already exists")
        
        # Create user entity
        user = User(
            id=str(uuid.uuid4()),
            username=username,
            email=email,
            full_name=full_name,
            created_at=datetime.now(),
            active=True
        )
        
        # Save user (password handling would be done in the repository)
        created_user = self.user_repository.create(user)
        
        return created_user
```

## Step 6: Implement Infrastructure Components

Infrastructure components implement the interfaces defined in the application layer:

```python
# infrastructure/repositories/sql_user_repository.py
from typing import List, Optional
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ...domain.entities.user import User
from ...application.interfaces.user_repository_interface import UserRepositoryInterface

Base = declarative_base()

class UserModel(Base):
    """SQLAlchemy model for User"""
    __tablename__ = 'users'
    
    id = sa.Column(sa.String, primary_key=True)
    username = sa.Column(sa.String, unique=True, nullable=False)
    email = sa.Column(sa.String, unique=True, nullable=False)
    full_name = sa.Column(sa.String, nullable=False)
    created_at = sa.Column(sa.DateTime, nullable=False)
    active = sa.Column(sa.Boolean, default=True)
    last_login = sa.Column(sa.DateTime, nullable=True)
    password_hash = sa.Column(sa.String, nullable=False)

class SqlUserRepository(UserRepositoryInterface):
    """SQL implementation of the user repository"""
    
    def __init__(self, connection_string: str):
        """Initialize the repository with a connection string"""
        self.engine = sa.create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
    
    def _to_entity(self, model: UserModel) -> User:
        """Convert ORM model to domain entity"""
        return User(
            id=model.id,
            username=model.username,
            email=model.email,
            full_name=model.full_name,
            created_at=model.created_at,
            active=model.active,
            last_login=model.last_login
        )
    
    def _to_model(self, entity: User, password_hash: str = None) -> UserModel:
        """Convert domain entity to ORM model"""
        model = UserModel(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            full_name=entity.full_name,
            created_at=entity.created_at,
            active=entity.active,
            last_login=entity.last_login
        )
        
        if password_hash:
            model.password_hash = password_hash
            
        return model
    
    def create(self, user: User, password_hash: str = None) -> User:
        """Create a new user"""
        with self.Session() as session:
            user_model = self._to_model(user, password_hash)
            session.add(user_model)
            session.commit()
            return self._to_entity(user_model)
    
    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        with self.Session() as session:
            user_model = session.query(UserModel).filter(UserModel.id == user_id).first()
            return self._to_entity(user_model) if user_model else None
    
    # Implement other interface methods...
```

## Step 7: Create Presentation Layer

The presentation layer exposes your use cases to users:

```python
# presentation/cli/user_cli.py
import click
from ...di_container import Container

@click.group()
def user_cli():
    """User management commands"""
    pass

@user_cli.command("create")
@click.option("--username", required=True, help="User's username")
@click.option("--email", required=True, help="User's email")
@click.option("--full-name", required=True, help="User's full name")
@click.option("--password", required=True, help="User's password", prompt=True, hide_input=True)
def create_user(username, email, full_name, password):
    """Create a new user"""
    container = Container()
    create_user_use_case = container.create_user_use_case()
    
    try:
        user = create_user_use_case.execute(
            username=username,
            email=email,
            full_name=full_name,
            password=password
        )
        click.echo(f"User created successfully: {user.id}")
    except ValueError as e:
        click.echo(f"Error: {str(e)}", err=True)

if __name__ == "__main__":
    user_cli()
```

## Step 8: Set Up Dependency Injection

The dependency injection container wires everything together:

```python
# di_container.py
from dependency_injector import containers, providers
import os

# Domain
from .domain.services.user_validation_service import UserValidationService

# Application
from .application.use_cases.create_user_use_case import CreateUserUseCase

# Infrastructure
from .infrastructure.repositories.sql_user_repository import SqlUserRepository

class Container(containers.DeclarativeContainer):
    """Dependency Injection Container"""
    
    config = providers.Configuration()
    
    # Set defaults
    config.set_default({
        'db_connection_string': os.environ.get('DB_CONNECTION', 'sqlite:///users.db'),
        'password_min_length': 8
    })
    
    # Domain Services
    user_validation_service = providers.Singleton(
        UserValidationService,
        password_min_length=config.password_min_length
    )
    
    # Repositories
    user_repository = providers.Singleton(
        SqlUserRepository,
        connection_string=config.db_connection_string
    )
    
    # Use Cases
    create_user_use_case = providers.Factory(
        CreateUserUseCase,
        user_repository=user_repository,
        user_validation_service=user_validation_service
    )
```

## Step 9: Testing

Test each layer separately:

```python
# tests/domain/test_user.py
import pytest
from datetime import datetime
from module_name.domain.entities.user import User

def test_user_validation():
    """Test user validation"""
    # Valid user
    valid_user = User(
        id="1",
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        created_at=datetime.now()
    )
    assert valid_user is not None
    
    # Invalid user (empty username)
    with pytest.raises(ValueError):
        User(
            id="2",
            username="",
            email="test@example.com",
            full_name="Test User",
            created_at=datetime.now()
        )
    
    # Invalid user (invalid email)
    with pytest.raises(ValueError):
        User(
            id="3",
            username="testuser2",
            email="not-an-email",
            full_name="Test User",
            created_at=datetime.now()
        )

def test_user_methods():
    """Test user methods"""
    user = User(
        id="1",
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        created_at=datetime.now()
    )
    
    # Test activation/deactivation
    assert user.active is True
    user.deactivate()
    assert user.active is False
    user.activate()
    assert user.active is True
    
    # Test login
    assert user.last_login is None
    user.update_last_login()
    assert user.last_login is not None
    
    # Test can_login
    assert user.can_login() is True
    user.deactivate()
    assert user.can_login() is False
```

## Best Practices

1. **Keep Layers Separate**: Don't mix concerns between layers
2. **Domain-Driven Design**: Focus on modeling your domain accurately
3. **Interface Segregation**: Create small, focused interfaces
4. **Test Each Layer**: Test domain, application, and infrastructure separately
5. **Use Value Objects**: For immutable concepts in your domain
6. **Make Dependencies Explicit**: Use constructor injection
7. **Follow the Dependency Rule**: Dependencies always point inward

## Common Pitfalls

1. **Domain Depends on Infrastructure**: Make sure your domain layer doesn't import from infrastructure
2. **Anemic Domain Model**: Don't put all logic in services; put business logic in entities
3. **Too Many Layers**: Don't create more layers than needed; stick to the essentials
4. **Fat Use Cases**: Keep use cases focused on a single responsibility
5. **Missing Validation**: Always validate input at the boundaries

## Conclusion

Following Clean Architecture principles leads to more maintainable, testable, and flexible code. By separating concerns into well-defined layers, you can change implementations with minimal impact on the rest of the system.

For reference, check the completed modules that follow this architecture:
- `core_banking/accounts`
- `core_banking/customer_management`
- `core_banking/loans`
- `digital_channels/atm_switch`
