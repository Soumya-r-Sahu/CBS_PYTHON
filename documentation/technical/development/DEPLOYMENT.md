# Deployment Guide

This guide explains how to deploy the Core Banking System in different environments.

## Environment Types

The CBS_PYTHON system supports three deployment environments:

1. **Development**: Local development environment
2. **Test**: Testing/QA environment
3. **Production**: Live production environment

## Prerequisites

Before deploying, ensure you have:

- Python 3.8+ (3.10+ recommended for production)
- PostgreSQL 13+ (for test/production environments)
- Sufficient storage for database and logs
- Network connectivity for external integrations

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/CBS_PYTHON.git
cd CBS_PYTHON
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Create an environment-specific `.env` file:

```bash
cp .env.example .env
# Edit .env with appropriate settings for your environment
```

Key configurations to update:
- `CBS_ENVIRONMENT`: Set to `development`, `test`, or `production`
- Database connection parameters
- JWT secret (use a strong random value in production)
- SMTP settings (for email notifications)
- External API endpoints

### 5. Initialize Database

```bash
# For first-time setup
python main.py --init-db

# For applying migrations to existing database
alembic upgrade head
```

### 6. Environment-Specific Configurations

#### Development Environment

For development, you can use SQLite as the database:

```
CBS_ENVIRONMENT=development
CBS_DB_TYPE=sqlite
CBS_DB_NAME=cbs_dev.db
```

Development environment features:
- Debug logging enabled
- Relaxed security constraints
- Sample data generation tools
- Auto-reload for code changes

#### Test Environment

Test environment requires more production-like settings:

```
CBS_ENVIRONMENT=test
CBS_DB_TYPE=postgresql
CBS_DB_NAME=cbs_test
CBS_DB_USER=test_user
CBS_DB_PASSWORD=test_password
CBS_DB_HOST=localhost
CBS_DB_PORT=5432
```

Test environment features:
- Sanitized data
- Integration with test payment gateways
- Performance benchmarking tools
- Automated test runners

#### Production Environment

Production requires the most secure and optimized settings:

```
CBS_ENVIRONMENT=production
CBS_DB_TYPE=postgresql
CBS_DB_NAME=cbs_production
CBS_DB_USER=production_user
CBS_DB_PASSWORD=strong_production_password
CBS_DB_HOST=db.example.com
CBS_DB_PORT=5432

# Security settings
CBS_JWT_SECRET=very_long_random_string
CBS_PASSWORD_MIN_LENGTH=14
CBS_PASSWORD_COMPLEXITY=True
CBS_SESSION_TIMEOUT_MINUTES=15
```

Production environment features:
- Detailed audit logging
- High-security settings
- Production API endpoints
- Regular database backups

### 7. Start the Application

#### Start the API Server

```bash
# Development with auto-reload
python run_api.py --debug

# Production with Gunicorn (recommended for production)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 run_api:app
```

#### Run CLI Commands

```bash
python -m scripts.cli.cbs_cli --help
```

## Deployment Architectures

### Development Deployment

A simple single-server deployment:
- Application code and API server
- Local SQLite database
- Local file storage

### Test Deployment

A multi-server setup:
- Application server
- Database server (PostgreSQL)
- Test integration points

### Production Deployment

A robust, scalable architecture:
- Multiple application servers behind load balancer
- Primary and replica database servers
- Redis cache servers
- Scheduled backup system
- Monitoring and alerting systems
- High availability configuration

## Production Hardening

For production deployments, implement these additional security measures:

1. **Use HTTPS**: Set up SSL/TLS certificates
2. **Network Firewall**: Restrict access to necessary ports only
3. **Database Encryption**: Enable data encryption at rest
4. **Regular Backups**: Implement automated database backups
5. **Monitoring**: Set up Prometheus/Grafana for system monitoring
6. **Rate Limiting**: Implement API rate limiting
7. **IP Restrictions**: Limit admin access to approved IPs
8. **Regular Updates**: Keep all dependencies up to date

## Containerization

The system can be containerized using Docker:

```bash
# Build the Docker image
docker build -t cbs-python:latest .

# Run the container
docker run -p 8000:8000 --env-file .env cbs-python:latest
```

A Docker Compose file is provided for multi-container setup:

```bash
# Start the entire stack (app, database, cache)
docker-compose up -d
```

## Continuous Integration/Deployment

The repository includes GitHub Actions workflows for:
- Running tests on pull requests
- Building and publishing Docker images
- Deploying to test environments
- Database migrations

## Monitoring and Logging

### Logging Configuration

Logs are stored in the `logs/` directory:
- Application logs: `logs/cbs.log`
- Access logs: `logs/access.log`
- Error logs: `logs/error.log`

In production, consider using a centralized logging system like ELK Stack or Graylog.

### Health Checks

Health check endpoints are available at:
- `/api/v1/health`: Basic health check
- `/api/v1/health/detailed`: Detailed component status

## Backup and Recovery

### Database Backups

Automated database backups are configured in `scripts/backup/`:

```bash
# Run a manual backup
python -m scripts.backup.db_backup

# Restore from backup
python -m scripts.backup.db_restore --backup-file backups/cbs_backup_2025-05-17.sql
```

### Disaster Recovery

Follow these steps for disaster recovery:
1. Restore the latest database backup
2. Deploy the application code
3. Apply any pending migrations
4. Verify system integrity with health checks

## Troubleshooting

Common deployment issues and solutions:
- **Database Connection Issues**: Check network connectivity and credentials
- **Permission Errors**: Ensure proper file system permissions
- **Memory Issues**: Adjust worker count and database connection pool size
- **Slow Performance**: Enable caching and optimize database queries

For more assistance, refer to the [Troubleshooting Guide](troubleshooting.md).
