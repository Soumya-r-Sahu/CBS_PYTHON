/**
 * Authentication JavaScript
 * Handles login, logout, and authentication state
 */

class AuthManager {
  constructor() {
    this.isAuthenticated = false;
    this.user = null;
    this.checkAuthStatus();
  }

  async checkAuthStatus() {
    try {
      const response = await fetch('/auth/status', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        this.isAuthenticated = data.authenticated;
        this.user = data.user;
        
        if (this.isAuthenticated && this.user) {
          this.updateUserDisplay();
        } else if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
    } catch (error) {
      console.error('Auth status check failed:', error);
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
  }

  async login(username, password, deviceId = null) {
    try {
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          username,
          password,
          deviceId: deviceId || this.generateDeviceId()
        })
      });

      const data = await response.json();

      if (data.success) {
        this.isAuthenticated = true;
        this.user = data.user;
        return { success: true, user: data.user };
      } else {
        throw new Error(data.message || 'Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async logout() {
    try {
      const response = await fetch('/auth/logout', {
        method: 'POST',
        credentials: 'include'
      });

      if (response.ok) {
        this.isAuthenticated = false;
        this.user = null;
        window.location.href = '/login';
      } else {
        throw new Error('Logout failed');
      }
    } catch (error) {
      console.error('Logout error:', error);
      // Force logout even if request fails
      this.isAuthenticated = false;
      this.user = null;
      window.location.href = '/login';
    }
  }

  async refreshToken() {
    try {
      const response = await fetch('/auth/refresh', {
        method: 'POST',
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        this.user = data.user;
        return true;
      }
      return false;
    } catch (error) {
      console.error('Token refresh failed:', error);
      return false;
    }
  }

  generateDeviceId() {
    // Generate a unique device ID based on browser characteristics
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Device fingerprint', 2, 2);
    
    const fingerprint = [
      navigator.userAgent,
      navigator.language,
      screen.width + 'x' + screen.height,
      new Date().getTimezoneOffset(),
      canvas.toDataURL()
    ].join('|');
    
    // Simple hash function
    let hash = 0;
    for (let i = 0; i < fingerprint.length; i++) {
      const char = fingerprint.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    
    return 'device_' + Math.abs(hash).toString(36);
  }

  updateUserDisplay() {
    const userNameElement = document.getElementById('user-name');
    if (userNameElement && this.user) {
      userNameElement.textContent = this.user.name || this.user.username;
    }
  }

  requireAuth() {
    if (!this.isAuthenticated) {
      window.location.href = '/login';
      return false;
    }
    return true;
  }

  hasRole(role) {
    return this.user && this.user.roles && this.user.roles.includes(role);
  }

  hasAnyRole(roles) {
    return this.user && this.user.roles && roles.some(role => this.user.roles.includes(role));
  }
}

// Global auth manager instance
window.authManager = new AuthManager();

// Handle logout button clicks
document.addEventListener('DOMContentLoaded', () => {
  const logoutBtn = document.getElementById('logout-btn');
  if (logoutBtn) {
    logoutBtn.addEventListener('click', (e) => {
      e.preventDefault();
      authManager.logout();
    });
  }
});

// Auto-refresh token every 30 minutes
setInterval(() => {
  if (authManager.isAuthenticated) {
    authManager.refreshToken().catch(() => {
      console.warn('Token refresh failed, redirecting to login');
      window.location.href = '/login';
    });
  }
}, 30 * 60 * 1000);

// Handle page visibility change to refresh auth status
document.addEventListener('visibilitychange', () => {
  if (!document.hidden && authManager.isAuthenticated) {
    authManager.checkAuthStatus();
  }
});
