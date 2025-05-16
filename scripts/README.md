# Core Banking System Scripts

This directory contains scripts for deploying, maintaining, and managing the Core Banking System.

## Directory Structure

- **[Maintenance](./maintenance/README.md)** - Scripts for system maintenance, troubleshooting, and routine upkeep
  - **[Environment](./maintenance/environment/README.md)** - Environment validation and management
  - **[System](./maintenance/system/README.md)** - System checks and requirements verification
  - **[Database](./maintenance/database/README.md)** - Database maintenance tasks
  - **[Code](./maintenance/code/README.md)** - Code maintenance utilities

- **[Deployment](./deployment/README.md)** - Scripts for deploying and setting up the system
  - **[App](./deployment/app/README.md)** - Application deployment automation
  - **[Infrastructure](./deployment/infrastructure/README.md)** - Infrastructure installation
  - **[Database](./deployment/database/README.md)** - Database migration scripts

- **[Database Scripts](./database_scripts/README.md)** - Legacy database scripts location
  - Note: Active database scripts have been moved to maintenance/database and deployment/database

## Quick Reference

See the **[Script Index](./SCRIPT_INDEX.md)** for a comprehensive list of all available scripts and their purposes.

## Getting Started

To use these scripts:

1. Navigate to the appropriate directory based on your task:
   ```
   cd maintenance/  # For maintenance tasks
   cd deployment/   # For deployment tasks
   ```

2. Run the appropriate script:
   ```
   python validate_environment.py --verbose  # Example maintenance script
   python install_postgresql.py              # Example deployment script
   ```

## Best Practices

- Always run maintenance scripts in a non-production environment first
- Back up data before running database maintenance scripts
- Use the `--help` flag to understand script options and parameters
- Consider security implications when running deployment scripts
