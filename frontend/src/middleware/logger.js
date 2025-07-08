/**
 * Request Logger Middleware
 * Logs all incoming requests with detailed information
 * 
 * @module request-logger
 */

const winston = require('winston');

// Configure Winston logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'cbs-frontend' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/combined.log' }),
  ],
});

// Add console transport for development
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    )
  }));
}

/**
 * Request logging middleware
 */
const requestLogger = (req, res, next) => {
  const start = Date.now();
  const requestId = require('crypto').randomUUID();
  
  // Add request ID to request object
  req.requestId = requestId;
  
  // Log request start
  logger.info('Request started', {
    requestId,
    method: req.method,
    url: req.url,
    userAgent: req.get('User-Agent'),
    ip: req.ip,
    timestamp: new Date().toISOString(),
    sessionId: req.sessionID,
    userId: req.user?.id
  });

  // Capture response details
  const originalSend = res.send;
  res.send = function(data) {
    const duration = Date.now() - start;
    
    logger.info('Request completed', {
      requestId,
      method: req.method,
      url: req.url,
      statusCode: res.statusCode,
      duration: `${duration}ms`,
      responseSize: Buffer.byteLength(data, 'utf8'),
      timestamp: new Date().toISOString(),
      userId: req.user?.id
    });

    originalSend.call(this, data);
  };

  next();
};

/**
 * Error logging middleware
 */
const errorLogger = (err, req, res, next) => {
  logger.error('Request error', {
    requestId: req.requestId,
    error: err.message,
    stack: err.stack,
    method: req.method,
    url: req.url,
    statusCode: res.statusCode,
    timestamp: new Date().toISOString(),
    userId: req.user?.id
  });

  next(err);
};

/**
 * API access logger for specific endpoints
 */
const apiLogger = (req, res, next) => {
  if (req.path.startsWith('/api/')) {
    logger.info('API access', {
      requestId: req.requestId,
      endpoint: req.path,
      method: req.method,
      params: req.params,
      query: req.query,
      body: req.method !== 'GET' ? req.body : undefined,
      timestamp: new Date().toISOString(),
      userId: req.user?.id
    });
  }
  
  next();
};

module.exports = {
  requestLogger,
  errorLogger,
  apiLogger,
  logger
};
