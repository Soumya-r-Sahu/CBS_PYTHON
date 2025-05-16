# CBS_PYTHON Import System Documentation

## Overview

The Core Banking System (CBS_PYTHON) uses a centralized import manager to handle module imports across the project. This document explains how the import system works, how to use it correctly, and how to troubleshoot common import issues.

## Import Manager (`packages.py`)

The centralized import manager is implemented in `utils/lib/packages.py`. It provides the following features:

1. **Automatic Path Management**: Automatically adds the project root to `sys.path` so that modules can be imported from anywhere in the project.
2. **Module Caching**: Caches imported modules to improve performance when importing the same module multiple times.
3. **Fallback Mechanisms**: Provides fallbacks for when modules cannot be imported directly.
4. **Virtual Modules**: Creates virtual modules when a module cannot be found, to prevent crashes.
5. **Module Aliasing**: Supports module aliases for backward compatibility and convenience.
6. **Direct Environment Functions**: Provides direct access to common environment functions.
7. **Database Connection Helper**: Simplifies database connection management across the system.
8. **Singleton Pattern**: Uses a singleton pattern to ensure only one instance of the import manager is created.

## How to Use the Import System

### Basic Usage

At the top of your Python file, add:

```python
# Option 1: Recommended approach - import and use the import manager functions
from utils.lib.packages import import_module, fix_path

# Option 2: Fallback if the import manager is not yet available
try:
    from utils.lib.packages import fix_path
    fix_path()  # This adds the project root to sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))  # Adjust levels as needed
```

### Importing Modules

#### Standard Import

For straightforward imports, use the `import_module` function:

```python
from utils.lib.packages import import_module

# Import a module
config_module = import_module("app.config.settings")
```

#### Import with Fallback

For imports with custom fallback behavior:

```python
from utils.lib.packages import import_module

# Define a fallback for when the module is not found
class DummyConfig:
    DEBUG = False
    LOG_LEVEL = "INFO"

# Import with fallback
config_module = import_module("app.config.settings", fallback=DummyConfig())
```

#### Importing Specific Items

To import specific items from a module:

```python
from utils.lib.packages import import_from

# Import specific items
items = import_from("app.config.settings", "DEBUG", "LOG_LEVEL")
debug_mode = items["DEBUG"]
log_level = items["LOG_LEVEL"]
```

### Using Environment Functions

The import manager provides direct access to environment functions:

```python
from utils.lib.packages import (
    is_production, is_development, is_test,
    is_debug_enabled, get_environment_name, Environment
)

# Check the current environment
if is_production():
    # Production-specific code
elif is_development():
    # Development-specific code

# Use the Environment class
if get_environment_name() == Environment.PRODUCTION:
    # Production-specific code
```

### Database Connection

Use the database connection helper:

```python
from utils.lib.packages import get_database_connection

# Get the connection class
DBConnection = get_database_connection()

# Use the connection
with DBConnection().transaction() as (connection, cursor):
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
```

### Best Practices

1. **Always Use the Import Manager**: Avoid modifying `sys.path` directly in your code.
2. **Place Imports at the Top**: Add the import manager code at the top of your file.
3. **Use Try-Except**: Always wrap imports in try-except blocks to handle errors gracefully.
4. **Provide Fallbacks**: For critical components, provide fallback implementations.
5. **Keep Dependencies Minimal**: Avoid circular dependencies.

## Troubleshooting

### Common Issues

1. **Import Error for `utils.lib.packages`**: 
   - The import manager itself cannot be found. Make sure the file exists in the correct path.
   - Try using relative imports: `from ...utils.lib.packages import fix_path`

2. **Module Not Found Errors**:
   - The module you're trying to import doesn't exist or is not in the path.
   - Make sure you've called `fix_path()` before trying to import other modules.
   - Check that the module name is correct (including case).

3. **Circular Import Dependencies**:
   - If module A imports module B, and module B imports module A, you have a circular dependency.
   - Restructure your code to avoid circular dependencies.
   - Move imports within functions where needed.

### Testing the Import Manager

The project includes test scripts to verify the functionality:

```
python scripts/utilities/test_packages.py
```

This script will test the main features of the import manager and report any issues.

## Technical Details

### Import Manager Implementation

The import manager uses a singleton pattern to ensure only one instance is created and uses the following techniques:

1. **Project Root Detection**: It automatically finds the project root directory based on marker files.
2. **Module Path Mapping**: It creates a map of module paths for quick access.
3. **Module Caching**: It maintains a cache of imported modules for performance.
4. **Virtual Module Creation**: It creates virtual modules as fallbacks when real modules cannot be imported.
5. **Module Aliasing**: It supports module aliases for backward compatibility.

### Performance Considerations

The import manager is designed to have minimal performance impact:

1. **Singleton Pattern**: Ensures the import manager is initialized only once.
2. **Path Management**: Only adds the project root to sys.path once.
3. **Module Caching**: Caches imported modules to avoid repeated imports.
