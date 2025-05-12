"""
Unit tests for security module - Multi-Factor Authentication
"""

import unittest
import time
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path to be able to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Check if pyotp is available for testing
try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False
    print("Warning: pyotp not available, some tests will be skipped")

from security.mfa import TOTPManager, BackupCodeManager, MFAManager, MFA_CONFIG


@unittest.skipIf(not PYOTP_AVAILABLE, "pyotp not available")
class TestTOTPManager(unittest.TestCase):
    """Test cases for TOTP Manager functionality"""
    
    def setUp(self):
        """Set up TOTP Manager for tests"""
        self.totp_manager = TOTPManager()
        self.test_secret = "JBSWY3DPEHPK3PXP"  # Test secret for consistency
        self.username = "test_user"
    
    def test_generate_secret(self):
        """Test TOTP secret generation"""
        secret = self.totp_manager.generate_secret()
        
        # Check that it's a valid base32 string
        self.assertTrue(all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567' for c in secret))
        self.assertGreaterEqual(len(secret), 16)  # Should be at least 16 chars (80 bits)
        
        # Different calls should generate different secrets
        another_secret = self.totp_manager.generate_secret()
        self.assertNotEqual(secret, another_secret)
    
    def test_get_totp_uri(self):
        """Test TOTP URI generation"""
        uri = self.totp_manager.get_totp_uri(self.username, self.test_secret)
        
        # Check URI format
        self.assertTrue(uri.startswith("otpauth://totp/"))
        self.assertIn(f"secret={self.test_secret}", uri)
        self.assertIn(f"issuer={MFA_CONFIG['totp_issuer']}", uri)
        self.assertIn(self.username, uri)
    
    def test_verify_totp(self):
        """Test TOTP verification"""
        # Generate a TOTP token with the test secret
        totp = pyotp.TOTP(self.test_secret)
        token = totp.now()
        
        # Verify the token
        self.assertTrue(self.totp_manager.verify_totp(self.test_secret, token))
        
        # Invalid token should fail
        self.assertFalse(self.totp_manager.verify_totp(self.test_secret, "000000"))
        
        # Wrong secret should fail
        wrong_secret = pyotp.random_base32()
        self.assertFalse(self.totp_manager.verify_totp(wrong_secret, token))


class TestBackupCodeManager(unittest.TestCase):
    """Test cases for Backup Code Manager functionality"""
    
    def setUp(self):
        """Set up Backup Code Manager for tests"""
        self.backup_manager = BackupCodeManager()
    
    def test_generate_backup_codes(self):
        """Test backup code generation"""
        codes = self.backup_manager.generate_backup_codes()
        
        # Check number of codes
        self.assertEqual(len(codes), MFA_CONFIG["backup_codes_count"])
        
        # Check format (8 chars with hyphen in middle: XXXX-XXXX)
        for code in codes:
            self.assertEqual(len(code), 9)  # 4 + hyphen + 4
            self.assertEqual(code[4], '-')
            self.assertTrue(all(c in '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ-' for c in code))
        
        # Different calls should generate different codes
        other_codes = self.backup_manager.generate_backup_codes()
        self.assertNotEqual(codes, other_codes)
    
    def test_hash_backup_codes(self):
        """Test backup code hashing"""
        codes = ["ABCD-1234", "EFGH-5678"]
        hashed_codes = self.backup_manager.hash_backup_codes(codes)
        
        # Check that we have the same number of hashes
        self.assertEqual(len(codes), len(hashed_codes))
        
        # Check format (salt:hash)
        for hashed in hashed_codes:
            parts = hashed.split(':', 1)
            self.assertEqual(len(parts), 2)
            salt, hash_value = parts
            self.assertTrue(len(salt) > 0)
            self.assertTrue(len(hash_value) > 0)
    
    def test_verify_backup_code(self):
        """Test backup code verification"""
        # Generate and hash backup codes
        codes = ["ABCD-1234", "EFGH-5678"]
        hashed_codes = self.backup_manager.hash_backup_codes(codes)
        
        # Valid code should pass and be removed
        is_valid, remaining_codes = self.backup_manager.verify_backup_code(codes[0], hashed_codes)
        self.assertTrue(is_valid)
        self.assertEqual(len(remaining_codes), len(hashed_codes) - 1)
        
        # Invalid code should fail
        is_valid, remaining_codes = self.backup_manager.verify_backup_code("XXXX-9999", hashed_codes)
        self.assertFalse(is_valid)
        self.assertEqual(len(remaining_codes), len(hashed_codes))
        
        # Code without hyphen should work too
        is_valid, remaining_codes = self.backup_manager.verify_backup_code("EFGH5678", hashed_codes)
        self.assertTrue(is_valid)


class TestMFAManager(unittest.TestCase):
    """Test cases for MFA Manager functionality"""
    
    def setUp(self):
        """Set up MFA Manager for tests"""
        self.mfa_manager = MFAManager()
        self.username = "test_user"
    
    def test_setup_mfa(self):
        """Test MFA setup"""
        setup_info = self.mfa_manager.setup_mfa(self.username)
        
        # Check setup info structure
        self.assertIn("mfa_data", setup_info)
        self.assertIn("qr_code", setup_info)
        self.assertIn("backup_codes", setup_info)
        self.assertIn("setup_instructions", setup_info)
        
        # Check MFA data
        mfa_data = setup_info["mfa_data"]
        self.assertTrue(mfa_data["enabled"])
        self.assertIn("secret", mfa_data)
        self.assertIn("backup_codes", mfa_data)
        self.assertIn("created_at", mfa_data)
        
        # Check backup codes
        backup_codes = setup_info["backup_codes"]
        self.assertEqual(len(backup_codes), MFA_CONFIG["backup_codes_count"])
    
    @unittest.skipIf(not PYOTP_AVAILABLE, "pyotp not available")
    def test_verify_mfa_with_totp(self):
        """Test MFA verification with TOTP"""
        # Set up MFA
        setup_info = self.mfa_manager.setup_mfa(self.username)
        mfa_data = setup_info["mfa_data"]
        
        # Generate a TOTP token
        secret = mfa_data["secret"]
        totp = pyotp.TOTP(secret)
        token = totp.now()
        
        # Verify the token
        is_valid, updated_mfa_data = self.mfa_manager.verify_mfa(token, mfa_data)
        self.assertTrue(is_valid)
        self.assertIsNotNone(updated_mfa_data["last_used"])
        
        # Invalid token should fail
        is_valid, _ = self.mfa_manager.verify_mfa("000000", mfa_data)
        self.assertFalse(is_valid)
    
    def test_verify_mfa_with_backup_code(self):
        """Test MFA verification with backup code"""
        # Set up MFA
        setup_info = self.mfa_manager.setup_mfa(self.username)
        mfa_data = setup_info["mfa_data"]
        backup_code = setup_info["backup_codes"][0]
        
        # Verify with backup code
        is_valid, updated_mfa_data = self.mfa_manager.verify_mfa(backup_code, mfa_data)
        self.assertTrue(is_valid)
        # Should have one less backup code
        self.assertEqual(len(updated_mfa_data["backup_codes"]), len(mfa_data["backup_codes"]) - 1)
        
        # Same code shouldn't work twice
        is_valid, _ = self.mfa_manager.verify_mfa(backup_code, updated_mfa_data)
        self.assertFalse(is_valid)
    
    def test_disable_mfa(self):
        """Test MFA disabling"""
        # Set up MFA
        setup_info = self.mfa_manager.setup_mfa(self.username)
        mfa_data = setup_info["mfa_data"]
        
        # Disable MFA
        updated_mfa_data = self.mfa_manager.disable_mfa(mfa_data)
        self.assertFalse(updated_mfa_data["enabled"])
        self.assertIn("disabled_at", updated_mfa_data)
    
    def test_regenerate_backup_codes(self):
        """Test backup code regeneration"""
        # Set up MFA
        setup_info = self.mfa_manager.setup_mfa(self.username)
        mfa_data = setup_info["mfa_data"]
        original_backup_codes = setup_info["backup_codes"]
        
        # Regenerate backup codes
        new_backup_codes, updated_mfa_data = self.mfa_manager.regenerate_backup_codes(mfa_data)
        
        # Should get new backup codes
        self.assertEqual(len(new_backup_codes), MFA_CONFIG["backup_codes_count"])
        self.assertNotEqual(new_backup_codes, original_backup_codes)
        
        # MFA data should be updated
        self.assertNotEqual(updated_mfa_data["backup_codes"], mfa_data["backup_codes"])


if __name__ == "__main__":
    unittest.main()
