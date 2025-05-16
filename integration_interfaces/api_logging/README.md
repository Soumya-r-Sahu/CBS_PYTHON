# API Logging Module

## Overview
The API Logging module provides comprehensive logging and analysis functionality for API calls in the Core Banking System. It supports logging to both files and a database, with features for sanitizing sensitive data, log rotation, and statistical analysis.

## Features
- Logging of API requests and responses
- Sanitization of sensitive data
- Configurable log rotation
- Database or file-based storage
- API call duration tracking
- Error analysis and grouping
- Log retention management
- Statistical reporting

## Directory Structure
- `config/`: Configuration settings for API logging
- `models/`: Data models for log entries and analysis
- `services/`: Core services for logging and retrieving logs
- `utils/`: Utility functions for working with logs
- `tests/`: Unit tests for the module

## Usage Examples

### Logging an API Call

```python
from integration_interfaces.api_logging.services import api_logger_service

# Log an API call
api_logger_service.log_api_call(
    endpoint="/api/v1/accounts",
    request_data={"customer_id": "12345", "token": "SECRET_TOKEN"},
    response_data={"accounts": [{"id": "ACC001", "balance": 1000.00}]},
    status="success",
    duration_ms=120,
    request_id="req-123-abc",
    user_id="user-456",
    ip_address="192.168.1.1"
)
```

### Retrieving and Analyzing Logs

```python
from integration_interfaces.api_logging.services import api_logger_service
from integration_interfaces.api_logging.utils import group_errors_by_type

# Get logs for the last 24 hours
from datetime import datetime, timedelta
start_date = (datetime.utcnow() - timedelta(days=1)).isoformat()

logs = api_logger_service.get_logs(
    start_date=start_date,
    status="error",  # Only get error logs
    limit=1000
)

# Analyze errors by type
error_groups = group_errors_by_type(logs)

for group in error_groups:
    print(f"{group.error_type}: {group.count} occurrences")
    print(f"Affected endpoints: {', '.join(group.endpoints)}")
```

### Getting a Log Summary

```python
from integration_interfaces.api_logging.services import api_logger_service

# Get summary for the current week
from datetime import datetime, timedelta
start_date = (datetime.utcnow() - timedelta(days=7)).isoformat()

summary = api_logger_service.get_log_summary(start_date=start_date)

print(f"Total requests: {summary.total_requests}")
print(f"Success rate: {summary.success_count/summary.total_requests*100:.1f}%")
print(f"Average response time: {summary.avg_duration_ms:.2f}ms")
```

### Command-line Interface

The module also provides a command-line interface for working with logs:

```bash
# Get a summary of API logs
python -m integration_interfaces.api_logging.main summary --start-date 2025-01-01T00:00:00Z

# Analyze API errors
python -m integration_interfaces.api_logging.main errors --days 7 --verbose

# Clean up old logs
python -m integration_interfaces.api_logging.main cleanup --days 90
```

## Configuration
The module can be configured via environment variables:

- `API_LOG_DIR`: Directory for log files
- `API_LOG_MAX_FILE_SIZE_MB`: Maximum log file size before rotation
- `API_LOG_ROTATION_COUNT`: Number of rotated log files to keep
- `API_LOG_ENABLE_DB`: Whether to log to database (true/false)
- `API_LOG_DB_CONNECTION`: Database connection string
- `API_LOG_SENSITIVE_FIELDS`: Comma-separated list of sensitive field names to redact
- `API_LOG_LEVEL`: Log level (INFO, DEBUG, etc.)
- `API_LOG_REQUEST_BODY`: Whether to log request bodies (true/false)
- `API_LOG_RESPONSE_BODY`: Whether to log response bodies (true/false)
- `API_LOG_MAX_BODY_SIZE_KB`: Maximum size to log for request/response bodies
- `API_LOG_STORE_DAYS`: Number of days to retain logs

## Testing
Run the unit tests to verify functionality:

```bash
python -m unittest integration_interfaces.api_logging.tests.test_api_logging
```
