# Django Integration Guide for CBS Banking API

This guide provides detailed instructions for integrating the CBS Banking API with Django projects. The CBS banking system has been designed to work seamlessly with Django applications, providing a powerful backend for building banking and financial services.

## Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Basic Setup](#basic-setup)
4. [Authentication Integration](#authentication-integration)
5. [CSRF Protection](#csrf-protection)
6. [Session Management](#session-management)
7. [Example Views](#example-views)
8. [Template Integration](#template-integration)
9. [Common Issues](#common-issues)
10. [Advanced Configuration](#advanced-configuration)

## Requirements

- Python 3.8+
- Django 3.2+
- Requests library
- CBS Banking API server running

## Installation

Install the Django client library directly from the CBS package:

```bash
pip install cbs-python-django-client
```

Or include it as a dependency in your project's requirements:

```
# requirements.txt
cbs-python-django-client>=1.0.0
```

## Basic Setup

1. Add the CBS Django client to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # CBS Banking API integration
    'cbs_django_client',
    # ...
]
```

2. Configure the CBS API connection in `settings.py`:

```python
# CBS Banking API configuration
CBS_API_BASE_URL = 'http://localhost:5000/api/v1'  # Change to your API URL
CBS_API_TIMEOUT = 30
CBS_API_RETRY_ATTEMPTS = 3
CBS_API_TOKEN_STORAGE_KEY = 'jwt_token'  # Session key for storing tokens
```

3. Create a configured client instance in your project:

```python
# my_app/banking_client.py
from django.conf import settings
from Backend.integration_interfaces.django_client import BankingAPIClient

# Create a globally accessible client
api_client = BankingAPIClient({
    'base_url': settings.CBS_API_BASE_URL,
    'timeout': settings.CBS_API_TIMEOUT,
    'retry_attempts': settings.CBS_API_RETRY_ATTEMPTS
})
```

## Authentication Integration

The CBS Banking API uses JWT tokens for authentication, which can be integrated with Django's authentication system:

1. Create a middleware to set API client authentication from Django session:

```python
# my_app/middleware.py
from django.utils.deprecation import MiddlewareMixin
from my_app.banking_client import api_client

class CBSAPIMiddleware(MiddlewareMixin):
    """Middleware to set API client authentication from Django session."""

    def process_request(self, request):
        # Set API client to use current request's session
        api_client.set_session_from_request(request)
        return None
```

2. Add the middleware to your settings:

```python
MIDDLEWARE = [
    # ...
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # CBS Banking API middleware
    'my_app.middleware.CBSAPIMiddleware',
]
```

3. Create authentication views:

```python
# my_app/views/auth.py
from django.shortcuts import render, redirect
from django.contrib import messages
from my_app.banking_client import api_client
from Backend.integration_interfaces.django_client import APIError

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            # Authenticate with API
            auth_data = api_client.authenticate(username, password)

            # Store token in session
            request.session['jwt_token'] = auth_data.get('token')

            messages.success(request, 'Login successful!')
            return redirect('dashboard')

        except APIError as e:
            messages.error(request, f'Login failed: {e.message}')

    return render(request, 'my_app/login.html')

def logout_view(request):
    # Call API logout
    if 'jwt_token' in request.session:
        try:
            api_client.logout()
        except APIError:
            pass  # Continue with logout even if API logout fails

    # Clear session
    if 'jwt_token' in request.session:
        del request.session['jwt_token']

    messages.success(request, 'You have been logged out.')
    return redirect('login')
```

## CSRF Protection

The Django client library automatically handles CSRF tokens for you:

1. The client extracts CSRF tokens from cookies
2. It adds the token to request headers
3. It handles token refreshing

You don't need any special configuration as long as you use the `set_session_from_request` method.

## Session Management

To ensure users are properly authenticated with the API:

1. Create a custom decorator for views that require API authentication:

```python
# my_app/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def api_login_required(view_func):
    """Decorator for views that require API authentication."""

    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if 'jwt_token' not in request.session:
            messages.warning(request, 'Please log in to access this page.')
            return redirect('login')
        return view_func(request, *args, **kwargs)

    return wrapped_view
```

2. Use the decorator on views that need authentication:

```python
from my_app.decorators import api_login_required

@api_login_required
def dashboard(request):
    # This view is protected and requires API authentication
    return render(request, 'my_app/dashboard.html')
```

## Example Views

Here are examples of common banking operations:

### Account Listing

```python
from my_app.decorators import api_login_required
from my_app.banking_client import api_client
from Backend.integration_interfaces.django_client import APIError
from django.shortcuts import render

@api_login_required
def accounts_list(request):
    try:
        # Get accounts from API
        accounts = api_client.get_accounts()

        return render(request, 'my_app/accounts_list.html', {
            'accounts': accounts
        })

    except APIError as e:
        messages.error(request, f'Failed to fetch accounts: {e.message}')
        return redirect('dashboard')
```

### Fund Transfer

```python
@api_login_required
def transfer(request):
    if request.method == 'POST':
        from_account = request.POST.get('from_account')
        to_account = request.POST.get('to_account')
        amount = float(request.POST.get('amount'))
        description = request.POST.get('description', '')

        try:
            # Execute transfer
            result = api_client.transfer_money(
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                description=description
            )

            messages.success(request, 'Transfer completed successfully!')
            return redirect('accounts')

        except APIError as e:
            messages.error(request, f'Transfer failed: {e.message}')

    # Get accounts for form
    try:
        accounts = api_client.get_accounts()
    except APIError:
        accounts = []

    return render(request, 'my_app/transfer.html', {
        'accounts': accounts
    })
```

## Template Integration

Example of displaying account data in a Django template:

```html
{% extends 'base.html' %}

{% block content %}
<h1>Your Accounts</h1>

{% if accounts %}
    <div class="accounts-container">
        {% for account in accounts %}
            <div class="account-card">
                <h3>{{ account.account_type }} Account</h3>
                <p class="account-number">{{ account.account_number }}</p>
                <p class="account-balance">Balance: ${{ account.balance }}</p>
                <div class="account-actions">
                    <a href="{% url 'account_detail' account.account_number %}" class="btn btn-primary">View Details</a>
                    <a href="{% url 'account_transactions' account.account_number %}" class="btn btn-secondary">Transactions</a>
                </div>
            </div>
        {% endfor %}
    </div>
{% else %}
    <p>You don't have any accounts yet.</p>
    <a href="{% url 'create_account' %}" class="btn btn-primary">Open New Account</a>
{% endif %}
{% endblock %}
```

## Common Issues

### Authentication Issues

**Problem**: API authentication fails despite correct credentials.

**Solution**:
- Check if your Django session is configured properly
- Verify that `SESSION_COOKIE_SECURE` is set correctly for your environment
- Make sure CSRF protection is not interfering with API requests

### CSRF Token Errors

**Problem**: API requests fail with CSRF validation errors.

**Solution**:
- Ensure the Django client is properly extracting tokens from cookies
- Verify that the API client is configured to use CSRF protection
- Check that the CSRF cookie name matches what the client expects

### Connection Timeouts

**Problem**: Requests to the API timeout.

**Solution**:
- Increase the timeout value in client configuration
- Check network connectivity between your Django app and the API server
- Verify that the API server is running and healthy

## Advanced Configuration

### Custom Authentication Flow

You can implement a custom authentication flow by subclassing the BankingAPIClient:

```python
from Backend.integration_interfaces.django_client import BankingAPIClient

class CustomBankingClient(BankingAPIClient):
    def __init__(self, config=None):
        super().__init__(config)

    def custom_authenticate(self, username, password, mfa_code=None):
        # Add custom authentication logic here
        data = {
            "username": username,
            "password": password
        }

        if mfa_code:
            data["mfa_code"] = mfa_code

        response = self.post("auth/custom-login", data)

        # Extract and store the token
        if "data" in response and "token" in response["data"]:
            self.set_auth_token(response["data"]["token"])

        return response["data"]
```

### Custom Error Handling

```python
from Backend.integration_interfaces.django_client import APIError

def api_view_with_error_handling(function):
    """Decorator to handle API errors in views."""

    @wraps(function)
    def wrapper(request, *args, **kwargs):
        try:
            return function(request, *args, **kwargs)
        except APIError as e:
            if e.status == 401:
                messages.error(request, "Your session has expired. Please log in again.")
                if 'jwt_token' in request.session:
                    del request.session['jwt_token']
                return redirect('login')
            elif e.status == 403:
                messages.error(request, "You do not have permission to perform this action.")
                return redirect('dashboard')
            elif e.status == 404:
                messages.error(request, "The requested resource was not found.")
                return redirect('dashboard')
            else:
                messages.error(request, f"An error occurred: {e.message}")
                return redirect('dashboard')

    return wrapper
```
