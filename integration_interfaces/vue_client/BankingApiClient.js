/**
 * CBS Banking API Client for Vue.js Applications
 * 
 * This client provides a simple interface for Vue.js applications to interact
 * with the Core Banking System API.
 * 
 * @version 1.0.0
 */

/**
 * API Error class for handling banking API errors
 */
export class BankingApiError extends Error {
  /**
   * Create a new BankingApiError
   * 
   * @param {string} message - Error message
   * @param {string} code - Error code
   * @param {number} status - HTTP status code
   * @param {Object} response - Full response object
   */
  constructor(message, code, status, response) {
    super(message);
    this.name = 'BankingApiError';
    this.code = code;
    this.status = status;
    this.response = response;
  }
}

/**
 * Core Banking System API Client for Vue.js
 */
export class BankingApiClient {
  /**
   * Create a new BankingApiClient
   * 
   * @param {Object} config - Client configuration
   * @param {string} config.baseUrl - API base URL
   * @param {number} config.timeout - Request timeout in milliseconds
   * @param {number} config.retryAttempts - Number of retry attempts
   * @param {Function} config.tokenProvider - Function that returns the auth token
   * @param {Function} config.onUnauthorized - Callback for unauthorized responses
   */
  constructor(config = {}) {
    this.baseUrl = config.baseUrl || process.env.VUE_APP_API_URL || 'http://localhost:5000/api/v1';
    this.timeout = config.timeout || 30000;
    this.retryAttempts = config.retryAttempts || 3;
    this.tokenProvider = config.tokenProvider || (() => localStorage.getItem('jwt_token'));
    this.onUnauthorized = config.onUnauthorized || (() => {});
  }

  /**
   * Helper method to create request headers
   * 
   * @returns {Object} Headers object
   */
  _createHeaders() {
    const token = this.tokenProvider();
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
  }

  /**
   * Helper method to handle API errors
   * 
   * @param {Object} response - API response
   * @returns {Promise} Rejected promise with error details
   */
  async _handleErrorResponse(response) {
    let errorData = {
      message: 'Unknown error',
      code: 'UNKNOWN_ERROR'
    };
    
    try {
      errorData = await response.json();
    } catch (e) {
      // Unable to parse error as JSON
    }
    
    // Handle unauthorized responses
    if (response.status === 401) {
      this.onUnauthorized();
    }
    
    return Promise.reject(
      new BankingApiError(
        errorData.message || response.statusText,
        errorData.code || `HTTP_${response.status}`,
        response.status,
        errorData
      )
    );
  }

  /**
   * Make an API request
   * 
   * @param {string} method - HTTP method
   * @param {string} endpoint - API endpoint
   * @param {Object} data - Request data
   * @returns {Promise} Promise resolving to response data
   */
  async request(method, endpoint, data = null) {
    const url = `${this.baseUrl}${endpoint}`;
    const options = {
      method: method.toUpperCase(),
      headers: this._createHeaders(),
      timeout: this.timeout
    };
    
    if (data && ['POST', 'PUT', 'PATCH'].includes(method.toUpperCase())) {
      options.body = JSON.stringify(data);
    }
    
    let retries = 0;
    let lastError = null;
    
    while (retries <= this.retryAttempts) {
      try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
          return this._handleErrorResponse(response);
        }
        
        // Handle no-content responses
        if (response.status === 204) {
          return null;
        }
        
        return await response.json();
      } catch (error) {
        lastError = error;
        retries++;
        
        if (retries > this.retryAttempts) {
          break;
        }
        
        // Add exponential backoff for retries
        await new Promise(resolve => setTimeout(resolve, 2 ** retries * 100));
      }
    }
    
    // If we've exhausted retries, throw the last error
    throw new BankingApiError(
      lastError?.message || 'Network error',
      'NETWORK_ERROR',
      0,
      lastError
    );
  }
  
  /**
   * ===============================================================
   * Authentication Methods
   * ===============================================================
   */
  
  /**
   * Log in a user
   * 
   * @param {string} username - User's username
   * @param {string} password - User's password
   * @returns {Promise} Promise resolving to authentication data
   */
  async login(username, password) {
    const data = await this.request('POST', '/auth/login', { username, password });
    
    if (data && data.token) {
      localStorage.setItem('jwt_token', data.token);
    }
    
    return data;
  }
  
  /**
   * Log out the current user
   * 
   * @returns {Promise} Promise resolving when logout is complete
   */
  async logout() {
    try {
      await this.request('POST', '/auth/logout');
    } finally {
      localStorage.removeItem('jwt_token');
    }
  }
  
  /**
   * ===============================================================
   * Account Methods
   * ===============================================================
   */
  
  /**
   * Get all accounts for the current user
   * 
   * @returns {Promise<Array>} Promise resolving to array of accounts
   */
  getAccounts() {
    return this.request('GET', '/accounts');
  }
  
  /**
   * Get details for a specific account
   * 
   * @param {string} accountId - Account ID
   * @returns {Promise<Object>} Promise resolving to account details
   */
  getAccountDetails(accountId) {
    return this.request('GET', `/accounts/${accountId}`);
  }
  
  /**
   * Get transactions for a specific account
   * 
   * @param {string} accountId - Account ID
   * @param {Object} params - Query parameters
   * @returns {Promise<Array>} Promise resolving to array of transactions
   */
  getAccountTransactions(accountId, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const endpoint = `/accounts/${accountId}/transactions${queryString ? `?${queryString}` : ''}`;
    return this.request('GET', endpoint);
  }
  
  /**
   * Get balance for a specific account
   * 
   * @param {string} accountId - Account ID
   * @returns {Promise<Object>} Promise resolving to account balance
   */
  getAccountBalance(accountId) {
    return this.request('GET', `/accounts/${accountId}/balance`);
  }
  
  /**
   * ===============================================================
   * Transaction Methods
   * ===============================================================
   */
  
  /**
   * Create a new transfer
   * 
   * @param {Object} transferData - Transfer details
   * @returns {Promise<Object>} Promise resolving to transfer result
   */
  createTransfer(transferData) {
    return this.request('POST', '/transactions/transfer', transferData);
  }
  
  /**
   * Get status of a transaction
   * 
   * @param {string} transactionId - Transaction ID
   * @returns {Promise<Object>} Promise resolving to transaction status
   */
  getTransactionStatus(transactionId) {
    return this.request('GET', `/transactions/${transactionId}/status`);
  }
  
  /**
   * ===============================================================
   * Customer Methods
   * ===============================================================
   */
  
  /**
   * Get the current customer's profile
   * 
   * @returns {Promise<Object>} Promise resolving to customer profile
   */
  getCustomerProfile() {
    return this.request('GET', '/customers/profile');
  }
  
  /**
   * Update the current customer's profile
   * 
   * @param {Object} profileData - Updated profile data
   * @returns {Promise<Object>} Promise resolving to updated profile
   */
  updateCustomerProfile(profileData) {
    return this.request('PUT', '/customers/profile', profileData);
  }
  
  /**
   * ===============================================================
   * Card Methods
   * ===============================================================
   */
  
  /**
   * Get all cards for the current user
   * 
   * @returns {Promise<Array>} Promise resolving to array of cards
   */
  getCards() {
    return this.request('GET', '/cards');
  }
  
  /**
   * Get details for a specific card
   * 
   * @param {string} cardId - Card ID
   * @returns {Promise<Object>} Promise resolving to card details
   */
  getCardDetails(cardId) {
    return this.request('GET', `/cards/${cardId}`);
  }
  
  /**
   * Update status for a specific card
   * 
   * @param {string} cardId - Card ID
   * @param {string} status - New card status
   * @returns {Promise<Object>} Promise resolving to updated card
   */
  updateCardStatus(cardId, status) {
    return this.request('PUT', `/cards/${cardId}/status`, { status });
  }
  
  /**
   * ===============================================================
   * UPI Methods
   * ===============================================================
   */
  
  /**
   * Get all UPI accounts for the current user
   * 
   * @returns {Promise<Array>} Promise resolving to array of UPI accounts
   */
  getUpiAccounts() {
    return this.request('GET', '/upi/accounts');
  }
  
  /**
   * Create a new UPI payment
   * 
   * @param {Object} paymentData - Payment details
   * @returns {Promise<Object>} Promise resolving to payment result
   */
  createUpiPayment(paymentData) {
    return this.request('POST', '/upi/pay', paymentData);
  }
  
  /**
   * Verify a UPI ID
   * 
   * @param {string} upiId - UPI ID to verify
   * @returns {Promise<Object>} Promise resolving to verification result
   */
  verifyUpiId(upiId) {
    return this.request('GET', `/upi/verify/${upiId}`);
  }
}
