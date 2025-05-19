# Frontend Integration Guide for CBS Banking API

This guide provides information for frontend developers integrating with the Core Banking System API, with a focus on cross-framework compatibility.

## Overview

The CBS Banking API is designed to work seamlessly with various frontend frameworks, including:

- Django (Python)
- React/Next.js (JavaScript/TypeScript)
- Angular (TypeScript)
- Vue.js (JavaScript)
- Flutter (Dart)
- Native mobile apps (iOS/Android)

## API Basics

- **Base URL**: `http://<host>:<port>/api/v1`
- **Authentication**: JWT tokens via Bearer authentication
- **Content Type**: JSON for both requests and responses
- **Error Handling**: Standardized error responses with codes

## CORS Configuration

The API supports Cross-Origin Resource Sharing (CORS) for secure communication with frontends from different origins. The following settings are configured:

- **Allowed Origins**: Configurable via environment variable `CBS_CORS_ALLOWED_ORIGINS`
- **Allowed Methods**: GET, POST, PUT, DELETE, PATCH, OPTIONS
- **Allowed Headers**: Authorization, Content-Type, Accept, Origin, X-Requested-With, X-CSRF-Token, etc.
- **Supports Credentials**: Yes (for authenticated requests)
- **Max Age**: 3600 seconds (1 hour cache for preflight requests)

## Framework-Specific Integration

### Django Integration

For Django frontends, use the provided Django API client:

```python
from Backend.integration_interfaces.django_client import BankingAPIClient

# Create client instance
api_client = BankingAPIClient()

# Authenticate
auth_data = api_client.authenticate('username', 'password')

# Get accounts
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

The client can also be integrated with Django views and sessions:

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

For more details and examples, see the [Django Client README](../Backend/integration_interfaces/django_client/README.md).

### React/Next.js Integration

The CBS Banking System provides a dedicated React client library that makes integration easy and provides useful hooks for common banking operations.

#### Using the Client Library

```jsx
import {
  BankingApiProvider,
  useAuth,
  useAccounts,
  useTransactions
} from 'Backend/integration_interfaces/react_client';

// Wrap your application with the provider
function App() {
  return (
    <BankingApiProvider
      config={{
        baseUrl: process.env.REACT_APP_API_URL,
        timeout: 30000
      }}
    >
      <YourAppComponents />
    </BankingApiProvider>
  );
}

// Use hooks in your components
function AccountsComponent() {
  const { accounts, loading, error } = useAccounts();

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <ul>
      {accounts.map(account => (
        <li key={account.account_number}>
          {account.account_type}: {account.balance} {account.currency}
        </li>
      ))}
    </ul>
  );
}
```

For more details and examples, see the [React Client README](../Backend/integration_interfaces/react_client/README.md).

#### Manual Integration

You can also manually integrate using the Fetch API:

```javascript
// API base URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api/v1';

// Get accounts
async function getAccounts() {
  const token = localStorage.getItem('jwt_token');

  const response = await fetch(`${API_BASE_URL}/accounts`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    credentials: 'include'
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || 'Failed to fetch accounts');
  }

  return data.data.accounts;
}

// Make a transfer
async function transferMoney(fromAccount, toAccount, amount, currency, description) {
  const token = localStorage.getItem('jwt_token');

  const response = await fetch(`${API_BASE_URL}/transactions/transfer`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    credentials: 'include',
    body: JSON.stringify({
      from_account: fromAccount,
      to_account: toAccount,
      amount: amount,
      currency: currency || 'USD',
      description: description
    })
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || 'Transfer failed');
  }

  return data.data;
}
```

### Angular Integration

For Angular applications, you can use HttpClient with appropriate interceptors:

```typescript
// auth.interceptor.ts
import { Injectable } from '@angular/core';
import { HttpRequest, HttpHandler, HttpEvent, HttpInterceptor } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private authService: AuthService) {}

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    // Get the token from the auth service
    const token = this.authService.getToken();

    if (token) {
      // Clone the request and add the token
      request = request.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`
        },
        withCredentials: true
      });
    }

    return next.handle(request);
  }
}

// banking-api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class BankingApiService {
  private apiUrl = environment.apiUrl + '/api/v1';

  constructor(private http: HttpClient) {}

  getAccounts(): Observable<any> {
    return this.http.get(`${this.apiUrl}/accounts`);
  }

  getAccountDetails(accountNumber: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/accounts/${accountNumber}`);
  }

  transferMoney(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/transactions/transfer`, data);
  }
}
```

### Vue.js Integration

For Vue.js applications, you can use Axios:

```javascript
// banking-api.js
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_URL + '/api/v1',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
});

// Add an interceptor to add the token to each request
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('jwt_token');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

export default {
  getAccounts() {
    return apiClient.get('/accounts');
  },
  getAccountDetails(accountNumber) {
    return apiClient.get(`/accounts/${accountNumber}`);
  },
  transferMoney(fromAccount, toAccount, amount, currency, description) {
    return apiClient.post('/transactions/transfer', {
      from_account: fromAccount,
      to_account: toAccount,
      amount: amount,
      currency: currency || 'USD',
      description: description
    });
  },
  login(username, password) {
    return apiClient.post('/auth/login', {
      username: username,
      password: password
    });
  }
};
```

## Environment Configuration

### Development Environment

In the development environment, CORS is configured to allow requests from common local development servers:

- Django: http://localhost:8000, http://127.0.0.1:8000
- React/Next.js: http://localhost:3000, http://127.0.0.1:3000
- Angular: http://localhost:4200, http://127.0.0.1:4200
- Vue.js: http://localhost:8080, http://127.0.0.1:8080

### Production Environment

In production, CORS is configured to allow requests only from specific origins. Configure these using the `CBS_CORS_ALLOWED_ORIGINS` environment variable:

```
CBS_CORS_ALLOWED_ORIGINS=https://bank.example.com,https://admin.bank.example.com
```

## Authentication Flow

### Obtaining a JWT Token

1. Make a POST request to `/api/v1/auth/login` with username and password
2. Save the returned token for subsequent requests
3. Include the token in the Authorization header as `Bearer <token>`

### Token Expiration and Refresh

JWT tokens expire after a configurable period (default: 60 minutes). To refresh a token:

1. Make a POST request to `/api/v1/auth/refresh` with the current token
2. Save the new token for subsequent requests

### Logout

To logout and invalidate a token:

1. Make a POST request to `/api/v1/auth/logout`
2. Remove the token from client storage

## API Documentation

Full API documentation is available at `/api/v1/docs` when running the server in development mode.

## Troubleshooting

### CORS Issues

If you encounter CORS errors:

1. Check that your frontend origin is allowed in the CORS configuration
2. Ensure your requests include the appropriate headers
3. For local development, make sure you're using the correct ports

### Authentication Issues

If you encounter authentication errors:

1. Check that the token is being sent correctly in the Authorization header
2. Verify that the token has not expired
3. Ensure the user has the necessary permissions for the requested operation

## Support

For further assistance, contact the CBS Banking API development team at api-support@cbs-banking.example.com.
