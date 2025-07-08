# Django Client for CBS Banking API

A client library for Django applications to integrate with the Core Banking System API.

## Overview

This client provides a simple way for Django-based frontends to communicate with the CBS Banking API. It handles:

- Authentication and token management
- API request and response formatting
- Error handling and retries
- CSRF protection integration with Django

## Installation

This client is part of the CBS_PYTHON codebase. If you need to use it as a standalone package, simply copy the `django_client` directory to your Django project.

## Usage

### Basic Usage

```python
from Backend.integration_interfaces.django_client import BankingAPIClient

# Create client instance (default configuration)
api_client = BankingAPIClient()

# Make API calls
accounts = api_client.get_accounts()

# Make a transfer
result = api_client.transfer_money(
    from_account='1234567890',
    to_account='0987654321',
    amount=100.00,
    currency='USD',
    description='Rent payment'
)
```

### Authentication

```python
# Authenticate and get token
auth_data = api_client.authenticate('username', 'password')

# Token is automatically stored in the client
# You can access it if needed
token = auth_data.get('token')

# Log out (invalidates token)
api_client.logout()
```

### Integration with Django Views

```python
from django.shortcuts import render
from Backend.integration_interfaces.django_client import BankingAPIClient, APIError

def account_view(request):
    # Create client
    api_client = BankingAPIClient()

    # Set session from Django request
    # This extracts the token and CSRF token automatically
    api_client.set_session_from_request(request)

    try:
        # Get accounts from API
        accounts = api_client.get_accounts()

        return render(request, 'accounts/list.html', {
            'accounts': accounts
        })
    except APIError as e:
        # Handle API errors
        return render(request, 'error.html', {
            'message': str(e),
            'code': e.code,
            'status': e.status
        })
```

### Custom Configuration

```python
# Custom configuration
config = {
    'base_url': 'https://api.bank.example.com/api/v1',
    'timeout': 60,
    'retry_attempts': 5
}

# Create client with custom configuration
api_client = BankingAPIClient(config)
```

## API Methods

The client provides both generic HTTP methods and banking-specific methods:

### Generic HTTP Methods

- `get(path, params=None, headers=None)`
- `post(path, data, params=None, headers=None)`
- `put(path, data, params=None, headers=None)`
- `patch(path, data, params=None, headers=None)`
- `delete(path, params=None, headers=None)`

### Banking-Specific Methods

- `get_accounts()`
- `get_account_details(account_number)`
- `get_transactions(account_number, **params)`
- `transfer_money(from_account, to_account, amount, currency="USD", description=None)`
- `authenticate(username, password, device_id=None)`
- `logout()`

## Error Handling

The client raises `APIError` exceptions when API requests fail:

```python
from Backend.integration_interfaces.django_client import BankingAPIClient, APIError

api_client = BankingAPIClient()

try:
    accounts = api_client.get_accounts()
except APIError as e:
    print(f"API Error: {e.message}")
    print(f"Error Code: {e.code}")
    print(f"HTTP Status: {e.status}")
```

## Configuration

The client uses the CBS Banking System's configuration system. Configuration can be provided in several ways:

1. Environment variables
2. Configuration passed to the constructor
3. Default fallback values

### Environment Variables

- `CBS_API_BASE_URL`: Base URL for the API
- `CBS_API_TIMEOUT`: Request timeout in seconds
- `CBS_API_RETRIES`: Number of retry attempts

## License

This client is part of the CBS_PYTHON project and is subject to the same license.
