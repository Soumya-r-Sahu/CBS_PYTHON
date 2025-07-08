# ATM Switch CLI Interface - Usage Guide

## Overview

The ATM Switch CLI Interface provides a command-line interface for interacting with the ATM system. This module is built following Clean Architecture principles, ensuring separation of concerns and easy maintenance.

## Features

- Card validation and PIN verification
- Cash withdrawal
- Balance inquiry
- Mini statement (transaction history)
- PIN change
- Session timeout handling (automatic logout after 3 minutes of inactivity)
- Input validation

## Running the CLI Interface

To start the ATM CLI interface, run:

```bash
python -m digital_channels.atm_switch.presentation.cli.atm_interface
```

## Usage Instructions

### 1. Insert Card & Enter PIN

- Enter your card number (16-19 digits)
- Enter your PIN (4-6 digits)
- Upon successful validation, a session is created

### 2. Withdraw Cash

- Select option 2 from the main menu
- Enter the amount to withdraw (must be a multiple of 10)
- The system will:
  - Validate the amount
  - Check for sufficient funds
  - Process the transaction
  - Display updated balance and transaction ID

### 3. Check Balance

- Select option 3 from the main menu
- The system will display:
  - Available balance
  - Ledger balance
  - Last updated timestamp

### 4. Mini Statement

- Select option 4 from the main menu
- The system will display:
  - Last 10 transactions with:
    - Date
    - Description
    - Amount
    - Running balance
  - Current available balance

### 5. Change PIN

- Select option 5 from the main menu
- Enter your current PIN
- Enter your new PIN
- Confirm your new PIN
- Confirm the change by typing 'YES'
- For security, the session ends after PIN change

### 6. Exit

- Select option 6 to log out and exit the system

## Security Features

- **Session Timeout**: Automatic logout after 3 minutes of inactivity
- **PIN Protection**: PIN is never displayed on screen
- **Input Validation**: All inputs are validated to prevent errors and security issues
- **Automatic Logout**: System logs out after sensitive operations
- **Error Handling**: Graceful handling of errors with user-friendly messages

## Error Handling

The system provides clear error messages for common issues:

- Invalid card number or PIN
- Insufficient funds
- Invalid amount (not a multiple of 10)
- Session timeout
- System errors

## Note for Developers

The CLI interface follows Clean Architecture principles:

- Presentation Layer: Handles user interaction only
- Application Layer: Contains use cases and services
- Domain Layer: Holds business rules and entities
- Infrastructure Layer: Provides data access and external services

When extending the CLI, maintain this separation of concerns to ensure maintainability.
