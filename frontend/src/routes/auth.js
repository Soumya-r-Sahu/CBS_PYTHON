/**
 * Authentication Router
 * Handles authentication flows and session management
 * 
 * @module auth-router
 */

const express = require('express');
const jwt = require('jsonwebtoken');
const axios = require('axios');
const router = express.Router();

// Backend authentication service
const BACKEND_BASE_URL = process.env.BACKEND_API_URL || 'http://localhost:8000';
const JWT_SECRET = process.env.JWT_SECRET || 'your-jwt-secret';
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '24h';

// Create axios instance for authentication
const authApi = axios.create({
  baseURL: BACKEND_BASE_URL,
  timeout: 10000
});

/**
 * Login endpoint
 * Authenticates user and establishes session
 */
router.post('/login', async (req, res) => {
  try {
    const { username, password, deviceId } = req.body;

    // Forward login request to backend
    const response = await authApi.post('/api/v1/auth/login', {
      username,
      password,
      device_id: deviceId
    });

    const { token, user, refresh_token } = response.data;

    // Set secure cookies
    res.cookie('auth_token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 24 * 60 * 60 * 1000 // 24 hours
    });

    if (refresh_token) {
      res.cookie('refresh_token', refresh_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'strict',
        maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days
      });
    }

    // Store user in session
    req.session.user = user;
    req.session.authenticated = true;

    res.json({
      success: true,
      user: {
        id: user.id,
        username: user.username,
        name: user.name,
        email: user.email,
        roles: user.roles
      },
      message: 'Login successful'
    });

  } catch (error) {
    console.error('Login error:', error.message);
    
    const status = error.response?.status || 500;
    const message = error.response?.data?.message || 'Login failed';
    
    res.status(status).json({
      success: false,
      message,
      error: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
});

/**
 * Logout endpoint
 * Invalidates session and tokens
 */
router.post('/logout', async (req, res) => {
  try {
    const token = req.cookies.auth_token || req.headers.authorization?.replace('Bearer ', '');

    if (token) {
      // Notify backend of logout
      try {
        await authApi.post('/api/v1/auth/logout', {}, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } catch (error) {
        console.warn('Backend logout notification failed:', error.message);
      }
    }

    // Clear cookies
    res.clearCookie('auth_token');
    res.clearCookie('refresh_token');

    // Destroy session
    req.session.destroy((err) => {
      if (err) {
        console.error('Session destruction error:', err);
      }
    });

    res.json({
      success: true,
      message: 'Logout successful'
    });

  } catch (error) {
    console.error('Logout error:', error.message);
    res.status(500).json({
      success: false,
      message: 'Logout failed'
    });
  }
});

/**
 * Token refresh endpoint
 */
router.post('/refresh', async (req, res) => {
  try {
    const refreshToken = req.cookies.refresh_token || req.body.refresh_token;

    if (!refreshToken) {
      return res.status(401).json({
        success: false,
        message: 'Refresh token not provided'
      });
    }

    // Request new token from backend
    const response = await authApi.post('/api/v1/auth/refresh', {
      refresh_token: refreshToken
    });

    const { token, user } = response.data;

    // Set new token cookie
    res.cookie('auth_token', token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'strict',
      maxAge: 24 * 60 * 60 * 1000 // 24 hours
    });

    // Update session
    req.session.user = user;

    res.json({
      success: true,
      user: {
        id: user.id,
        username: user.username,
        name: user.name,
        email: user.email,
        roles: user.roles
      }
    });

  } catch (error) {
    console.error('Token refresh error:', error.message);
    
    // Clear invalid refresh token
    res.clearCookie('refresh_token');
    
    res.status(401).json({
      success: false,
      message: 'Token refresh failed'
    });
  }
});

/**
 * Get current user info
 */
router.get('/me', async (req, res) => {
  try {
    const token = req.cookies.auth_token || req.headers.authorization?.replace('Bearer ', '');

    if (!token) {
      return res.status(401).json({
        success: false,
        message: 'No authentication token provided'
      });
    }

    // Verify token with backend
    const response = await authApi.get('/api/v1/auth/me', {
      headers: { Authorization: `Bearer ${token}` }
    });

    const user = response.data.user;

    // Update session
    req.session.user = user;
    req.session.authenticated = true;

    res.json({
      success: true,
      user: {
        id: user.id,
        username: user.username,
        name: user.name,
        email: user.email,
        roles: user.roles
      }
    });

  } catch (error) {
    console.error('User info error:', error.message);
    
    // Clear invalid token
    res.clearCookie('auth_token');
    req.session.authenticated = false;
    
    res.status(401).json({
      success: false,
      message: 'Authentication verification failed'
    });
  }
});

/**
 * Change password endpoint
 */
router.post('/change-password', async (req, res) => {
  try {
    const token = req.cookies.auth_token || req.headers.authorization?.replace('Bearer ', '');
    const { currentPassword, newPassword } = req.body;

    if (!token) {
      return res.status(401).json({
        success: false,
        message: 'Authentication required'
      });
    }

    // Forward request to backend
    await authApi.post('/api/v1/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    }, {
      headers: { Authorization: `Bearer ${token}` }
    });

    res.json({
      success: true,
      message: 'Password changed successfully'
    });

  } catch (error) {
    console.error('Password change error:', error.message);
    
    const status = error.response?.status || 500;
    const message = error.response?.data?.message || 'Password change failed';
    
    res.status(status).json({
      success: false,
      message
    });
  }
});

/**
 * Session status check
 */
router.get('/status', (req, res) => {
  res.json({
    authenticated: !!req.session.authenticated,
    user: req.session.user || null,
    session_id: req.sessionID
  });
});

module.exports = router;
