# Database Maintenance Scripts

This directory contains scripts for database maintenance, migration, and management.

## Scripts

- `manage_database.py` - Handles database migrations and maintenance tasks
  - Supports both migration and maintenance operations
  - Safe to use in all environments with proper privileges

## Usage

```bash
python manage_database.py

# When prompted, enter either:
# "migrate" - to run database migrations
# "maintain" - to perform database maintenance
```

## Notes

A reference to this script is available in the deployment directory for convenience:
`../../deployment/database_migrations.py`
