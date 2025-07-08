# Database Deployment Scripts

This directory contains scripts for deploying and migrating the database for the Core Banking System.

## Scripts

- `database_migrations.py` - Reference to the database migration script in the maintenance directory
  - This is a convenience script that redirects to the main database management script
  - Handles database migrations during deployment

## Usage

```bash
python database_migrations.py
```

## Notes

This script is a reference to the main database management script located at:
```
../../maintenance/database/manage_database.py
```

For more comprehensive database management capabilities, use the original script directly.
