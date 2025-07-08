# Core Banking System Scripts Index

This document provides a quick reference to all scripts available in the CBS_PYTHON project.

## Maintenance Scripts

### Environment Management
- `maintenance/environment/validate_environment.py` - Validates environment configuration
- `maintenance/environment/show_environment.py` - Displays current environment settings

### Database Maintenance
- `maintenance/database/manage_database.py` - Handles database migrations and maintenance

### System Maintenance
- `maintenance/system/system_maintenance.py` - Performs routine system maintenance
- `maintenance/system/check_system_requirements.py` - Validates system requirements
- `maintenance/system/troubleshoot.py` - Diagnoses system issues

### Code Maintenance
- `maintenance/code/fix_indentation.py` - Fixes code indentation issues

## Deployment Scripts

### Application Deployment
- `deployment/app/deploy_app.py` - Deploys the CBS application
- `deployment/app/deploy_environment.py` - Sets up deployment environment

### Infrastructure Setup
- `deployment/infrastructure/install_postgresql.py` - Installs PostgreSQL
- `deployment/infrastructure/setup_security.py` - Configures security settings

### Database Deployment
- `deployment/database/database_migrations.py` - Handles database migrations (reference file)

## Quick Usage Guide

### Common Maintenance Tasks
```bash
# Validate environment
python maintenance/environment/validate_environment.py --verbose

# Database maintenance
python maintenance/database/manage_database.py
# Then select "maintain" when prompted

# System health check
python maintenance/system/check_system_requirements.py
```

### Common Deployment Tasks
```bash
# Install infrastructure
python deployment/infrastructure/install_postgresql.py

# Deploy application
python deployment/app/deploy_environment.py
python deployment/app/deploy_app.py

# Database migration
python deployment/database/database_migrations.py
# Or use directly:
python maintenance/database/manage_database.py
# Then select "migrate" when prompted
```
