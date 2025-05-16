# CBS Command-Line Interface (CLI)

This directory contains the centralized Command-Line Interface (CLI) implementation for the Core Banking System.

## Overview

The CBS CLI provides a unified command-line interface to interact with all modules of the Core Banking System. It serves as a central entry point for various banking operations through the command line.

## Structure

```
cli/
├── cbs_cli.py                # Main CLI entry point
└── __init__.py               # Package initialization
```

## Features

- **Unified Command Interface**: Single entry point for all banking modules
- **Dynamic Module Loading**: Loads module-specific CLIs on demand
- **Consistent Command Structure**: Standard command format across all modules
- **Environment-Aware Operation**: Adapts to development, test, and production environments
- **Comprehensive Logging**: Detailed logging for troubleshooting

## Usage

```bash
python -m scripts.cli.cbs_cli [options] <module> <command> [<args>...]
```

### Global Options

- `--debug`: Enable debug logging
- `--config <file>`: Specify a custom configuration file
- `--version`: Show version and exit

### Available Modules

Currently implemented modules:
- `accounts`: Account management operations
- `customers`: Customer management operations (coming soon)
- `loans`: Loan management operations (coming soon)
- `transactions`: Transaction operations (coming soon)
- `payments`: Payment processing operations (coming soon)
- `upi`: UPI payment operations (coming soon)

### Example Commands

```bash
# Get help
python -m scripts.cli.cbs_cli --help

# Check version and available modules
python -m scripts.cli.cbs_cli --version

# Create a new account
python -m scripts.cli.cbs_cli accounts create-account --customer-id <uuid> --account-type SAVINGS --initial-deposit 5000

# Get account details
python -m scripts.cli.cbs_cli accounts get-account --account-id <uuid>

# Transfer funds
python -m scripts.cli.cbs_cli accounts transfer --source-account-id <uuid> --target-account-id <uuid> --amount 1000 --description "Rent payment"
```

## Implementation Details

The CBS CLI follows Clean Architecture principles:

1. **Presentation Layer**: The CLI is part of the presentation layer of the Clean Architecture implementation
2. **Command Routing**: Commands are routed to the appropriate module-specific CLI implementation
3. **Module Integration**: Each banking module integrates with the central CLI through a standard interface
4. **Command Processing**: Commands are processed by the appropriate module's use cases

## Adding New Modules

To add a new module to the CLI:

1. Implement a module-specific CLI in the module's presentation layer
2. Ensure the module CLI provides a `setup_cli()` function that returns an `ArgumentParser`
3. Register the module in the `load_cli_module` function in `cbs_cli.py`

## Documentation

For detailed documentation, refer to:
- [CLI User Guide](../../documentation/cli/cli_user_guide.md)
- [Module-Specific CLI Commands](../../documentation/cli/module_commands.md)