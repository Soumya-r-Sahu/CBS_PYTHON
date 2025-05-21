# Centralized Utilities Implementation Guide

## Overview

This guide explains the new centralized utility system implemented in the Core Banking System (CBS). The goal of this centralization is to:

1. Reduce code duplication across modules
2. Ensure consistent error handling and validation
3. Make the codebase more maintainable and easier to update
4. Provide a consistent API for common operations

## Key Changes

### 1. Centralized Error Handling

The error handling system has been centralized in `utils/error_handling.py`. This provides:

- A consistent base error class (`CBSError`)
- Standardized error types for common scenarios
- Consistent error response formatting
- Unified logging approach

Module-specific error classes now extend the centralized base classes, ensuring both consistency and module-specific customization.

### 2. Centralized Validation

Validation utilities have been centralized in `utils/validators.py`. This includes:

- Common data validation functions (account numbers, amounts, dates, etc.)
- Standard validation patterns and regular expressions
- Rich metadata for AI-powered analysis
- Consistent return patterns for all validators

### 3. Import System

The import system has been updated to expose the centralized utilities directly from the `utils` package. You can now import them directly:

```python
# Old way
from utils.common.validators import validate_account_number
from utils.common.error_handling import handle_exception

# New way
from utils import validate_account_number, handle_exception
```

Legacy imports still work but are deprecated and will be removed in future versions.

## How to Use

### Error Handling

For module-specific error handling, extend the centralized error classes:

```python
from utils.error_handling import CBSError, ValidationError

class MyModuleError(CBSError):
    """Base exception class for my module"""
    
    def __init__(self, 
                 message: str, 
                 error_code: str = "MY_MODULE_ERROR", 
                 status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
                 context: Optional[Dict[str, Any]] = None,
                 details: Optional[str] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            context=context,
            details=details
        )
```

### Validation

For validation, use the centralized validators directly:

```python
from utils import validate_account_number, validate_amount

def process_transfer(account_number, amount):
    # Validate inputs
    is_valid, error_message = validate_account_number(account_number)
    if not is_valid:
        raise ValidationError(f"Invalid account number: {error_message}", field="account_number")
    
    is_valid, error_message, amount = validate_amount(amount)
    if not is_valid:
        raise ValidationError(f"Invalid amount: {error_message}", field="amount")
    
    # Process the transfer...
```

## Migration Guide

### Updating Existing Code

1. Replace module-specific validation functions with centralized ones
2. Update error handling to extend the centralized base classes
3. Update imports to use the centralized system

You can use the utility scripts in the `scripts` directory to help with this migration:

- `utility_migration.py`: Assists with migrating to centralized utilities
- `cleanup_utility.py`: Cleans up unnecessary files and updates imports

### Creating New Modules

When creating new modules:

1. Create a module-specific `utils` directory with:
   - `__init__.py`
   - `error_handling.py` (extending the centralized error classes)
   - Module-specific utilities as needed

2. Import centralized utilities directly:
   ```python
   from utils import validate_account_number, handle_exception
   ```

3. Add AI-friendly metadata to all new code:
   ```python
   """
   My function description

   AI-Metadata:
       component_type: validator
       criticality: high
       purpose: account_validation
   """
   ```

## Best Practices

1. **Avoid Duplication**: If you need a utility function, check if it already exists in the centralized utilities before creating a new one.

2. **Extend, Don't Replace**: When you need custom behavior, extend the centralized classes rather than replacing them.

3. **Consistent Error Handling**: Use the centralized error classes for all error handling.

4. **Add Metadata**: Include AI-friendly metadata in all new code.

5. **Keep Module-Specific Logic Separate**: Only centralize utilities that are truly common across modules.

## Troubleshooting

### Import Errors

If you encounter import errors:

1. Check that you're importing from the correct location
2. Ensure the module you're importing exists
3. Check for circular imports

### Runtime Errors

If you encounter runtime errors:

1. Check that you're using the correct parameters for centralized functions
2. Ensure that you're handling errors consistently
3. Check for type mismatches

## Contact

For questions or issues with the centralized utilities, contact the system architecture team.
