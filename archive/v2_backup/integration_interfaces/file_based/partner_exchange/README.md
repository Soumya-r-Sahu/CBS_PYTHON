# Partner File Exchange Module

## Overview
The Partner File Exchange module handles file-based integration with external partner systems by processing and generating standardized file formats. It supports various file formats like CSV, JSON, and XML.

## Features
- Process incoming partner files
- Generate outgoing partner files
- Support for multiple file formats (CSV, JSON)
- File archiving and error handling
- Configurable directory structure and settings

## Directory Structure
- `controllers/`: Interface for client code to work with partner files
- `services/`: Core business logic for file processing
- `models/`: Data models for partner file entries
- `config/`: Configuration settings for the module
- `utils/`: Utility functions
- `tests/`: Unit tests for the module

## Usage Examples

### Processing an Incoming File
```python
from integration_interfaces.file_based.partner_exchange.controllers import PartnerFileController

# Process an incoming file
result = PartnerFileController.process_incoming_file("partner_20250513_settlement.csv")
print(result["status"])  # Should print 'success'
```

### Generating a New Partner File
```python
from integration_interfaces.file_based.partner_exchange.controllers import PartnerFileController

# Sample transaction data
transactions = [
    {
        "transaction_id": "TX123456",
        "amount": 1000.00,
        "status": "SUCCESS",
        "timestamp": "2025-05-13T10:00:00Z"
    },
    {
        "transaction_id": "TX789012",
        "amount": 2500.50,
        "status": "SUCCESS",
        "timestamp": "2025-05-13T11:30:00Z"
    }
]

# Generate a settlement file
result = PartnerFileController.generate_partner_file(
    partner_id="PARTNERBANK",
    entries=transactions,
    file_type="settlement",
    file_format="csv"
)

print(result["filename"])  # Will print the generated filename
```

## Configuration
The module can be configured via environment variables:

- `PARTNER_FILE_BASE_DIRECTORY`: Base directory for all partner file operations
- `PARTNER_FILE_INCOMING_DIRECTORY`: Directory for incoming files
- `PARTNER_FILE_OUTGOING_DIRECTORY`: Directory for outgoing files
- `PARTNER_FILE_ARCHIVE_DIRECTORY`: Directory for archiving processed files
- `PARTNER_FILE_ERROR_DIRECTORY`: Directory for files with processing errors
- `PARTNER_FILE_FILE_RETENTION_DAYS`: Number of days to retain archived files
- `PARTNER_FILE_SUPPORTED_FORMATS`: Comma-separated list of supported file formats
- `PARTNER_FILE_DEFAULT_ENCODING`: Default encoding for reading/writing files
- `PARTNER_FILE_MAX_FILE_SIZE_MB`: Maximum allowed file size in MB
- `PARTNER_FILE_AUTO_ARCHIVE`: Whether to automatically archive files after processing

## Testing
Run the unit tests to verify functionality:

```bash
python -m unittest integration_interfaces.file_based.partner_exchange.tests.test_file_service
```
