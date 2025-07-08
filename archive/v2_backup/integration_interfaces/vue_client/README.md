# Vue.js Client for CBS Banking API

This package provides Vue.js composables and a client to interact with the Core Banking System API.

## Installation

```bash
npm install @cbs/vue-banking-api
```

## Usage

### Basic Setup

```javascript
import { createApp } from 'vue'
import App from './App.vue'
import { BankingApiClient } from '@cbs/vue-banking-api'

// Create a global API client instance
const apiClient = new BankingApiClient({
  baseUrl: process.env.VUE_APP_API_URL,
  timeout: 30000,
  retryAttempts: 3,
  onUnauthorized: () => {
    // Redirect to login page
    router.push('/login')
  }
})

// Provide the client to the app
const app = createApp(App)
app.provide('bankingApi', apiClient)
app.mount('#app')
```

### Using Composables

```vue
<template>
  <div>
    <div v-if="isLoading">Loading accounts...</div>
    <div v-else-if="error">Error: {{ error.message }}</div>
    <div v-else>
      <h2>Your Accounts</h2>
      <ul>
        <li v-for="account in accounts" :key="account.id">
          {{ account.accountNumber }} - {{ account.type }}
          <strong>Balance: {{ account.balance }} {{ account.currency }}</strong>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAccounts } from '@cbs/vue-banking-api'

// Use the accounts composable
const { accounts, isLoading, error, fetchAccounts } = useAccounts()

// Load accounts when component mounts
onMounted(() => {
  fetchAccounts()
})
</script>
```

## Available Composables

### `useBankingApiClient(config)`

Creates a new BankingApiClient instance.

```javascript
import { useBankingApiClient } from '@cbs/vue-banking-api'

const client = useBankingApiClient({
  baseUrl: 'https://api.mybank.com/v1',
  timeout: 30000
})
```

### `useAuth(client)`

Provides authentication functionality.

```javascript
import { useAuth } from '@cbs/vue-banking-api'

const { isAuthenticated, isLoading, error, user, login, logout } = useAuth()

// Login
const handleLogin = async () => {
  try {
    await login('username', 'password')
    // Redirect on success
  } catch (err) {
    // Handle error
  }
}
```

### `useAccounts(client)`

Provides account management functionality.

```javascript
import { useAccounts } from '@cbs/vue-banking-api'

const {
  accounts,
  selectedAccount,
  isLoading,
  error,
  fetchAccounts,
  selectAccount,
  getBalance
} = useAccounts()
```

### `useTransactions(client)`

Provides transaction functionality.

```javascript
import { useTransactions } from '@cbs/vue-banking-api'

const {
  transactions,
  isLoading,
  error,
  transfer,
  fetchTransactions,
  createTransfer
} = useTransactions()
```

### `useCustomerProfile(client)`

Provides customer profile management.

```javascript
import { useCustomerProfile } from '@cbs/vue-banking-api'

const {
  profile,
  isLoading,
  error,
  isSaving,
  fetchProfile,
  updateProfile
} = useCustomerProfile()
```

### `useCards(client)`

Provides card management functionality.

```javascript
import { useCards } from '@cbs/vue-banking-api'

const {
  cards,
  selectedCard,
  isLoading,
  error,
  fetchCards,
  selectCard,
  updateCardStatus
} = useCards()
```

### `useUpi(client)`

Provides UPI payment functionality.

```javascript
import { useUpi } from '@cbs/vue-banking-api'

const {
  upiAccounts,
  isLoading,
  error,
  fetchUpiAccounts,
  verifyUpiId,
  createUpiPayment
} = useUpi()
```

## Error Handling

All composables provide an `error` ref that contains any API errors that occur.

```javascript
import { useAccounts, BankingApiError } from '@cbs/vue-banking-api'

const { accounts, isLoading, error, fetchAccounts } = useAccounts()

const loadAccounts = async () => {
  try {
    await fetchAccounts()
  } catch (err) {
    if (err instanceof BankingApiError) {
      console.log(err.message)  // Error message
      console.log(err.code)     // Error code
      console.log(err.status)   // HTTP status
      console.log(err.response) // Full response object
    }
  }
}
```
