/**
 * CBS Banking API Client for React Applications
 * 
 * This client provides a simple interface for React applications to interact
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
 * Core Banking System API Client
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
    this.baseUrl = config.baseUrl || process.env.REACT_APP_API_URL || 'http://localhost:5000/api/v1';
    this.timeout = config.timeout || 30000;
    this.retryAttempts = config.retryAttempts || 3;
    this.tokenProvider = config.tokenProvider || (() => localStorage.getItem('jwt_token'));
    this.onUnauthorized = config.onUnauthorized || (() => {});
    
    // Remove trailing slash from baseUrl if present
    if (this.baseUrl.endsWith('/')) {
      this.baseUrl = this.baseUrl.slice(0, -1);
    }
  }

  /**
   * Set the authentication token directly
   * 
   * @param {string} token - JWT token
   */
  setToken(token) {
    if (token) {
      localStorage.setItem('jwt_token', token);
    } else {
      localStorage.removeItem('jwt_token');
    }
  }

  /**
   * Clear the authentication token
   */
  clearToken() {
    localStorage.removeItem('jwt_token');
  }

  /**
   * Get the current authentication token
   * 
   * @returns {string} JWT token
   */
  getToken() {
    return this.tokenProvider();
  }

  /**
   * Build a full URL from a path
   * 
   * @param {string} path - API endpoint path
   * @returns {string} Full URL
   */
  _buildUrl(path) {
    // Handle paths with or without leading slash
    const normalizedPath = path.startsWith('/') ? path.slice(1) : path;
    return `${this.baseUrl}/${normalizedPath}`;
  }

  /**
   * Make an API request
   * 
   * @param {string} method - HTTP method
   * @param {string} path - API endpoint path
   * @param {Object} options - Request options
   * @param {Object} options.data - Request body data
   * @param {Object} options.params - URL query parameters
   * @param {Object} options.headers - Additional request headers
   * @param {boolean} options.retry - Whether to retry on failure
   * @returns {Promise<Object>} Response data
   * @throws {BankingApiError} If the API returns an error
   */
  async request(method, path, options = {}) {
    const { 
      data, 
      params, 
      headers: customHeaders = {}, 
      retry = true 
    } = options;
    
    const url = this._buildUrl(path);
    const token = this.getToken();
    
    // Prepare request headers
    const headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...customHeaders
    };
    
    // Add authorization header if token is available
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    // Prepare request options
    const fetchOptions = {
      method,
      headers,
      credentials: 'include'
    };
    
    // Add request body if provided
    if (data) {
      fetchOptions.body = JSON.stringify(data);
    }
    
    // Add URL parameters if provided
    let fetchUrl = url;
    if (params) {
      const queryParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        queryParams.append(key, value);
      });
      fetchUrl = `${url}?${queryParams.toString()}`;
    }
    
    // Make the request with retries
    let attempts = 0;
    const maxAttempts = retry ? this.retryAttempts : 1;
    
    while (attempts < maxAttempts) {
      attempts++;
      
      try {
        // Add timeout using AbortController
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        fetchOptions.signal = controller.signal;
        
        const response = await fetch(fetchUrl, fetchOptions);
        clearTimeout(timeoutId);
        
        // Handle JSON parsing
        let responseData;
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          responseData = await response.json();
        } else {
          responseData = await response.text();
        }
        
        // Handle unauthorized responses
        if (response.status === 401) {
          this.onUnauthorized();
        }
        
        // Handle API errors
        if (!response.ok || (responseData.status === 'error')) {
          const errorMessage = responseData.message || 'Unknown API error';
          const errorCode = responseData.code || 'UNKNOWN_ERROR';
          throw new BankingApiError(
            errorMessage,
            errorCode,
            response.status,
            responseData
          );
        }
        
        return responseData;
      } catch (error) {
        // Handle abort (timeout)
        if (error.name === 'AbortError') {
          if (attempts < maxAttempts) {
            console.warn(`Request timeout, retrying (${attempts}/${maxAttempts})`);
            continue;
          }
          throw new BankingApiError('Request timed out', 'TIMEOUT', 408);
        }
        
        // Handle network errors
        if (error.message === 'Failed to fetch' || error.message.includes('NetworkError')) {
          if (attempts < maxAttempts) {
            console.warn(`Network error, retrying (${attempts}/${maxAttempts})`);
            continue;
          }
          throw new BankingApiError('Network error', 'NETWORK_ERROR', 0);
        }
        
        // Re-throw BankingApiError
        if (error instanceof BankingApiError) {
          throw error;
        }
        
        // Handle other errors
        throw new BankingApiError(error.message, 'CLIENT_ERROR', 0);
      }
    }
  }

  /**
   * Make a GET request
   * 
   * @param {string} path - API endpoint path
   * @param {Object} params - URL query parameters
   * @param {Object} headers - Additional request headers
   * @returns {Promise<Object>} Response data
   */
  async get(path, params, headers) {
    return this.request('GET', path, { params, headers });
  }

  /**
   * Make a POST request
   * 
   * @param {string} path - API endpoint path
   * @param {Object} data - Request body data
   * @param {Object} params - URL query parameters
   * @param {Object} headers - Additional request headers
   * @returns {Promise<Object>} Response data
   */
  async post(path, data, params, headers) {
    return this.request('POST', path, { data, params, headers });
  }

  /**
   * Make a PUT request
   * 
   * @param {string} path - API endpoint path
   * @param {Object} data - Request body data
   * @param {Object} params - URL query parameters
   * @param {Object} headers - Additional request headers
   * @returns {Promise<Object>} Response data
   */
  async put(path, data, params, headers) {
    return this.request('PUT', path, { data, params, headers });
  }

  /**
   * Make a PATCH request
   * 
   * @param {string} path - API endpoint path
   * @param {Object} data - Request body data
   * @param {Object} params - URL query parameters
   * @param {Object} headers - Additional request headers
   * @returns {Promise<Object>} Response data
   */
  async patch(path, data, params, headers) {
    return this.request('PATCH', path, { data, params, headers });
  }

  /**
   * Make a DELETE request
   * 
   * @param {string} path - API endpoint path
   * @param {Object} params - URL query parameters
   * @param {Object} headers - Additional request headers
   * @returns {Promise<Object>} Response data
   */
  async delete(path, params, headers) {
    return this.request('DELETE', path, { params, headers });
  }

  // Banking-specific methods

  /**
   * Authenticate with the API
   * 
   * @param {string} username - Username or customer ID
   * @param {string} password - Password
   * @param {string} deviceId - Device identifier
   * @returns {Promise<Object>} Authentication response with token
   */
  async authenticate(username, password, deviceId = null) {
    const data = {
      username,
      password
    };
    
    if (deviceId) {
      data.device_id = deviceId;
    }
    
    const response = await this.post('auth/login', data);
    
    // Store the token if provided
    if (response.data && response.data.token) {
      this.setToken(response.data.token);
    }
    
    return response.data;
  }

  /**
   * Log out and invalidate the current token
   * 
   * @returns {Promise<Object>} Logout response
   */
  async logout() {
    try {
      const response = await this.post('auth/logout', {});
      this.clearToken();
      return response;
    } catch (error) {
      // Always clear token even if logout fails
      this.clearToken();
      throw error;
    }
  }

  /**
   * Get all accounts for the authenticated user
   * 
   * @returns {Promise<Array>} List of accounts
   */
  async getAccounts() {
    const response = await this.get('accounts');
    return response.data?.accounts || [];
  }

  /**
   * Get details for a specific account
   * 
   * @param {string} accountNumber - Account number
   * @returns {Promise<Object>} Account details
   */
  async getAccountDetails(accountNumber) {
    const response = await this.get(`accounts/${accountNumber}`);
    return response.data?.account || {};
  }

  /**
   * Get transactions for an account
   * 
   * @param {string} accountNumber - Account number
   * @param {Object} params - Filter parameters
   * @param {string} params.dateFrom - Start date (YYYY-MM-DD)
   * @param {string} params.dateTo - End date (YYYY-MM-DD)
   * @param {number} params.limit - Maximum number of transactions to return
   * @param {number} params.offset - Number of transactions to skip
   * @returns {Promise<Array>} List of transactions
   */
  async getTransactions(accountNumber, params = {}) {
    const response = await this.get(`accounts/${accountNumber}/transactions`, params);
    return response.data?.transactions || [];
  }

  /**
   * Transfer money between accounts
   * 
   * @param {string} fromAccount - Source account number
   * @param {string} toAccount - Destination account number
   * @param {number} amount - Amount to transfer
   * @param {string} currency - Currency code (default: USD)
   * @param {string} description - Transaction description
   * @returns {Promise<Object>} Transaction details
   */
  async transferMoney(fromAccount, toAccount, amount, currency = 'USD', description = null) {
    const data = {
      from_account: fromAccount,
      to_account: toAccount,
      amount,
      currency
    };
    
    if (description) {
      data.description = description;
    }
    
    const response = await this.post('transactions/transfer', data);
    return response.data?.transaction || {};
  }
}

export default BankingApiClient;
