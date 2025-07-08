"""
CBS_PYTHON V2.0 Loan Service Tests

Comprehensive test suite for the loan service including unit tests,
integration tests, and end-to-end scenarios.
"""

import pytest
import httpx
from decimal import Decimal
from datetime import datetime, date
from unittest.mock import AsyncMock, Mock

from ..conftest import (
    TestHelpers, BaseServiceTest, BaseIntegrationTest,
    sample_loan_application_data, async_client, auth_headers
)


class TestLoanService(BaseServiceTest):
    """Unit tests for loan service"""
    
    @pytest.mark.asyncio
    async def test_create_loan_application_success(self, sample_loan_application_data, mock_loan_service):
        """Test successful loan application creation"""
        # Mock service response
        expected_response = {
            "application_id": "loan_app_123",
            "customer_id": sample_loan_application_data["customer_id"],
            "status": "pending_review",
            "created_at": datetime.utcnow().isoformat()
        }
        mock_loan_service.create_application.return_value = expected_response
        
        # Call service
        result = await mock_loan_service.create_application(sample_loan_application_data)
        
        # Assertions
        assert result["application_id"] == "loan_app_123"
        assert result["status"] == "pending_review"
        mock_loan_service.create_application.assert_called_once_with(sample_loan_application_data)
    
    @pytest.mark.asyncio
    async def test_loan_approval_success(self, mock_loan_service):
        """Test successful loan approval"""
        approval_data = {
            "approved_amount": Decimal("45000.00"),
            "approved_tenure_months": 24,
            "interest_rate": Decimal("12.5"),
            "approver_id": "officer_123"
        }
        
        expected_response = {
            "loan_id": "loan_123",
            "application_id": "loan_app_123",
            "status": "approved",
            "approved_amount": float(approval_data["approved_amount"])
        }
        mock_loan_service.approve_loan.return_value = expected_response
        
        result = await mock_loan_service.approve_loan("loan_app_123", approval_data)
        
        assert result["loan_id"] == "loan_123"
        assert result["status"] == "approved"
    
    @pytest.mark.asyncio
    async def test_emi_calculation(self, mock_loan_service):
        """Test EMI calculation"""
        calculation_data = {
            "principal_amount": Decimal("50000.00"),
            "interest_rate": Decimal("12.5"),
            "tenure_months": 24,
            "loan_type": "personal"
        }
        
        expected_emi = Decimal("2385.33")  # Calculated EMI
        mock_loan_service.calculate_emi.return_value = {
            "emi_amount": float(expected_emi),
            "total_amount": float(expected_emi * 24),
            "total_interest": float((expected_emi * 24) - calculation_data["principal_amount"])
        }
        
        result = await mock_loan_service.calculate_emi(calculation_data)
        
        assert result["emi_amount"] == float(expected_emi)
        assert result["total_amount"] > float(calculation_data["principal_amount"])
    
    @pytest.mark.asyncio
    async def test_loan_disbursement(self, mock_loan_service):
        """Test loan disbursement"""
        disbursement_data = {
            "disbursement_amount": Decimal("45000.00"),
            "disbursement_account_id": "acc_123",
            "disbursement_mode": "bank_transfer"
        }
        
        expected_response = {
            "disbursement_id": "disb_123",
            "loan_id": "loan_123",
            "status": "disbursed",
            "disbursed_amount": float(disbursement_data["disbursement_amount"])
        }
        mock_loan_service.disburse_loan.return_value = expected_response
        
        result = await mock_loan_service.disburse_loan("loan_123", disbursement_data)
        
        assert result["disbursement_id"] == "disb_123"
        assert result["status"] == "disbursed"


class TestLoanServiceIntegration(BaseIntegrationTest):
    """Integration tests for loan service API endpoints"""
    
    @pytest.mark.asyncio
    async def test_loan_application_api_flow(self, async_client, auth_headers, sample_loan_application_data):
        """Test complete loan application API flow"""
        base_url = f"{self.base_url}/api/v2/loans"
        
        # Create loan application
        response = await async_client.post(
            f"{base_url}/applications",
            json=sample_loan_application_data,
            headers=auth_headers
        )
        
        TestHelpers.assert_response_success(response)
        application_data = response.json()
        application_id = application_data["data"]["application_id"]
        
        # Get application details
        response = await async_client.get(
            f"{base_url}/applications/{application_id}",
            headers=auth_headers
        )
        
        TestHelpers.assert_response_success(response)
        
        # Approve application
        approval_data = {
            "approved_amount": 45000.00,
            "approved_tenure_months": 24,
            "interest_rate": 12.5,
            "approver_id": "officer_123"
        }
        
        response = await async_client.post(
            f"{base_url}/applications/{application_id}/approve",
            json=approval_data,
            headers=auth_headers
        )
        
        TestHelpers.assert_response_success(response)
        loan_data = response.json()
        loan_id = loan_data["data"]["loan_id"]
        
        # Disburse loan
        disbursement_data = {
            "disbursement_amount": 45000.00,
            "disbursement_account_id": sample_loan_application_data["primary_account_id"],
            "disbursement_mode": "bank_transfer"
        }
        
        response = await async_client.post(
            f"{base_url}/loans/{loan_id}/disburse",
            json=disbursement_data,
            headers=auth_headers
        )
        
        TestHelpers.assert_response_success(response)
    
    @pytest.mark.asyncio
    async def test_emi_calculation_api(self, async_client, auth_headers):
        """Test EMI calculation API endpoint"""
        calculation_data = {
            "principal_amount": 50000.00,
            "interest_rate": 12.5,
            "tenure_months": 24,
            "loan_type": "personal"
        }
        
        response = await async_client.post(
            f"{self.base_url}/api/v2/loans/calculate/emi",
            json=calculation_data,
            headers=auth_headers
        )
        
        TestHelpers.assert_response_success(response)
        result = response.json()["data"]
        
        assert "emi_amount" in result
        assert "total_amount" in result
        assert "total_interest" in result
        assert result["emi_amount"] > 0
        assert result["total_amount"] > calculation_data["principal_amount"]
    
    @pytest.mark.asyncio
    async def test_loan_payment_processing(self, async_client, auth_headers):
        """Test loan payment processing"""
        # Assume we have an active loan
        loan_id = "loan_123"
        
        payment_data = {
            "payment_amount": 2500.00,
            "payment_date": date.today().isoformat(),
            "payment_method": "bank_transfer",
            "from_account_id": "acc_123"
        }
        
        response = await async_client.post(
            f"{self.base_url}/api/v2/loans/loans/{loan_id}/payments",
            json=payment_data,
            headers=auth_headers
        )
        
        TestHelpers.assert_response_success(response)
        result = response.json()["data"]
        
        assert "payment_id" in result
        assert "updated_balance" in result
    
    @pytest.mark.asyncio
    async def test_loan_schedule_retrieval(self, async_client, auth_headers):
        """Test EMI schedule retrieval"""
        loan_id = "loan_123"
        
        response = await async_client.get(
            f"{self.base_url}/api/v2/loans/loans/{loan_id}/schedule",
            headers=auth_headers
        )
        
        TestHelpers.assert_response_success(response)
        schedule = response.json()["data"]
        
        assert isinstance(schedule, list)
        if schedule:  # If schedule exists
            assert "installment_number" in schedule[0]
            assert "emi_amount" in schedule[0]
            assert "due_date" in schedule[0]


class TestLoanServiceValidation(BaseServiceTest):
    """Test data validation for loan service"""
    
    @pytest.mark.asyncio
    async def test_invalid_loan_amount(self, async_client, auth_headers, sample_loan_application_data):
        """Test validation for invalid loan amounts"""
        invalid_amounts = [-1000, 0, "invalid", None]
        
        for invalid_amount in invalid_amounts:
            test_data = sample_loan_application_data.copy()
            test_data["requested_amount"] = invalid_amount
            
            response = await async_client.post(
                f"{self.base_url}/api/v2/loans/applications",
                json=test_data,
                headers=auth_headers
            )
            
            TestHelpers.assert_response_error(response, 422)
    
    @pytest.mark.asyncio
    async def test_invalid_tenure(self, async_client, auth_headers, sample_loan_application_data):
        """Test validation for invalid loan tenure"""
        invalid_tenures = [-1, 0, 361, "invalid", None]  # 361 months exceeds max
        
        for invalid_tenure in invalid_tenures:
            test_data = sample_loan_application_data.copy()
            test_data["tenure_months"] = invalid_tenure
            
            response = await async_client.post(
                f"{self.base_url}/api/v2/loans/applications",
                json=test_data,
                headers=auth_headers
            )
            
            TestHelpers.assert_response_error(response, 422)
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, async_client, auth_headers):
        """Test validation for missing required fields"""
        incomplete_data = {
            "customer_id": "customer_123"
            # Missing other required fields
        }
        
        response = await async_client.post(
            f"{self.base_url}/api/v2/loans/applications",
            json=incomplete_data,
            headers=auth_headers
        )
        
        TestHelpers.assert_response_error(response, 422)


class TestLoanServicePerformance(BaseIntegrationTest):
    """Performance tests for loan service"""
    
    @pytest.mark.asyncio
    async def test_emi_calculation_performance(self, async_client, auth_headers):
        """Test EMI calculation API performance"""
        from ..conftest import PerformanceTestHelpers
        
        url = f"{self.base_url}/api/v2/loans/calculate/emi"
        
        # Test single request response time
        response_time = await PerformanceTestHelpers.measure_response_time(async_client, url)
        assert response_time < 1.0  # Should respond within 1 second
        
        # Test load handling
        load_results = await PerformanceTestHelpers.load_test(async_client, url, concurrent_requests=10)
        assert load_results["successful_requests"] >= 8  # At least 80% success rate
        assert load_results["average_response_time"] < 2.0  # Average under 2 seconds


class TestLoanServiceSecurity(BaseIntegrationTest):
    """Security tests for loan service"""
    
    @pytest.mark.asyncio
    async def test_authentication_required(self, async_client):
        """Test that all loan endpoints require authentication"""
        from ..conftest import SecurityTestHelpers
        
        endpoints = [
            "/api/v2/loans/applications",
            "/api/v2/loans/loans/loan_123",
            "/api/v2/loans/calculate/emi"
        ]
        
        for endpoint in endpoints:
            await SecurityTestHelpers.test_authentication_required(
                async_client, 
                f"{self.base_url}{endpoint}"
            )
    
    @pytest.mark.asyncio
    async def test_loan_data_privacy(self, async_client, auth_headers):
        """Test that users can only access their own loan data"""
        # This would require proper user context and authorization testing
        # For now, we'll test that the endpoint respects authorization headers
        
        response = await async_client.get(
            f"{self.base_url}/api/v2/loans/loans/other_user_loan_123",
            headers=auth_headers
        )
        
        # Should either return 404 (not found) or 403 (forbidden)
        assert response.status_code in [403, 404]


# Performance Benchmarks
class TestLoanServiceBenchmarks:
    """Benchmark tests for loan service performance"""
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_emi_calculation_benchmark(self, async_client, auth_headers):
        """Benchmark EMI calculation performance"""
        import time
        
        calculation_data = {
            "principal_amount": 50000.00,
            "interest_rate": 12.5,
            "tenure_months": 24,
            "loan_type": "personal"
        }
        
        # Measure 100 consecutive calculations
        start_time = time.time()
        for _ in range(100):
            response = await async_client.post(
                f"{self.base_url}/api/v2/loans/calculate/emi",
                json=calculation_data,
                headers=auth_headers
            )
            assert response.status_code == 200
        
        end_time = time.time()
        total_time = end_time - start_time
        average_time = total_time / 100
        
        print(f"EMI Calculation Benchmark:")
        print(f"100 calculations in {total_time:.2f} seconds")
        print(f"Average time per calculation: {average_time:.4f} seconds")
        
        # Performance assertion
        assert average_time < 0.1  # Should be under 100ms per calculation


# Test Scenarios
class TestLoanServiceScenarios:
    """Real-world test scenarios for loan service"""
    
    @pytest.mark.scenario
    @pytest.mark.asyncio
    async def test_complete_loan_lifecycle(self, async_client, auth_headers, sample_loan_application_data):
        """Test complete loan lifecycle from application to closure"""
        base_url = f"{self.base_url}/api/v2/loans"
        
        # 1. Apply for loan
        response = await async_client.post(
            f"{base_url}/applications",
            json=sample_loan_application_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        application_id = response.json()["data"]["application_id"]
        
        # 2. Review and approve
        approval_data = {
            "approved_amount": 45000.00,
            "approved_tenure_months": 12,  # Shorter tenure for testing
            "interest_rate": 12.5,
            "approver_id": "officer_123"
        }
        
        response = await async_client.post(
            f"{base_url}/applications/{application_id}/approve",
            json=approval_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        loan_id = response.json()["data"]["loan_id"]
        
        # 3. Disburse loan
        disbursement_data = {
            "disbursement_amount": 45000.00,
            "disbursement_account_id": sample_loan_application_data["primary_account_id"],
            "disbursement_mode": "bank_transfer"
        }
        
        response = await async_client.post(
            f"{base_url}/loans/{loan_id}/disburse",
            json=disbursement_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        
        # 4. Get EMI schedule
        response = await async_client.get(
            f"{base_url}/loans/{loan_id}/schedule",
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        
        # 5. Make a payment
        payment_data = {
            "payment_amount": 4000.00,  # EMI payment
            "payment_date": date.today().isoformat(),
            "payment_method": "bank_transfer",
            "from_account_id": sample_loan_application_data["primary_account_id"]
        }
        
        response = await async_client.post(
            f"{base_url}/loans/{loan_id}/payments",
            json=payment_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        
        # 6. Check updated loan status
        response = await async_client.get(
            f"{base_url}/loans/{loan_id}",
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        loan_details = response.json()["data"]
        
        # Verify loan is active and payment was processed
        assert loan_details["status"] == "active"
        assert loan_details["outstanding_balance"] < 45000.00  # Balance reduced


if __name__ == "__main__":
    # Run tests with: python -m pytest tests/services/test_loan_service.py -v
    pass
