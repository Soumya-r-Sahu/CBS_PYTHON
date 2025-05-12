"""
API Integration Tests for the Core Banking System

This module tests the integration between API endpoints and the backend services.
"""

import pytest
import json
from datetime import datetime

class TestAPIIntegration:
    """Integration tests for API endpoints"""
    
    def test_api_health_check(self, api_client):
        """Test API health endpoint"""
        response = api_client.get("health")
        
        assert response.status_code == 200
        assert response.json().get("status") == "UP"
    
    def test_authentication_flow(self, api_client):
        """Test authentication flow"""
        # Login
        success = api_client.login()
        assert success, "Login failed"
        
        # Verify token works
        response = api_client.get("accounts")
        assert response.status_code == 200, "Token authentication failed"
        
    def test_upi_registration_flow(self, api_client):
        """Test UPI registration flow"""
        # Login
        success = api_client.login()
        assert success, "Login failed"
        
        # Register UPI ID
        data = {
            "account_number": "12345678901234",
            "username": f"testuser{datetime.now().strftime('%H%M%S')}",
            "device_info": {
                "device_id": "TEST_DEVICE_001",
                "device_model": "Test Model",
                "os_version": "Test OS 1.0"
            },
            "upi_pin": "123456"
        }
        
        response = api_client.post("upi/register", data)
        assert response.status_code == 200, f"UPI registration failed: {response.text}"
        
        # Extract UPI ID from response
        resp_data = response.json()
        assert resp_data.get("status") == "SUCCESS", "UPI registration status not success"
        
        upi_id = resp_data.get("data", {}).get("upi_id")
        assert upi_id is not None, "UPI ID not returned in response"
        
        # Check UPI balance
        balance_data = {
            "upi_id": upi_id
        }
        balance_response = api_client.post("upi/balance", balance_data)
        assert balance_response.status_code == 200, f"UPI balance check failed: {balance_response.text}"
        
        # Verify we got balance info
        balance_resp = balance_response.json()
        assert balance_resp.get("status") == "SUCCESS", "Balance check status not success"
        assert "balance" in balance_resp.get("data", {}), "Balance not in response"
        
    def test_transaction_history(self, api_client):
        """Test transaction history endpoint"""
        # Login
        success = api_client.login()
        assert success, "Login failed"
        
        # Get transaction history
        params = {
            "account_number": "12345678901234",
            "from_date": (datetime.now().replace(day=1)).strftime("%Y-%m-%d"),
            "to_date": datetime.now().strftime("%Y-%m-%d"),
            "limit": 10
        }
        
        response = api_client.get("transactions/history", params)
        assert response.status_code == 200, f"Transaction history failed: {response.text}"
        
        # Verify response structure
        resp_data = response.json()
        assert resp_data.get("status") in ["SUCCESS", "NO_DATA"], "Unexpected status in response"
        assert "transactions" in resp_data.get("data", {}), "Transactions not in response"
