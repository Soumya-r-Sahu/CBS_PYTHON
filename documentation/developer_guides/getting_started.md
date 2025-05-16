# Developer Setup Guide

This guide will help you set up the CBS_PYTHON development environment.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.8+ (3.10+ recommended)
- Git
- A code editor (VS Code, PyCharm, etc.)
- Database (PostgreSQL recommended for production, SQLite for development)

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/CBS_PYTHON.git
cd CBS_PYTHON
```

### 2. Create and Activate a Virtual Environment

#### Windows
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file at the project root from the template:

```bash
cp .env.example .env
```

Edit the `.env` file to configure your environment:

```ini
# Environment (development, test, production)
CBS_ENVIRONMENT=development

# Database Connection
CBS_DB_TYPE=sqlite  # Options: sqlite, postgresql, mysql
CBS_DB_NAME=cbs_python_dev
CBS_DB_USER=developer
CBS_DB_PASSWORD=dev_password
CBS_DB_HOST=localhost
CBS_DB_PORT=5432

# API Configuration
CBS_API_PORT=8000
CBS_API_HOST=localhost
CBS_JWT_SECRET=your_jwt_secret_key_change_me_in_production

# Email Configuration (for notifications)
CBS_SMTP_HOST=smtp.example.com
CBS_SMTP_PORT=587
CBS_SMTP_USER=notifications@example.com
CBS_SMTP_PASSWORD=your_password
CBS_FROM_EMAIL=banking@example.com

# SMS Configuration
CBS_SMS_GATEWAY=https://sms.example.com/api
CBS_SMS_API_KEY=your_sms_api_key

# Logging
CBS_LOG_LEVEL=DEBUG
```

### 5. Initialize the Database

```bash
python main.py --init-db
```

## Development Workflow

### Running the System

#### CLI Mode

```bash
# Run the CLI
python -m scripts.cli.cbs_cli --help

# Run the CLI with a specific module command
python -m scripts.cli.cbs_cli accounts create-account --customer-id <uuid> --account-type SAVINGS --initial-deposit 5000
```

#### API Mode

```bash
# Start the API server
python run_api.py --port 8000
```

#### GUI Mode

```bash
# Start the GUI application
python main.py --mode gui
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=.

# Run tests for a specific module
pytest tests/core_banking/accounts/
```

### Code Quality Checks

Before committing, run these tools to ensure code quality:

```bash
# Format code with Black
black .

# Check for style issues with flake8
flake8 .

# Run type checking with mypy
mypy .
```

## Clean Architecture Development

When developing new features or fixing issues, follow these guidelines:

1. **Identify the Domain**: Determine which module the change belongs to (e.g., accounts, loans, etc.)

2. **Layer Placement**:
   - Domain logic goes in the domain layer
   - Use cases go in the application layer
   - External interfaces go in the infrastructure layer
   - User interfaces go in the presentation layer

3. **Dependency Rule**: Always ensure dependencies point inward (outer layers depend on inner layers)

4. **Testing**: Write tests for all layers, with a focus on domain and application layers

## Database Management

### Migrations

The CBS_PYTHON project uses Alembic for database migrations:

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Run migrations
alembic upgrade head

# Downgrade to a previous version
alembic downgrade -1
```

### Database Connection

Database connections are managed through the dependency injection container in each module. If you need to directly access the database for debugging or maintenance:

```python
from core_banking.database.python.db_connection import get_database_connection

# Get a database connection
connection = get_database_connection()
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure your virtual environment is activated and all dependencies are installed
2. **Database Errors**: Check your database configuration in the `.env` file
3. **JWT Errors**: Ensure your JWT secret key is properly set in the `.env` file

### Getting Help

If you encounter issues:
1. Check the logs in the `logs/` directory
2. Run with debug logging enabled: `python main.py --debug`
3. Refer to the documentation
4. Open an issue on GitHub

## Next Steps

After setting up your development environment:

1. Read the [Clean Architecture Overview](../clean_architecture/overview.md)
2. Review the [Contributing Guidelines](../../CONTRIBUTING.md)
3. Check the [API Documentation](../api/api_overview.md)
4. Start with a simple feature or bug fix