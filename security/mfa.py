"""
Two-Factor Authentication Module for Core Banking System

This module implements TOTP-based two-factor authentication
and backup code management for additional security.
"""

import os
import time
import base64
import hashlib
import secrets
import logging
import json
import qrcode
from typing import Dict, List, Tuple, Optional
from io import BytesIO

# Try to import pyotp for TOTP implementation
try:
    import pyotp
    PYOTP_AVAILABLE = True
except ImportError:
    PYOTP_AVAILABLE = False
    logging.warning("pyotp module not found. TOTP functionality will be limited.")

# Import configuration
from security.config import MFA_CONFIG

# Configure logger
logger = logging.getLogger(__name__)


class TOTPManager:
    """Manager for Time-Based One-Time Password (TOTP) authentication"""
    
    def __init__(
        self,
        issuer: str = MFA_CONFIG["totp_issuer"],
        digits: int = MFA_CONFIG["totp_digits"],
        interval: int = MFA_CONFIG["totp_interval"],
    ):
        """
        Initialize TOTP Manager
        
        Args:
            issuer (str): Name of the issuer for TOTP
            digits (int): Number of digits in TOTP code
            interval (int): Time interval in seconds for TOTP
        """
        self.issuer = issuer
        self.digits = digits
        self.interval = interval
        
        if not PYOTP_AVAILABLE:
            logger.warning("TOTP functionality is limited without pyotp module")
    
    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret key
        
        Returns:
            str: Base32 encoded secret key
        """
        if PYOTP_AVAILABLE:
            return pyotp.random_base32()
        else:
            # Fallback implementation if pyotp is not available
            # Generate a 20-byte (160-bit) random key
            random_bytes = os.urandom(20)
            # Convert to base32 encoding (as per RFC 4648)
            base32_bytes = base64.b32encode(random_bytes)
            return base32_bytes.decode('utf-8')
    
    def get_totp_uri(self, username: str, secret: str) -> str:
        """
        Get the TOTP URI for QR code generation
        
        Args:
            username (str): Username for TOTP
            secret (str): TOTP secret key
            
        Returns:
            str: TOTP URI
        """
        if PYOTP_AVAILABLE:
            totp = pyotp.TOTP(secret, digits=self.digits, interval=self.interval)
            return totp.provisioning_uri(username, issuer_name=self.issuer)
        else:
            # Fallback implementation
            return (f"otpauth://totp/{self.issuer}:{username}?"
                   f"secret={secret}&issuer={self.issuer}"
                   f"&algorithm=SHA1&digits={self.digits}&period={self.interval}")
    
    def generate_qr_code(self, username: str, secret: str) -> bytes:
        """
        Generate QR code for TOTP setup
        
        Args:
            username (str): Username for TOTP
            secret (str): TOTP secret key
            
        Returns:
            bytes: PNG image data of QR code
        """
        uri = self.get_totp_uri(username, secret)
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to bytes
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    
    def verify_totp(self, secret: str, token: str) -> bool:
        """
        Verify a TOTP token
        
        Args:
            secret (str): TOTP secret key
            token (str): TOTP token to verify
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        if not PYOTP_AVAILABLE:
            logger.error("Cannot verify TOTP without pyotp module")
            return False
        
        try:
            totp = pyotp.TOTP(secret, digits=self.digits, interval=self.interval)
            # Allow a bit of time drift (one interval before and after)
            return totp.verify(token, valid_window=1)
        except Exception as e:
            logger.error(f"Error verifying TOTP: {str(e)}")
            return False


class BackupCodeManager:
    """Manager for backup authentication codes"""
    
    def __init__(self, code_count: int = MFA_CONFIG["backup_codes_count"]):
        """
        Initialize Backup Code Manager
        
        Args:
            code_count (int): Number of backup codes to generate
        """
        self.code_count = code_count
    
    def generate_backup_codes(self) -> List[str]:
        """
        Generate a set of backup codes
        
        Returns:
            List[str]: List of backup codes
        """
        # Generate alphanumeric codes
        codes = []
        for _ in range(self.code_count):
            # Generate 8-character backup codes
            code = ''.join(secrets.choice('0123456789ABCDEFGHJKLMNPQRSTUVWXYZ') for _ in range(8))
            # Add a hyphen for readability
            codes.append(f"{code[:4]}-{code[4:]}")
        
        return codes
    
    def hash_backup_codes(self, codes: List[str]) -> List[str]:
        """
        Hash backup codes for secure storage
        
        Args:
            codes (List[str]): List of backup codes
            
        Returns:
            List[str]: List of hashed backup codes
        """
        hashed_codes = []
        
        for code in codes:
            # Remove hyphen if present
            code = code.replace('-', '')
            # Create salted hash
            salt = secrets.token_hex(8)
            code_hash = hashlib.sha256((code + salt).encode('utf-8')).hexdigest()
            hashed_codes.append(f"{salt}:{code_hash}")
        
        return hashed_codes
    
    def verify_backup_code(self, code: str, hashed_codes: List[str]) -> Tuple[bool, List[str]]:
        """
        Verify a backup code and return remaining valid codes
        
        Args:
            code (str): Backup code to verify
            hashed_codes (List[str]): List of hashed backup codes
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, remaining_hashed_codes)
        """
        # Remove hyphen if present
        code = code.replace('-', '')
        
        for i, hashed_code in enumerate(hashed_codes):
            try:
                # Split salt and hash
                salt, code_hash = hashed_code.split(':', 1)
                
                # Hash the provided code with the same salt
                test_hash = hashlib.sha256((code + salt).encode('utf-8')).hexdigest()
                
                # Check if hashes match
                if test_hash == code_hash:
                    # Code is valid, remove it from the list
                    remaining_codes = hashed_codes.copy()
                    remaining_codes.pop(i)
                    return True, remaining_codes
            except Exception as e:
                logger.error(f"Error verifying backup code: {str(e)}")
                continue
        
        # No matching code found
        return False, hashed_codes


class MFAManager:
    """Manager for Multi-Factor Authentication"""
    
    def __init__(self):
        """Initialize MFA Manager with TOTP and backup code functionality"""
        self.totp_manager = TOTPManager()
        self.backup_code_manager = BackupCodeManager()
    
    def setup_mfa(self, username: str) -> Dict[str, any]:
        """
        Set up MFA for a user
        
        Args:
            username (str): Username to set up MFA for
            
        Returns:
            Dict[str, any]: MFA setup information
        """
        # Generate TOTP secret
        secret = self.totp_manager.generate_secret()
        
        # Generate backup codes
        backup_codes = self.backup_code_manager.generate_backup_codes()
        hashed_backup_codes = self.backup_code_manager.hash_backup_codes(backup_codes)
        
        # Generate QR code
        try:
            qr_code = self.totp_manager.generate_qr_code(username, secret)
            qr_code_b64 = base64.b64encode(qr_code).decode('utf-8')
        except Exception as e:
            logger.error(f"Error generating QR code: {str(e)}")
            qr_code_b64 = None
        
        # Create MFA data
        mfa_data = {
            "enabled": True,
            "secret": secret,
            "backup_codes": hashed_backup_codes,
            "created_at": time.time(),
            "last_used": None,
        }
        
        # Return setup information
        return {
            "mfa_data": mfa_data,
            "qr_code": qr_code_b64,
            "backup_codes": backup_codes,  # Clear text codes to show to the user once
            "setup_instructions": (
                f"1. Scan the QR code with your authenticator app\n"
                f"2. Enter the code shown in your app to verify setup\n"
                f"3. Save your backup codes in a secure location"
            ),
        }
    
    def verify_mfa(self, token: str, mfa_data: Dict[str, any]) -> Tuple[bool, Dict[str, any]]:
        """
        Verify an MFA token or backup code
        
        Args:
            token (str): TOTP token or backup code to verify
            mfa_data (Dict[str, any]): User's MFA data
            
        Returns:
            Tuple[bool, Dict[str, any]]: (is_valid, updated_mfa_data)
        """
        if not mfa_data.get("enabled", False):
            logger.warning("MFA verification attempted but MFA is not enabled")
            return False, mfa_data
        
        # Try as TOTP token first
        if len(token) == MFA_CONFIG["totp_digits"] and token.isdigit():
            is_valid = self.totp_manager.verify_totp(mfa_data["secret"], token)
            if is_valid:
                # Update last used timestamp
                mfa_data["last_used"] = time.time()
                return True, mfa_data
        
        # Try as backup code
        is_valid, updated_backup_codes = self.backup_code_manager.verify_backup_code(
            token, mfa_data["backup_codes"]
        )
        
        if is_valid:
            # Update backup codes and last used timestamp
            mfa_data["backup_codes"] = updated_backup_codes
            mfa_data["last_used"] = time.time()
            return True, mfa_data
        
        return False, mfa_data
    
    def disable_mfa(self, mfa_data: Dict[str, any]) -> Dict[str, any]:
        """
        Disable MFA for a user
        
        Args:
            mfa_data (Dict[str, any]): User's MFA data
            
        Returns:
            Dict[str, any]: Updated MFA data
        """
        mfa_data["enabled"] = False
        mfa_data["disabled_at"] = time.time()
        return mfa_data
    
    def regenerate_backup_codes(self, mfa_data: Dict[str, any]) -> Tuple[List[str], Dict[str, any]]:
        """
        Regenerate backup codes for a user
        
        Args:
            mfa_data (Dict[str, any]): User's MFA data
            
        Returns:
            Tuple[List[str], Dict[str, any]]: (new_backup_codes, updated_mfa_data)
        """
        # Generate new backup codes
        backup_codes = self.backup_code_manager.generate_backup_codes()
        hashed_backup_codes = self.backup_code_manager.hash_backup_codes(backup_codes)
        
        # Update MFA data
        mfa_data["backup_codes"] = hashed_backup_codes
        
        return backup_codes, mfa_data


# Create a singleton MFA manager
mfa_manager = MFAManager()

# Export main functions for easy access
setup_mfa = mfa_manager.setup_mfa
verify_mfa = mfa_manager.verify_mfa
disable_mfa = mfa_manager.disable_mfa
regenerate_backup_codes = mfa_manager.regenerate_backup_codes


if __name__ == "__main__":
    # Example usage
    username = "test_user"
    
    # Set up MFA
    setup_info = setup_mfa(username)
    print(f"TOTP Secret: {setup_info['mfa_data']['secret']}")
    print(f"Backup codes: {setup_info['backup_codes']}")
    
    # Simulate storing MFA data in user profile
    mfa_data = setup_info['mfa_data']
    
    # In a real application, you'd save this to a database
    print(f"\nMFA data to store:\n{json.dumps(mfa_data, indent=2)}")
    
    # Demonstration only - in real app user would enter code from their authenticator app
    if PYOTP_AVAILABLE:
        totp = pyotp.TOTP(mfa_data['secret'])
        test_token = totp.now()
        print(f"\nCurrent TOTP token: {test_token}")
        
        # Verify the token
        is_valid, updated_mfa_data = verify_mfa(test_token, mfa_data)
        print(f"Token verification result: {'Success' if is_valid else 'Failed'}")
        
        # Try a backup code
        test_backup_code = setup_info['backup_codes'][0]
        print(f"\nTesting backup code: {test_backup_code}")
        is_valid, updated_mfa_data = verify_mfa(test_backup_code, updated_mfa_data)
        print(f"Backup code verification result: {'Success' if is_valid else 'Failed'}")
        print(f"Remaining backup codes: {len(updated_mfa_data['backup_codes'])}")
    else:
        print("\nPyOTP not available for testing TOTP functionality")
