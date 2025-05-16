# Module-Specific CLI Commands

This document provides detailed reference information for each module's CLI commands in the CBS system.

## Accounts Module

The Accounts module provides commands for managing banking accounts.

### `create-account`

Creates a new bank account for a specified customer.

**Usage:**
```bash
python -m scripts.cli.cbs_cli accounts create-account --customer-id <uuid> --account-type <type> [--initial-deposit <amount>] [--currency <code>]
```

**Parameters:**
- `--customer-id`: Customer ID (UUID format) [Required]
- `--account-type`: Type of account [Required]
  - Valid options: `SAVINGS`, `CURRENT`, `FIXED_DEPOSIT`, `LOAN`
- `--initial-deposit`: Initial deposit amount (Decimal) [Optional]
- `--currency`: Currency code (Default: INR) [Optional]

**Examples:**
```bash
# Create a savings account with an initial deposit
python -m scripts.cli.cbs_cli accounts create-account --customer-id 123e4567-e89b-12d3-a456-426614174000 --account-type SAVINGS --initial-deposit 5000

# Create a current account in USD currency
python -m scripts.cli.cbs_cli accounts create-account --customer-id 123e4567-e89b-12d3-a456-426614174000 --account-type CURRENT --currency USD
```

### `get-account`

Retrieves details for a specific account.

**Usage:**
```bash
python -m scripts.cli.cbs_cli accounts get-account --account-id <uuid>
```

**Parameters:**
- `--account-id`: Account ID (UUID format) [Required]

**Examples:**
```bash
python -m scripts.cli.cbs_cli accounts get-account --account-id 456e4567-e89b-12d3-a456-426614174000
```

### `deposit`

Deposits funds into an account.

**Usage:**
```bash
python -m scripts.cli.cbs_cli accounts deposit --account-id <uuid> --amount <amount> [--description <text>] [--reference-id <id>]
```

**Parameters:**
- `--account-id`: Account ID (UUID format) [Required]
- `--amount`: Amount to deposit (Decimal) [Required]
- `--description`: Transaction description [Optional]
- `--reference-id`: External reference ID [Optional]

**Examples:**
```bash
# Simple deposit
python -m scripts.cli.cbs_cli accounts deposit --account-id 456e4567-e89b-12d3-a456-426614174000 --amount 1000

# Deposit with description
python -m scripts.cli.cbs_cli accounts deposit --account-id 456e4567-e89b-12d3-a456-426614174000 --amount 1000 --description "Salary deposit"

# Deposit with reference ID
python -m scripts.cli.cbs_cli accounts deposit --account-id 456e4567-e89b-12d3-a456-426614174000 --amount 1000 --description "Salary deposit" --reference-id SALARY-MAY-2025
```

### `withdraw`

Withdraws funds from an account.

**Usage:**
```bash
python -m scripts.cli.cbs_cli accounts withdraw --account-id <uuid> --amount <amount> [--description <text>] [--reference-id <id>]
```

**Parameters:**
- `--account-id`: Account ID (UUID format) [Required]
- `--amount`: Amount to withdraw (Decimal) [Required]
- `--description`: Transaction description [Optional]
- `--reference-id`: External reference ID [Optional]

**Examples:**
```bash
# Simple withdrawal
python -m scripts.cli.cbs_cli accounts withdraw --account-id 456e4567-e89b-12d3-a456-426614174000 --amount 500

# Withdrawal with description
python -m scripts.cli.cbs_cli accounts withdraw --account-id 456e4567-e89b-12d3-a456-426614174000 --amount 500 --description "ATM withdrawal"
```

### `transfer`

Transfers funds between accounts.

**Usage:**
```bash
python -m scripts.cli.cbs_cli accounts transfer --source-account-id <uuid> --target-account-id <uuid> --amount <amount> [--description <text>] [--reference-id <id>]
```

**Parameters:**
- `--source-account-id`: Source Account ID (UUID format) [Required]
- `--target-account-id`: Target Account ID (UUID format) [Required]
- `--amount`: Amount to transfer (Decimal) [Required]
- `--description`: Transaction description [Optional]
- `--reference-id`: External reference ID [Optional]

**Examples:**
```bash
# Simple transfer
python -m scripts.cli.cbs_cli accounts transfer --source-account-id 123e4567-e89b-12d3-a456-426614174000 --target-account-id 987e4567-e89b-12d3-a456-426614174000 --amount 1000

# Transfer with description
python -m scripts.cli.cbs_cli accounts transfer --source-account-id 123e4567-e89b-12d3-a456-426614174000 --target-account-id 987e4567-e89b-12d3-a456-426614174000 --amount 1000 --description "Rent payment"
```

## Customer Management Module (Coming Soon)

The Customer Management module will provide commands for managing customer information.

Planned commands:
- `create-customer`: Create a new customer
- `get-customer`: Get customer details
- `update-customer`: Update customer information
- `list-customers`: List all customers
- `kyc-update`: Update customer KYC information

## Loans Module (Coming Soon)

The Loans module will provide commands for loan management.

Planned commands:
- `create-loan-application`: Create a new loan application
- `get-loan`: Get loan details
- `make-payment`: Make a loan payment
- `get-payment-schedule`: Get loan payment schedule
- `calculate-emi`: Calculate loan EMI

## Transactions Module (Coming Soon)

The Transactions module will provide commands for transaction management.

Planned commands:
- `get-transaction`: Get transaction details
- `list-transactions`: List transactions for an account
- `reverse-transaction`: Reverse a transaction
- `export-transactions`: Export transactions to a file

## Payments Module (Coming Soon)

The Payments module will provide commands for payment processing.

Planned commands:
- `neft-transfer`: Initiate NEFT transfer
- `rtgs-transfer`: Initiate RTGS transfer
- `imps-transfer`: Initiate IMPS transfer
- `schedule-payment`: Schedule a future payment

## UPI Module (Coming Soon)

The UPI module will provide commands for UPI payment operations.

Planned commands:
- `register-upi`: Register UPI ID
- `verify-upi`: Verify UPI ID
- `upi-transfer`: Make UPI transfer
- `collect-request`: Create collect request