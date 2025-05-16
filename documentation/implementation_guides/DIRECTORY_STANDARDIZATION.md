# Directory Structure Standardization

## Overview

As part of our Clean Architecture implementation, we've standardized the directory structure across the CBS_PYTHON project to follow Python best practices for package naming.

## Key Changes

1. **Removed Hyphenated Directories**: 
   - All directories with hyphens have been renamed to use underscores
   - This improves compatibility with Python's import system, which doesn't support hyphens in module names

2. **Standardized Naming Convention**:
   - All module and package names now follow PEP 8 naming guidelines
   - Consistent use of lowercase with underscores for all directories

3. **Eliminated Custom Import Hooks**:
   - Removed the need for custom import hooks or workarounds
   - Standard Python import statements now work directly

## Directory Mapping

| Before Standardization | After Standardization |
|------------------------|----------------------|
| `analytics-bi/`        | `analytics_bi/`      |
| `digital-channels/`    | `digital_channels/`  |
| `hr-erp/`              | `hr_erp/`            |
| `risk-compliance/`     | `risk_compliance/`   |
| `integration-interfaces/` | `integration_interfaces/` |
| `atm-switch/`          | `atm_switch/`        |
| `internet-banking/`    | `internet_banking/`  |
| `mobile-banking/`      | `mobile_banking/`    |
| `chatbot-whatsapp/`    | `chatbot_whatsapp/`  |
| `soap-apis/`           | `soap_apis/`         |
| `file-based/`          | `file_based/`        |
| `mq-interfaces/`       | `mq_interfaces/`     |

## Benefits

1. **Improved Import Compatibility**:
   - Standard Python imports work without special handling
   - No more reliance on custom import hooks

2. **Code Clarity**:
   - Consistent naming conventions make the codebase more readable
   - Easier for new developers to understand the project structure

3. **IDE Support**:
   - Better auto-completion and navigation in IDEs
   - Improved code analysis and refactoring tools

4. **Simplified Deployment**:
   - No special configuration needed for deployments
   - Standard Python tools work as expected

## Migration Guide

### Updating Imports

If you have existing code that uses the old hyphenated directory names, update your imports as follows:

```python
# Old imports (no longer works)
from digital-channels.atm-switch import transaction_processor

# New imports (standard Python syntax)
from digital_channels.atm_switch import transaction_processor
```

### Handling Missing Modules

If you encounter any missing module errors after the standardization:

1. Check that you're using underscores in import statements
2. Verify that all packages have `__init__.py` files
3. Make sure your import statements match the new directory structure

## Conclusion

The directory structure standardization simplifies the codebase and removes a layer of complexity that was previously required for handling hyphenated directory names. This change aligns our project with Python best practices and provides a more maintainable foundation for our Clean Architecture implementation.
