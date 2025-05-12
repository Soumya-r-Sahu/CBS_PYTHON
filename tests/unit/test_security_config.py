"""
Unit tests for security module - Configuration
"""

import unittest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add project root to path to be able to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from security.config import (
    get_config_value,
    JWT_CONFIG,
    PASSWORD_POLICY,
    ENCRYPTION_CONFIG,
    MFA_CONFIG,
    RATE_LIMIT_CONFIG,
    SECURITY_HEADERS,
    CERTIFICATE_CONFIG,
    AUDIT_LOG_CONFIG,
    SECURITY_MONITORING,
    SESSION_CONFIG,
    CORS_CONFIG,
    ENVIRONMENT
)


class TestSecurityConfig(unittest.TestCase):
    """Test cases for Security Configuration functionality"""
    
    def test_config_structures(self):
        """Test that all configuration structures are present and have expected keys"""
        # JWT configuration
        self.assertIn("secret_key", JWT_CONFIG)
        self.assertIn("algorithm", JWT_CONFIG)
        self.assertIn("access_token_expire_minutes", JWT_CONFIG)
        
        # Password policy
        self.assertIn("min_length", PASSWORD_POLICY)
        self.assertIn("min_uppercase", PASSWORD_POLICY)
        self.assertIn("min_lowercase", PASSWORD_POLICY)
        self.assertIn("min_digits", PASSWORD_POLICY)
        self.assertIn("min_special", PASSWORD_POLICY)
        
        # Encryption configuration
        self.assertIn("algorithm", ENCRYPTION_CONFIG)
        self.assertIn("key_derivation", ENCRYPTION_CONFIG)
        
        # MFA configuration
        self.assertIn("enabled", MFA_CONFIG)
        self.assertIn("totp_issuer", MFA_CONFIG)
        self.assertIn("totp_digits", MFA_CONFIG)
        
        # Rate limiting
        self.assertIn("default_limits", RATE_LIMIT_CONFIG)
        self.assertIn("login_limits", RATE_LIMIT_CONFIG)
        
        # Security headers
        self.assertIn("Strict-Transport-Security", SECURITY_HEADERS)
        self.assertIn("X-Content-Type-Options", SECURITY_HEADERS)
        self.assertIn("X-Frame-Options", SECURITY_HEADERS)
        
        # Certificate configuration
        self.assertIn("cert_dir", CERTIFICATE_CONFIG)
        self.assertIn("key_size", CERTIFICATE_CONFIG)
        
        # Audit logging
        self.assertIn("log_file_path", AUDIT_LOG_CONFIG)
        self.assertIn("sensitive_actions", AUDIT_LOG_CONFIG)
        
        # Security monitoring
        self.assertIn("anomaly_detection_enabled", SECURITY_MONITORING)
        self.assertIn("alert_threshold", SECURITY_MONITORING)
        
        # Session configuration
        self.assertIn("cookie_secure", SESSION_CONFIG)
        self.assertIn("session_timeout_minutes", SESSION_CONFIG)
        
        # CORS configuration
        self.assertIn("allowed_origins", CORS_CONFIG)
        self.assertIn("allowed_methods", CORS_CONFIG)
    
    def test_get_config_value(self):
        """Test getting configuration values"""
        # Get existing values
        jwt_secret = get_config_value("JWT_CONFIG", "secret_key")
        self.assertEqual(jwt_secret, JWT_CONFIG["secret_key"])
        
        min_length = get_config_value("PASSWORD_POLICY", "min_length")
        self.assertEqual(min_length, PASSWORD_POLICY["min_length"])
        
        # Non-existent config should raise KeyError
        with self.assertRaises(KeyError):
            get_config_value("NONEXISTENT_CONFIG", "key")
        
        # Non-existent key should raise KeyError
        with self.assertRaises(KeyError):
            get_config_value("JWT_CONFIG", "nonexistent_key")
    
    @patch.dict(os.environ, {"CBS_ENVIRONMENT": "production"})
    def test_production_environment_settings(self):
        """Test configuration in production environment"""
        # In a real test, we would need to reload the config module
        # This is a simplified test that demonstrates the concept
        self.assertGreaterEqual(PASSWORD_POLICY["min_length"], 10)
        self.assertTrue(SESSION_CONFIG["cookie_secure"])
    
    def test_environment_specific_settings(self):
        """Test that environment-specific settings are applied"""
        # Verify that the environment is recognized
        self.assertIn(ENVIRONMENT, ["development", "test", "production"])
        
        # Development environment should have longer token expiry
        if ENVIRONMENT == "development":
            self.assertGreaterEqual(JWT_CONFIG["access_token_expire_minutes"], 60)
        
        # Test environment should have more permissive rate limits
        if ENVIRONMENT == "test":
            self.assertTrue(any("1000" in limit for limit in RATE_LIMIT_CONFIG["default_limits"]))


if __name__ == "__main__":
    unittest.main()
