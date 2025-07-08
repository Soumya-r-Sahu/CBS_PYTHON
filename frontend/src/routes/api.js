/**
 * API Router - Central routing to backend services
 * All API calls from frontend components go through this router
 * 
 * @module api-router
 */

const express = require('express');
const axios = require('axios');
const router = express.Router();

// Backend service configuration
const BACKEND_BASE_URL = process.env.BACKEND_API_URL || 'http://localhost:8000';
const API_TIMEOUT = parseInt(process.env.API_TIMEOUT) || 30000;

// Create axios instance for backend communication
const backendApi = axios.create({
  baseURL: BACKEND_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor to add authentication
backendApi.interceptors.request.use((config) => {
  // Forward Authorization header from frontend request
  if (config.headers.authorization) {
    config.headers.Authorization = config.headers.authorization;
  }
  
  // Add correlation ID for tracing
  config.headers['X-Correlation-ID'] = require('crypto').randomUUID();
  
  return config;
});

// Response interceptor for error handling
backendApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Backend API Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      message: error.message
    });
    return Promise.reject(error);
  }
);

/**
 * Generic proxy middleware for backend API calls
 */
const proxyToBackend = async (req, res, next) => {
  try {
    const { method, url, body, headers } = req;
    
    // Forward relevant headers
    const forwardHeaders = {
      'Authorization': headers.authorization,
      'Content-Type': headers['content-type'],
      'X-User-Agent': headers['user-agent'],
      'X-Real-IP': req.ip,
      'X-Forwarded-For': req.get('X-Forwarded-For')
    };

    // Remove undefined headers
    Object.keys(forwardHeaders).forEach(key => {
      if (!forwardHeaders[key]) delete forwardHeaders[key];
    });

    const response = await backendApi({
      method: method.toLowerCase(),
      url: url.replace('/api', ''), // Remove /api prefix
      data: body,
      headers: forwardHeaders
    });

    // Forward response headers
    const responseHeaders = response.headers;
    if (responseHeaders['content-type']) {
      res.set('Content-Type', responseHeaders['content-type']);
    }
    if (responseHeaders['cache-control']) {
      res.set('Cache-Control', responseHeaders['cache-control']);
    }

    res.status(response.status).json(response.data);
  } catch (error) {
    next(error);
  }
};

// Account Management Routes
router.get('/accounts', proxyToBackend);
router.get('/accounts/:accountId', proxyToBackend);
router.get('/accounts/:accountId/balance', proxyToBackend);
router.get('/accounts/:accountId/transactions', proxyToBackend);
router.post('/accounts', proxyToBackend);
router.put('/accounts/:accountId', proxyToBackend);
router.delete('/accounts/:accountId', proxyToBackend);

// Transaction Routes
router.get('/transactions', proxyToBackend);
router.get('/transactions/:transactionId', proxyToBackend);
router.post('/transactions/transfer', proxyToBackend);
router.post('/transactions/deposit', proxyToBackend);
router.post('/transactions/withdrawal', proxyToBackend);
router.get('/transactions/:transactionId/status', proxyToBackend);

// Customer Management Routes
router.get('/customers', proxyToBackend);
router.get('/customers/:customerId', proxyToBackend);
router.get('/customers/profile', proxyToBackend);
router.post('/customers', proxyToBackend);
router.put('/customers/:customerId', proxyToBackend);
router.put('/customers/profile', proxyToBackend);
router.delete('/customers/:customerId', proxyToBackend);

// Card Management Routes
router.get('/cards', proxyToBackend);
router.get('/cards/:cardId', proxyToBackend);
router.post('/cards', proxyToBackend);
router.put('/cards/:cardId', proxyToBackend);
router.put('/cards/:cardId/status', proxyToBackend);
router.delete('/cards/:cardId', proxyToBackend);

// Loan Management Routes
router.get('/loans', proxyToBackend);
router.get('/loans/:loanId', proxyToBackend);
router.post('/loans', proxyToBackend);
router.put('/loans/:loanId', proxyToBackend);
router.post('/loans/:loanId/payment', proxyToBackend);
router.get('/loans/:loanId/schedule', proxyToBackend);

// Payment Routes
router.get('/payments', proxyToBackend);
router.post('/payments', proxyToBackend);
router.get('/payments/:paymentId', proxyToBackend);
router.post('/payments/upi', proxyToBackend);
router.get('/payments/upi/accounts', proxyToBackend);
router.get('/payments/upi/verify/:upiId', proxyToBackend);

// Reports Routes
router.get('/reports/accounts', proxyToBackend);
router.get('/reports/transactions', proxyToBackend);
router.get('/reports/customers', proxyToBackend);
router.post('/reports/custom', proxyToBackend);

// Admin Routes
router.get('/admin/users', proxyToBackend);
router.post('/admin/users', proxyToBackend);
router.get('/admin/system/status', proxyToBackend);
router.get('/admin/audit-logs', proxyToBackend);

// Risk & Compliance Routes
router.get('/risk/assessments', proxyToBackend);
router.post('/risk/assessments', proxyToBackend);
router.get('/compliance/reports', proxyToBackend);

// Treasury Routes
router.get('/treasury/positions', proxyToBackend);
router.post('/treasury/trades', proxyToBackend);

// Health check for backend connectivity
router.get('/health', async (req, res) => {
  try {
    const response = await backendApi.get('/health');
    res.json({
      frontend: 'healthy',
      backend: response.data,
      connectivity: 'ok',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(503).json({
      frontend: 'healthy',
      backend: 'unreachable',
      connectivity: 'error',
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Catch-all route for unmatched API endpoints
router.all('*', (req, res) => {
  res.status(404).json({
    error: 'API endpoint not found',
    path: req.path,
    method: req.method,
    timestamp: new Date().toISOString()
  });
});

module.exports = router;
