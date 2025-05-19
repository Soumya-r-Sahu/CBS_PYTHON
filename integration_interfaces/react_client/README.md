# React Client for CBS Banking API

A client library for React applications to integrate with the Core Banking System API.

## Overview

This client provides React components and hooks to easily connect to the CBS Banking API. It includes:

- API client for making authenticated requests
- React hooks for common banking operations
- Error handling and automatic retries
- TypeScript support (coming soon)

## Installation

This client is part of the CBS_PYTHON codebase. If you need to use it as a standalone package, simply copy the `react_client` directory to your React project.

## Usage

### Setting Up the Provider

Wrap your application with the `BankingApiProvider` to make the API client available to all components:

```jsx
import { BankingApiProvider } from './react_client/hooks';

function App() {
  const apiConfig = {
    baseUrl: process.env.REACT_APP_API_URL || 'http://localhost:5000/api/v1',
    timeout: 30000,
    retryAttempts: 3,
    onUnauthorized: () => {
      // Handle unauthorized responses (e.g., redirect to login)
      window.location.href = '/login';
    }
  };

  return (
    <BankingApiProvider config={apiConfig}>
      <YourApp />
    </BankingApiProvider>
  );
}
```

### Using the Hooks

#### Authentication

```jsx
import { useAuth } from './react_client/hooks';

function LoginPage() {
  const { login, isAuthenticated, user } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError(null);

    try {
      await login(username, password);
      // Navigate to dashboard on success
    } catch (err) {
      setError(err.message);
    }
  };

  if (isAuthenticated) {
    return <div>Welcome, {user?.name}!</div>;
  }

  return (
    <form onSubmit={handleLogin}>
      {error && <div className="error">{error}</div>}
      <input
        type="text"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        placeholder="Username"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
      />
      <button type="submit">Login</button>
    </form>
  );
}
```

#### Fetching Accounts

```jsx
import { useAccounts } from './react_client/hooks';

function AccountsList() {
  const { accounts, loading, error, refetch } = useAccounts();

  if (loading) return <div>Loading accounts...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h2>Your Accounts</h2>
      <button onClick={refetch}>Refresh</button>
      <ul>
        {accounts.map(account => (
          <li key={account.account_number}>
            {account.account_type}: {account.balance} {account.currency}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

#### Fetching Transactions

```jsx
import { useTransactions } from './react_client/hooks';

function TransactionsList({ accountNumber }) {
  const { transactions, loading, error } = useTransactions(accountNumber, {
    dateFrom: '2023-01-01',
    dateTo: '2023-12-31',
    limit: 20
  });

  if (loading) return <div>Loading transactions...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h2>Recent Transactions</h2>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Description</th>
            <th>Amount</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map(transaction => (
            <tr key={transaction.id}>
              <td>{transaction.date}</td>
              <td>{transaction.description}</td>
              <td className={transaction.amount < 0 ? 'debit' : 'credit'}>
                {transaction.amount} {transaction.currency}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

#### Money Transfer

```jsx
import { useTransfer, useAccounts } from './react_client/hooks';

function TransferForm() {
  const { accounts } = useAccounts();
  const { transferMoney, loading, error } = useTransfer();
  const [fromAccount, setFromAccount] = useState('');
  const [toAccount, setToAccount] = useState('');
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [description, setDescription] = useState('');
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSuccess(false);

    try {
      await transferMoney(fromAccount, toAccount, parseFloat(amount), currency, description);
      setSuccess(true);
      // Reset form
      setAmount('');
      setDescription('');
    } catch (err) {
      // Error is handled by the hook
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {error && <div className="error">{error.message}</div>}
      {success && <div className="success">Transfer successful!</div>}

      <div>
        <label htmlFor="fromAccount">From Account</label>
        <select
          id="fromAccount"
          value={fromAccount}
          onChange={(e) => setFromAccount(e.target.value)}
          required
        >
          <option value="">Select account</option>
          {accounts.map(account => (
            <option key={account.account_number} value={account.account_number}>
              {account.account_type}: {account.account_number} ({account.balance} {account.currency})
            </option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="toAccount">To Account</label>
        <input
          id="toAccount"
          type="text"
          value={toAccount}
          onChange={(e) => setToAccount(e.target.value)}
          placeholder="Recipient account number"
          required
        />
      </div>

      <div>
        <label htmlFor="amount">Amount</label>
        <input
          id="amount"
          type="number"
          step="0.01"
          min="0.01"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          required
        />
      </div>

      <div>
        <label htmlFor="currency">Currency</label>
        <select
          id="currency"
          value={currency}
          onChange={(e) => setCurrency(e.target.value)}
        >
          <option value="USD">USD</option>
          <option value="EUR">EUR</option>
          <option value="GBP">GBP</option>
          <option value="INR">INR</option>
        </select>
      </div>

      <div>
        <label htmlFor="description">Description</label>
        <input
          id="description"
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Transfer description"
        />
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Processing...' : 'Transfer Money'}
      </button>
    </form>
  );
}
```

### Direct API Client Usage

You can also use the API client directly without the hooks:

```jsx
import { useBankingApi } from './react_client/hooks';
import { useState, useEffect } from 'react';

function CustomComponent() {
  const api = useBankingApi();
  const [data, setData] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        // Make a custom API call
        const response = await api.get('custom/endpoint');
        setData(response.data);
      } catch (error) {
        console.error('API error:', error);
      }
    }

    fetchData();
  }, [api]);

  return (
    <div>
      {/* Render your component using the data */}
    </div>
  );
}
```

## Error Handling

The client includes a custom `BankingApiError` class that provides detailed information about API errors:

```jsx
import { useBankingApi } from './react_client/hooks';
import { BankingApiError } from './react_client/BankingApiClient';

function ErrorHandlingExample() {
  const api = useBankingApi();

  const handleApiCall = async () => {
    try {
      await api.get('some/endpoint');
    } catch (error) {
      if (error instanceof BankingApiError) {
        console.log('Error message:', error.message);
        console.log('Error code:', error.code);
        console.log('HTTP status:', error.status);

        // Handle specific error codes
        if (error.code === 'INSUFFICIENT_FUNDS') {
          alert('You do not have enough funds to complete this transaction.');
        }
      } else {
        console.error('Unexpected error:', error);
      }
    }
  };

  return (
    <button onClick={handleApiCall}>Make API Call</button>
  );
}
```

## Configuration

The client can be configured through the props passed to the `BankingApiProvider`:

| Option | Description | Default |
|--------|-------------|---------|
| `baseUrl` | Base URL for the API | `http://localhost:5000/api/v1` |
| `timeout` | Request timeout in milliseconds | `30000` |
| `retryAttempts` | Number of retry attempts for failed requests | `3` |
| `tokenProvider` | Function that returns the auth token | `() => localStorage.getItem('jwt_token')` |
| `onUnauthorized` | Callback for unauthorized responses | `() => {}` |

## License

This client is part of the CBS_PYTHON project and is subject to the same license.
