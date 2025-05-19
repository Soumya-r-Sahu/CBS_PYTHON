# CBS_PYTHON Quick Start Guide

This guide provides a quick introduction to using the Core Banking System (CBS).

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/CBS_PYTHON.git
   cd CBS_PYTHON
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize the database**:
   ```bash
   python main.py --init-db
   ```

## Using the Command-Line Interface (CLI)

The CBS system provides a powerful CLI for various banking operations:

### View available commands:
```bash
python -m scripts.cli.cbs_cli --help
```

### Create a new account:
```bash
python -m scripts.cli.cbs_cli accounts create-account --customer-id <uuid> --account-type SAVINGS --initial-deposit 5000
```

### Get account details:
```bash
python -m scripts.cli.cbs_cli accounts get-account --account-id <uuid>
```

### Make a transaction:
```bash
python -m scripts.cli.cbs_cli transactions create --from-account <uuid> --to-account <uuid> --amount 100.50 --description "Monthly rent"
```

### Generate account statement:
```bash
python -m scripts.cli.cbs_cli accounts generate-statement --account-id <uuid> --start-date 2025-01-01 --end-date 2025-01-31
```

## Using the API

The CBS system also provides a RESTful API:

### Start the API server:
```bash
python -m scripts.api.start_server
```

### API Endpoints:

- **Accounts**:
  - `GET /api/v1/accounts` - List all accounts
  - `GET /api/v1/accounts/{id}` - Get account details
  - `POST /api/v1/accounts` - Create a new account
  - `PUT /api/v1/accounts/{id}` - Update account details

- **Transactions**:
  - `GET /api/v1/transactions` - List all transactions
  - `GET /api/v1/transactions/{id}` - Get transaction details
  - `POST /api/v1/transactions` - Create a new transaction

## Configuration

The system can be configured by editing the `.env` file:

```
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=cbs_db
DB_USER=cbs_user
DB_PASSWORD=password

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=False

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=cbs.log
```

## Troubleshooting

If you encounter issues:

1. Check logs in the `logs/` directory
2. Ensure database connection is active
3. Verify environment variables are set correctly
4. Check that you're running the latest version

## Additional Resources

- [Complete User Manual](./USER_MANUAL_TEMPLATE.md)
- [Administrator Guide](../manuals/admin-guide.md)
- [API Documentation](../../api/reference/API_REFERENCE.md)

Last updated: May 19, 2025
