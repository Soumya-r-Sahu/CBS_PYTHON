"""
CBS_PYTHON Module Creator

This script creates standardized modules, files, and directories according to the 
project's rules and standards document.

Author: cbs-core-dev
Version: 1.1.2
"""

import os
import sys
import argparse
import datetime
from pathlib import Path

# Constants
VERSION = "1.1.2"
GITHUB_USERNAME = "cbs-core-dev"
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Templates for file content
INIT_TEMPLATE = '''"""
{module_name} Package

This module provides {module_description}.

Author: {author}
Version: {version}
"""

__version__ = "{version}"

# Public API exports
'''

MODULE_INTERFACE_TEMPLATE = '''"""
{module_name} Module Interface

This module implements the standard interface for the {module_name}
component, providing standardized integration with the system.

Author: {author}
Version: {version}
"""

import logging
from typing import Dict, Any, List, Optional

from utils.lib.module_interface import ModuleInterface
from utils.lib.service_registry import ServiceRegistry

# Configure logger
logger = logging.getLogger(__name__)

class {class_name}Interface(ModuleInterface):
    """
    Module interface for {module_name}
    
    Description:
        This class implements the standard module interface for the {module_name} 
        component, providing standardized integration with the system.
    """
    
    def __init__(self):
        """Initialize the module interface"""
        super().__init__("{module_id}", "{version}")
        # Module-specific initialization
        logger.info(f"{module_name} module initialized")
    
    def register_services(self):
        """Register module services with the service registry"""
        registry = self.get_registry()
        
        # Register module-specific services
        # registry.register("{module_id}.service", self.service_function, 
        #                  version="{version}", module_name=self.name)
        
        logger.info(f"{module_name} services registered")
'''

CONFIG_TEMPLATE = '''"""
{module_name} Configuration

This module provides configuration settings for the {module_name} component.

Author: {author}
Version: {version}
"""

from utils.config.config import get_module_config

# Get module config with defaults
MODULE_CONFIG = get_module_config('{module_id}', {{
    # Default configuration values
    'setting1': 'default_value',
    'setting2': 123,
    'enabled': True,
}})

# Export configuration values for module use
SETTING1 = MODULE_CONFIG.get('setting1')
SETTING2 = MODULE_CONFIG.get('setting2')
ENABLED = MODULE_CONFIG.get('enabled')
'''

README_TEMPLATE = '''# {module_name}

## Overview
{module_description}

## Key Features
- Feature 1
- Feature 2
- Feature 3

## Dependencies
- List of dependencies

## Usage
```python
from {module_id} import SomeClass

# Example code
instance = SomeClass()
result = instance.some_method()
```

## Configuration
Key configuration options:
- `setting1`: Description of setting1
- `setting2`: Description of setting2
- `enabled`: Enable/disable the module

## API Reference
See detailed API documentation in the `docs` directory.
'''

ERROR_HANDLING_TEMPLATE = '''"""
{module_name} Error Handling

This module provides error handling utilities specific to the {module_name} component.

Author: {author}
Version: {version}
"""

import logging
from typing import Dict, Any, Optional

from utils.lib.error_handling import CbsError, BusinessLogicError

# Configure logger
logger = logging.getLogger(__name__)

class {class_prefix}Error(BusinessLogicError):
    """Base exception class for {module_name} errors"""
    def __init__(self, error_code="{error_code_prefix}_ERROR", message=None, details=None):
        """Initialize {module_name} error"""
        super().__init__(error_code, message or "An error occurred in {module_name}", details)

class {class_prefix}ValidationError(BusinessLogicError):
    """Exception raised for validation errors in {module_name}"""
    def __init__(self, message=None, details=None):
        """Initialize validation error"""
        super().__init__("{error_code_prefix}_VALIDATION_ERROR", message or "{module_name} validation error", details)

# Handle module-specific exceptions
def handle_module_error(exception: Exception) -> Dict[str, Any]:
    """
    Handle module-specific errors
    
    Args:
        exception: The exception to handle
        
    Returns:
        dict: Error response
    """
    logger.error(f"{module_name} error: {str(exception)}")
    
    if isinstance(exception, {class_prefix}Error):
        return {{
            "error_code": exception.error_code,
            "message": exception.message,
            "details": exception.details
        }}
    else:
        # Convert to module error if it's a different type
        module_error = {class_prefix}Error(message=str(exception))
        return {{
            "error_code": module_error.error_code,
            "message": module_error.message,
            "details": {{"original_type": exception.__class__.__name__}}
        }}
'''

VALIDATORS_TEMPLATE = '''"""
{module_name} Validators

This module provides data validation utilities for the {module_name} component.

Author: {author}
Version: {version}
"""

import re
import logging
from typing import Dict, Any, List, Union, Optional

# Configure logger
logger = logging.getLogger(__name__)

def validate_data(data: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validate input data for {module_name}
    
    Args:
        data: The data to validate
        
    Returns:
        dict: Dictionary of field validation errors, empty if valid
    """
    errors = {{}}
    
    # Validate required fields
    required_fields = ['field1', 'field2']
    for field in required_fields:
        if field not in data or not data[field]:
            if field not in errors:
                errors[field] = []
            errors[field].append(f"The {field} field is required")
    
    # Validate field1 if present
    if 'field1' in data and data['field1']:
        # Example validation
        if not isinstance(data['field1'], str):
            if 'field1' not in errors:
                errors['field1'] = []
            errors['field1'].append("The field1 must be a string")
    
    return errors

def is_valid_input(input_data: Dict[str, Any]) -> bool:
    """
    Check if input data is valid
    
    Args:
        input_data: The data to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    errors = validate_data(input_data)
    return len(errors) == 0
'''

ARCHITECTURE_TEMPLATE = '''# {module_name} Architecture

## Overview
This document describes the architecture of the {module_name} component within the CBS_PYTHON system.

## Design Principles
- List design principles

## Component Structure
The {module_name} component is organized into the following sub-components:

1. **Module Interface**: Central integration point with the system
2. **Service Layer**: Business logic implementation
3. **Data Layer**: Data storage and retrieval

## Interactions
Describe how this module interacts with other components in the system.

## Sequence Diagrams
Include or reference key sequence diagrams for important processes.

## Future Enhancements
Planned future enhancements for this module:

1. Feature A
2. Feature B
3. Performance optimizations
'''

CHANGELOG_TEMPLATE = '''# {module_name} Changelog

All notable changes to the {module_name} component will be documented in this file.

## [1.1.2] - {date}

### Added
- Initial implementation of the module
- Core functionality for feature X

### Changed
- None (initial release)

### Fixed
- None (initial release)
'''

TEST_MODULE_INTERFACE_TEMPLATE = '''"""
Tests for {module_name} module interface

This module contains tests for the {module_name} module interface.

Author: {author}
Version: {version}
"""

import pytest
from unittest.mock import MagicMock, patch

from {module_id}.module_interface import {class_name}Interface

def test_module_interface_initialization():
    """Test module interface initialization"""
    # Arrange & Act
    module = {class_name}Interface()
    
    # Assert
    assert module.name == "{module_id}"
    assert module.version == "{version}"

def test_register_services():
    """Test service registration"""
    # Arrange
    mock_registry = MagicMock()
    module = {class_name}Interface()
    
    # Mock the get_registry method
    module.get_registry = MagicMock(return_value=mock_registry)
    
    # Act
    module.register_services()
    
    # Assert
    assert mock_registry.register.call_count >= 0  # At least no errors
'''

EXAMPLE_TEMPLATE = '''"""
Example script for {module_name}

This example demonstrates how to use the {module_name} component.

Author: {author}
Version: {version}
"""

def main():
    """Example implementation demonstrating {module_name} usage"""
    print("Example {module_name} implementation")
    
    # Import module components
    # from {module_id} import SomeClass
    
    # Example usage
    # instance = SomeClass()
    # result = instance.some_method()
    # print(f"Result: {{result}}")

if __name__ == "__main__":
    main()
'''

def format_module_id(name):
    """Convert module name to module ID (snake_case)"""
    return name.lower().replace(' ', '_').replace('-', '_')

def format_class_name(name):
    """Convert module name to class name (PascalCase)"""
    words = name.split('_')
    return ''.join(word.title() for word in words)

def format_error_code_prefix(name):
    """Convert module name to error code prefix (UPPERCASE_SNAKE_CASE)"""
    return name.upper().replace(' ', '_').replace('-', '_')

def create_directory(path, exists_ok=True):
    """Create directory if it doesn't exist"""
    try:
        os.makedirs(path, exist_ok=exists_ok)
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {str(e)}")
        return False

def write_file(path, content):
    """Write content to file"""
    try:
        with open(path, 'w') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing file {path}: {str(e)}")
        return False

def create_module(name, description):
    """Create a new module with all required files and directories"""
    module_id = format_module_id(name)
    class_name = format_class_name(module_id)
    error_code_prefix = format_error_code_prefix(module_id)
    class_prefix = class_name
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Create module directory
    module_path = PROJECT_ROOT / module_id
    if not create_directory(module_path):
        return False
    
    # Create module files
    write_file(module_path / "__init__.py", 
               INIT_TEMPLATE.format(
                   module_name=name,
                   module_description=description,
                   author=GITHUB_USERNAME,
                   version=VERSION
               ))
               
    write_file(module_path / "module_interface.py", 
               MODULE_INTERFACE_TEMPLATE.format(
                   module_name=name,
                   module_id=module_id,
                   class_name=class_name,
                   author=GITHUB_USERNAME,
                   version=VERSION
               ))
               
    write_file(module_path / "config.py", 
               CONFIG_TEMPLATE.format(
                   module_name=name,
                   module_id=module_id,
                   author=GITHUB_USERNAME,
                   version=VERSION
               ))
               
    write_file(module_path / "README.md", 
               README_TEMPLATE.format(
                   module_name=name,
                   module_description=description,
                   module_id=module_id
               ))
    
    # Create utils subdirectory and files
    utils_path = module_path / "utils"
    if not create_directory(utils_path):
        return False
        
    write_file(utils_path / "__init__.py", 
               INIT_TEMPLATE.format(
                   module_name=f"{name} Utils",
                   module_description="utility functions for " + name,
                   author=GITHUB_USERNAME,
                   version=VERSION
               ))
               
    write_file(utils_path / "error_handling.py", 
               ERROR_HANDLING_TEMPLATE.format(
                   module_name=name,
                   error_code_prefix=error_code_prefix,
                   class_prefix=class_prefix,
                   author=GITHUB_USERNAME,
                   version=VERSION
               ))
               
    write_file(utils_path / "validators.py", 
               VALIDATORS_TEMPLATE.format(
                   module_name=name,
                   author=GITHUB_USERNAME,
                   version=VERSION
               ))
    
    # Create docs subdirectory and files
    docs_path = module_path / "docs"
    if not create_directory(docs_path):
        return False
        
    write_file(docs_path / "ARCHITECTURE.md", 
               ARCHITECTURE_TEMPLATE.format(
                   module_name=name
               ))
               
    write_file(docs_path / "CHANGELOG.md", 
               CHANGELOG_TEMPLATE.format(
                   module_name=name,
                   date=today
               ))
    
    # Create tests subdirectory and files
    tests_path = module_path / "tests"
    if not create_directory(tests_path):
        return False
        
    write_file(tests_path / "__init__.py", 
               INIT_TEMPLATE.format(
                   module_name=f"{name} Tests",
                   module_description="test suite for " + name,
                   author=GITHUB_USERNAME,
                   version=VERSION
               ))
               
    write_file(tests_path / "test_module_interface.py", 
               TEST_MODULE_INTERFACE_TEMPLATE.format(
                   module_name=name,
                   module_id=module_id,
                   class_name=class_name,
                   author=GITHUB_USERNAME,
                   version=VERSION
               ))
    
    # Create examples subdirectory and files
    examples_path = module_path / "examples"
    if not create_directory(examples_path):
        return False
        
    write_file(examples_path / f"example_{module_id}.py", 
               EXAMPLE_TEMPLATE.format(
                   module_name=name,
                   module_id=module_id,
                   author=GITHUB_USERNAME,
                   version=VERSION
               ))
    
    print(f"Module '{name}' created successfully in {module_path}")
    print("Files and directories created:")
    print(f"- {module_id}/__init__.py")
    print(f"- {module_id}/module_interface.py")
    print(f"- {module_id}/config.py")
    print(f"- {module_id}/README.md")
    print(f"- {module_id}/utils/__init__.py")
    print(f"- {module_id}/utils/error_handling.py")
    print(f"- {module_id}/utils/validators.py")
    print(f"- {module_id}/docs/ARCHITECTURE.md")
    print(f"- {module_id}/docs/CHANGELOG.md")
    print(f"- {module_id}/tests/__init__.py")
    print(f"- {module_id}/tests/test_module_interface.py")
    print(f"- {module_id}/examples/example_{module_id}.py")
    
    print("\nNext steps:")
    print("1. Implement the module functionality")
    print(f"2. Register the module in register_modules.py")
    print("3. Add unit tests for the module")
    print("4. Update the module documentation")
    
    return True

def update_register_modules(module_name):
    """Update register_modules.py to include the new module"""
    module_id = format_module_id(module_name)
    class_name = format_class_name(module_id)
    
    register_path = PROJECT_ROOT / "register_modules.py"
    
    try:
        # Read the existing file
        with open(register_path, 'r') as f:
            content = f.read()
        
        # Check if module is already registered
        if f"register_{module_id}" in content:
            print(f"Module '{module_name}' is already registered in register_modules.py")
            return True
        
        # Find the modules dictionary
        modules_dict = "modules = {"
        if modules_dict not in content:
            print(f"Could not find modules dictionary in register_modules.py")
            return False
        
        # Add import statement
        import_stmt = f"from {module_id}.module_interface import {class_name}Interface\n"
        imports_end = "# Import module interfaces"
        if imports_end in content:
            content = content.replace(imports_end, imports_end + "\n" + import_stmt)
        else:
            # Add after existing imports
            content = import_stmt + content
        
        # Add registration function
        register_func = f"""
def register_{module_id}():
    \"\"\"Register the {module_name} module\"\"\"
    module = {class_name}Interface()
    module.register_services()
    return module
"""
        # Add before modules dictionary
        modules_index = content.find(modules_dict)
        if modules_index > 0:
            content = content[:modules_index] + register_func + content[modules_index:]
        
        # Add to modules dictionary
        modules_entry = f'    "{module_id}": register_{module_id},\n'
        modules_end_index = content.find("}", modules_index)
        if modules_end_index > 0:
            content = content[:modules_end_index] + modules_entry + content[modules_end_index:]
        
        # Write the updated file
        with open(register_path, 'w') as f:
            f.write(content)
            
        print(f"Updated register_modules.py to include '{module_name}'")
        return True
    except Exception as e:
        print(f"Error updating register_modules.py: {str(e)}")
        return False

def create_custom_file(file_type, module_name, file_name, description=None):
    """Create a custom file based on file type"""
    if not description:
        description = f"{file_name} for {module_name}"
    
    module_id = format_module_id(module_name)
    class_name = format_class_name(file_name)
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Ensure the module directory exists
    module_path = PROJECT_ROOT / module_id
    if not os.path.isdir(module_path):
        print(f"Module directory '{module_id}' does not exist")
        return False
    
    file_content = ""
    file_path = None
    
    if file_type == "class":
        file_path = module_path / f"{format_module_id(file_name)}.py"
        file_content = f'''"""
{class_name} Class

This module provides the {class_name} class for {description}.

Author: {GITHUB_USERNAME}
Version: {VERSION}
"""

import logging
from typing import Dict, Any, List, Optional

# Configure logger
logger = logging.getLogger(__name__)

class {class_name}:
    """
    {class_name} class for {description}
    
    Description:
        This class implements functionality for {description}.
    
    Usage:
        instance = {class_name}(param1, param2)
        result = instance.method()
    """
    
    def __init__(self, param1: str, param2: Optional[int] = None):
        """
        Initialize the {class_name}
        
        Args:
            param1: Description of param1
            param2: Description of param2
        """
        self.param1 = param1
        self.param2 = param2
        logger.debug(f"{class_name} initialized with {param1}, {param2}")
    
    def method(self) -> Any:
        """
        Example method of {class_name}
        
        Returns:
            The result of the operation
        """
        logger.info(f"Executing {class_name}.method()")
        # Implementation
        return f"{{self.param1}}-{{self.param2 or 'default'}}"
'''
    
    elif file_type == "util":
        file_path = module_path / "utils" / f"{format_module_id(file_name)}.py"
        file_content = f'''"""
{file_name} Utility Functions

This module provides utility functions for {description}.

Author: {GITHUB_USERNAME}
Version: {VERSION}
"""

import logging
from typing import Dict, Any, List, Optional

# Configure logger
logger = logging.getLogger(__name__)

def utility_function(param: Any) -> Any:
    """
    Utility function for {description}
    
    Args:
        param: Description of the parameter
        
    Returns:
        The result of the operation
    """
    logger.debug(f"utility_function called with {param}")
    # Implementation
    return param
'''
    
    elif file_type == "test":
        test_name = file_name if file_name.startswith("test_") else f"test_{file_name}"
        file_path = module_path / "tests" / f"{test_name}.py"
        file_content = f'''"""
Tests for {description}

This module contains tests for {description}.

Author: {GITHUB_USERNAME}
Version: {VERSION}
"""

import pytest
from unittest.mock import MagicMock, patch

# Import the module to test
# from {module_id} import ClassName

def test_functionality_name():
    """Test specific functionality"""
    # Arrange
    # Create test data and expected results
    
    # Act
    # Call the function or method being tested
    
    # Assert
    # Check that the actual result matches the expected result
    assert True  # Replace with actual assertion
'''
    
    elif file_type == "example":
        example_name = file_name if file_name.startswith("example_") else f"example_{file_name}"
        file_path = module_path / "examples" / f"{example_name}.py"
        file_content = f'''"""
Example for {description}

This example demonstrates {description}.

Author: {GITHUB_USERNAME}
Version: {VERSION}
"""

def main():
    """Example implementation demonstrating {description}"""
    print("Example for {description}")
    
    # Import module components
    # from {module_id} import SomeClass
    
    # Example usage
    # instance = SomeClass()
    # result = instance.some_method()
    # print(f"Result: {{result}}")

if __name__ == "__main__":
    main()
'''
    
    elif file_type == "doc":
        file_path = module_path / "docs" / f"{file_name.upper()}.md"
        file_content = f'''# {file_name.replace('_', ' ').title()}

## Overview
This document provides {description}.

## Key Points
- Point 1
- Point 2
- Point 3

## Related Documents
- [README.md](../README.md)
- [ARCHITECTURE.md](./ARCHITECTURE.md)

## Version History
- {today}: Initial version
'''
    
    if file_path and file_content:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(file_path)
        if not os.path.isdir(parent_dir):
            create_directory(parent_dir)
        
        # Write the file
        result = write_file(file_path, file_content)
        if result:
            print(f"Created {file_type} file: {file_path}")
        return result
    
    print(f"Unknown file type: {file_type}")
    return False

def main():
    """Main function to parse arguments and execute commands"""
    parser = argparse.ArgumentParser(
        description="CBS_PYTHON Module Creator - Creates standardized files and directories"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Create module command
    module_parser = subparsers.add_parser("module", help="Create a new module")
    module_parser.add_argument("name", help="Name of the module")
    module_parser.add_argument("description", help="Brief description of the module")
    module_parser.add_argument("--register", action="store_true", help="Register the module in register_modules.py")
    
    # Create file command
    file_parser = subparsers.add_parser("file", help="Create a custom file")
    file_parser.add_argument("type", choices=["class", "util", "test", "example", "doc"], help="Type of file to create")
    file_parser.add_argument("module", help="Name of the module")
    file_parser.add_argument("name", help="Name of the file")
    file_parser.add_argument("description", nargs="?", help="Brief description of the file")
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == "module":
        result = create_module(args.name, args.description)
        if result and args.register:
            update_register_modules(args.name)
    
    elif args.command == "file":
        create_custom_file(args.type, args.module, args.name, args.description)

if __name__ == "__main__":
    main()
