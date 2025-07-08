/**
 * Dashboard JavaScript
 * Handles dashboard data loading and display
 */

document.addEventListener('DOMContentLoaded', async () => {
  // Ensure user is authenticated
  if (!window.authManager.requireAuth()) {
    return;
  }

  try {
    await loadDashboardData();
  } catch (error) {
    console.error('Failed to load dashboard data:', error);
    CBSUtils.showNotification('Failed to load dashboard data', 'error');
  }
});

async function loadDashboardData() {
  CBSUtils.showLoading('Loading dashboard...');

  try {
    // Load data in parallel
    const [accounts, transactions] = await Promise.all([
      loadAccounts(),
      loadRecentTransactions()
    ]);

    // Display data
    displayAccounts(accounts);
    displayRecentTransactions(transactions);
    
  } catch (error) {
    console.error('Dashboard data loading error:', error);
    throw error;
  } finally {
    CBSUtils.hideLoading();
  }
}

async function loadAccounts() {
  try {
    const response = await window.bankingApi.getAccounts();
    return response.accounts || response || [];
  } catch (error) {
    console.error('Failed to load accounts:', error);
    return [];
  }
}

async function loadRecentTransactions() {
  try {
    const response = await window.bankingApi.getTransactions({
      limit: 10,
      sort: 'date',
      order: 'desc'
    });
    return response.transactions || response || [];
  } catch (error) {
    console.error('Failed to load transactions:', error);
    return [];
  }
}

function displayAccounts(accounts) {
  const container = document.getElementById('accounts-container');
  
  if (!accounts || accounts.length === 0) {
    container.innerHTML = `
      <div class="card">
        <div class="card-body text-center">
          <p>No accounts found.</p>
          <a href="/accounts" class="btn btn-primary">Manage Accounts</a>
        </div>
      </div>
    `;
    return;
  }

  const accountsHtml = accounts.map(account => `
    <div class="account-card">
      <div class="account-header">
        <span class="account-number">${account.account_number || account.accountNumber}</span>
        <span class="account-type">${account.account_type || account.accountType || 'Savings'}</span>
      </div>
      <div class="account-balance">${CBSUtils.formatCurrency(account.balance || 0, account.currency || 'USD')}</div>
      <div class="account-currency">${account.currency || 'USD'}</div>
      <div class="account-actions">
        <button class="btn btn-primary" onclick="viewAccountDetails('${account.id || account.account_id}')">
          View Details
        </button>
        <button class="btn btn-outline" onclick="viewAccountTransactions('${account.id || account.account_id}')">
          Transactions
        </button>
      </div>
    </div>
  `).join('');

  container.innerHTML = accountsHtml;
}

function displayRecentTransactions(transactions) {
  const container = document.getElementById('transactions-container');
  
  if (!transactions || transactions.length === 0) {
    container.innerHTML = `
      <div class="card">
        <div class="card-body text-center">
          <p>No recent transactions found.</p>
          <a href="/transactions" class="btn btn-primary">View All Transactions</a>
        </div>
      </div>
    `;
    return;
  }

  const transactionsHtml = transactions.map(transaction => {
    const isPositive = transaction.amount > 0 || transaction.type === 'credit' || transaction.type === 'deposit';
    const amountClass = isPositive ? 'positive' : 'negative';
    const amountSymbol = isPositive ? '+' : '';
    
    return `
      <div class="transaction-item">
        <div class="transaction-info">
          <h4>${transaction.description || transaction.type || 'Transaction'}</h4>
          <p>${transaction.reference || transaction.transaction_id || ''}</p>
        </div>
        <div class="transaction-amount">
          <div class="amount ${amountClass}">
            ${amountSymbol}${CBSUtils.formatCurrency(Math.abs(transaction.amount || 0), transaction.currency || 'USD')}
          </div>
          <div class="date">${CBSUtils.formatDate(transaction.date || transaction.created_at)}</div>
        </div>
      </div>
    `;
  }).join('');

  container.innerHTML = transactionsHtml;
}

// Dashboard action functions
window.viewAccountDetails = (accountId) => {
  window.location.href = `/accounts?id=${accountId}`;
};

window.viewAccountTransactions = (accountId) => {
  window.location.href = `/transactions?account=${accountId}`;
};

window.refreshDashboard = async () => {
  try {
    await loadDashboardData();
    CBSUtils.showNotification('Dashboard refreshed', 'success');
  } catch (error) {
    CBSUtils.showNotification('Failed to refresh dashboard', 'error');
  }
};

// Auto-refresh dashboard every 5 minutes
setInterval(() => {
  if (document.visibilityState === 'visible' && window.authManager.isAuthenticated) {
    refreshDashboard();
  }
}, 5 * 60 * 1000);

// Refresh when page becomes visible
document.addEventListener('visibilitychange', () => {
  if (!document.hidden && window.authManager.isAuthenticated) {
    loadDashboardData().catch(console.error);
  }
});
