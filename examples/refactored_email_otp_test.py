"""
Test Script for Refactored Email OTP Module

This script demonstrates the usage of the refactored Email OTP module
with its improved error handling and design patterns.
"""

import logging
from security.authentication.refactored_email_otp import EmailOTPManager
from utils.unified_error_handling import ValidationException, NotFoundException

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__name__)

def test_email_otp():
    """Test the refactored Email OTP functionality"""
    
    logger.info("==== Testing Refactored Email OTP Manager ====")
    
    try:
        # Create OTP manager (uses singleton pattern)
        otp_manager1 = EmailOTPManager()
        otp_manager2 = EmailOTPManager()
        
        # Demonstrate that both instances are the same (singleton)
        logger.info(f"Singleton test: Same instance? {otp_manager1 is otp_manager2}")
        
        # Test data
        user_id = "test_user_001"
        email = "user@example.com"
        
        # Generate OTP
        logger.info(f"Generating OTP for user {user_id}")
        otp = otp_manager1.generate_otp(user_id)
        logger.info(f"Generated OTP: {otp}")
        
        # Send OTP via email (simulated)
        logger.info(f"Sending OTP email to {email}")
        # In a real environment, this would actually send an email
        success = otp_manager1.send_otp_email(email, user_id, "login verification")
        logger.info(f"Email sent: {success}")
        
        # Test OTP verification
        logger.info("Testing OTP verification:")
        
        # Test with correct OTP
        is_valid, message = otp_manager1.verify_otp(user_id, otp)
        logger.info(f"Verification with correct OTP: {is_valid}, Message: {message}")
        
        # Generate a new OTP since the previous one was consumed
        otp = otp_manager1.generate_otp(user_id)
        
        # Test with incorrect OTP
        incorrect_otp = "000000"
        is_valid, message = otp_manager1.verify_otp(user_id, incorrect_otp)
        logger.info(f"Verification with incorrect OTP: {is_valid}, Message: {message}")
        
        # Test with invalid user
        invalid_user = "nonexistent_user"
        is_valid, message = otp_manager1.verify_otp(invalid_user, "123456")
        logger.info(f"Verification with invalid user: {is_valid}, Message: {message}")
        
        # Test handling of validation exceptions
        try:
            logger.info("Testing validation exception handling")
            otp_manager1.generate_otp("")  # Empty user_id should trigger validation exception
        except ValidationException as e:
            logger.info(f"Caught expected validation exception: {e.message}")
            logger.info(f"Exception details: {e.to_dict()}")
        
        # Test cleanup
        logger.info("Testing cleanup of expired OTPs")
        count = otp_manager1.cleanup_expired_otps()
        logger.info(f"Cleaned up {count} expired OTPs")
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_email_otp()
