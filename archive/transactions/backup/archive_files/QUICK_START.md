# Banking System Quick Start Guide

Welcome to the Core Banking System! This guide will help you quickly set up and start using the system.

## Getting Started in 5 Minutes

### 1. Set Up Your Environment

Make sure you have Python 3.8+ installed, then install the requirements:

```powershell
# Install all required packages
pip install -r requirements.txt
```

### 2. Start the Banking System

The easiest way to start the system is to use the friendly startup script:

```powershell
# Start the entire banking system
python start_banking_server.py

# If you only need the API server
python start_banking_server.py --api-only
```

### 3. Update the Database (if needed)

If you need to update your database to match code changes:

```powershell
# Update the development database safely
python Backend\scripts\deployment\database\update_banking_database.py
```

## Common Tasks

### View Available API Endpoints

Once the system is running, you can access:
- API documentation: http://localhost:5000/api/docs
- Health check: http://localhost:5000/api/v1/health

### Run Database Maintenance

To keep your database performing well:

```powershell
# Perform maintenance on development database
python Backend\scripts\maintenance\database\banking_database_manager.py --task=maintain
```

## Frontend Integration

The banking system is designed to work with various frontend frameworks, including Django, React, Angular, and Vue.js.

### Connecting a Django Frontend

```python
# In your Django views.py
from Backend.integration_interfaces.django_client import BankingAPIClient

def account_view(request):
    client = BankingAPIClient()
    client.set_session_from_request(request)
    accounts = client.get_accounts()
    return render(request, 'accounts/list.html', {'accounts': accounts})
```

### Connecting a React Frontend

```javascript
// In your React component
import {
  BankingApiProvider,
  useAccounts
} from 'Backend/integration_interfaces/react_client';

// Wrap your app with the provider
function App() {
  return (
    <BankingApiProvider>
      <YourAppComponents />
    </BankingApiProvider>
  );
}

// Use the hooks in your components
function AccountsList() {
  const { accounts, loading, error } = useAccounts();

  if (loading) return <div>Loading...</div>;

  return (
    <ul>
      {accounts.map(account => (
        <li key={account.account_number}>
          {account.account_type}: {account.balance}
        </li>
      ))}
    </ul>
  );
}
```

### Connecting Other Frontend Frameworks

For other frontend frameworks, you can use the REST API directly:

```javascript
// Example using fetch (JavaScript)
async function getAccounts() {
  const response = await fetch('http://localhost:5000/api/v1/accounts', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  return await response.json();
}
```

### Testing Cross-Framework Compatibility

To verify that the API works correctly with different frontend frameworks:

```powershell
# Run compatibility tests for all supported frameworks
python Tests\integration\cross_framework_compatibility_test.py
```

For detailed frontend integration information, see the [Frontend Integration Guide](Documentation/api_guides/FRONTEND_INTEGRATION.md) and [Cross-Framework Updates](Documentation/api_guides/CROSS_FRAMEWORK_UPDATES.md).
```

### Check System Status

To verify all components are running properly:

```powershell
# Check status of all services
python Backend\scripts\maintenance\system\check_system_health.py
```

## Getting Help

If you need assistance, you can:

1. Check the documentation in the `Documentation/` folder
2. Look at examples in the `Backend/examples/` directory
3. Run the test suite to verify your setup:
   ```powershell
   python Tests\run_tests.py
   ```

Happy banking!
