# CBS_PYTHON Project Rules and Standards

## 1. Directory Structure Standards

### 1.1 Module Directory Structure
Every module in the CBS_PYTHON project must adhere to the following directory structure:

```
module_name/
├── __init__.py                # Package initialization, exports public API
├── module_interface.py        # Implements ModuleInterface base class
├── config.py                  # Module-specific configuration
├── README.md                  # Module documentation
├── utils/                     # Module-specific utilities
│   ├── __init__.py
│   ├── error_handling.py      # Error handling for this module 
│   └── validators.py          # Data validation utilities
├── docs/                      # Module documentation
│   ├── ARCHITECTURE.md        # Architecture documentation
│   └── CHANGELOG.md           # Change history
├── tests/                     # Module tests
│   ├── __init__.py
│   ├── test_module_interface.py
│   └── test_<feature>.py      # Feature-specific tests
└── examples/                  # Example code demonstrating usage
    └── example_<feature>.py
```

### 1.2 Core System Directories
The following core directories must be maintained in the project root:

- `config/`: System-wide configuration files
- `utils/`: System-wide utility functions used across modules
- `docs/`: System-wide documentation
- `scripts/`: Maintenance and deployment scripts
- `tests/`: System-level tests
- `database/`: Database-related files (schemas, migrations)
- `security/`: Security-related functionality
- `integration_interfaces/`: External integration points

## 2. File Naming Conventions

### 2.1 Python Files
- Use snake_case for all Python files (e.g., `account_manager.py`, `payment_processor.py`)
- Test files must start with `test_` (e.g., `test_account_manager.py`)
- Example files should start with `example_` (e.g., `example_payment_processing.py`)

### 2.2 Documentation Files
- Use UPPERCASE for primary documentation files (e.g., `README.md`, `CHANGELOG.md`, `ARCHITECTURE.md`)
- Use Title_Case for supporting documentation files (e.g., `Installation_Guide.md`)

### 2.3 Configuration Files
- Use snake_case for configuration files (e.g., `database_config.json`, `api_settings.yml`)

## 3. File Content Standards

### 3.1 Python File Header Template
Every Python file must include the following header:

```python
"""
{Brief description of the file}

This module {provides/implements/defines} {purpose of the file}.
{Additional details if necessary}

Author: cbs-core-dev
Version: {module_version}
"""

# Import standard libraries

# Import third-party libraries

# Import local modules
```

### 3.2 Python Class Template
Classes should follow this standard structure:

```python
class ClassName:
    """
    Brief description of the class
    
    Description:
        Detailed description of what this class does and its purpose
        within the system.
    
    Usage:
        # Example code showing how to use the class
        instance = ClassName(param1, param2)
        result = instance.method()
    """
    
    def __init__(self, param1, param2):
        """
        Initialize the class
        
        Args:
            param1 (type): Description of param1
            param2 (type): Description of param2
        """
        self.param1 = param1
        self.param2 = param2
        
    def method(self):
        """
        Brief description of method
        
        Args:
            None
            
        Returns:
            type: Description of return value
            
        Raises:
            ExceptionType: When/why this exception is raised
        """
        # Method implementation
```

### 3.3 Module Interface Implementation
Every module must implement the ModuleInterface class in its `module_interface.py` file:

```python
from utils.lib.module_interface import ModuleInterface

class MyModuleInterface(ModuleInterface):
    """
    Module interface for MyModule
    
    This class implements the standard module interface for the MyModule 
    component, providing standardized integration with the system.
    """
    
    def __init__(self):
        """Initialize the module interface"""
        super().__init__("module_name", "1.1.2")
        # Module-specific initialization
    
    def register_services(self):
        """Register module services with the service registry"""
        registry = self.get_registry()
        
        # Register module-specific services
        registry.register("module.service_name", self.service_function, 
                         version="1.1.2", module_name=self.name)
```

## 4. Code Style Guidelines

### 4.1 Python Style
- Follow PEP 8 for code style
- Maximum line length: 100 characters
- Use 4 spaces for indentation (no tabs)
- Use single quotes for short strings, double quotes for docstrings and multi-line strings
- Add docstrings to all modules, classes, and methods

### 4.2 Variable Naming
- Use snake_case for variable and function names
- Use PascalCase for class names
- Use ALL_UPPERCASE for constants
- Use _single_leading_underscore for internal/private variables

### 4.3 Comment Standards
- Comments should explain "why" not "what"
- Keep comments current when code changes
- Use TODO, FIXME, and NOTE tags for special comments

## 5. File Modification Guidelines

### 5.1 Modification Header
When modifying an existing file, add a modification entry to the file's header:

```python
# Modified: YYYY-MM-DD by cbs-core-dev
# Changes: Brief description of changes
```

### 5.2 Code Change Documentation
For significant changes, document them in the following format:

```python
# START MODIFICATION: [JIRA-123] Brief description
# Original code:
# def original_function():
#     return "original"
# Modified to support new feature X
def modified_function():
    return "modified"
# END MODIFICATION
```

### 5.3 Testing Requirements
- All new and modified files must have corresponding test coverage
- Tests must verify both expected behavior and error handling

## 6. Module Registration Process

### 6.1 Module Registration
Each module must be registered in `register_modules.py`:

```python
from module_name.module_interface import ModuleNameInterface

def register_module_name():
    """Register the module_name module"""
    module = ModuleNameInterface()
    module.register_services()
    return module

# Add to modules dictionary
modules["module_name"] = register_module_name
```

### 6.2 Service Registration
Services within modules must be registered with the ServiceRegistry:

```python
def register_services(self):
    """Register module services with service registry"""
    registry = ServiceRegistry.get_instance()
    
    # Register primary service
    registry.register("module.service_name", self.service_implementation, 
                     version="1.1.2", module_name=self.name)
                     
    # Register additional services as needed
```

## 7. Version Control Guidelines

### 7.1 Version Format
All modules must follow semantic versioning (MAJOR.MINOR.PATCH):
- MAJOR: Breaking changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes, backward compatible

### 7.2 Version Consistency
Version numbers should be consistent across:
- Module `__init__.py`
- Module interface
- Documentation
- API endpoints

## 8. Error Handling Standards

### 8.1 Exception Classes
Custom exceptions must inherit from appropriate base classes:

```python
from utils.lib.error_handling import CbsError, AppError, BusinessLogicError

class ModuleSpecificError(BusinessLogicError):
    """Exception raised for specific module error conditions"""
    def __init__(self, message=None, details=None):
        super().__init__("MODULE_ERROR_CODE", message or "Default message", details)
```

### 8.2 Error Logging
Error handling should include appropriate logging:

```python
try:
    # Operation that might fail
    result = perform_operation()
except Exception as e:
    logger.error(f"Operation failed: {str(e)}", exc_info=True)
    raise ModuleSpecificError(message=f"Operation failed: {str(e)}")
```

## 9. Database Interaction Standards

### 9.1 Connection Handling
Database connections must use the centralized connection manager:

```python
from database.python.common.database_operations import DatabaseOperations

db_ops = DatabaseOperations.get_instance()
result = db_ops.execute_query("SELECT * FROM table")
```

### 9.2 Query Definition
SQL queries should be defined separately from execution logic:

```python
QUERY_GET_CUSTOMER = """
SELECT 
    customer_id, first_name, last_name, email 
FROM 
    cbs_customers 
WHERE 
    customer_id = %s
"""

def get_customer(customer_id):
    """Get customer details by ID"""
    return db_ops.execute_query(QUERY_GET_CUSTOMER, [customer_id])
```

## 10. Security Standards

### 10.1 Authentication
All authentication must use the central security services:

```python
from security.common.security_operations import verify_password, hash_password

# Hashing a password
hashed = hash_password("user_password")

# Verifying a password
is_valid = verify_password("user_password", stored_hash)
```

### 10.2 Data Encryption
Sensitive data must be encrypted:

```python
from security.common.security_operations import encrypt_data, decrypt_data

encrypted = encrypt_data("sensitive information")
decrypted = decrypt_data(encrypted)
```

## 11. Configuration Management

### 11.1 Configuration Access
Access configuration via the centralized config system:

```python
from utils.config.config import DATABASE_CONFIG, API_CONFIG

db_host = DATABASE_CONFIG['host']
api_port = API_CONFIG['port']
```

### 11.2 Module-Specific Configuration
Module-specific configuration must be isolated:

```python
# In module_name/config.py
"""Module-specific configuration"""

from utils.config.config import get_module_config

# Get module config with defaults
MODULE_CONFIG = get_module_config('module_name', {
    'setting1': 'default_value',
    'setting2': 123,
})
```

## 12. File and Directory Creation Checklist

### 12.1 New Module Checklist
When creating a new module:

- [ ] Create the module directory with proper structure
- [ ] Add `__init__.py` with version and exports
- [ ] Create `module_interface.py` implementing ModuleInterface
- [ ] Add standard subdirectories (utils, docs, tests, examples)
- [ ] Create README.md with module documentation
- [ ] Register the module in register_modules.py
- [ ] Add unit tests for the module

### 12.2 New Feature Checklist
When adding a new feature:

- [ ] Update module version if necessary
- [ ] Add feature implementation
- [ ] Update module documentation
- [ ] Add unit tests for the feature
- [ ] Register any new services
- [ ] Update examples demonstrating the feature

## 13. Documentation Requirements

### 13.1 Module Documentation
Each module must include:

- Purpose and overview
- Dependencies
- Installation instructions
- Usage examples
- API reference
- Configuration options

### 13.2 API Documentation
API endpoints must document:

- URL structure
- HTTP methods
- Request parameters
- Response format
- Error codes
- Authentication requirements
- Rate limiting

## 14. Compliance and Auditing

### 14.1 Logging Standards
All modules must implement standard logging:

```python
import logging

# Configure logger
logger = logging.getLogger(__name__)

def function():
    logger.debug("Detailed information")
    logger.info("General information")
    logger.warning("Warning message")
    logger.error("Error message")
```

### 14.2 Audit Trail
Security-sensitive operations must create audit trails:

```python
from utils.lib.audit import create_audit_entry

def sensitive_operation(user_id, data):
    # Perform operation
    result = process_data(data)
    
    # Create audit entry
    create_audit_entry(
        action="SENSITIVE_OPERATION",
        user_id=user_id,
        resource_id=data.id,
        old_value=None,
        new_value=result,
        status="SUCCESS"
    )
    
    return result
```

## 15. Deprecation Policy

### 15.1 Deprecation Marking
Deprecated functionality must be clearly marked:

```python
import warnings

def old_function():
    warnings.warn(
        "old_function is deprecated and will be removed in version 2.0.0. Use new_function instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # Implementation
```

### 15.2 Deprecation Timeline
- Functions marked as deprecated must remain for at least one MINOR version cycle
- Removal must happen during a MAJOR version upgrade