# Infrastructure Deployment Scripts

This directory contains scripts for setting up and configuring the infrastructure for the Core Banking System.

## Scripts

- `install_postgresql.py` - Installs and configures PostgreSQL database
  - Installs PostgreSQL with specified version
  - Sets up database users and permissions
  - Configures database settings

- `setup_security.py` - Configures security settings for the system
  - Sets up firewall rules
  - Configures SSL/TLS
  - Implements security policies

## Usage

```bash
python install_postgresql.py --version=14 --username=admin --password=secure_password
python setup_security.py --config=security_config.yaml
```

## Requirements

- Administrative privileges are required to run these scripts
- Internet connectivity for downloading necessary packages
- Sufficient disk space for installations
