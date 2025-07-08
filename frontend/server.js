/**
 * Core Banking System Frontend Server
 * Express.js Application with API Router for Backend Communication
 * 
 * @version 2.0.0
 * @description Serves frontend assets and provides API routing to backend services
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const morgan = require('morgan');
const path = require('path');
const dotenv = require('dotenv');
const cookieParser = require('cookie-parser');
const session = require('express-session');
const RedisStore = require('connect-redis')(session);
const redis = require('redis');

// Load environment variables
dotenv.config();

// Import routes
const apiRouter = require('./src/routes/api');
const authRouter = require('./src/routes/auth');
const staticRouter = require('./src/routes/static');

// Import middleware
const { errorHandler } = require('./src/middleware/errorHandler');
const { authMiddleware } = require('./src/middleware/auth');
const { requestLogger } = require('./src/middleware/logger');

const app = express();
const PORT = process.env.FRONTEND_PORT || 3000;

// Security middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
      fontSrc: ["'self'", "https://fonts.gstatic.com"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'", process.env.BACKEND_API_URL || "http://localhost:8000"]
    }
  }
}));

// Compression middleware
app.use(compression());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 1000, // limit each IP to 1000 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});
app.use(limiter);

// CORS configuration
app.use(cors({
  origin: [
    'http://localhost:3000',
    'http://localhost:3001',
    'http://localhost:8000',
    process.env.FRONTEND_URL,
    process.env.BACKEND_API_URL
  ].filter(Boolean),
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(cookieParser());

// Request logging
app.use(morgan('combined'));
app.use(requestLogger);

// Session configuration
if (process.env.REDIS_URL) {
  const redisClient = redis.createClient({
    url: process.env.REDIS_URL
  });
  
  app.use(session({
    store: new RedisStore({ client: redisClient }),
    secret: process.env.SESSION_SECRET || 'your-secret-key',
    resave: false,
    saveUninitialized: false,
    cookie: {
      secure: process.env.NODE_ENV === 'production',
      httpOnly: true,
      maxAge: 24 * 60 * 60 * 1000 // 24 hours
    }
  }));
} else {
  app.use(session({
    secret: process.env.SESSION_SECRET || 'your-secret-key',
    resave: false,
    saveUninitialized: false,
    cookie: {
      secure: process.env.NODE_ENV === 'production',
      httpOnly: true,
      maxAge: 24 * 60 * 60 * 1000 // 24 hours
    }
  }));
}

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));
app.use('/assets', express.static(path.join(__dirname, 'src/assets')));

// API Routes
app.use('/api', apiRouter);
app.use('/auth', authRouter);
app.use('/', staticRouter);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'cbs-frontend',
    version: '2.0.0',
    timestamp: new Date().toISOString(),
    backend_url: process.env.BACKEND_API_URL
  });
});

// Error handling middleware
app.use(errorHandler);

// Start server
const server = app.listen(PORT, () => {
  console.log(`🚀 CBS Frontend Server running on port ${PORT}`);
  console.log(`📡 Backend API URL: ${process.env.BACKEND_API_URL || 'http://localhost:8000'}`);
  console.log(`🌍 Environment: ${process.env.NODE_ENV || 'development'}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  server.close(() => {
    console.log('Process terminated');
  });
});

module.exports = app;
