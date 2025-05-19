# Database SQL Structure

This directory contains all SQL files needed for the Core Banking System database setup.

## Directory Structure

```
sql/
├── schema/                 # Database schema definitions
│   └── main_schema.sql     # Consolidated schema with all table definitions
│
├── procedures/             # Stored procedures
│   ├── withdrawal_procedures.sql   # Withdrawal-related procedures
│   ├── transfer_procedures.sql     # Transfer-related procedures
│   └── triggers.sql                # Database triggers
│
├── id_standards/           # ID validation and generation functions
│   ├── banking_id_validation.sql   # Functions to validate banking IDs
│   ├── banking_id_generation.sql   # Functions to generate new banking IDs
│   └── international_id_standards.sql  # International banking standards
│
├── setup_database_new.sql  # Main setup script that imports all components
└── README.md               # This file
```

## Setup Instructions

To set up the database:

1. Start your MySQL/MariaDB server
2. Run the main setup script:
   ```
   mysql -u [username] -p < setup_database_new.sql
   ```

## File Descriptions

### Schema Files

- `main_schema.sql`: Contains all table definitions for the Core Banking System

### Procedure Files

- `withdrawal_procedures.sql`: Contains procedures for withdrawal operations
- `transfer_procedures.sql`: Contains procedures for fund transfer operations
- `triggers.sql`: Contains database triggers for various tables

### ID Standards Files

- `banking_id_validation.sql`: Functions to validate various banking IDs
- `banking_id_generation.sql`: Functions to generate new banking IDs
- `international_id_standards.sql`: Functions for international banking ID standards

## Development Guidelines

1. Add new tables to the appropriate schema file
2. Create new procedures in topic-specific files
3. Update the main setup script if adding new files
4. Test all changes before committing

## Version History

- 2025-05-19: Initial reorganization of SQL files
