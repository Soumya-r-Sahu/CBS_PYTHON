# Maintenance Scripts

This directory contains scripts for maintaining and troubleshooting the Core Banking System.

## Directory Structure

### System Maintenance (`./system/`)
- `system_maintenance.py` - Performs routine system maintenance tasks
- `check_system_requirements.py` - Verifies system requirements for the CBS application
- `troubleshoot.py` - Helps diagnose common issues in the system

### Environment Management (`./environment/`)
- `validate_environment.py` - Enhanced environment validator for ensuring correct configuration
- `show_environment.py` - Displays current environment information

### Database Maintenance (`./database/`)
- `manage_database.py` - Handles database migrations and maintenance tasks

### Code Maintenance (`./code/`)
- `fix_indentation.py` - Fixes indentation issues in Python code

## Usage

Most scripts can be run directly:

```bash
python validate_environment.py --verbose
```

For help with a specific script:

```bash
python <script_name> --help
```
