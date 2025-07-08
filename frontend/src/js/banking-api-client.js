/**
 * Banking API Client Library
 * Handles communication with the backend through the Express API router
 * 
 * @module banking-api-client
 */

class BankingApiClient {
  constructor(config = {}) {
    this.baseUrl = config.baseUrl || '/api'; // Use frontend's API router
    this.timeout = config.timeout || 30000;
    this.retryAttempts = config.retryAttempts || 3;
    this.onUnauthorized = config.onUnauthorized || (() => window.location.href = '/login');
  }

  /**
   * Make API request through the Express router
   */
  async request(method, endpoint, data = null, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      credentials: 'include', // Include cookies for authentication
      ...options
    };

    if (data && ['POST', 'PUT', 'PATCH'].includes(method)) {
      config.body = JSON.stringify(data);
    }

    try {
      const response = await fetch(url, config);
      
      if (response.status === 401) {
        this.onUnauthorized();
        throw new Error('Unauthorized');
      }

      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.message || 'Request failed');
      }

      return result;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Account methods
  async getAccounts() {
    return this.request('GET', '/accounts');
  }

  async getAccount(accountId) {
    return this.request('GET', `/accounts/${accountId}`);
  }

  async getAccountBalance(accountId) {
    return this.request('GET', `/accounts/${accountId}/balance`);
  }

  async getAccountTransactions(accountId, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request('GET', `/accounts/${accountId}/transactions?${queryString}`);
  }

  async createAccount(accountData) {
    return this.request('POST', '/accounts', accountData);
  }

  async updateAccount(accountId, accountData) {
    return this.request('PUT', `/accounts/${accountId}`, accountData);
  }

  // Transaction methods
  async getTransactions(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request('GET', `/transactions?${queryString}`);
  }

  async getTransaction(transactionId) {
    return this.request('GET', `/transactions/${transactionId}`);
  }

  async createTransfer(transferData) {
    return this.request('POST', '/transactions/transfer', transferData);
  }

  async createDeposit(depositData) {
    return this.request('POST', '/transactions/deposit', depositData);
  }

  async createWithdrawal(withdrawalData) {
    return this.request('POST', '/transactions/withdrawal', withdrawalData);
  }

  async getTransactionStatus(transactionId) {
    return this.request('GET', `/transactions/${transactionId}/status`);
  }

  // Customer methods
  async getCustomers(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request('GET', `/customers?${queryString}`);
  }

  async getCustomer(customerId) {
    return this.request('GET', `/customers/${customerId}`);
  }

  async getCustomerProfile() {
    return this.request('GET', '/customers/profile');
  }

  async updateCustomerProfile(profileData) {
    return this.request('PUT', '/customers/profile', profileData);
  }

  async createCustomer(customerData) {
    return this.request('POST', '/customers', customerData);
  }

  async updateCustomer(customerId, customerData) {
    return this.request('PUT', `/customers/${customerId}`, customerData);
  }

  // Card methods
  async getCards() {
    return this.request('GET', '/cards');
  }

  async getCard(cardId) {
    return this.request('GET', `/cards/${cardId}`);
  }

  async createCard(cardData) {
    return this.request('POST', '/cards', cardData);
  }

  async updateCard(cardId, cardData) {
    return this.request('PUT', `/cards/${cardId}`, cardData);
  }

  async updateCardStatus(cardId, status) {
    return this.request('PUT', `/cards/${cardId}/status`, { status });
  }

  // Loan methods
  async getLoans() {
    return this.request('GET', '/loans');
  }

  async getLoan(loanId) {
    return this.request('GET', `/loans/${loanId}`);
  }

  async createLoan(loanData) {
    return this.request('POST', '/loans', loanData);
  }

  async updateLoan(loanId, loanData) {
    return this.request('PUT', `/loans/${loanId}`, loanData);
  }

  async makeLoanPayment(loanId, paymentData) {
    return this.request('POST', `/loans/${loanId}/payment`, paymentData);
  }

  async getLoanSchedule(loanId) {
    return this.request('GET', `/loans/${loanId}/schedule`);
  }

  // Payment methods
  async getPayments(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request('GET', `/payments?${queryString}`);
  }

  async createPayment(paymentData) {
    return this.request('POST', '/payments', paymentData);
  }

  async getPayment(paymentId) {
    return this.request('GET', `/payments/${paymentId}`);
  }

  async createUpiPayment(paymentData) {
    return this.request('POST', '/payments/upi', paymentData);
  }

  async getUpiAccounts() {
    return this.request('GET', '/payments/upi/accounts');
  }

  async verifyUpiId(upiId) {
    return this.request('GET', `/payments/upi/verify/${upiId}`);
  }

  // Report methods
  async getAccountReports(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request('GET', `/reports/accounts?${queryString}`);
  }

  async getTransactionReports(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request('GET', `/reports/transactions?${queryString}`);
  }

  async getCustomerReports(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request('GET', `/reports/customers?${queryString}`);
  }

  async generateCustomReport(reportData) {
    return this.request('POST', '/reports/custom', reportData);
  }

  // Admin methods
  async getUsers(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request('GET', `/admin/users?${queryString}`);
  }

  async createUser(userData) {
    return this.request('POST', '/admin/users', userData);
  }

  async getSystemStatus() {
    return this.request('GET', '/admin/system/status');
  }

  async getAuditLogs(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request('GET', `/admin/audit-logs?${queryString}`);
  }

  // Health check
  async checkHealth() {
    return this.request('GET', '/health');
  }
}

// Export as both named and default export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = BankingApiClient;
} else {
  window.BankingApiClient = BankingApiClient;
}
