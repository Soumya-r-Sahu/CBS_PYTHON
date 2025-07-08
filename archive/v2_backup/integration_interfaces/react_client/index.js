/**
 * CBS Banking API React Client
 * 
 * Main entry point for the React client library.
 * 
 * @version 1.0.0
 */

import BankingApiClient, { BankingApiError } from './BankingApiClient';
import {
  BankingApiProvider,
  useBankingApi,
  useAuth,
  useAccounts,
  useTransactions,
  useTransfer
} from './hooks';

// Export all components and hooks
export {
  BankingApiClient,
  BankingApiError,
  BankingApiProvider,
  useBankingApi,
  useAuth,
  useAccounts,
  useTransactions,
  useTransfer
};

// Default export
export default {
  BankingApiClient,
  BankingApiError,
  BankingApiProvider,
  useBankingApi,
  useAuth,
  useAccounts,
  useTransactions,
  useTransfer
};
