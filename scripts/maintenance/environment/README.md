# Environment Management Scripts

This directory contains scripts related to environment management, validation, and configuration.

## Scripts

- `validate_environment.py` - Enhanced environment validator that ensures the system is correctly configured
  - Features robust environment detection
  - Checks for configuration inconsistencies
  - Provides recommendations for issues
  - Run with `--verbose` flag for detailed information

- `show_environment.py` - Displays current environment information
  - Shows active environment settings
  - Lists configured variables
  - Helps diagnose environment-related issues

## Usage

```bash
python validate_environment.py --verbose
python show_environment.py
```
