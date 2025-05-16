# Application Deployment Scripts

This directory contains scripts for deploying the Core Banking System application.

## Scripts

- `deploy_app.py` - Deploys the Core Banking System application
  - Handles binary file copying
  - Sets up application configurations
  - Registers services
  
- `deploy_environment.py` - Sets up the environment for deployment
  - Configures environment variables
  - Sets up necessary paths
  - Ensures proper permissions

## Usage

```bash
python deploy_app.py --env=production
python deploy_environment.py --config=prod_config.yaml
```

## Deployment Process

1. First, run `deploy_environment.py` to set up the environment
2. Then run `deploy_app.py` to deploy the application
3. Verify the deployment with health checks

## Notes

- Always make sure infrastructure is set up before running these scripts
- Back up any existing deployment before running these scripts
