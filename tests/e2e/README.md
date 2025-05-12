# End-to-End Tests

This directory contains end-to-end tests for the Core Banking System.

End-to-End tests focus on testing the entire system:
- Tests full user workflows
- Uses actual database and environment
- Tests the system as a user would experience it

## Test Categories

### Complete Workflow Tests
- `test_database_workflow.py`: Tests database in complete workflows (account creation to transaction)
- `test_placeholder.py`: Template for future E2E tests

## Running E2E Tests

```bash
# Run all end-to-end tests
python -m unittest discover tests/e2e

# Run a specific test file
python -m unittest tests/e2e/test_file.py
```
