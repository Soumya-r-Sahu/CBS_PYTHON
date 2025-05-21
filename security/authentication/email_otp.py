"""
Email OTP Authentication Module for Core Banking System

This module implements email-based One-Time Password (OTP) authentication
for the Core Banking System. It generates, sends, and verifies OTP codes
for secure user authentication via email.
"""

import os
import time
import random
import string
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta

# Import notification service for sending emails
from utils.lib.notification_service import NotificationService

# Import configuration
from security.config import MFA_CONFIG

# Configure logger
logger = logging.getLogger(__name__)

# Default OTP configuration
DEFAULT_OTP_LENGTH = 6
DEFAULT_OTP_EXPIRY_MINUTES = 10
DEFAULT_OTP_NUMERIC_ONLY = True
DEFAULT_MAX_VERIFICATION_ATTEMPTS = 3

class EmailOTPManager:
    """Manager for Email-based One-Time Password (OTP) authentication"""
    
    def __init__(
        self,
        otp_length: int = DEFAULT_OTP_LENGTH,
        expiry_minutes: int = DEFAULT_OTP_EXPIRY_MINUTES,
        numeric_only: bool = DEFAULT_OTP_NUMERIC_ONLY,
        max_verification_attempts: int = DEFAULT_MAX_VERIFICATION_ATTEMPTS
    ):
        """
        Initialize Email OTP Manager
        
        Args:
            otp_length (int): Length of OTP code
            expiry_minutes (int): OTP validity period in minutes
            numeric_only (bool): If True, generate only numeric OTPs
            max_verification_attempts (int): Maximum verification attempts before OTP is invalidated
        """
        self.otp_length = otp_length
        self.expiry_minutes = expiry_minutes
        self.numeric_only = numeric_only
        self.max_verification_attempts = max_verification_attempts
        self.notification_service = NotificationService()
        
        # Store active OTPs with expiry timestamps and attempt counters
        # Format: {user_id: {'code': 'otp_code', 'expiry': timestamp, 'attempts': count}}
        self._active_otps = {}
        
        logger.info("Email OTP Manager initialized")

    def _generate_otp_code(self) -> str:
        """
        Generate a random OTP code
        
        Returns:
            str: Generated OTP code
        """
        if self.numeric_only:
            # Generate numeric OTP
            return ''.join(random.choices(string.digits, k=self.otp_length))
        else:
            # Generate alphanumeric OTP (excluding similar looking characters)
            chars = string.ascii_uppercase + string.digits
            # Remove similar looking characters
            chars = chars.replace('O', '').replace('0', '').replace('I', '').replace('1', '')
            return ''.join(random.choices(chars, k=self.otp_length))

    def generate_otp(self, user_id: str) -> str:
        """
        Generate a new OTP for the user
        
        Args:
            user_id (str): User identifier
            
        Returns:
            str: Generated OTP code
        """
        # Generate OTP code
        otp_code = self._generate_otp_code()
        
        # Calculate expiry time
        expiry_time = datetime.now() + timedelta(minutes=self.expiry_minutes)
        
        # Store OTP with expiry and reset attempts
        self._active_otps[user_id] = {
            'code': otp_code,
            'expiry': expiry_time,
            'attempts': 0
        }
        
        logger.debug(f"Generated OTP for user {user_id} (expires in {self.expiry_minutes} minutes)")
        return otp_code

    def send_otp_email(self, email: str, user_id: str, purpose: str = "authentication") -> bool:
        """
        Generate and send OTP via email
        
        Args:
            email (str): Recipient email address
            user_id (str): User identifier
            purpose (str): Purpose of OTP (for customizing message)
            
        Returns:
            bool: True if OTP was successfully sent, False otherwise
        """
        try:
            # Generate new OTP
            otp_code = self.generate_otp(user_id)
            
            # Prepare email subject and message
            subject = f"Your verification code for {MFA_CONFIG.get('totp_issuer', 'Core Banking System')}"
            
            # Build the message with OTP
            message = f"""
Dear Customer,

Your verification code for {purpose} is: {otp_code}

This code will expire in {self.expiry_minutes} minutes.
If you did not request this code, please ignore this email or contact our support team.

Do not share this code with anyone.

Best regards,
Security Team
{MFA_CONFIG.get('totp_issuer', 'Core Banking System')}
"""
            
            # Send email using notification service
            return self.notification_service.send_email(
                recipient=email,
                subject=subject,
                message=message
            )
            
        except Exception as e:
            logger.error(f"Failed to send OTP email to {email}: {str(e)}")
            return False

    def verify_otp(self, user_id: str, otp_code: str) -> Tuple[bool, str]:
        """
        Verify the provided OTP code
        
        Args:
            user_id (str): User identifier
            otp_code (str): OTP code to verify
            
        Returns:
            Tuple[bool, str]: (is_valid, message)
                - is_valid: True if OTP is valid, False otherwise
                - message: Explanation message for the result
        """
        # Check if user has an active OTP
        if user_id not in self._active_otps:
            return False, "No active OTP found for this user"
        
        # Get OTP data
        otp_data = self._active_otps[user_id]
        
        # Check if OTP is expired
        if datetime.now() > otp_data['expiry']:
            # Clean up expired OTP
            self._active_otps.pop(user_id, None)
            return False, "OTP has expired"
        
        # Increment attempt counter
        otp_data['attempts'] += 1
        
        # Check if maximum attempts exceeded
        if otp_data['attempts'] > self.max_verification_attempts:
            # Clean up OTP after max attempts
            self._active_otps.pop(user_id, None)
            return False, "Maximum verification attempts exceeded"
        
        # Verify OTP code (case insensitive)
        if otp_data['code'].upper() == otp_code.upper():
            # OTP verified, clean up
            self._active_otps.pop(user_id, None)
            return True, "OTP verified successfully"
        else:
            attempts_left = self.max_verification_attempts - otp_data['attempts']
            return False, f"Invalid OTP code. {attempts_left} attempts remaining"

    def cleanup_expired_otps(self) -> int:
        """
        Clean up expired OTP entries
        
        Returns:
            int: Number of expired entries cleaned up
        """
        current_time = datetime.now()
        expired_ids = [
            user_id for user_id, data in self._active_otps.items()
            if current_time > data['expiry']
        ]
        
        # Remove expired entries
        for user_id in expired_ids:
            self._active_otps.pop(user_id, None)
        
        if expired_ids:
            logger.debug(f"Cleaned up {len(expired_ids)} expired OTP entries")
        
        return len(expired_ids)


# Example usage
if __name__ == "__main__":
    # Configure logging for standalone testing
    logging.basicConfig(level=logging.DEBUG)
    
    # Create OTP manager
    otp_manager = EmailOTPManager()
    
    # Test OTP generation and verification
    user_id = "test_user_123"
    email = "test@example.com"
    
    # Generate and send OTP
    print(f"Sending OTP to {email}")
    success = otp_manager.send_otp_email(email, user_id, "login verification")
    print(f"OTP sent: {success}")
    
    # For demonstration: get the OTP code directly (in real scenario, user gets it from email)
    otp_code = otp_manager._active_otps[user_id]['code']
    print(f"Generated OTP: {otp_code}")
    
    # Verify OTP
    is_valid, message = otp_manager.verify_otp(user_id, otp_code)
    print(f"Verification result: {is_valid}, Message: {message}")
    
    # Test invalid OTP
    invalid_user = "nonexistent_user"
    is_valid, message = otp_manager.verify_otp(invalid_user, "123456")
    print(f"Invalid user verification: {is_valid}, Message: {message}")
