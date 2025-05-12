"""
End-to-End Test for UPI Mobile Banking Flows

This script tests the complete UPI flow from registration through transactions
in an end-to-end scenario that simulates real user behavior.
"""

import requests
import json
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from tests.integration.test_upi_api import (
    get_auth_token, 
    TEST_CUSTOMER_ID,
    TEST_ACCOUNT_NUMBER,
    TEST_UPI_ID,
    TEST_DEVICE_ID
)

BASE_URL = "http://localhost:5000/api/v1"

def test_complete_upi_flow():
    """
    Test the complete UPI flow:
    1. Register UPI ID
    2. Check balance
    3. Generate QR code
    4. Make a payment
    5. Check transaction history
    6. Create and respond to collect request
    7. Change UPI PIN
    """
    print("\n=== Starting Complete UPI Flow Test ===\n")
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("Failed to get auth token. Test aborted.")
        return False
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Step 1: Register UPI ID
        print("\n--- Step 1: UPI Registration ---")
        
        reg_data = {
            "account_number": TEST_ACCOUNT_NUMBER,
            "username": "testuser",
            "device_info": {
                "device_id": TEST_DEVICE_ID,
                "device_model": "Test Model",
                "os_version": "Test OS 1.0"
            },
            "upi_pin": "123456"
        }
        
        reg_response = requests.post(f"{BASE_URL}/upi/register", headers=headers, json=reg_data)
        if reg_response.status_code != 200:
            print(f"UPI Registration failed: {reg_response.text}")
            return False
        
        print("UPI registration successful")
        print(json.dumps(reg_response.json(), indent=2))
        
        # Step 2: Check balance
        print("\n--- Step 2: Check UPI Balance ---")
        
        balance_data = {
            "upi_id": TEST_UPI_ID
        }
        
        balance_response = requests.post(f"{BASE_URL}/upi/balance", headers=headers, json=balance_data)
        if balance_response.status_code != 200:
            print(f"UPI Balance check failed: {balance_response.text}")
            return False
        
        balance = balance_response.json().get("data", {}).get("balance", 0)
        print(f"Current balance: {balance}")
        print(json.dumps(balance_response.json(), indent=2))
        
        # Step 3: Generate QR code
        print("\n--- Step 3: Generate QR Code ---")
        
        qr_data = {
            "upi_id": TEST_UPI_ID,
            "amount": 50.75,
            "purpose": "Test payment",
            "qr_type": "STATIC"
        }
        
        qr_response = requests.post(f"{BASE_URL}/upi/qr/generate", headers=headers, json=qr_data)
        if qr_response.status_code != 200:
            print(f"QR code generation failed: {qr_response.text}")
            return False
        
        print("QR code generated successfully")
        # Not printing QR code data as it might be large
        
        # Step 4: Make a payment
        print("\n--- Step 4: Make UPI Payment ---")
        
        payment_data = {
            "sender_upi_id": TEST_UPI_ID,
            "receiver_upi_id": "merchant@upi",
            "amount": 100.50,
            "purpose": "Test payment",
            "upi_pin": "123456"
        }
        
        payment_response = requests.post(f"{BASE_URL}/upi/transaction", headers=headers, json=payment_data)
        if payment_response.status_code != 200:
            print(f"UPI Payment failed: {payment_response.text}")
            return False
        
        transaction_id = payment_response.json().get("data", {}).get("transaction_id")
        print(f"Payment successful, transaction ID: {transaction_id}")
        print(json.dumps(payment_response.json(), indent=2))
        
        # Step 5: Check transaction history
        print("\n--- Step 5: Check Transaction History ---")
        
        # Allow some time for transaction to be processed
        time.sleep(1)
        
        history_response = requests.get(
            f"{BASE_URL}/upi/transactions/history?upi_id={TEST_UPI_ID}&limit=5", 
            headers=headers
        )
        if history_response.status_code != 200:
            print(f"Transaction history check failed: {history_response.text}")
            return False
        
        transactions = history_response.json().get("data", {}).get("transactions", [])
        print(f"Found {len(transactions)} recent transactions")
        print(json.dumps(history_response.json(), indent=2))
        
        # Step 6: Create and respond to collect request
        print("\n--- Step 6: Process Collect Request ---")
        
        # Create collect request
        collect_data = {
            "requester_upi_id": "merchant@upi",
            "payer_upi_id": TEST_UPI_ID,
            "amount": 75.25,
            "purpose": "Test collect request"
        }
        
        collect_response = requests.post(f"{BASE_URL}/upi/collect/request", headers=headers, json=collect_data)
        if collect_response.status_code != 200:
            print(f"Create collect request failed: {collect_response.text}")
            return False
        
        collect_id = collect_response.json().get("data", {}).get("collect_id")
        print(f"Collect request created, ID: {collect_id}")
        
        # Respond to collect request
        if collect_id:
            response_data = {
                "collect_id": collect_id,
                "action": "ACCEPT",
                "upi_pin": "123456"
            }
            
            response = requests.post(f"{BASE_URL}/upi/collect/response", headers=headers, json=response_data)
            if response.status_code != 200:
                print(f"Collect request response failed: {response.text}")
                return False
                
            print("Collect request accepted successfully")
            print(json.dumps(response.json(), indent=2))
        
        # Step 7: Change UPI PIN
        print("\n--- Step 7: Change UPI PIN ---")
        
        pin_data = {
            "upi_id": TEST_UPI_ID,
            "old_pin": "123456",
            "new_pin": "654321",
            "confirm_pin": "654321"
        }
        
        pin_response = requests.post(f"{BASE_URL}/upi/pin/change", headers=headers, json=pin_data)
        if pin_response.status_code != 200:
            print(f"UPI PIN change failed: {pin_response.text}")
            return False
        
        print("UPI PIN changed successfully")
        print(json.dumps(pin_response.json(), indent=2))
        
        print("\n=== Complete UPI Flow Test Successful ===")
        return True
        
    except Exception as e:
        print(f"Test failed with exception: {e}")
        return False

def main():
    """Run the tests"""
    success = test_complete_upi_flow()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
