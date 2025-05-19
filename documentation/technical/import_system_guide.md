# CBS_PYTHON Import System Guide

## Overview

This guide explains how to use the centralized import system in the CBS_PYTHON project. The import system solves common issues like:

1. **Path Resolution**: Ensuring imports work regardless of where the calling module is located
2. **Environment Detection**: Providing consistent environment detection across the codebase
3. **Module Importing**: Standardized approach to dynamic module imports

## Key Components

The import system is primarily implemented in `utils/lib/packages.py` and includes:

- **Path Fixing**: Functions to ensure the project root is in `sys.path`
- **Environment Detection**: Functions to detect and work with different environments
- **Dynamic Imports**: Functions for importing modules dynamically

## Basic Usage

### Standard Import Pattern

At the top of your Python file, use this pattern:

```python
# Import the core import system
from utils.lib.packages import fix_path, import_module
fix_path()  # Ensure project root is in sys.path

# Now you can import any module in the project
from core_banking.accounts.domain.models import Account
from payments.upi.services import UPIPaymentService
```

### Environment Detection

Use these functions to check the current environment:

```python
from utils.lib.packages import is_production, is_development, is_test

if is_production():
    # Use production settings
    db_host = PRODUCTION_DB_HOST
elif is_development():
    # Use development settings
    db_host = DEV_DB_HOST
elif is_test():
    # Use test settings
    db_host = TEST_DB_HOST
```

### Dynamic Module Importing

When you need to import modules dynamically:

```python
from utils.lib.packages import import_module

# Import a module dynamically
validator_module = import_module('utils.validators')
account_validator = import_module('core_banking.accounts.domain.validators.account_validator')

# Use the imported modules
is_valid = validator_module.is_valid_email(email)
is_valid_account = account_validator.is_valid_account_number(account_number)
```

## Migration from Legacy Import System

The project is migrating from a legacy import system (`app/lib/import_manager.py`) to the new centralized system (`utils/lib/packages.py`).

### Identifying Legacy Import Usage

Look for patterns like:

```python
# Legacy import pattern (replace with new system)
from app.lib.import_manager import fix_path, import_component
fix_path()
```

### Replacing with New System

Replace legacy patterns with:

```python
# New import system
from utils.lib.packages import fix_path, import_module
fix_path()
```

## Best Practices

1. **Always Use fix_path()**: Add this at the top of your modules to ensure imports work
2. **Standardize Imports**: Use the centralized import system in all new modules
3. **Avoid sys.path Manipulation**: Don't manually modify sys.path; use fix_path() instead
4. **Check Environment Properly**: Use the provided environment detection functions

## Common Issues and Solutions

### Module Not Found Errors

If you encounter "ModuleNotFoundError", ensure:
1. You've called `fix_path()` at the top of your module
2. The module you're importing exists and has the correct name
3. All parent directories have `__init__.py` files

### Environment Detection Issues

If environment detection seems incorrect:
1. Check that you're using the functions from `utils.lib.packages`
2. Verify the environment variables are set correctly
3. Check for overrides in your configuration

---

*Last Updated: May 19, 2025 (v1.1.1)*
