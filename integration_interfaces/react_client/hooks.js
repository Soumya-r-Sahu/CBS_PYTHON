/**
 * React Hooks for CBS Banking API
 * 
 * This file provides React hooks for easy integration with the Core Banking System API.
 * 
 * @version 1.0.0
 */

import { useState, useEffect, useCallback, useContext, createContext } from 'react';
import BankingApiClient from './BankingApiClient';

// Create Banking API context
const BankingApiContext = createContext(null);

/**
 * Provider component for Banking API context
 * 
 * Wraps your application to provide API client to all components
 * 
 * @param {Object} props - Component props
 * @param {Object} props.config - API client configuration
 * @param {ReactNode} props.children - Child components
 */
export function BankingApiProvider({ config, children }) {
  // Create API client instance
  const apiClient = new BankingApiClient(config);
  
  return (
    <BankingApiContext.Provider value={apiClient}>
      {children}
    </BankingApiContext.Provider>
  );
}

/**
 * Hook to access the Banking API client
 * 
 * @returns {BankingApiClient} API client instance
 */
export function useBankingApi() {
  const context = useContext(BankingApiContext);
  
  if (!context) {
    throw new Error('useBankingApi must be used within a BankingApiProvider');
  }
  
  return context;
}

/**
 * Hook for authentication state
 * 
 * @returns {Object} Authentication utilities
 * @returns {boolean} .isAuthenticated - Whether user is authenticated
 * @returns {Object} .user - User data
 * @returns {Function} .login - Login function
 * @returns {Function} .logout - Logout function
 */
export function useAuth() {
  const api = useBankingApi();
  const [isAuthenticated, setIsAuthenticated] = useState(!!api.getToken());
  const [user, setUser] = useState(null);
  
  // Check if token exists on mount
  useEffect(() => {
    const token = api.getToken();
    setIsAuthenticated(!!token);
    
    // If authenticated, load user data
    if (token) {
      api.get('auth/me')
        .then(response => {
          setUser(response.data.user);
        })
        .catch(() => {
          // Token is invalid
          api.clearToken();
          setIsAuthenticated(false);
          setUser(null);
        });
    }
  }, [api]);
  
  // Login function
  const login = useCallback(async (username, password, deviceId) => {
    try {
      const data = await api.authenticate(username, password, deviceId);
      setIsAuthenticated(true);
      setUser(data.user);
      return data;
    } catch (error) {
      setIsAuthenticated(false);
      setUser(null);
      throw error;
    }
  }, [api]);
  
  // Logout function
  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      setIsAuthenticated(false);
      setUser(null);
    }
  }, [api]);
  
  return {
    isAuthenticated,
    user,
    login,
    logout
  };
}

/**
 * Hook to fetch accounts for the authenticated user
 * 
 * @returns {Object} Accounts data and utilities
 * @returns {Array} .accounts - List of accounts
 * @returns {boolean} .loading - Whether accounts are being loaded
 * @returns {Error} .error - Error if fetch failed
 * @returns {Function} .refetch - Function to refetch accounts
 */
export function useAccounts() {
  const api = useBankingApi();
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const fetchAccounts = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const accounts = await api.getAccounts();
      setAccounts(accounts);
      return accounts;
    } catch (error) {
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [api]);
  
  // Fetch accounts on mount
  useEffect(() => {
    fetchAccounts().catch(() => {});
  }, [fetchAccounts]);
  
  return {
    accounts,
    loading,
    error,
    refetch: fetchAccounts
  };
}

/**
 * Hook to fetch transactions for a specific account
 * 
 * @param {string} accountNumber - Account number
 * @param {Object} params - Filter parameters
 * @returns {Object} Transactions data and utilities
 * @returns {Array} .transactions - List of transactions
 * @returns {boolean} .loading - Whether transactions are being loaded
 * @returns {Error} .error - Error if fetch failed
 * @returns {Function} .refetch - Function to refetch transactions
 */
export function useTransactions(accountNumber, params = {}) {
  const api = useBankingApi();
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const fetchTransactions = useCallback(async () => {
    if (!accountNumber) {
      setTransactions([]);
      setLoading(false);
      return [];
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const transactions = await api.getTransactions(accountNumber, params);
      setTransactions(transactions);
      return transactions;
    } catch (error) {
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [api, accountNumber, params]);
  
  // Fetch transactions when account number or params change
  useEffect(() => {
    fetchTransactions().catch(() => {});
  }, [fetchTransactions]);
  
  return {
    transactions,
    loading,
    error,
    refetch: fetchTransactions
  };
}

/**
 * Hook to transfer money between accounts
 * 
 * @returns {Object} Transfer utilities
 * @returns {Function} .transferMoney - Function to transfer money
 * @returns {boolean} .loading - Whether transfer is in progress
 * @returns {Error} .error - Error if transfer failed
 */
export function useTransfer() {
  const api = useBankingApi();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const transferMoney = useCallback(async (fromAccount, toAccount, amount, currency, description) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await api.transferMoney(fromAccount, toAccount, amount, currency, description);
      return result;
    } catch (error) {
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, [api]);
  
  return {
    transferMoney,
    loading,
    error
  };
}

export default {
  BankingApiProvider,
  useBankingApi,
  useAuth,
  useAccounts,
  useTransactions,
  useTransfer
};
