"""
Django Frontend Integration Example

This example demonstrates how to integrate the CBS Banking API with a Django frontend
using the provided Django client library.

Usage:
    1. Install the CBS_PYTHON package
    2. Copy this file to your Django project
    3. Use the BankingAPIClient in your views

Requirements:
    - Django 3.2+
    - CBS_PYTHON
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect

# Import the Django client from the CBS_PYTHON package
try:
    from Backend.integration_interfaces.django_client import BankingAPIClient, APIError
except ImportError:
    # If package is not installed, provide a helpful message
    import sys
    print("ERROR: Could not import BankingAPIClient from CBS_PYTHON package.")
    print("Make sure the CBS_PYTHON package is installed or in your Python path.")
    print("You can install it using: pip install -e /path/to/CBS_PYTHON")
    sys.exit(1)


# Create a client instance
api_client = BankingAPIClient()

# Example view for account listing
@csrf_protect
def accounts_view(request):
    """Display a list of customer accounts"""
    
    # Set session from Django request (extracts token and CSRF token)
    api_client.set_session_from_request(request)
    
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        # Get accounts from API
        accounts = api_client.get_accounts()
        
        # Pass data to template
        context = {
            'accounts': accounts,
            'title': 'Your Accounts'
        }
        
        return render(request, 'banking/accounts.html', context)
    
    except APIError as e:
        # Handle API errors
        messages.error(request, f"Error: {e.message}")
        return render(request, 'banking/error.html', {
            'error_message': e.message,
            'error_code': e.code,
            'title': 'Error'
        })


# Example view for account details
@csrf_protect
def account_details_view(request, account_number):
    """Display details for a specific account"""
    
    # Set session from Django request
    api_client.set_session_from_request(request)
    
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')
    
    try:
        # Get account details from API
        account = api_client.get_account_details(account_number)
        
        # Get recent transactions
        transactions = api_client.get_transactions(
            account_number,
            limit=10,
            sort='date:desc'
        )
        
        # Pass data to template
        context = {
            'account': account,
            'transactions': transactions,
            'title': f'Account: {account_number}'
        }
        
        return render(request, 'banking/account_details.html', context)
    
    except APIError as e:
        # Handle API errors
        messages.error(request, f"Error: {e.message}")
        return render(request, 'banking/error.html', {
            'error_message': e.message,
            'error_code': e.code,
            'title': 'Error'
        })


# Example view for money transfer
@csrf_protect
def transfer_view(request):
    """Handle money transfer between accounts"""
    
    # Set session from Django request
    api_client.set_session_from_request(request)
    
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect('login')
    
    # Get user accounts for the form
    try:
        accounts = api_client.get_accounts()
    except APIError as e:
        messages.error(request, f"Error loading accounts: {e.message}")
        accounts = []
    
    # Handle form submission
    if request.method == 'POST':
        try:
            # Extract form data
            from_account = request.POST.get('from_account')
            to_account = request.POST.get('to_account')
            amount = float(request.POST.get('amount', 0))
            currency = request.POST.get('currency', 'USD')
            description = request.POST.get('description', '')
            
            # Validate input
            if not from_account or not to_account:
                messages.error(request, "Please select source and destination accounts")
                return render(request, 'banking/transfer.html', {
                    'accounts': accounts,
                    'title': 'Money Transfer'
                })
            
            if amount <= 0:
                messages.error(request, "Amount must be greater than zero")
                return render(request, 'banking/transfer.html', {
                    'accounts': accounts,
                    'title': 'Money Transfer'
                })
            
            # Execute transfer
            result = api_client.transfer_money(
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                currency=currency,
                description=description
            )
            
            # Show success message
            messages.success(request, "Transfer completed successfully!")
            
            # Redirect to account details
            return redirect('account_details', account_number=from_account)
            
        except APIError as e:
            # Handle API errors
            messages.error(request, f"Transfer failed: {e.message}")
        
        except ValueError as e:
            # Handle invalid input
            messages.error(request, f"Invalid input: {str(e)}")
    
    # Display transfer form
    return render(request, 'banking/transfer.html', {
        'accounts': accounts,
        'title': 'Money Transfer'
    })


# Example API endpoint that proxies to the banking API
def api_proxy_view(request, endpoint):
    """Proxy API requests to the banking API"""
    
    # Set session from Django request
    api_client.set_session_from_request(request)
    
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'message': 'Authentication required'
        }, status=401)
    
    try:
        # Determine the HTTP method
        method = request.method.lower()
        
        # Extract request parameters
        if method == 'get':
            params = request.GET.dict()
            response = api_client.get(endpoint, params=params)
        elif method == 'post':
            data = request.POST.dict()
            response = api_client.post(endpoint, data=data)
        elif method == 'put':
            data = request.POST.dict()
            response = api_client.put(endpoint, data=data)
        elif method == 'delete':
            params = request.GET.dict()
            response = api_client.delete(endpoint, params=params)
        else:
            return JsonResponse({
                'status': 'error',
                'message': f'Unsupported method: {method}'
            }, status=405)
        
        # Return the API response
        return JsonResponse(response)
    
    except APIError as e:
        # Handle API errors
        return JsonResponse({
            'status': 'error',
            'message': e.message,
            'code': e.code
        }, status=e.status or 500)
    
    except Exception as e:
        # Handle other errors
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


# Example Django authentication integration
def login_view(request):
    """Handle user login and get JWT token"""
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if not username or not password:
            messages.error(request, "Please enter both username and password")
            return render(request, 'banking/login.html', {'title': 'Login'})
        
        try:
            # Authenticate with the banking API
            auth_data = api_client.authenticate(username, password)
            
            # Store the token in the session
            request.session['jwt_token'] = auth_data.get('token')
            
            # Redirect to accounts page
            return redirect('accounts')
            
        except APIError as e:
            # Handle authentication errors
            messages.error(request, f"Login failed: {e.message}")
    
    return render(request, 'banking/login.html', {'title': 'Login'})


def logout_view(request):
    """Handle user logout"""
    
    # Set session from Django request
    api_client.set_session_from_request(request)
    
    try:
        # Log out from the banking API
        api_client.logout()
    except:
        # Ignore API errors during logout
        pass
    
    # Clear the token from the session
    if 'jwt_token' in request.session:
        del request.session['jwt_token']
    
    # Log out from Django
    from django.contrib.auth import logout
    logout(request)
    
    # Redirect to login page
    return redirect('login')


# Example URL configuration
"""
# Add these to your urls.py file:

from django.urls import path
from .views import (
    accounts_view,
    account_details_view,
    transfer_view,
    login_view,
    logout_view,
    api_proxy_view
)

urlpatterns = [
    path('accounts/', accounts_view, name='accounts'),
    path('accounts/<str:account_number>/', account_details_view, name='account_details'),
    path('transfer/', transfer_view, name='transfer'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('api/<path:endpoint>/', api_proxy_view, name='api_proxy'),
]
"""
