# Example of how to use the centralized configuration

"""
Example Module

This module demonstrates how to use the centralized configuration system.
Follow this pattern for all new code.
"""

# Import directly from the main config file
from config import DATABASE_CONFIG, EMAIL_CONFIG, UPI_CONFIG, DEBUG_MODE

def connect_to_database():
    """Example function that uses the database configuration"""
    host = DATABASE_CONFIG['host']
    port = DATABASE_CONFIG['port']
    user = DATABASE_CONFIG['user']
    password = DATABASE_CONFIG['password']  # Securely stored in config
    
    print(f"Connecting to database at {host}:{port} as {user}")
    # In real code, you would use these values to establish a database connection
    
def send_notification(recipient, message):
    """Example function that uses email configuration"""
    smtp_host = EMAIL_CONFIG['host']
    smtp_port = EMAIL_CONFIG['port']
    sender = EMAIL_CONFIG['default_sender']
    
    print(f"Sending email to {recipient} via {smtp_host}:{smtp_port}")
    print(f"From: {sender}")
    print(f"Message: {message}")
    
    if DEBUG_MODE:
        print("Debug mode is on, logging extra information")
        
def process_upi_payment(upi_id, amount):
    """Example function that uses UPI configuration"""
    provider = UPI_CONFIG['provider']
    api_key = UPI_CONFIG['api_key']  # Securely stored in config
    
    print(f"Processing UPI payment of {amount} to {upi_id}")
    print(f"Using provider: {provider}")
    
    # In real code, you would use the API key to authenticate with the UPI service
    
if __name__ == "__main__":
    # Example usage
    connect_to_database()
    send_notification("example@example.com", "Hello from CBS!")
    process_upi_payment("user@upi", 1000.00)
