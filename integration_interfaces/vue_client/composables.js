/**
 * Vue.js composables for interacting with the CBS Banking API
 */
import { ref, reactive, computed } from 'vue';
import { BankingApiClient, BankingApiError } from './BankingApiClient';

/**
 * Create a banking API client instance
 * 
 * @param {Object} config - Client configuration
 * @returns {BankingApiClient} Banking API client instance
 */
export function useBankingApiClient(config = {}) {
  return new BankingApiClient(config);
}

/**
 * Authentication composable
 * 
 * @param {BankingApiClient} client - Banking API client instance
 * @returns {Object} Authentication state and methods
 */
export function useAuth(client = null) {
  if (!client) {
    client = useBankingApiClient();
  }
  
  const isAuthenticated = ref(!!localStorage.getItem('jwt_token'));
  const isLoading = ref(false);
  const error = ref(null);
  const user = ref(null);
  
  const login = async (username, password) => {
    isLoading.value = true;
    error.value = null;
    
    try {
      const data = await client.login(username, password);
      isAuthenticated.value = true;
      user.value = data.user;
      return data;
    } catch (err) {
      error.value = err instanceof BankingApiError ? err : new Error('Login failed');
      throw err;
    } finally {
      isLoading.value = false;
    }
  };
  
  const logout = async () => {
    isLoading.value = true;
    
    try {
      await client.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      isAuthenticated.value = false;
      user.value = null;
      isLoading.value = false;
    }
  };
  
  return {
    isAuthenticated,
    isLoading,
    error,
    user,
    login,
    logout
  };
}

/**
 * Accounts composable
 * 
 * @param {BankingApiClient} client - Banking API client instance
 * @returns {Object} Accounts state and methods
 */
export function useAccounts(client = null) {
  if (!client) {
    client = useBankingApiClient();
  }
  
  const accounts = ref([]);
  const selectedAccount = ref(null);
  const isLoading = ref(false);
  const error = ref(null);
  
  const fetchAccounts = async () => {
    isLoading.value = true;
    error.value = null;
    
    try {
      accounts.value = await client.getAccounts();
    } catch (err) {
      error.value = err;
      accounts.value = [];
    } finally {
      isLoading.value = false;
    }
  };
  
  const selectAccount = async (accountId) => {
    isLoading.value = true;
    error.value = null;
    
    try {
      selectedAccount.value = await client.getAccountDetails(accountId);
    } catch (err) {
      error.value = err;
      selectedAccount.value = null;
    } finally {
      isLoading.value = false;
    }
  };
  
  const getBalance = async (accountId) => {
    try {
      return await client.getAccountBalance(accountId);
    } catch (err) {
      error.value = err;
      throw err;
    }
  };
  
  return {
    accounts,
    selectedAccount,
    isLoading,
    error,
    fetchAccounts,
    selectAccount,
    getBalance
  };
}

/**
 * Transactions composable
 * 
 * @param {BankingApiClient} client - Banking API client instance
 * @returns {Object} Transactions state and methods
 */
export function useTransactions(client = null) {
  if (!client) {
    client = useBankingApiClient();
  }
  
  const transactions = ref([]);
  const isLoading = ref(false);
  const error = ref(null);
  const transfer = reactive({
    fromAccount: '',
    toAccount: '',
    amount: 0,
    description: '',
    status: null
  });
  
  const fetchTransactions = async (accountId, params = {}) => {
    isLoading.value = true;
    error.value = null;
    
    try {
      transactions.value = await client.getAccountTransactions(accountId, params);
    } catch (err) {
      error.value = err;
      transactions.value = [];
    } finally {
      isLoading.value = false;
    }
  };
  
  const createTransfer = async (transferData) => {
    isLoading.value = true;
    error.value = null;
    transfer.status = null;
    
    try {
      const result = await client.createTransfer({
        fromAccount: transfer.fromAccount,
        toAccount: transfer.toAccount,
        amount: transfer.amount,
        description: transfer.description,
        ...transferData
      });
      
      transfer.status = 'success';
      return result;
    } catch (err) {
      error.value = err;
      transfer.status = 'error';
      throw err;
    } finally {
      isLoading.value = false;
    }
  };
  
  return {
    transactions,
    isLoading,
    error,
    transfer,
    fetchTransactions,
    createTransfer
  };
}

/**
 * Customer profile composable
 * 
 * @param {BankingApiClient} client - Banking API client instance
 * @returns {Object} Customer profile state and methods
 */
export function useCustomerProfile(client = null) {
  if (!client) {
    client = useBankingApiClient();
  }
  
  const profile = ref(null);
  const isLoading = ref(false);
  const error = ref(null);
  const isSaving = ref(false);
  
  const fetchProfile = async () => {
    isLoading.value = true;
    error.value = null;
    
    try {
      profile.value = await client.getCustomerProfile();
    } catch (err) {
      error.value = err;
      profile.value = null;
    } finally {
      isLoading.value = false;
    }
  };
  
  const updateProfile = async (profileData) => {
    isSaving.value = true;
    error.value = null;
    
    try {
      profile.value = await client.updateCustomerProfile(profileData);
      return profile.value;
    } catch (err) {
      error.value = err;
      throw err;
    } finally {
      isSaving.value = false;
    }
  };
  
  return {
    profile,
    isLoading,
    error,
    isSaving,
    fetchProfile,
    updateProfile
  };
}

/**
 * Cards composable
 * 
 * @param {BankingApiClient} client - Banking API client instance
 * @returns {Object} Cards state and methods
 */
export function useCards(client = null) {
  if (!client) {
    client = useBankingApiClient();
  }
  
  const cards = ref([]);
  const selectedCard = ref(null);
  const isLoading = ref(false);
  const error = ref(null);
  
  const fetchCards = async () => {
    isLoading.value = true;
    error.value = null;
    
    try {
      cards.value = await client.getCards();
    } catch (err) {
      error.value = err;
      cards.value = [];
    } finally {
      isLoading.value = false;
    }
  };
  
  const selectCard = async (cardId) => {
    isLoading.value = true;
    error.value = null;
    
    try {
      selectedCard.value = await client.getCardDetails(cardId);
    } catch (err) {
      error.value = err;
      selectedCard.value = null;
    } finally {
      isLoading.value = false;
    }
  };
  
  const updateCardStatus = async (cardId, status) => {
    isLoading.value = true;
    error.value = null;
    
    try {
      const updatedCard = await client.updateCardStatus(cardId, status);
      
      // Update the card in the cards array
      const index = cards.value.findIndex(card => card.id === cardId);
      if (index !== -1) {
        cards.value[index] = updatedCard;
      }
      
      // Update selected card if it's the one being updated
      if (selectedCard.value && selectedCard.value.id === cardId) {
        selectedCard.value = updatedCard;
      }
      
      return updatedCard;
    } catch (err) {
      error.value = err;
      throw err;
    } finally {
      isLoading.value = false;
    }
  };
  
  return {
    cards,
    selectedCard,
    isLoading,
    error,
    fetchCards,
    selectCard,
    updateCardStatus
  };
}

/**
 * UPI composable
 * 
 * @param {BankingApiClient} client - Banking API client instance
 * @returns {Object} UPI state and methods
 */
export function useUpi(client = null) {
  if (!client) {
    client = useBankingApiClient();
  }
  
  const upiAccounts = ref([]);
  const isLoading = ref(false);
  const error = ref(null);
  
  const fetchUpiAccounts = async () => {
    isLoading.value = true;
    error.value = null;
    
    try {
      upiAccounts.value = await client.getUpiAccounts();
    } catch (err) {
      error.value = err;
      upiAccounts.value = [];
    } finally {
      isLoading.value = false;
    }
  };
  
  const verifyUpiId = async (upiId) => {
    isLoading.value = true;
    error.value = null;
    
    try {
      return await client.verifyUpiId(upiId);
    } catch (err) {
      error.value = err;
      throw err;
    } finally {
      isLoading.value = false;
    }
  };
  
  const createUpiPayment = async (paymentData) => {
    isLoading.value = true;
    error.value = null;
    
    try {
      return await client.createUpiPayment(paymentData);
    } catch (err) {
      error.value = err;
      throw err;
    } finally {
      isLoading.value = false;
    }
  };
  
  return {
    upiAccounts,
    isLoading,
    error,
    fetchUpiAccounts,
    verifyUpiId,
    createUpiPayment
  };
}
