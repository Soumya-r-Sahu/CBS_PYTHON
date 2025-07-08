/**
 * Login Page JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('login-form');
  const errorMessage = document.getElementById('error-message');
  const successMessage = document.getElementById('success-message');

  // Check if already authenticated
  if (window.authManager && window.authManager.isAuthenticated) {
    window.location.href = '/dashboard';
    return;
  }

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    const deviceId = document.getElementById('device-id').value.trim();
    const rememberMe = document.getElementById('remember-me').checked;

    // Validate inputs
    if (!username || !password) {
      showError('Please enter both username and password');
      return;
    }

    // Show loading state
    const submitBtn = loginForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Logging in...';
    submitBtn.disabled = true;

    hideMessages();

    try {
      // Use the global auth manager
      const result = await window.authManager.login(username, password, deviceId || null);
      
      if (result.success) {
        showSuccess('Login successful! Redirecting...');
        
        // Redirect after a short delay
        setTimeout(() => {
          const redirectUrl = new URLSearchParams(window.location.search).get('redirect') || '/dashboard';
          window.location.href = redirectUrl;
        }, 1000);
      }
    } catch (error) {
      showError(error.message || 'Login failed. Please try again.');
    } finally {
      // Reset button state
      submitBtn.textContent = originalText;
      submitBtn.disabled = false;
    }
  });

  // Auto-generate device ID if field is empty
  const deviceIdInput = document.getElementById('device-id');
  if (!deviceIdInput.value) {
    deviceIdInput.placeholder = 'Auto-generated: ' + generateSimpleDeviceId();
  }

  function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
    successMessage.classList.add('hidden');
  }

  function showSuccess(message) {
    successMessage.textContent = message;
    successMessage.classList.remove('hidden');
    errorMessage.classList.add('hidden');
  }

  function hideMessages() {
    errorMessage.classList.add('hidden');
    successMessage.classList.add('hidden');
  }

  function generateSimpleDeviceId() {
    return 'device_' + Math.random().toString(36).substr(2, 9);
  }

  // Handle "Remember Me" functionality
  const rememberMeCheckbox = document.getElementById('remember-me');
  const usernameInput = document.getElementById('username');

  // Load saved username if "Remember Me" was previously checked
  const savedUsername = localStorage.getItem('cbs_saved_username');
  if (savedUsername) {
    usernameInput.value = savedUsername;
    rememberMeCheckbox.checked = true;
  }

  // Save/clear username based on "Remember Me" state
  rememberMeCheckbox.addEventListener('change', () => {
    if (rememberMeCheckbox.checked) {
      localStorage.setItem('cbs_saved_username', usernameInput.value);
    } else {
      localStorage.removeItem('cbs_saved_username');
    }
  });

  // Update saved username when it changes
  usernameInput.addEventListener('input', () => {
    if (rememberMeCheckbox.checked) {
      localStorage.setItem('cbs_saved_username', usernameInput.value);
    }
  });

  // Handle Enter key in password field
  document.getElementById('password').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      loginForm.dispatchEvent(new Event('submit'));
    }
  });

  // Focus on username field when page loads
  usernameInput.focus();
});
