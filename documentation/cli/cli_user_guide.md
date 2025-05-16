# CBS Command Line Interface (CLI)

This guide explains how to use the CBS Core Banking System's command-line interface for various banking operations.

## Installation

First, ensure you have installed the CBS_PYTHON package:

```bash
# Install from the project directory
pip install -e .

# Or install the specific dependencies
pip install -r requirements.txt
```

## General Usage

The CBS CLI follows this general pattern:

```bash
python -m scripts.cli.cbs_cli [options] <module> <command> [<args>...]
```

Where:
- `[options]` are global options like `--debug` or `--config`
- `<module>` is the banking module you want to use (e.g., accounts, customers)
- `<command>` is the specific operation you want to perform
- `[<args>...]` are the command-specific arguments

## Available Modules

The following modules are currently available in the CLI:

1. **accounts** - Account management operations
2. **customers** - Customer management operations (coming soon)
3. **loans** - Loan management operations (coming soon)
4. **transactions** - Transaction operations (coming soon)
5. **payments** - Payment processing operations (coming soon)
6. **upi** - UPI payment operations (coming soon)

## Global Options

The following global options are available for all commands:

- `--debug`: Enable debug logging
- `--config <file>`: Specify a custom configuration file
- `--version`: Show the version information and exit

## Module: Accounts

The accounts module provides commands for managing banking accounts.

### Commands

#### Create Account

Create a new bank account for a customer.

```bash
python -m scripts.cli.cbs_cli accounts create-account --customer-id <uuid> --account-type <type> [--initial-deposit <amount>] [--currency <code>]
```

Arguments:
- `--customer-id`: Customer ID (UUID format)
- `--account-type`: Type of account (choices: SAVINGS, CURRENT, FIXED_DEPOSIT, LOAN)
- `--initial-deposit`: Initial deposit amount (optional)
- `--currency`: Currency code (default: INR)

Example:
```bash
python -m scripts.cli.cbs_cli accounts create-account --customer-id 123e4567-e89b-12d3-a456-426614174000 --account-type SAVINGS --initial-deposit 5000
```

#### Get Account Details

Retrieve details for a specific account.

```bash
python -m scripts.cli.cbs_cli accounts get-account --account-id <uuid>
```

Arguments:
- `--account-id`: Account ID (UUID format)

Example:
```bash
python -m scripts.cli.cbs_cli accounts get-account --account-id 123e4567-e89b-12d3-a456-426614174000
```

#### Deposit Funds

Deposit funds into an account.

```bash
python -m scripts.cli.cbs_cli accounts deposit --account-id <uuid> --amount <amount> [--description <text>] [--reference-id <id>]
```

Arguments:
- `--account-id`: Account ID (UUID format)
- `--amount`: Amount to deposit
- `--description`: Transaction description (optional)
- `--reference-id`: External reference ID (optional)

Example:
```bash
python -m scripts.cli.cbs_cli accounts deposit --account-id 123e4567-e89b-12d3-a456-426614174000 --amount 1000 --description "Salary deposit"
```

#### Withdraw Funds

Withdraw funds from an account.

```bash
python -m scripts.cli.cbs_cli accounts withdraw --account-id <uuid> --amount <amount> [--description <text>] [--reference-id <id>]
```

Arguments:
- `--account-id`: Account ID (UUID format)
- `--amount`: Amount to withdraw
- `--description`: Transaction description (optional)
- `--reference-id`: External reference ID (optional)

Example:
```bash
python -m scripts.cli.cbs_cli accounts withdraw --account-id 123e4567-e89b-12d3-a456-426614174000 --amount 500 --description "ATM withdrawal"
```

#### Transfer Funds

Transfer funds between accounts.

```bash
python -m scripts.cli.cbs_cli accounts transfer --source-account-id <uuid> --target-account-id <uuid> --amount <amount> [--description <text>] [--reference-id <id>]
```

Arguments:
- `--source-account-id`: Source Account ID (UUID format)
- `--target-account-id`: Target Account ID (UUID format)
- `--amount`: Amount to transfer
- `--description`: Transaction description (optional)
- `--reference-id`: External reference ID (optional)

Example:
```bash
python -m scripts.cli.cbs_cli accounts transfer --source-account-id 123e4567-e89b-12d3-a456-426614174000 --target-account-id 876e4567-e89b-12d3-a456-426614174000 --amount 1000 --description "Rent payment"
```

## Coming Soon

Additional modules and commands are under development. Check back for updates on:

- Customer management operations
- Loan processing and management
- Transaction reporting and analysis
- Payment processing (NEFT, RTGS, etc.)
- UPI payment interfaces

## Troubleshooting

If you encounter issues with the CLI:

1. Try running with the `--debug` flag for more detailed logging.
2. Check the logs in the `logs/cbs_cli.log` file.
3. Ensure that your database configuration is correct.
4. Verify that your environment variables are set properly.

For more assistance, refer to the full documentation or open an issue on GitHub.