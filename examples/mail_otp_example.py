"""
Mail OTP Utility Example

This example demonstrates how to use the Mail OTP utility for email-based
verification in different scenarios such as login verification, 
transaction approval, and password reset.
"""

import logging
import time
from utils.common.mail_otp_util import (
    send_login_verification,
    send_transaction_verification,
    send_password_reset_code,
    verify_code,
    get_custom_otp_manager
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def example_login_verification():
    """Example of using OTP for login verification"""
    print("\n=== Login Verification Example ===")
    
    # Simulate a login attempt that requires 2FA
    email = "customer@example.com"
    user_id = "user_12345"
    
    print(f"User {user_id} is attempting to login")
    print(f"Sending verification code to {email}")
    
    # Send verification code
    if send_login_verification(email, user_id):
        print("✅ Verification code sent successfully")
        
        # In a real application, the user would receive the code via email
        # and enter it in a form. Here we'll simulate it:
        
        # Simulate user entering the code (in real scenario this would come from user input)
        user_entered_code = "123456"  # This would be wrong in a real scenario
        
        print(f"User entered code: {user_entered_code}")
        
        # Verify the code
        is_valid, message = verify_code(user_id, user_entered_code)
        
        if is_valid:
            print(f"✅ Code verified: {message}")
            print("User logged in successfully")
        else:
            print(f"❌ Verification failed: {message}")
    else:
        print("❌ Failed to send verification code")

def example_transaction_verification():
    """Example of using OTP for transaction verification"""
    print("\n=== Transaction Verification Example ===")
    
    # Simulate a high-value transaction that requires verification
    email = "customer@example.com"
    user_id = "user_12345"
    transaction_amount = 50000.00
    
    print(f"User {user_id} is attempting a transaction of ${transaction_amount:,.2f}")
    print(f"This exceeds the no-verification threshold. Sending OTP to {email}")
    
    # Send transaction verification code
    if send_transaction_verification(email, user_id):
        print("✅ Transaction verification code sent successfully")
        
        # Simulate user entering the code
        user_entered_code = "654321"  # This would be wrong in a real scenario
        
        print(f"User entered code: {user_entered_code}")
        
        # Verify the code
        is_valid, message = verify_code(user_id, user_entered_code)
        
        if is_valid:
            print(f"✅ Code verified: {message}")
            print(f"Transaction of ${transaction_amount:,.2f} approved and processed")
        else:
            print(f"❌ Verification failed: {message}")
            print("Transaction cancelled due to failed verification")
    else:
        print("❌ Failed to send transaction verification code")

def example_password_reset():
    """Example of using OTP for password reset"""
    print("\n=== Password Reset Example ===")
    
    # Simulate a password reset request
    email = "customer@example.com"
    user_id = "user_12345"
    
    print(f"Password reset requested for user {user_id}")
    print(f"Sending password reset code to {email}")
    
    # Send password reset code
    if send_password_reset_code(email, user_id):
        print("✅ Password reset code sent successfully")
        
        # Simulate user entering the reset code
        user_entered_code = "987654"  # This would be wrong in a real scenario
        
        print(f"User entered code: {user_entered_code}")
        
        # Verify the code
        is_valid, message = verify_code(user_id, user_entered_code)
        
        if is_valid:
            print(f"✅ Code verified: {message}")
            print("User allowed to set new password")
        else:
            print(f"❌ Verification failed: {message}")
            print("Password reset request rejected")
    else:
        print("❌ Failed to send password reset code")

def example_custom_otp_configuration():
    """Example of using a custom OTP configuration"""
    print("\n=== Custom OTP Configuration Example ===")
    
    # Create a custom OTP manager with longer codes and shorter expiry
    custom_otp_manager = get_custom_otp_manager(
        otp_length=8,           # 8-digit OTP instead of default 6
        expiry_minutes=5,       # 5 minute expiry instead of default 10
        numeric_only=False,     # Use alphanumeric codes
        max_attempts=5          # Allow 5 attempts instead of default 3
    )
    
    # Use the custom manager
    email = "customer@example.com"
    user_id = "user_12345"
    
    print("Using custom OTP configuration:")
    print(f"- 8-character alphanumeric code")
    print(f"- 5 minute expiry")
    print(f"- 5 maximum attempts")
    
    # Generate OTP using custom manager
    otp = custom_otp_manager.generate_otp(user_id)
    
    print(f"Generated code: {otp}")
    
    # In a real scenario, this would be sent via email
    success = custom_otp_manager.send_otp_email(
        email=email,
        user_id=user_id,
        purpose="secure transaction"
    )
    
    if success:
        print(f"✅ OTP sent to {email}")
    else:
        print(f"❌ Failed to send OTP")
    
    # Verification would happen normally using the same custom manager

if __name__ == "__main__":
    print("Mail OTP Utility Examples")
    print("=========================")
    
    # Run examples
    example_login_verification()
    example_transaction_verification()
    example_password_reset()
    example_custom_otp_configuration()
    
    print("\nAll examples completed")
