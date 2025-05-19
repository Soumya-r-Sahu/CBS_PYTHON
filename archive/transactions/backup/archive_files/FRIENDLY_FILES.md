# Banking System Friendly File Guide

This document explains the purpose of the user-friendly filenames in the Banking System.
These names make it easier to understand the system's structure and functionality.

## Core System Files

- **banking_system_server.py** - The main entry point for the entire banking system. This file starts and manages all banking services.
- **start_banking_server.py** - A simple script to launch the banking system with various configuration options.
- **config.py** - Central configuration file for the entire banking system.

## API and Controllers

- **banking_api_endpoints.py** - Defines all available banking API services and their URL structures.
- **customer_accounts_controller.py** - Handles customer account information and balances.
- **money_transfer_controller.py** - Manages money transfers, payments, and transaction history.

## Database Management

- **banking_database_manager.py** - Internal tool for managing database structure and maintenance.
- **update_banking_database.py** - User-friendly tool for safely updating the database schema.

## Using the Friendly Names

To start the banking system using the user-friendly files:

```powershell
# Start the full banking system
python start_banking_server.py

# Start just the API server
python start_banking_server.py --api-only

# Update the database safely
python Backend\scripts\deployment\database\update_banking_database.py
```

## Original File Mappings

For reference, here are the original technical filenames and their friendly replacements:

| Original Filename | User-Friendly Name |
|-------------------|-------------------|
| backend.py | banking_system_server.py |
| run_backend.py | start_banking_server.py |
| routes.py | banking_api_endpoints.py |
| account_controller.py | customer_accounts_controller.py |
| transaction_controller.py | money_transfer_controller.py |
| manage_database.py | banking_database_manager.py |
| run_migrations.py | update_banking_database.py |
