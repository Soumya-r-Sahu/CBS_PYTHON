"""
Integration tests for the security module components working together.
"""

import unittest
import os
import sys
import time
import json
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add project root to path to be able to import modules

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


# Import security components
from security import (
    authenticate_user, verify_permissions, check_access, create_token,
    encrypt_data, decrypt_data, hash_password, verify_password,
    setup_mfa, verify_mfa
)
from security.password_manager import validate_password_policy, generate_secure_password
from security.config import JWT_CONFIG, PASSWORD_POLICY
from security.logs.audit_logger import AuditLogger
from security.mfa import TOTPManager, MFAManager


class TestSecurityIntegration(unittest.TestCase):
    """Integration tests for security module components"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a mock database for users
        self.mock_db = {
            "users": {
                "user1": {
                    "username": "user1",
                    "password_hash": None,  # Will be set in tests
                    "password_salt": None,  # Will be set in tests
                    "roles": ["user"],
                    "mfa_enabled": False,
                    "mfa_data": None,
                    "last_login": time.time() - 86400,  # 1 day ago
                },
                "admin1": {
                    "username": "admin1",
                    "password_hash": None,  # Will be set in tests
                    "password_salt": None,  # Will be set in tests
                    "roles": ["admin", "user"],
                    "mfa_enabled": False,
                    "mfa_data": None,
                    "last_login": time.time() - 3600,  # 1 hour ago
                }
            }
        }
        
        # Set up passwords for mock users
        user_password = "UserPassword123!"
        admin_password = "AdminPass456@"
        
        user_hash, user_salt = hash_password(user_password)
        admin_hash, admin_salt = hash_password(admin_password)
        
        self.mock_db["users"]["user1"]["password_hash"] = user_hash
        self.mock_db["users"]["user1"]["password_salt"] = user_salt
        self.mock_db["users"]["admin1"]["password_hash"] = admin_hash
        self.mock_db["users"]["admin1"]["password_salt"] = admin_salt
        
        # Store passwords for testing
        self.test_passwords = {
            "user1": user_password,
            "admin1": admin_password
        }
        
        # Set up audit logger
        self.audit_logger = AuditLogger()
        
        # Temporary directory for log files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, "security_test.log")
    
    def tearDown(self):
        """Clean up after tests"""
        self.temp_dir.cleanup()
    
    def test_user_authentication_flow(self):
        """Test full user authentication flow with password and token"""
        # Define a mock authentication function
        def mock_authenticate(username, password):
            user = self.mock_db["users"].get(username)
            if not user:
                return None
            
            if verify_password(password, user["password_hash"], user["password_salt"]):
                token = create_token(username, user["roles"])
                return {
                    "username": username,
                    "roles": user["roles"],
                    "token": token
                }
            return None
        
        # Test authentication with correct credentials
        auth_result = mock_authenticate("user1", self.test_passwords["user1"])
        self.assertIsNotNone(auth_result)
        self.assertEqual(auth_result["username"], "user1")
        self.assertIn("token", auth_result)
        
        # Test authentication with incorrect credentials
        auth_result = mock_authenticate("user1", "wrong_password")
        self.assertIsNone(auth_result)
        
        # Test permissions using the token
        token = mock_authenticate("admin1", self.test_passwords["admin1"])["token"]
        
        # Mock token verification
        def mock_verify_token_and_get_roles(token):
            # In a real system, this would decode and verify the JWT token
            # For testing, we'll just return the admin roles
            return ["admin", "user"]
        
        # Define a permission check function using the mock token verification
        def has_permission(token, required_roles):
            user_roles = mock_verify_token_and_get_roles(token)
            return any(role in user_roles for role in required_roles)
        
        # Test permission checks
        self.assertTrue(has_permission(token, ["admin"]))
        self.assertTrue(has_permission(token, ["user"]))
        self.assertFalse(has_permission(token, ["super_admin"]))
    
    def test_password_management_and_policy(self):
        """Test password management and policy enforcement"""
        # Test password policy validation
        valid_password = "ValidPass123!"
        policy_result = validate_password_policy(valid_password)
        self.assertTrue(policy_result["valid"])
        
        # Test with invalid password
        invalid_password = "weak"
        policy_result = validate_password_policy(invalid_password)
        self.assertFalse(policy_result["valid"])
        self.assertGreater(len(policy_result["errors"]), 0)
        
        # Test password generation
        generated_password = generate_secure_password()
        policy_result = validate_password_policy(generated_password)
        self.assertTrue(policy_result["valid"])
        
        # Test password change flow
        def change_password(username, old_password, new_password):
            user = self.mock_db["users"].get(username)
            if not user:
                return {"success": False, "message": "User not found"}
            
            # Verify old password
            if not verify_password(old_password, user["password_hash"], user["password_salt"]):
                return {"success": False, "message": "Current password is incorrect"}
            
            # Check password policy
            policy_result = validate_password_policy(new_password)
            if not policy_result["valid"]:
                return {"success": False, "errors": policy_result["errors"]}
            
            # Hash new password
            new_hash, new_salt = hash_password(new_password)
            
            # Update user record
            user["password_hash"] = new_hash
            user["password_salt"] = new_salt
            
            return {"success": True}
        
        # Test successful password change
        result = change_password("user1", self.test_passwords["user1"], "NewSecurePass456!")
        self.assertTrue(result["success"])
        
        # Test failed password change with wrong current password
        result = change_password("user1", "wrong_password", "NewSecurePass789@")
        self.assertFalse(result["success"])
        
        # Test failed password change with policy violation
        result = change_password("user1", "NewSecurePass456!", "weak")
        self.assertFalse(result["success"])
    
    def test_encryption_and_decryption(self):
        """Test data encryption and decryption"""
        # Test text encryption
        sensitive_data = "1234-5678-9012-3456"  # Credit card number
        encrypted = encrypt_data(sensitive_data)
        
        # Encrypted data should be different from original
        self.assertNotEqual(sensitive_data, encrypted)
        
        # Decrypt and verify
        decrypted = decrypt_data(encrypted)
        self.assertEqual(sensitive_data, decrypted)
        
        # Test encryption of structured data
        complex_data = {
            "card_number": "1234-5678-9012-3456",
            "cvv": "123",
            "expiry": "12/25",
            "holder": "John Doe"
        }
        
        # Convert to JSON string before encryption
        json_data = json.dumps(complex_data)
        encrypted_json = encrypt_data(json_data)
        
        # Decrypt and parse back to object
        decrypted_json = decrypt_data(encrypted_json)
        recovered_data = json.loads(decrypted_json)
        
        self.assertEqual(complex_data["card_number"], recovered_data["card_number"])
        self.assertEqual(complex_data["cvv"], recovered_data["cvv"])
    
    def test_mfa_setup_and_verification(self):
        """Test MFA setup and verification flow"""
        # Skip if pyotp is not available
        try:
            import pyotp
        except ImportError:
            self.skipTest("pyotp not available")
        
        # Set up MFA for a user
        username = "user1"
        setup_info = setup_mfa(username)
        
        # Check setup info structure
        self.assertIn("mfa_data", setup_info)
        self.assertIn("backup_codes", setup_info)
        
        # Store MFA data in mock database
        self.mock_db["users"][username]["mfa_enabled"] = True
        self.mock_db["users"][username]["mfa_data"] = setup_info["mfa_data"]
        
        # Create a TOTP token using the secret
        totp = pyotp.TOTP(setup_info["mfa_data"]["secret"])
        token = totp.now()
        
        # Verify the token
        is_valid, updated_mfa_data = verify_mfa(token, self.mock_db["users"][username]["mfa_data"])
        self.assertTrue(is_valid)
        
        # Test backup code
        backup_code = setup_info["backup_codes"][0]
        is_valid, updated_mfa_data = verify_mfa(backup_code, updated_mfa_data)
        self.assertTrue(is_valid)
        
        # Update MFA data in mock database
        self.mock_db["users"][username]["mfa_data"] = updated_mfa_data
        
        # Same backup code shouldn't work twice
        is_valid, _ = verify_mfa(backup_code, updated_mfa_data)
        self.assertFalse(is_valid)
    
    def test_audit_logging(self):
        """Test security audit logging"""
        # Configure logger to use test file
        with patch.object(self.audit_logger, 'log_file_path', self.log_file):
            # Log some security events
            self.audit_logger.log_event(
                event_type="login",
                user_id="user1",
                description="User login",
                metadata={"ip": "192.168.1.100", "browser": "Chrome"}
            )
            
            self.audit_logger.log_event(
                event_type="password_change",
                user_id="user1",
                description="Password changed",
                metadata={"ip": "192.168.1.100"}
            )
            
            # Check that log file was created
            self.assertTrue(os.path.exists(self.log_file))
            
            # Read log file and check contents
            with open(self.log_file, 'r') as f:
                log_content = f.read()
                
                # Check for event details in logs
                self.assertIn("login", log_content)
                self.assertIn("user1", log_content)
                self.assertIn("password_change", log_content)


if __name__ == "__main__":
    unittest.main()