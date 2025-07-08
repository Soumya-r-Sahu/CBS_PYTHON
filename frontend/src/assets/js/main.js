/**
 * Main JavaScript functionality
 * Common utilities and helper functions
 */

// Global utilities
window.CBSUtils = {
  // Format currency
  formatCurrency: (amount, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  },

  // Format date
  formatDate: (date, options = {}) => {
    const defaultOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    };
    return new Date(date).toLocaleDateString('en-US', { ...defaultOptions, ...options });
  },

  // Format datetime
  formatDateTime: (date) => {
    return new Date(date).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  },

  // Show loading overlay
  showLoading: (message = 'Loading...') => {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
      overlay.querySelector('p').textContent = message;
      overlay.classList.remove('hidden');
    }
  },

  // Hide loading overlay
  hideLoading: () => {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
      overlay.classList.add('hidden');
    }
  },

  // Show notification
  showNotification: (message, type = 'info') => {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
      <span>${message}</span>
      <button onclick="this.parentElement.remove()">&times;</button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (notification.parentElement) {
        notification.remove();
      }
    }, 5000);
  },

  // Debounce function
  debounce: (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  // Copy to clipboard
  copyToClipboard: async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      CBSUtils.showNotification('Copied to clipboard', 'success');
    } catch (err) {
      console.error('Failed to copy:', err);
      CBSUtils.showNotification('Failed to copy to clipboard', 'error');
    }
  },

  // Validate form
  validateForm: (form) => {
    const errors = [];
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    inputs.forEach(input => {
      if (!input.value.trim()) {
        errors.push(`${input.name || input.id} is required`);
        input.classList.add('error');
      } else {
        input.classList.remove('error');
      }
      
      // Email validation
      if (input.type === 'email' && input.value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(input.value)) {
          errors.push('Please enter a valid email address');
          input.classList.add('error');
        }
      }
      
      // Phone validation
      if (input.type === 'tel' && input.value) {
        const phoneRegex = /^\+?[\d\s\-\(\)]+$/;
        if (!phoneRegex.test(input.value)) {
          errors.push('Please enter a valid phone number');
          input.classList.add('error');
        }
      }
    });
    
    return errors;
  }
};

// Initialize Banking API Client
window.bankingApi = new BankingApiClient({
  baseUrl: '/api',
  onUnauthorized: () => {
    window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
  }
});

// Global error handler
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
  CBSUtils.showNotification('An unexpected error occurred', 'error');
});

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  CBSUtils.showNotification('A network error occurred', 'error');
});

// Common DOM helpers
document.addEventListener('DOMContentLoaded', () => {
  // Add active nav link styling
  const currentPath = window.location.pathname;
  const navLinks = document.querySelectorAll('.nav-link');
  
  navLinks.forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // Handle form submissions with loading states
  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', (e) => {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn && !submitBtn.hasAttribute('data-no-loading')) {
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Loading...';
        submitBtn.disabled = true;
        
        // Re-enable after 10 seconds max (safety net)
        setTimeout(() => {
          submitBtn.textContent = originalText;
          submitBtn.disabled = false;
        }, 10000);
      }
    });
  });

  // Handle table row clicks for navigation
  const tableRows = document.querySelectorAll('table tr[data-href]');
  tableRows.forEach(row => {
    row.style.cursor = 'pointer';
    row.addEventListener('click', () => {
      window.location.href = row.getAttribute('data-href');
    });
  });

  // Auto-resize textareas
  const textareas = document.querySelectorAll('textarea[data-auto-resize]');
  textareas.forEach(textarea => {
    textarea.addEventListener('input', () => {
      textarea.style.height = 'auto';
      textarea.style.height = textarea.scrollHeight + 'px';
    });
  });

  // Initialize tooltips (simple implementation)
  const tooltips = document.querySelectorAll('[data-tooltip]');
  tooltips.forEach(element => {
    element.addEventListener('mouseenter', (e) => {
      const tooltip = document.createElement('div');
      tooltip.className = 'tooltip';
      tooltip.textContent = element.getAttribute('data-tooltip');
      document.body.appendChild(tooltip);
      
      const rect = element.getBoundingClientRect();
      tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
      tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
    });
    
    element.addEventListener('mouseleave', () => {
      const tooltip = document.querySelector('.tooltip');
      if (tooltip) tooltip.remove();
    });
  });
});

// Add CSS for notifications and tooltips
const style = document.createElement('style');
style.textContent = `
  .notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 1rem 1.5rem;
    border-radius: 8px;
    color: white;
    font-weight: 500;
    z-index: 10000;
    display: flex;
    align-items: center;
    gap: 1rem;
    max-width: 400px;
    word-wrap: break-word;
  }
  
  .notification-info { background-color: #3b82f6; }
  .notification-success { background-color: #10b981; }
  .notification-warning { background-color: #f59e0b; }
  .notification-error { background-color: #ef4444; }
  
  .notification button {
    background: none;
    border: none;
    color: white;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .tooltip {
    position: absolute;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
    white-space: nowrap;
    z-index: 10001;
    pointer-events: none;
  }
  
  .input.error, input.error {
    border-color: #ef4444 !important;
    box-shadow: 0 0 0 3px rgb(239 68 68 / 0.1) !important;
  }
`;
document.head.appendChild(style);
