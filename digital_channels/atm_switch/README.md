# ATM Switch Interface

This directory contains the ATM interface components for the Core Banking System.

## Components

- **ATM Interface**: Main interface for ATM operations
- **Card Processor**: Handles card reading and validation
- **Transaction Processor**: Processes ATM transactions
- **Receipt Generator**: Generates receipts for ATM transactions
- **PIN Management**: Handles PIN changes and validations

## Supported Operations

- Cash withdrawal
- Balance inquiry
- Mini statements
- PIN changes
- Funds transfer
- Card activation/deactivation

## Implementation Notes

- Implements ISO 8583 message format for ATM communications
- Supports EMV chip cards
- Includes fallback handling for magnetic stripe
- Maintains transaction logs for reconciliation
- Supports multi-currency operations
