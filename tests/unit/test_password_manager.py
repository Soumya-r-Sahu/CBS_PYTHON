"""
Unit tests for security module - Password Manager
"""

import unittest
import time
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path to be able to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from security.password_manager import (
    hash_password,
    verify_password,
    validate_password_policy,
    generate_secure_password,
    check_password_expiration,
    is_password_reused,
    PASSWORD_MIN_LENGTH, 
    PASSWORD_MIN_UPPERCASE,
    PASSWORD_MIN_LOWERCASE,
    PASSWORD_MIN_DIGITS,
    PASSWORD_MIN_SPECIAL,
    PASSWORD_MAX_AGE_DAYS
)


class TestPasswordManager(unittest.TestCase):
    """Test cases for Password Manager functionality"""
    
    def test_hash_password(self):
        """Test password hashing with and without salt"""
        password = "TestPassword123!"
        
        # Test with auto-generated salt
        hashed1, salt1 = hash_password(password)
        self.assertIsNotNone(hashed1)
        self.assertIsNotNone(salt1)
        
        # Test with provided salt
        hashed2, salt2 = hash_password(password, salt1)
        self.assertEqual(salt1, salt2)
        
        # Different passwords should produce different hashes
        hashed3, salt3 = hash_password("DifferentPassword123!")
        self.assertNotEqual(hashed1, hashed3)
    
    def test_verify_password(self):
        """Test password verification"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        
        hashed, salt = hash_password(password)
        
        # Correct password should verify
        self.assertTrue(verify_password(password, hashed, salt))
        
        # Wrong password should not verify
        self.assertFalse(verify_password(wrong_password, hashed, salt))
    
    def test_validate_password_policy(self):
        """Test password policy validation"""
        # Valid password
        valid_password = "ValidPass1!"
        result = validate_password_policy(valid_password)
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        
        # Too short
        short_password = "Short1!"
        result = validate_password_policy(short_password)
        self.assertFalse(result["valid"])
        self.assertIn("length", result["errors"][0])
        
        # No uppercase
        no_upper_password = "lowercase1!"
        result = validate_password_policy(no_upper_password)
        self.assertFalse(result["valid"])
        self.assertIn("uppercase", result["errors"][0])
        
        # No lowercase
        no_lower_password = "UPPERCASE1!"
        result = validate_password_policy(no_lower_password)
        self.assertFalse(result["valid"])
        self.assertIn("lowercase", result["errors"][0])
        
        # No digits
        no_digit_password = "NoDigitPass!"
        result = validate_password_policy(no_digit_password)
        self.assertFalse(result["valid"])
        self.assertIn("digit", result["errors"][0])
        
        # No special characters
        no_special_password = "NoSpecial123"
        result = validate_password_policy(no_special_password)
        self.assertFalse(result["valid"])
        self.assertIn("special", result["errors"][0])
        
        # Common pattern
        common_pattern_password = "Password123!"
        result = validate_password_policy(common_pattern_password)
        self.assertFalse(result["valid"])
        self.assertIn("common pattern", result["errors"][0])
    
    def test_generate_secure_password(self):
        """Test secure password generation"""
        password = generate_secure_password()
        
        # Check length
        self.assertGreaterEqual(len(password), PASSWORD_MIN_LENGTH)
        
        # Validate generated password against policy
        result = validate_password_policy(password)
        self.assertTrue(result["valid"])
        
        # Different calls should generate different passwords
        another_password = generate_secure_password()
        self.assertNotEqual(password, another_password)
        
        # Test with custom length
        custom_length = 20
        long_password = generate_secure_password(custom_length)
        self.assertEqual(len(long_password), custom_length)
    
    def test_check_password_expiration(self):
        """Test password expiration checking"""
        # Not expired
        current_time = time.time()
        days_ago_10 = current_time - (10 * 24 * 60 * 60)
        result = check_password_expiration(days_ago_10)
        self.assertFalse(result["expired"])
        self.assertEqual(result["days_since_change"], 10)
        self.assertEqual(result["days_left"], PASSWORD_MAX_AGE_DAYS - 10)
        
        # Expired
        days_ago_100 = current_time - (100 * 24 * 60 * 60)
        result = check_password_expiration(days_ago_100)
        self.assertTrue(result["expired"])
        self.assertEqual(result["days_since_change"], 100)
        self.assertEqual(result["days_left"], 0)
    
    def test_is_password_reused(self):
        """Test password reuse detection"""
        password = "TestPassword123!"
        new_password = "NewPassword456!"
        
        # Create a history of passwords
        hashed1, salt1 = hash_password(password)
        password_history = [
            {"hash": hashed1, "salt": salt1}
        ]
        
        # Should detect reuse of the same password
        self.assertTrue(is_password_reused(password, password_history))
        
        # Should not detect the new password as a reuse
        self.assertFalse(is_password_reused(new_password, password_history))


if __name__ == "__main__":
    unittest.main()
