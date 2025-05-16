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

### Deposit funds:
```bash
python -m scripts.cli.cbs_cli accounts deposit --account-id <uuid> --amount 1000 --description "Salary deposit"
```

### Transfer funds:
```bash
python -m scripts.cli.cbs_cli accounts transfer --source-account-id <uuid> --target-account-id <uuid> --amount 500 --description "Rent payment"
```

## Using the API

The CBS system also provides a RESTful API:

1. **Start the API server**:
   ```bash
   python run_api.py
   ```

2. **Access the API documentation**:
   Open your browser and go to `http://localhost:8000/api/v1/docs`

3. **API endpoints examples**:
   - List accounts: `GET /api/v1/accounts`
   - Create account: `POST /api/v1/accounts`
   - Get account details: `GET /api/v1/accounts/{id}`
   - Deposit funds: `POST /api/v1/accounts/{id}/deposit`

## Environment Settings

The CBS system supports multiple environments:

- **Development**: For development and testing
  ```bash
  # Set in .env file
  CBS_ENVIRONMENT=development
  ```

- **Test**: For QA and testing
  ```bash
  # Set in .env file
  CBS_ENVIRONMENT=test
  ```

- **Production**: For live operations
  ```bash
  # Set in .env file
  CBS_ENVIRONMENT=production
  ```

The environment affects database table naming, logging levels, and feature availability.

## Key Modules

The CBS system is organized into domains:

- **Core Banking**: Accounts, Customers, Loans, Transactions
- **Digital Channels**: ATM, Internet Banking, Mobile Banking
- **Payments**: UPI, NEFT, RTGS, IMPS
- **Risk Compliance**: Fraud Detection, Audit Trail

## Further Documentation

For more detailed information, refer to:

- [CLI User Guide](../cli/cli_user_guide.md): Detailed CLI documentation
- [API Documentation](../api/api_overview.md): Detailed API documentation
- [System Architecture](../architecture_diagrams/clean_architecture_diagrams.md): System architecture diagrams
- [Developer Guide](../developer_guides/getting_started.md): Guide for developers

## Getting Help

If you encounter issues:

1. Check the logs in the `logs/` directory
2. Run with debug logging: `python main.py --debug`
3. Refer to troubleshooting guides
4. Open an issue on GitHub