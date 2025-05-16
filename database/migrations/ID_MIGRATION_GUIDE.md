# ID Format Migration Guide

This document provides information about the new ID formats implemented in the CBS_PYTHON system and the migration process to convert existing IDs to the new formats.

## New ID Formats

### Customer ID Format
**New Format**: `YYDDD-BBBBB-SSSS`
- YY: Last 2 digits of creation year
- DDD: Day of year (001-366)
- BBBBB: Branch code (5 digits)
- SSSS: Customer sequence number (4 digits)

### Account Number Format
**New Format**: `BBBBB-AATT-CCCCCC-CC`
- BBBBB: Branch code (5 digits)
- AA: Account type (01=Savings, 02=Current, etc.)
- TT: Account sub-type/product code (2 digits)
- CCCCCC: Customer serial number (6 digits)
- CC: Checksum (2 digits calculated using Luhn algorithm)

### Transaction ID Format
**New Format**: `TRX-YYYYMMDD-SSSSSS`
- TRX: Fixed prefix
- YYYYMMDD: Date (full year, month, day)
- SSSSSS: Sequence number (6 digits)

### Employee ID Format
**New Format**: `ZZBB-DD-EEEE` (Bank of Baroda style)
- ZZ: Zone code (2 digits, e.g., North = 01)
- BB: Branch or Department code (2 digits)
- DD: Designation code (2 digits)
- EEEE: Employee sequence number (4 digits)

## Migration Process

### Step 1: Update Models
We have updated the database models to reflect the new ID formats:
- Updated `Customer` model with new customer_id format
- Updated `Account` model with new account_number format
- Updated `Transaction` model with new transaction_id format
- Updated `EmployeeDirectory` model with new employee_id format

### Step 2: Update ID Generators
We have updated the ID generator functions to produce IDs in the new formats:
- Updated `generate_customer_id()` in id_generator.py
- Updated `generate_account_number()` in id_generator.py
- Updated `generate_transaction_id()` in id_generator.py
- Updated `generate_employee_id()` in id_generator.py

### Step 3: Update ID Validators
We have updated the ID validator functions to validate the new formats:
- Updated `validate_customer_id()` in id_validator.py
- Updated `validate_account_number()` in id_validator.py
- Updated `validate_transaction_id()` in id_validator.py
- Updated `validate_employee_id()` in id_validator.py

### Step 4: Create Migration Script
We have created a migration script to convert existing IDs to the new formats:
- Created `id_format_migration.py` script in database/migrations/
- Created mapping tables to track old and new IDs
- Implemented conversion functions for each ID type

## Running the Migration

### Test Mode
To test the migration script without making changes to the database:
```
python database/migrations/id_format_migration.py --dry-run
```

### Partial Migration
To migrate only specific ID types:
```
python database/migrations/id_format_migration.py --customers --dry-run
python database/migrations/id_format_migration.py --accounts --dry-run
python database/migrations/id_format_migration.py --transactions --dry-run
python database/migrations/id_format_migration.py --employees --dry-run
```

### Full Migration
To migrate all ID types:
```
python database/migrations/id_format_migration.py --all
```

## Post-Migration Tasks

After running the migration script, you should:

1. Update any frontend code that depends on the old ID formats
2. Update any API documentation to reflect the new ID formats
3. Update any reports or export functions to use the new formats
4. Test all functionality that interacts with these IDs

## ID Format Reference

### Account Type Codes
- 01: Savings Account
- 02: Current Account
- 03: Term Deposit (Fixed Deposit)
- 04: Recurring Deposit
- 05: Loan Account
- 06: Overdraft Account

### Employee Designation Codes
- 01: Teller
- 02: Clerk
- 03-04: Officer Scale I-II
- 05: Branch Manager
- 06: Zonal Manager 
- 07-08: Head Office Roles
- 99: IT Administrator
- 90: Internal Auditor

## Troubleshooting

If you encounter any issues during the migration process:

1. Check the mapping tables (`cbs_id_migration_*`) to see which records were migrated
2. Restore from backup if necessary
3. Contact the system administrator for assistance
