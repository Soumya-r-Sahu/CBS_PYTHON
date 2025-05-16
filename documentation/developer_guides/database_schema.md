# CBS Database Schema

This document provides an overview of the database schema used in the Core Banking System.

## Schema Overview

The CBS_PYTHON database is organized around banking domain entities with clear relationships between tables. The database schema follows third normal form (3NF) for optimal data integrity and performance.

## Environment-Specific Table Naming

In development and test environments, tables are prefixed with the environment name to prevent data conflicts:

| Environment | Table Name Example |
|-------------|-------------------|
| Development | `development_customers` |
| Test | `test_customers` |
| Production | `customers` |

## Core Banking Tables

### Customers

Stores customer information and serves as the central entity for customer relationships.

| Column | Type | Description |
|--------|------|-------------|
| customer_id | UUID | Primary key |
| first_name | VARCHAR(100) | Customer's first name |
| last_name | VARCHAR(100) | Customer's last name |
| date_of_birth | DATE | Date of birth |
| email | VARCHAR(255) | Email address |
| phone | VARCHAR(20) | Phone number |
| address | TEXT | Physical address |
| kyc_status | ENUM | KYC verification status (PENDING, VERIFIED, REJECTED) |
| risk_category | ENUM | Risk categorization (LOW, MEDIUM, HIGH) |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Record update timestamp |
| is_active | BOOLEAN | Account status (active/inactive) |

### Accounts

Stores account information linked to customers.

| Column | Type | Description |
|--------|------|-------------|
| account_id | UUID | Primary key |
| account_number | VARCHAR(20) | Unique account number (human-readable) |
| customer_id | UUID | Foreign key to customers table |
| account_type | ENUM | Type of account (SAVINGS, CURRENT, FIXED_DEPOSIT, LOAN) |
| balance | DECIMAL(18,2) | Current balance |
| currency | VARCHAR(3) | Currency code (ISO 4217) |
| interest_rate | DECIMAL(5,2) | Interest rate percentage |
| created_at | TIMESTAMP | Account creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| status | ENUM | Account status (ACTIVE, INACTIVE, CLOSED, FROZEN) |
| branch_id | UUID | Foreign key to branch table |

### Transactions

Records all financial transactions in the system.

| Column | Type | Description |
|--------|------|-------------|
| transaction_id | UUID | Primary key |
| transaction_reference | VARCHAR(50) | Unique reference number |
| account_id | UUID | Foreign key to accounts table |
| transaction_type | ENUM | Type (DEPOSIT, WITHDRAWAL, TRANSFER, INTEREST, FEE) |
| amount | DECIMAL(18,2) | Transaction amount |
| currency | VARCHAR(3) | Currency code |
| balance_after | DECIMAL(18,2) | Account balance after transaction |
| description | TEXT | Transaction description |
| created_at | TIMESTAMP | Transaction timestamp |
| status | ENUM | Status (PENDING, COMPLETED, FAILED, REVERSED) |
| reference_id | VARCHAR(255) | External reference ID |
| reversing_transaction_id | UUID | ID of transaction that reverses this one (if applicable) |

### Account Relationships

Links between accounts (for transfers, joint accounts, etc.)

| Column | Type | Description |
|--------|------|-------------|
| relationship_id | UUID | Primary key |
| primary_account_id | UUID | Foreign key to accounts table |
| related_account_id | UUID | Foreign key to accounts table |
| relationship_type | ENUM | Type (JOINT, NOMINEE, TRANSFER_AUTHORIZED) |
| created_at | TIMESTAMP | Relationship creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| is_active | BOOLEAN | Whether the relationship is active |

## Loans Tables

### Loans

Stores loan information linked to customers.

| Column | Type | Description |
|--------|------|-------------|
| loan_id | UUID | Primary key |
| loan_account_id | UUID | Foreign key to accounts table |
| customer_id | UUID | Foreign key to customers table |
| loan_type | ENUM | Type (PERSONAL, HOME, VEHICLE, EDUCATION, BUSINESS) |
| principal_amount | DECIMAL(18,2) | Original loan amount |
| interest_rate | DECIMAL(5,2) | Annual interest rate |
| term_months | INTEGER | Loan term in months |
| emi_amount | DECIMAL(18,2) | Equated Monthly Installment amount |
| disbursement_date | DATE | Date when loan was disbursed |
| maturity_date | DATE | Loan maturity date |
| current_balance | DECIMAL(18,2) | Current outstanding balance |
| status | ENUM | Status (APPLIED, APPROVED, DISBURSED, COMPLETED, DEFAULTED) |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Record update timestamp |

### Loan Payments

Records payments made against loans.

| Column | Type | Description |
|--------|------|-------------|
| payment_id | UUID | Primary key |
| loan_id | UUID | Foreign key to loans table |
| transaction_id | UUID | Foreign key to transactions table |
| payment_date | DATE | Date of payment |
| amount | DECIMAL(18,2) | Payment amount |
| principal_component | DECIMAL(18,2) | Amount applied to principal |
| interest_component | DECIMAL(18,2) | Amount applied to interest |
| penalties | DECIMAL(18,2) | Penalties applied |
| balance_after | DECIMAL(18,2) | Loan balance after payment |
| payment_method | ENUM | Method (CASH, TRANSFER, CHEQUE, AUTO_DEBIT) |
| status | ENUM | Status (PENDING, PROCESSED, FAILED, REVERSED) |

## KYC Tables

### KYC Documents

Stores customer KYC document information.

| Column | Type | Description |
|--------|------|-------------|
| document_id | UUID | Primary key |
| customer_id | UUID | Foreign key to customers table |
| document_type | ENUM | Type (ID_PROOF, ADDRESS_PROOF, INCOME_PROOF, PHOTO) |
| document_number | VARCHAR(100) | Document identifier |
| issuing_authority | VARCHAR(255) | Authority that issued the document |
| issue_date | DATE | Date of issue |
| expiry_date | DATE | Date of expiry |
| verification_status | ENUM | Status (PENDING, VERIFIED, REJECTED) |
| verification_date | TIMESTAMP | Date of verification |
| verification_notes | TEXT | Notes from verification process |
| document_hash | VARCHAR(255) | Hash of the document for integrity |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Record update timestamp |

## Payment System Tables

### UPI Registrations

Stores UPI registration information.

| Column | Type | Description |
|--------|------|-------------|
| upi_id | UUID | Primary key |
| virtual_payment_address | VARCHAR(255) | UPI ID (e.g., username@bankcode) |
| customer_id | UUID | Foreign key to customers table |
| account_id | UUID | Foreign key to accounts table |
| device_id | VARCHAR(255) | Device used for registration |
| mobile_number | VARCHAR(20) | Linked mobile number |
| status | ENUM | Status (ACTIVE, INACTIVE, BLOCKED) |
| created_at | TIMESTAMP | Registration timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| last_used_at | TIMESTAMP | Last usage timestamp |

### UPI Transactions

Records UPI payment transactions.

| Column | Type | Description |
|--------|------|-------------|
| upi_transaction_id | UUID | Primary key |
| transaction_id | UUID | Foreign key to transactions table |
| sender_vpa | VARCHAR(255) | Sender's Virtual Payment Address |
| receiver_vpa | VARCHAR(255) | Receiver's Virtual Payment Address |
| amount | DECIMAL(18,2) | Transaction amount |
| reference_id | VARCHAR(255) | UPI reference ID |
| transaction_note | VARCHAR(255) | Transaction note |
| status | ENUM | Status (INITIATED, COMPLETED, FAILED, EXPIRED) |
| created_at | TIMESTAMP | Transaction timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

## System Tables

### Branches

Stores branch information.

| Column | Type | Description |
|--------|------|-------------|
| branch_id | UUID | Primary key |
| branch_name | VARCHAR(255) | Branch name |
| branch_code | VARCHAR(20) | Unique branch code |
| address | TEXT | Branch address |
| contact_number | VARCHAR(20) | Contact number |
| manager_id | UUID | Manager's employee ID |
| status | ENUM | Status (ACTIVE, INACTIVE) |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Record update timestamp |

### Audit Logs

Tracks all audit-worthy actions in the system.

| Column | Type | Description |
|--------|------|-------------|
| log_id | UUID | Primary key |
| user_id | UUID | User who performed the action |
| user_type | ENUM | Type (CUSTOMER, EMPLOYEE, SYSTEM) |
| action | VARCHAR(255) | Action performed |
| entity_type | VARCHAR(100) | Type of entity affected |
| entity_id | UUID | ID of entity affected |
| old_values | JSONB | Previous values before change |
| new_values | JSONB | New values after change |
| ip_address | VARCHAR(45) | User's IP address |
| user_agent | VARCHAR(255) | User's browser/app info |
| timestamp | TIMESTAMP | When the action occurred |
| status | ENUM | Status (SUCCESS, FAILURE) |
| notes | TEXT | Additional information |

## Database Relationships Diagram

![Database Schema Diagram](database_schema.png)

*Note: You will need to add this diagram image file after GitHub repository setup.*

## Entity Relationships

- One **Customer** can have multiple **Accounts**
- One **Customer** can have multiple **KYC Documents**
- One **Customer** can have multiple **Loans**
- One **Account** can have multiple **Transactions**
- One **Loan** can have multiple **Loan Payments**
- One **Customer** can have multiple **UPI Registrations**
- One **Account** can have one **UPI Registration**
- One **UPI Registration** can have multiple **UPI Transactions**

## Environment Setup Notes

The database schema is managed through SQLAlchemy ORM and Alembic migrations. When initializing the system, the appropriate tables will be created for the current environment:

```bash
# Initialize database for the current environment
python main.py --init-db
```

## Database Management

Database management tools are located in `database/` directory:
- SQL scripts for initial setup: `database/sql/`
- Migration scripts: `database/migrations/`
- Backup tools: `database/backups/`

## Related Documentation

- [Database Setup Guide](database_setup.md)
- [Migration Management](migration_management.md)
- [Database Best Practices](database_best_practices.md)