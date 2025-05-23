# Database Configuration

This document provides detailed information about database configuration in the CBS_PYTHON system.

## Supported Database Systems

The CBS_PYTHON system supports multiple database backends:

- **SQLite**: For development and small deployments
- **PostgreSQL**: Recommended for production deployments
- **MySQL**: Supported as an alternative

## Database Configuration Parameters

### Core Parameters

```yaml
database:
  type: postgresql  # sqlite, postgresql, mysql
  name: cbs_python  # Database name
  host: localhost   # Database host (not needed for SQLite)
  port: 5432        # Database port (not needed for SQLite)
  user: cbs_user    # Database user (not needed for SQLite)
  password: ${CBS_DB_PASSWORD}  # From environment variable
  charset: utf8     # Character set
  timezone: UTC     # Database timezone
```

### Connection Pool Configuration

```yaml
database:
  pool:
    size: 10             # Number of connections in the pool
    max_overflow: 20     # Max additional connections when pool is full
    timeout: 30          # Timeout for getting a connection from pool (seconds)
    recycle: 3600        # Recycle connections after this many seconds
    pre_ping: true       # Check connection validity before using
    use_lifo: true       # Use Last-In-First-Out instead of First-In-First-Out
```

### Performance Tuning

```yaml
database:
  performance:
    echo: false           # Echo SQL queries (development only)
    echo_pool: false      # Echo connection pool events (development only)
    statement_timeout: 60  # Statement timeout in seconds
    idle_in_transaction_session_timeout: 60  # Idle in transaction timeout
    application_name: "CBS_PYTHON"  # Application name for connection
    prepared_statements: true  # Use prepared statements
    server_side_cursors: true  # Use server-side cursors for large results
    use_batch: true           # Use batch processing where possible
```

### SQLite-Specific Configuration

```yaml
database:
  sqlite:
    journal_mode: WAL     # Write-Ahead Logging mode
    synchronous: NORMAL   # Synchronous mode (FULL, NORMAL, OFF)
    foreign_keys: true    # Enable foreign key constraints
    temp_store: MEMORY    # Store temp tables in memory
    cache_size: -2000     # Cache size in KB (negative for memory)
    mmap_size: 0          # Memory-mapped I/O size
```

### PostgreSQL-Specific Configuration

```yaml
database:
  postgresql:
    schema: public         # Schema name
    client_encoding: UTF8  # Client encoding
    application_name: "CBS_PYTHON"  # Application name
    client_min_messages: error  # Client min messages level
    sslmode: prefer        # SSL mode (disable, allow, prefer, require, verify-ca, verify-full)
    target_session_attrs: read-write  # Session type (any, read-write)
    server_prepare_threshold: 5  # Prepare statements after this many uses
    numeric_precision: high  # Numeric precision
```

### MySQL-Specific Configuration

```yaml
database:
  mysql:
    charset: utf8mb4       # Character set
    collation: utf8mb4_unicode_ci  # Collation
    sql_mode: TRADITIONAL  # SQL mode
    autocommit: true       # Auto-commit
    pool_recycle: 3600     # Recycle connections after this many seconds
    ssl_ca: null           # SSL CA certificate
    ssl_cert: null         # SSL certificate
    ssl_key: null          # SSL key
    use_pure: true         # Use pure Python implementation
```

## Environment-Specific Configurations

### Development Environment

```yaml
# development.yaml
database:
  type: sqlite
  name: cbs_development.db
  pool:
    size: 5
  performance:
    echo: true
    echo_pool: true
  sqlite:
    journal_mode: WAL
    synchronous: NORMAL
```

### Test Environment

```yaml
# test.yaml
database:
  type: postgresql
  name: cbs_test
  host: localhost
  port: 5432
  user: test_user
  password: ${CBS_TEST_DB_PASSWORD}
  pool:
    size: 10
    max_overflow: 20
  performance:
    echo: false
    statement_timeout: 60
  postgresql:
    schema: public
```

### Production Environment

```yaml
# production.yaml
database:
  type: postgresql
  name: cbs_production
  host: ${CBS_DB_HOST}
  port: ${CBS_DB_PORT}
  user: ${CBS_DB_USER}
  password: ${CBS_DB_PASSWORD}
  pool:
    size: 20
    max_overflow: 30
    recycle: 1800
  performance:
    statement_timeout: 30
    prepared_statements: true
  postgresql:
    schema: public
    sslmode: require
```

## Database Connection String

The system constructs a database connection string from the configuration parameters:

```python
def build_connection_string(config):
    db_type = config.get("database.type")

    if db_type == "sqlite":
        db_name = config.get("database.name")
        return f"sqlite:///{db_name}"

    elif db_type in ["postgresql", "mysql"]:
        db_user = config.get("database.user")
        db_password = config.get("database.password")
        db_host = config.get("database.host")
        db_port = config.get_int("database.port")
        db_name = config.get("database.name")

        if db_type == "postgresql":
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        else:  # mysql
            charset = config.get("database.mysql.charset", "utf8mb4")
            return f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset={charset}"

    else:
        raise ValueError(f"Unsupported database type: {db_type}")
```

## Using Environment Variables

For security, sensitive database configuration values should be stored in environment variables:

```bash
# For PostgreSQL
export CBS_DB_HOST=db.example.com
export CBS_DB_PORT=5432
export CBS_DB_NAME=cbs_production
export CBS_DB_USER=cbs_user
export CBS_DB_PASSWORD=secure_password_here
```

## Database Migration Configuration

The CBS_PYTHON system uses Alembic for database migrations:

```yaml
database:
  migrations:
    auto_migrate: false  # Automatically run migrations on startup
    location: database/migrations  # Location of migration scripts
    naming_convention:
      ix: ix_%(column_0_label)s
      uq: uq_%(table_name)s_%(column_0_name)s
      ck: ck_%(table_name)s_%(constraint_name)s
      fk: fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s
      pk: pk_%(table_name)s
```

## Database Backup Configuration

```yaml
database:
  backup:
    auto_backup: true  # Automatically backup database
    backup_dir: backups/database  # Backup directory
    compression: true  # Compress backups
    retention_days: 30  # Number of days to keep backups
    schedule:
      daily: true  # Daily backups
      time: "03:00"  # Backup time (24-hour format)
```

## Multi-Database Configuration

For systems requiring multiple databases:

```yaml
databases:
  default:
    type: postgresql
    name: cbs_main
    host: main-db.example.com
    # ... other parameters

  reporting:
    type: postgresql
    name: cbs_reporting
    host: reporting-db.example.com
    # ... other parameters

  archive:
    type: postgresql
    name: cbs_archive
    host: archive-db.example.com
    # ... other parameters
```

## Read-Write Splitting Configuration

For high-volume applications, read-write splitting can be configured:

```yaml
database:
  read_write_splitting:
    enabled: true
    strategy: round_robin  # round_robin, random, least_connections
    writer:
      host: primary-db.example.com
      port: 5432
      # ... other parameters
    readers:
      - host: replica-db-1.example.com
        port: 5432
        # ... other parameters
      - host: replica-db-2.example.com
        port: 5432
        # ... other parameters
```

## Database Monitoring Configuration

```yaml
database:
  monitoring:
    enabled: true
    slow_query_threshold_ms: 500  # Threshold for slow query logging
    log_queries: false  # Log all queries (development only)
    log_slow_queries: true  # Log slow queries
    query_stats_enabled: true  # Collect query statistics
    connection_stats_enabled: true  # Collect connection statistics
    metrics_enabled: true  # Export metrics for monitoring systems
```

## Database Access in Code

### Accessing the Database

```python
from core_banking.database.connection import get_db_session

# Using context manager (recommended)
with get_db_session() as session:
    result = session.execute("SELECT * FROM accounts WHERE customer_id = :customer_id",
                             {"customer_id": customer_id})
    accounts = result.fetchall()

# Alternative approach
session = get_db_session()
try:
    result = session.execute("SELECT * FROM accounts WHERE customer_id = :customer_id",
                             {"customer_id": customer_id})
    accounts = result.fetchall()
    session.commit()
finally:
    session.close()
```

### Using Repositories

The preferred way to access the database is through repositories:

```python
from core_banking.accounts.infrastructure.repositories.sql_account_repository import SQLAccountRepository
from core_banking.utils.di_container import get_container

# Get repository from DI container
container = get_container()
account_repository = container.get(SQLAccountRepository)

# Use repository
account = account_repository.get_by_id(account_id)
```

## Common Database Configuration Issues

### Connection Issues

If you encounter database connection issues:

1. Verify database host, port, user, and password
2. Check network connectivity
3. Verify that the database exists
4. Check database server logs
5. Verify that the database user has the necessary permissions

### Performance Issues

For performance issues:

1. Check connection pool size
2. Review slow query logs
3. Consider adding indexes
4. Review transaction isolation level
5. Consider read-write splitting for read-heavy workloads

### Migration Issues

For migration issues:

1. Check alembic version table
2. Review migration scripts
3. Run migrations manually with `alembic upgrade head`
4. Check for migration errors in logs

## Related Documentation

- [Environment-Specific Configurations](environment_configs.md)
- [Configuration System](configuration_system.md)
- [Database Schema](../technical/development/database_schema.md)
