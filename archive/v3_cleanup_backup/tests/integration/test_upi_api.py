"""
Test script for the UPI API endpoints
"""

import requests
import json
import base64
import hmac
import hashlib
import time

# Add parent directory to path

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


BASE_URL = "http://localhost:5000/api/v1"

# Test data
TEST_CUSTOMER_ID = "CUST123456"
TEST_PASSWORD = "Password123!"
TEST_DEVICE_ID = "TEST_DEVICE_001"
TEST_UPI_ID = "testuser@sbi"
TEST_ACCOUNT_NUMBER = "12345678901234"

def get_auth_token():
    """Get authentication token"""
    login_data = {
        "customer_id": TEST_CUSTOMER_ID,
        "password": TEST_PASSWORD,
        "device_id": TEST_DEVICE_ID,
        "device_info": {
            "device_model": "Test Model",
            "os_version": "Test OS 1.0",
            "app_version": "1.0.0"
        }
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        return response.json()["data"]["token"]
    else:
        print(f"Login failed: {response.text}")
        return None

def test_upi_registration(token):
    """Test UPI registration"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "account_number": TEST_ACCOUNT_NUMBER,
        "username": "testuser",
        "device_info": {
            "device_id": TEST_DEVICE_ID,
            "device_model": "Test Model",
            "os_version": "Test OS 1.0"
        },
        "upi_pin": "123456"
    }
    
    response = requests.post(f"{BASE_URL}/upi/register", headers=headers, json=data)
    print(f"UPI Registration: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_upi_balance(token):
    """Test UPI balance check"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "upi_id": TEST_UPI_ID
    }
    
    response = requests.post(f"{BASE_URL}/upi/balance", headers=headers, json=data)
    print(f"UPI Balance: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_upi_transaction(token):
    """Test UPI transaction"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "sender_upi_id": TEST_UPI_ID,
        "receiver_upi_id": "merchant@upi",
        "amount": 100.50,
        "purpose": "Test payment",
        "upi_pin": "123456"
    }
    
    response = requests.post(f"{BASE_URL}/upi/transaction", headers=headers, json=data)
    print(f"UPI Transaction: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_generate_qr(token):
    """Test QR code generation"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "upi_id": TEST_UPI_ID,
        "amount": 50.75,
        "purpose": "Test QR payment",
        "qr_type": "STATIC"
    }
    
    response = requests.post(f"{BASE_URL}/upi/qr/generate", headers=headers, json=data)
    print(f"Generate QR: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_transaction_history(token):
    """Test transaction history"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/upi/transactions/history?upi_id={TEST_UPI_ID}&limit=10&offset=0", 
        headers=headers
    )
    print(f"Transaction History: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_change_pin(token):
    """Test UPI PIN change"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "upi_id": TEST_UPI_ID,
        "old_pin": "123456",
        "new_pin": "654321",
        "confirm_pin": "654321"
    }
    
    response = requests.post(f"{BASE_URL}/upi/pin/change", headers=headers, json=data)
    print(f"Change PIN: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_upi_collect_request(token):
    """Test UPI collect request"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "requester_upi_id": TEST_UPI_ID,
        "payer_upi_id": "payer@upi",
        "amount": 75.25,
        "purpose": "Test collect request"
    }
    
    response = requests.post(f"{BASE_URL}/upi/collect/request", headers=headers, json=data)
    print(f"UPI Collect Request: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_upi_collect_response(token, collect_id):
    """Test responding to a UPI collect request"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "collect_id": collect_id,
        "action": "ACCEPT",
        "upi_pin": "123456"
    }
    
    response = requests.post(f"{BASE_URL}/upi/collect/response", headers=headers, json=data)
    print(f"UPI Collect Response: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def test_get_pending_collects(token):
    """Test getting pending collect requests"""
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/upi/collect/pending?upi_id={TEST_UPI_ID}",
        headers=headers
    )
    print(f"Pending Collect Requests: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def run_tests():
    """Run all tests"""
    token = get_auth_token()
    if not token:
        print("Failed to get auth token. Tests aborted.")
        return
        
    print("\n=== Running UPI API Tests ===\n")
    
    # Run tests
    test_upi_registration(token)
    test_upi_balance(token)
    test_upi_transaction(token)
    test_generate_qr(token)
    test_transaction_history(token)
    test_change_pin(token)
    collect_request_response = test_upi_collect_request(token)
    if "data" in collect_request_response and "collect_id" in collect_request_response["data"]:
        collect_id = collect_request_response["data"]["collect_id"]
        test_upi_collect_response(token, collect_id)
    test_get_pending_collects(token)
    
    print("\n=== Tests Complete ===")

if __name__ == "__main__":
    run_tests()