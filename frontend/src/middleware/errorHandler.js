/**
 * Error Handler Middleware
 * Centralized error handling for the frontend server
 * 
 * @module error-handler
 */

const errorHandler = (err, req, res, next) => {
  console.error('Error occurred:', {
    message: err.message,
    stack: err.stack,
    url: req.url,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent'),
    timestamp: new Date().toISOString()
  });

  // Default error response
  let status = 500;
  let message = 'Internal Server Error';
  let code = 'INTERNAL_ERROR';

  // Handle specific error types
  if (err.code === 'ECONNREFUSED') {
    status = 503;
    message = 'Backend service unavailable';
    code = 'SERVICE_UNAVAILABLE';
  } else if (err.code === 'ENOTFOUND') {
    status = 503;
    message = 'Backend service not found';
    code = 'SERVICE_NOT_FOUND';
  } else if (err.code === 'ETIMEDOUT') {
    status = 504;
    message = 'Backend service timeout';
    code = 'SERVICE_TIMEOUT';
  } else if (err.response) {
    // Axios error with response
    status = err.response.status;
    message = err.response.data?.message || err.message;
    code = err.response.data?.code || 'BACKEND_ERROR';
  } else if (err.request) {
    // Network error
    status = 503;
    message = 'Network error - unable to reach backend';
    code = 'NETWORK_ERROR';
  } else if (err.name === 'ValidationError') {
    status = 400;
    message = 'Invalid request data';
    code = 'VALIDATION_ERROR';
  } else if (err.name === 'UnauthorizedError') {
    status = 401;
    message = 'Authentication required';
    code = 'UNAUTHORIZED';
  } else if (err.name === 'ForbiddenError') {
    status = 403;
    message = 'Access denied';
    code = 'FORBIDDEN';
  }

  // Send error response
  res.status(status).json({
    success: false,
    error: {
      message,
      code,
      status,
      timestamp: new Date().toISOString(),
      ...(process.env.NODE_ENV === 'development' && {
        stack: err.stack,
        details: err.response?.data
      })
    }
  });
};

/**
 * 404 Handler
 */
const notFoundHandler = (req, res) => {
  res.status(404).json({
    success: false,
    error: {
      message: 'Resource not found',
      code: 'NOT_FOUND',
      status: 404,
      path: req.path,
      method: req.method,
      timestamp: new Date().toISOString()
    }
  });
};

module.exports = {
  errorHandler,
  notFoundHandler
};
