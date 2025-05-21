"""
Mail OTP Utility

This utility provides simplified functions for email-based OTP verification,
abstracting the details of the EmailOTPManager class for easier integration
with other modules in the Core Banking System.
"""

import logging
from typing import Tuple, Dict, Optional
from security.authentication.email_otp import EmailOTPManager

# Configure logger
logger = logging.getLogger(__name__)

# Create a singleton instance of the OTP manager for reuse
_otp_manager = EmailOTPManager()

def send_verification_code(email: str, user_id: str, purpose: str = "account verification") -> bool:
    """
    Send a verification code to the user's email
    
    Args:
        email (str): Recipient email address
        user_id (str): User identifier
        purpose (str): Purpose of verification (for email message customization)
        
    Returns:
        bool: True if code was sent successfully, False otherwise
    """
    try:
        return _otp_manager.send_otp_email(email, user_id, purpose)
    except Exception as e:
        logger.error(f"Error sending verification code: {str(e)}")
        return False

def verify_code(user_id: str, code: str) -> Tuple[bool, str]:
    """
    Verify the OTP code provided by the user
    
    Args:
        user_id (str): User identifier
        code (str): OTP code to verify
        
    Returns:
        Tuple[bool, str]: (is_valid, message)
            - is_valid: True if OTP is valid, False otherwise
            - message: Explanation message for the result
    """
    try:
        return _otp_manager.verify_otp(user_id, code)
    except Exception as e:
        logger.error(f"Error verifying code: {str(e)}")
        return False, f"Error during verification: {str(e)}"

def get_custom_otp_manager(
    otp_length: int = 6,
    expiry_minutes: int = 10,
    numeric_only: bool = True,
    max_attempts: int = 3
) -> EmailOTPManager:
    """
    Get a custom configured OTP manager instance
    
    Args:
        otp_length (int): Length of OTP code
        expiry_minutes (int): OTP validity period in minutes
        numeric_only (bool): If True, generate only numeric OTPs
        max_attempts (int): Maximum verification attempts before OTP is invalidated
        
    Returns:
        EmailOTPManager: Configured instance of EmailOTPManager
    """
    return EmailOTPManager(
        otp_length=otp_length,
        expiry_minutes=expiry_minutes,
        numeric_only=numeric_only,
        max_verification_attempts=max_attempts
    )

# Examples of common use cases

def send_login_verification(email: str, user_id: str) -> bool:
    """
    Send a login verification code
    
    Args:
        email (str): User email address
        user_id (str): User ID
        
    Returns:
        bool: Success status
    """
    return send_verification_code(email, user_id, "login verification")

def send_transaction_verification(email: str, user_id: str) -> bool:
    """
    Send a transaction verification code
    
    Args:
        email (str): User email address
        user_id (str): User ID
        
    Returns:
        bool: Success status
    """
    return send_verification_code(email, user_id, "transaction verification")

def send_password_reset_code(email: str, user_id: str) -> bool:
    """
    Send a password reset code
    
    Args:
        email (str): User email address
        user_id (str): User ID
        
    Returns:
        bool: Success status
    """
    return send_verification_code(email, user_id, "password reset")

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    email = "user@example.com"
    user_id = "user123"
    
    # Send verification
    print(f"Sending verification to {email}")
    success = send_login_verification(email, user_id)
    print(f"Verification sent: {success}")
    
    # In real scenario, user would input code from email
    code = "123456"  # Example code
    
    # Verify code
    valid, message = verify_code(user_id, code)
    print(f"Verification result: {valid}, Message: {message}")
