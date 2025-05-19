# Database Python Module

This directory contains the Python database layer for the Core Banking System.

## Directory Structure

```
database/python/
├── __init__.py                 # Main module entry point
├── connection/                 # Database connection management
│   ├── __init__.py
│   ├── db_connection.py        # Direct database connection class
│   └── connection_manager.py   # SQLAlchemy connection utilities
├── models/                     # SQLAlchemy ORM models
│   ├── __init__.py
│   ├── base_models.py          # Base classes and enum types
│   ├── banking_models.py       # Core banking entity models
│   └── international_models.py # International banking models
└── utilities/                  # Database helper utilities
    ├── __init__.py
    ├── backup_utilities.py     # Backup and restore functionality
    ├── compare_tools.py        # Database comparison tools
    └── migration_helpers.py    # Schema migration utilities
```

## Usage

### Database Connection

```python
# Using SQLAlchemy ORM connection
from database.python import engine, SessionLocal, get_db

# Get a database session
db = SessionLocal()
try:
    # Use the session
    result = db.execute("SELECT * FROM customers")
    # ...
finally:
    db.close()

# Using the context manager pattern
def get_customer(customer_id):
    with SessionLocal() as db:
        return db.query(Customer).filter_by(customer_id=customer_id).first()

# Using the direct connection
from database.python import DatabaseConnection

# Get a connection instance
db_conn = DatabaseConnection()

# Execute a query
results = db_conn.execute_query("SELECT * FROM customers WHERE status = %s", ["ACTIVE"])
```

### Working with Models

```python
from database.python import Customer, Account, Transaction
from database.python.models import CustomerStatus, AccountType

# Create a new customer
customer = Customer(
    customer_id="CST12345",
    first_name="John",
    last_name="Doe",
    customer_status=CustomerStatus.ACTIVE
    # ...other fields
)

# Add to database
with SessionLocal() as db:
    db.add(customer)
    db.commit()
    db.refresh(customer)
```

### Using Utilities

```python
from database.python import create_backup, restore_backup, compare_databases

# Create a database backup
backup_info = create_backup(compress=True)

# Generate a schema report
from database.python import generate_schema_report
report = generate_schema_report("database_schema.md")

# Run database migrations
from database.python import migrate_schema
result = migrate_schema("database/migrations")
```

## Migration

The database module provides tools to help with schema migrations. Migration files should be placed in a `migrations` directory and follow the naming convention `V{version}__{description}.sql`, e.g., `V001__initial_schema.sql`.

## Backup and Restore

The backup utilities provide functionality to create and restore database backups, with options for compression and metadata tracking.
