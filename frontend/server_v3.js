/**
 * Core Banking System V3.0 - Frontend Server
 * 
 * Express.js server that serves the frontend and proxies API requests to the backend gateway.
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const axios = require('axios');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;
const API_GATEWAY_URL = process.env.API_GATEWAY_URL || 'http://localhost:8000';

// Security middleware
app.use(helmet({
    contentSecurityPolicy: {
        directives: {
            defaultSrc: ["'self'"],
            styleSrc: ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com"],
            scriptSrc: ["'self'", "'unsafe-inline'", "https://cdnjs.cloudflare.com"],
            imgSrc: ["'self'", "data:", "https:"],
            connectSrc: ["'self'", API_GATEWAY_URL],
        },
    },
}));

// CORS configuration
app.use(cors({
    origin: process.env.FRONTEND_URL || 'http://localhost:3000',
    credentials: true
}));

// Compression and parsing
app.use(compression());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // Limit each IP to 100 requests per windowMs
    message: 'Too many requests from this IP, please try again later.'
});
app.use('/api', limiter);

// Static file serving
app.use(express.static(path.join(__dirname, 'public')));
app.use('/assets', express.static(path.join(__dirname, 'src/assets')));

// API proxy middleware
app.use('/api', async (req, res) => {
    try {
        const config = {
            method: req.method,
            url: `${API_GATEWAY_URL}${req.url}`,
            headers: {
                ...req.headers,
                host: undefined, // Remove host header
            },
            timeout: 30000,
        };

        // Add request body for POST/PUT/PATCH requests
        if (['POST', 'PUT', 'PATCH'].includes(req.method)) {
            config.data = req.body;
        }

        const response = await axios(config);
        
        // Copy response headers
        Object.keys(response.headers).forEach(key => {
            if (key !== 'content-encoding' && key !== 'transfer-encoding') {
                res.set(key, response.headers[key]);
            }
        });

        res.status(response.status).json(response.data);
    } catch (error) {
        console.error('API Proxy Error:', error.message);
        
        if (error.response) {
            // Backend returned an error response
            res.status(error.response.status).json(error.response.data);
        } else if (error.code === 'ECONNREFUSED') {
            // Backend is not available
            res.status(503).json({
                error: 'Service Unavailable',
                message: 'Backend service is not available'
            });
        } else {
            // Other errors
            res.status(500).json({
                error: 'Internal Server Error',
                message: 'An unexpected error occurred'
            });
        }
    }
});

// Health check endpoint
app.get('/health', async (req, res) => {
    try {
        const backendHealth = await axios.get(`${API_GATEWAY_URL}/health`, { timeout: 5000 });
        res.json({
            status: 'healthy',
            frontend: 'running',
            backend: backendHealth.data,
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        res.status(503).json({
            status: 'degraded',
            frontend: 'running',
            backend: 'unavailable',
            error: error.message,
            timestamp: new Date().toISOString()
        });
    }
});

// Serve React app for all other routes
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('Server Error:', error);
    res.status(500).json({
        error: 'Internal Server Error',
        message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong'
    });
});

// Start server
const server = app.listen(PORT, () => {
    console.log(`🌐 Core Banking Frontend Server running on port ${PORT}`);
    console.log(`📊 Frontend URL: http://localhost:${PORT}`);
    console.log(`🔗 API Gateway URL: ${API_GATEWAY_URL}`);
    console.log(`🏥 Health Check: http://localhost:${PORT}/health`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM received, shutting down gracefully');
    server.close(() => {
        console.log('Frontend server closed');
        process.exit(0);
    });
});

module.exports = app;
