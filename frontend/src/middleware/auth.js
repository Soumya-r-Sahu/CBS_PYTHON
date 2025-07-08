/**
 * Authentication Middleware
 * Handles authentication checks for protected routes
 * 
 * @module auth-middleware
 */

const jwt = require('jsonwebtoken');
const axios = require('axios');

const BACKEND_BASE_URL = process.env.BACKEND_API_URL || 'http://localhost:8000';
const JWT_SECRET = process.env.JWT_SECRET || 'your-jwt-secret';

/**
 * Middleware to check if user is authenticated
 */
const requireAuth = async (req, res, next) => {
  try {
    const token = req.cookies.auth_token || 
                  req.headers.authorization?.replace('Bearer ', '') ||
                  req.headers['x-auth-token'];

    if (!token) {
      return res.status(401).json({
        success: false,
        message: 'Authentication token required',
        code: 'NO_TOKEN'
      });
    }

    // Verify token with backend
    try {
      const response = await axios.get(`${BACKEND_BASE_URL}/api/v1/auth/verify`, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 5000
      });

      req.user = response.data.user;
      req.token = token;
      next();

    } catch (verifyError) {
      // Token verification failed
      res.clearCookie('auth_token');
      req.session.authenticated = false;
      
      return res.status(401).json({
        success: false,
        message: 'Invalid or expired token',
        code: 'INVALID_TOKEN'
      });
    }

  } catch (error) {
    console.error('Auth middleware error:', error.message);
    res.status(500).json({
      success: false,
      message: 'Authentication service error',
      code: 'AUTH_SERVICE_ERROR'
    });
  }
};

/**
 * Middleware to check user roles
 */
const requireRole = (roles) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        message: 'Authentication required',
        code: 'UNAUTHORIZED'
      });
    }

    const userRoles = req.user.roles || [];
    const hasRole = roles.some(role => userRoles.includes(role));

    if (!hasRole) {
      return res.status(403).json({
        success: false,
        message: 'Insufficient permissions',
        code: 'FORBIDDEN',
        required_roles: roles,
        user_roles: userRoles
      });
    }

    next();
  };
};

/**
 * Optional authentication middleware
 * Sets user info if authenticated, but doesn't block unauthenticated requests
 */
const optionalAuth = async (req, res, next) => {
  try {
    const token = req.cookies.auth_token || 
                  req.headers.authorization?.replace('Bearer ', '');

    if (token) {
      try {
        const response = await axios.get(`${BACKEND_BASE_URL}/api/v1/auth/verify`, {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 5000
        });

        req.user = response.data.user;
        req.token = token;
      } catch (error) {
        // Token invalid, but continue without authentication
        console.warn('Optional auth failed:', error.message);
      }
    }

    next();
  } catch (error) {
    console.error('Optional auth middleware error:', error.message);
    next(); // Continue without authentication
  }
};

/**
 * Middleware to add auth header to backend requests
 */
const addAuthHeader = (req, res, next) => {
  const token = req.cookies.auth_token || 
                req.headers.authorization?.replace('Bearer ', '');

  if (token) {
    req.headers.authorization = `Bearer ${token}`;
  }

  next();
};

module.exports = {
  requireAuth,
  requireRole,
  optionalAuth,
  addAuthHeader,
  authMiddleware: requireAuth // alias for backward compatibility
};
