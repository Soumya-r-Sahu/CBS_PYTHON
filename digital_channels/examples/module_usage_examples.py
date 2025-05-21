"""
Digital Channels Usage Examples

This file provides examples of how to use the Digital Channels module.
"""

import logging
import json
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import required modules
try:
    from digital_channels.module_interface import DigitalChannelsModule
    from digital_channels.utils.error_handling import handle_exception
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    raise

def demonstrate_web_authentication():
    """
    Demonstrate web authentication process
    """
    print("\n=== Web Authentication Example ===")
    
    # Initialize the Digital Channels module
    digital_channels = DigitalChannelsModule()
    
    # Register services
    digital_channels.register_services()
    
    # Simulate web authentication
    try:
        response = digital_channels.authenticate_web(
            username="customer123",
            password="demo_password",
            device_info={"browser": "Chrome", "os": "Windows"}
        )
        
        # Pretty print the response
        print(f"Authentication Response:")
        print(json.dumps(response, indent=2))
        
        # Check for success
        if response.get("success"):
            print(f"✅ Authentication successful")
            print(f"Token: {response.get('token')}")
        else:
            print(f"❌ Authentication failed: {response.get('error', {}).get('message')}")
            
    except Exception as e:
        error_response = handle_exception(e)
        print(f"❌ Error: {error_response.get('error', {}).get('message')}")

def demonstrate_account_summary():
    """
    Demonstrate retrieving account summary
    """
    print("\n=== Account Summary Example ===")
    
    # Initialize the Digital Channels module
    digital_channels = DigitalChannelsModule()
    
    # Register services
    digital_channels.register_services()
    
    # Authenticate first (simplified)
    auth_response = digital_channels.authenticate_web(
        username="customer123",
        password="demo_password"
    )
    
    if not auth_response.get("success"):
        print(f"❌ Authentication failed, cannot proceed")
        return
    
    # Get the authentication token
    token = auth_response.get("token")
    customer_id = auth_response.get("user_info", {}).get("customer_id")
    
    # Retrieve account summary
    try:
        response = digital_channels.get_account_summary(
            customer_id=customer_id,
            token=token,
            include_details=True
        )
        
        # Pretty print the response
        print(f"Account Summary Response:")
        print(json.dumps(response, indent=2))
        
        # Process the accounts
        if response.get("accounts"):
            print(f"Found {len(response.get('accounts'))} accounts:")
            for account in response.get("accounts"):
                print(f"  - {account.get('account_type')} Account: {account.get('account_number')}")
                print(f"    Balance: {account.get('balance')} {account.get('currency')}")
        else:
            print("No accounts found")
            
    except Exception as e:
        error_response = handle_exception(e)
        print(f"❌ Error: {error_response.get('error', {}).get('message')}")

def demonstrate_transaction_history():
    """
    Demonstrate retrieving transaction history
    """
    print("\n=== Transaction History Example ===")
    
    # Initialize the Digital Channels module
    digital_channels = DigitalChannelsModule()
    
    # Register services
    digital_channels.register_services()
    
    # Authenticate first (simplified)
    auth_response = digital_channels.authenticate_web(
        username="customer123",
        password="demo_password"
    )
    
    if not auth_response.get("success"):
        print(f"❌ Authentication failed, cannot proceed")
        return
    
    # Get the authentication token
    token = auth_response.get("token")
    
    # Retrieve transaction history for an account
    try:
        response = digital_channels.get_transaction_history(
            account_number="1234567890",
            token=token,
            start_date="2025-01-01",
            end_date="2025-04-30",
            limit=5
        )
        
        # Pretty print the response
        print(f"Transaction History Response:")
        print(json.dumps(response, indent=2))
        
        # Process the transactions
        if response.get("transactions"):
            print(f"Found {len(response.get('transactions'))} transactions:")
            for transaction in response.get("transactions"):
                print(f"  - {transaction.get('date')}: {transaction.get('description')}")
                print(f"    Amount: {transaction.get('amount')} ({transaction.get('type')})")
        else:
            print("No transactions found")
            
    except Exception as e:
        error_response = handle_exception(e)
        print(f"❌ Error: {error_response.get('error', {}).get('message')}")

def demonstrate_payment_processing():
    """
    Demonstrate payment processing
    """
    print("\n=== Payment Processing Example ===")
    
    # Initialize the Digital Channels module
    digital_channels = DigitalChannelsModule()
    
    # Register services
    digital_channels.register_services()
    
    # Authenticate first (simplified)
    auth_response = digital_channels.authenticate_web(
        username="customer123",
        password="demo_password"
    )
    
    if not auth_response.get("success"):
        print(f"❌ Authentication failed, cannot proceed")
        return
    
    # Get the authentication token
    token = auth_response.get("token")
    
    # Process a payment
    try:
        response = digital_channels.process_payment(
            from_account="1234567890",
            to_account="0987654321",
            amount=100.50,
            currency="USD",
            description="Monthly rent payment",
            token=token
        )
        
        # Pretty print the response
        print(f"Payment Response:")
        print(json.dumps(response, indent=2))
        
        # Check payment status
        if response.get("success"):
            print(f"✅ Payment successful")
            print(f"Transaction ID: {response.get('transaction_id')}")
            print(f"Status: {response.get('status')}")
        else:
            print(f"❌ Payment failed: {response.get('error', {}).get('message')}")
            
    except Exception as e:
        error_response = handle_exception(e)
        print(f"❌ Error: {error_response.get('error', {}).get('message')}")

def run_all_examples():
    """
    Run all example demonstrations
    """
    print("=== Digital Channels Usage Examples ===")
    
    demonstrate_web_authentication()
    demonstrate_account_summary()
    demonstrate_transaction_history()
    demonstrate_payment_processing()
    
    print("\n=== Examples Complete ===")

if __name__ == "__main__":
    run_all_examples()
