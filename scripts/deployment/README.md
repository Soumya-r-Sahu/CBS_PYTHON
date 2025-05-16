# Deployment Scripts

This directory contains scripts for deploying and setting up the Core Banking System.

## Directory Structure

### Application Deployment (`./app/`)
- `deploy_app.py` - Deploys the Core Banking System application
- `deploy_environment.py` - Sets up the environment for deployment

### Infrastructure Setup (`./infrastructure/`)
- `install_postgresql.py` - Installs and configures PostgreSQL database
- `setup_security.py` - Configures security settings for the system

### Database Deployment (`./database/`)
- `database_migrations.py` - Reference to the database migration script in the maintenance directory

## Usage

Most scripts require administrative privileges:

```bash
python install_postgresql.py --version=14
```

For help with a specific script:

```bash
python <script_name> --help
```

## Deployment Workflow

1. Install prerequisite software using `install_postgresql.py`
2. Set up security configurations using `setup_security.py`
3. Deploy the environment using `deploy_environment.py`
4. Deploy the application using `deploy_app.py`
