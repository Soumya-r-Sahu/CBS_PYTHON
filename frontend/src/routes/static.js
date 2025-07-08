/**
 * Static Routes
 * Serves frontend pages and assets
 * 
 * @module static-router
 */

const express = require('express');
const path = require('path');
const router = express.Router();

// Serve the main application
router.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '../../public/index.html'));
});

// Banking dashboard
router.get('/dashboard', (req, res) => {
  res.sendFile(path.join(__dirname, '../../public/dashboard.html'));
});

// Account management
router.get('/accounts', (req, res) => {
  res.sendFile(path.join(__dirname, '../../public/accounts.html'));
});

// Transaction management
router.get('/transactions', (req, res) => {
  res.sendFile(path.join(__dirname, '../../public/transactions.html'));
});

// Customer profile
router.get('/profile', (req, res) => {
  res.sendFile(path.join(__dirname, '../../public/profile.html'));
});

// Card management
router.get('/cards', (req, res) => {
  res.sendFile(path.join(__dirname, '../../public/cards.html'));
});

// Payments
router.get('/payments', (req, res) => {
  res.sendFile(path.join(__dirname, '../../public/payments.html'));
});

// Loans
router.get('/loans', (req, res) => {
  res.sendFile(path.join(__dirname, '../../public/loans.html'));
});

// Reports
router.get('/reports', (req, res) => {
  res.sendFile(path.join(__dirname, '../../public/reports.html'));
});

// Admin panel
router.get('/admin', (req, res) => {
  res.sendFile(path.join(__dirname, '../../public/admin.html'));
});

// Login page
router.get('/login', (req, res) => {
  res.sendFile(path.join(__dirname, '../../public/login.html'));
});

// Error pages
router.get('/404', (req, res) => {
  res.status(404).sendFile(path.join(__dirname, '../../public/404.html'));
});

router.get('/500', (req, res) => {
  res.status(500).sendFile(path.join(__dirname, '../../public/500.html'));
});

// Catch-all for SPA routing
router.get('*', (req, res) => {
  // Check if it's an API call that wasn't handled
  if (req.path.startsWith('/api/')) {
    res.status(404).json({
      error: 'API endpoint not found',
      path: req.path
    });
  } else {
    // Serve the main app for client-side routing
    res.sendFile(path.join(__dirname, '../../public/index.html'));
  }
});

module.exports = router;
