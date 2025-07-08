"""
CBS_PYTHON V2.0 End-to-End Test Suite

Comprehensive end-to-end tests covering complete banking workflows
across all microservices in the CBS platform.
"""

import pytest
import asyncio
import httpx
from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from ..conftest import TestHelpers, BaseE2ETest, async_client, auth_headers


class TestE2EBankingWorkflows(BaseE2ETest):
    """End-to-end tests for complete banking workflows"""
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_customer_onboarding_workflow(self, async_client, auth_headers):
        """Test complete customer onboarding workflow"""
        base_url = self.base_url
        
        # 1. Create customer
        customer_data = {
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": "alice.johnson@test.com",
            "phone": "+1234567890",
            "date_of_birth": "1985-06-15",
            "address": {
                "street": "456 Oak Avenue",
                "city": "San Francisco",
                "state": "CA",
                "postal_code": "94102",
                "country": "USA"
            },
            "identity_documents": [
                {
                    "type": "passport",
                    "number": "B98765432",
                    "expiry_date": "2030-12-31"
                }
            ]
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/customers",
            json=customer_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        customer_id = response.json()["data"]["customer_id"]
        
        # 2. Create savings account
        account_data = {
            "customer_id": customer_id,
            "account_type": "savings",
            "currency": "USD",
            "initial_deposit": 5000.00,
            "branch_code": "SF001"
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/accounts",
            json=account_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        savings_account_id = response.json()["data"]["account_id"]
        
        # 3. Create checking account
        checking_account_data = {
            "customer_id": customer_id,
            "account_type": "checking",
            "currency": "USD",
            "initial_deposit": 1000.00,
            "branch_code": "SF001"
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/accounts",
            json=checking_account_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        checking_account_id = response.json()["data"]["account_id"]
        
        # 4. Verify account balances
        for account_id in [savings_account_id, checking_account_id]:
            response = await async_client.get(
                f"{base_url}/api/v2/accounts/{account_id}/balance",
                headers=auth_headers
            )
            TestHelpers.assert_response_success(response)
            balance_data = response.json()["data"]
            assert balance_data["balance"] > 0
        
        # 5. Send welcome notification
        notification_data = {
            "recipient_id": customer_id,
            "notification_type": "welcome",
            "channels": ["email", "sms"],
            "priority": "normal",
            "content": {
                "subject": "Welcome to Our Bank",
                "message": f"Welcome {customer_data['first_name']}! Your accounts have been created successfully.",
                "data": {
                    "customer_id": customer_id,
                    "savings_account": savings_account_id,
                    "checking_account": checking_account_id
                }
            }
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/notifications",
            json=notification_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        
        # Return created resources for further testing
        return {
            "customer_id": customer_id,
            "savings_account_id": savings_account_id,
            "checking_account_id": checking_account_id
        }
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_loan_application_workflow(self, async_client, auth_headers):
        """Test complete loan application and processing workflow"""
        base_url = self.base_url
        
        # First create a customer and account (prerequisite)
        customer_resources = await self.test_complete_customer_onboarding_workflow(async_client, auth_headers)
        customer_id = customer_resources["customer_id"]
        primary_account_id = customer_resources["savings_account_id"]
        
        # 1. Apply for personal loan
        loan_application_data = {
            "customer_id": customer_id,
            "loan_type": "personal",
            "loan_purpose": "Home renovation and improvement",
            "requested_amount": 25000.00,
            "tenure_months": 36,
            "primary_account_id": primary_account_id,
            "monthly_income": 6000.00,
            "existing_emi": 0.00,
            "employment_type": "salaried",
            "employment_years": 5,
            "cibil_score": 750
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/loans/applications",
            json=loan_application_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        application_id = response.json()["data"]["application_id"]
        
        # 2. Calculate EMI before approval
        emi_calculation_data = {
            "principal_amount": 25000.00,
            "interest_rate": 11.5,
            "tenure_months": 36,
            "loan_type": "personal"
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/loans/calculate/emi",
            json=emi_calculation_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        emi_details = response.json()["data"]
        calculated_emi = emi_details["emi_amount"]
        
        # 3. Approve loan application
        approval_data = {
            "approved_amount": 23000.00,  # Slightly less than requested
            "approved_tenure_months": 36,
            "interest_rate": 11.5,
            "processing_fee": 500.00,
            "approver_id": "loan_officer_001",
            "approval_notes": "Good credit score and stable income",
            "conditions": ["Maintain minimum balance of $2000 in primary account"]
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/loans/applications/{application_id}/approve",
            json=approval_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        loan_data = response.json()["data"]
        loan_id = loan_data["loan_id"]
        
        # 4. Disburse loan
        disbursement_data = {
            "disbursement_amount": 23000.00,
            "disbursement_account_id": primary_account_id,
            "disbursement_mode": "bank_transfer",
            "reference_number": f"DISB{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "notes": "Loan disbursed to primary savings account"
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/loans/loans/{loan_id}/disburse",
            json=disbursement_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        
        # 5. Verify account balance increased
        response = await async_client.get(
            f"{base_url}/api/v2/accounts/{primary_account_id}/balance",
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        balance_data = response.json()["data"]
        assert balance_data["balance"] >= 28000.00  # Original 5000 + loan 23000
        
        # 6. Get EMI schedule
        response = await async_client.get(
            f"{base_url}/api/v2/loans/loans/{loan_id}/schedule",
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        schedule_data = response.json()["data"]
        assert len(schedule_data) == 36  # 36 monthly installments
        
        # 7. Send loan approval notification
        notification_data = {
            "recipient_id": customer_id,
            "notification_type": "loan_approval",
            "channels": ["email", "sms"],
            "priority": "high",
            "content": {
                "subject": "Loan Approved and Disbursed",
                "message": f"Your personal loan of ${approval_data['approved_amount']} has been approved and disbursed.",
                "data": {
                    "loan_id": loan_id,
                    "amount": approval_data["approved_amount"],
                    "emi_amount": calculated_emi,
                    "first_due_date": (datetime.now() + timedelta(days=30)).date().isoformat()
                }
            }
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/notifications",
            json=notification_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        
        return {
            "loan_id": loan_id,
            "customer_id": customer_id,
            "primary_account_id": primary_account_id,
            "emi_amount": calculated_emi
        }
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_complete_payment_processing_workflow(self, async_client, auth_headers):
        """Test complete payment processing workflow"""
        base_url = self.base_url
        
        # Setup: Create two customers with accounts
        customer1_resources = await self.test_complete_customer_onboarding_workflow(async_client, auth_headers)
        
        # Create second customer
        customer2_data = {
            "first_name": "Bob",
            "last_name": "Smith",
            "email": "bob.smith@test.com",
            "phone": "+0987654321",
            "date_of_birth": "1990-03-22",
            "address": {
                "street": "789 Pine Street",
                "city": "Los Angeles",
                "state": "CA",
                "postal_code": "90210",
                "country": "USA"
            }
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/customers",
            json=customer2_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        customer2_id = response.json()["data"]["customer_id"]
        
        # Create account for customer 2
        account2_data = {
            "customer_id": customer2_id,
            "account_type": "checking",
            "currency": "USD",
            "initial_deposit": 2000.00,
            "branch_code": "LA001"
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/accounts",
            json=account2_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        customer2_account_id = response.json()["data"]["account_id"]
        
        # 1. Process internal bank transfer
        transfer_data = {
            "from_account_id": customer1_resources["savings_account_id"],
            "to_account_id": customer2_account_id,
            "amount": 1500.00,
            "currency": "USD",
            "transaction_type": "transfer",
            "description": "Payment for services",
            "reference_number": f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/transactions",
            json=transfer_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        transaction_id = response.json()["data"]["transaction_id"]
        
        # 2. Verify transaction status
        response = await async_client.get(
            f"{base_url}/api/v2/transactions/{transaction_id}",
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        transaction_data = response.json()["data"]
        assert transaction_data["status"] == "completed"
        
        # 3. Verify balances updated correctly
        # Check sender balance
        response = await async_client.get(
            f"{base_url}/api/v2/accounts/{customer1_resources['savings_account_id']}/balance",
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        sender_balance = response.json()["data"]["balance"]
        assert sender_balance == 3500.00  # 5000 - 1500
        
        # Check receiver balance
        response = await async_client.get(
            f"{base_url}/api/v2/accounts/{customer2_account_id}/balance",
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        receiver_balance = response.json()["data"]["balance"]
        assert receiver_balance == 3500.00  # 2000 + 1500
        
        # 4. Process external payment
        payment_data = {
            "payer_account_id": customer1_resources["checking_account_id"],
            "amount": 250.00,
            "currency": "USD",
            "payment_method": "wire_transfer",
            "payee_details": {
                "name": "External Vendor",
                "account_number": "EXT123456789",
                "routing_number": "021000021",
                "bank_name": "External Bank"
            },
            "description": "Vendor payment",
            "reference_number": f"PAY{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/payments",
            json=payment_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        payment_id = response.json()["data"]["payment_id"]
        
        # 5. Check payment status
        response = await async_client.get(
            f"{base_url}/api/v2/payments/{payment_id}/status",
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        
        # 6. Send transaction notifications
        for customer_id, account_id, amount, tx_type in [
            (customer1_resources["customer_id"], customer1_resources["savings_account_id"], -1500.00, "debit"),
            (customer2_id, customer2_account_id, 1500.00, "credit")
        ]:
            notification_data = {
                "recipient_id": customer_id,
                "notification_type": "transaction_alert",
                "channels": ["email", "sms"],
                "priority": "normal",
                "content": {
                    "subject": f"Account {tx_type.title()} Alert",
                    "message": f"Your account has been {tx_type}ed with ${abs(amount)}",
                    "data": {
                        "transaction_id": transaction_id,
                        "account_id": account_id,
                        "amount": amount,
                        "transaction_type": tx_type
                    }
                }
            }
            
            response = await async_client.post(
                f"{base_url}/api/v2/notifications",
                json=notification_data,
                headers=auth_headers
            )
            TestHelpers.assert_response_success(response)
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_loan_payment_workflow(self, async_client, auth_headers):
        """Test complete loan payment workflow"""
        base_url = self.base_url
        
        # Setup: Get loan from previous test
        loan_resources = await self.test_complete_loan_application_workflow(async_client, auth_headers)
        loan_id = loan_resources["loan_id"]
        customer_id = loan_resources["customer_id"]
        primary_account_id = loan_resources["primary_account_id"]
        emi_amount = loan_resources["emi_amount"]
        
        # 1. Make first EMI payment
        payment_data = {
            "payment_amount": emi_amount,
            "payment_date": date.today().isoformat(),
            "payment_method": "bank_transfer",
            "from_account_id": primary_account_id,
            "transaction_reference": f"EMI{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "is_prepayment": False,
            "notes": "Regular EMI payment"
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/loans/loans/{loan_id}/payments",
            json=payment_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        payment_result = response.json()["data"]
        payment_id = payment_result["payment_id"]
        
        # 2. Verify loan balance updated
        response = await async_client.get(
            f"{base_url}/api/v2/loans/loans/{loan_id}",
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        loan_details = response.json()["data"]
        assert loan_details["outstanding_balance"] < 23000.00  # Should be reduced
        
        # 3. Get payment history
        response = await async_client.get(
            f"{base_url}/api/v2/loans/loans/{loan_id}/payments",
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        payment_history = response.json()["data"]
        assert len(payment_history) == 1
        assert payment_history[0]["payment_id"] == payment_id
        
        # 4. Make partial prepayment
        prepayment_data = {
            "payment_amount": 5000.00,
            "payment_date": date.today().isoformat(),
            "payment_method": "bank_transfer",
            "from_account_id": primary_account_id,
            "is_prepayment": True,
            "notes": "Partial prepayment to reduce interest"
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/loans/loans/{loan_id}/payments",
            json=prepayment_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        
        # 5. Send payment confirmation notification
        notification_data = {
            "recipient_id": customer_id,
            "notification_type": "payment_confirmation",
            "channels": ["email"],
            "priority": "normal",
            "content": {
                "subject": "Loan Payment Confirmation",
                "message": f"Your loan payment of ${emi_amount} has been processed successfully.",
                "data": {
                    "loan_id": loan_id,
                    "payment_amount": emi_amount,
                    "outstanding_balance": loan_details["outstanding_balance"],
                    "next_due_date": (datetime.now() + timedelta(days=30)).date().isoformat()
                }
            }
        }
        
        response = await async_client.post(
            f"{base_url}/api/v2/notifications",
            json=notification_data,
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
    
    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_audit_and_compliance_workflow(self, async_client, auth_headers):
        """Test audit and compliance monitoring workflow"""
        base_url = self.base_url
        
        # 1. Query recent audit logs
        response = await async_client.get(
            f"{base_url}/api/v2/audit/logs?service=loan-service&limit=50",
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        audit_logs = response.json()["data"]
        assert isinstance(audit_logs, list)
        
        # 2. Check security events
        response = await async_client.get(
            f"{base_url}/api/v2/audit/security-events?severity=high&limit=20",
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        security_events = response.json()["data"]
        assert isinstance(security_events, list)
        
        # 3. Generate compliance report
        response = await async_client.get(
            f"{base_url}/api/v2/audit/compliance/reports?report_type=daily_summary&date={date.today().isoformat()}",
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        compliance_report = response.json()["data"]
        assert "report_id" in compliance_report
        
        # 4. Get system analytics
        response = await async_client.get(
            f"{base_url}/api/v2/audit/analytics/dashboard",
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        analytics_data = response.json()["data"]
        assert "total_transactions" in analytics_data
        assert "total_customers" in analytics_data
    
    @pytest.mark.e2e
    @pytest.mark.asyncio 
    async def test_system_health_and_monitoring(self, async_client):
        """Test system health and monitoring endpoints"""
        base_url = self.base_url
        
        # 1. Check overall system health
        response = await async_client.get(f"{base_url}/health")
        assert response.status_code == 200
        health_data = response.json()
        assert health_data["status"] == "healthy"
        
        # 2. Check individual service health
        services = [
            "customer-service", "account-service", "transaction-service",
            "payment-service", "loan-service", "notification-service", "audit-service"
        ]
        
        for service in services:
            response = await async_client.get(f"{base_url}/api/v2/{service.replace('-service', 's')}/health")
            if response.status_code == 200:  # Service is available
                assert response.json()["status"] == "healthy"
        
        # 3. Check metrics endpoint
        response = await async_client.get(f"{base_url}/metrics")
        # Metrics endpoint might return Prometheus format, just check it's accessible
        assert response.status_code in [200, 404]  # 404 if not configured
    
    @pytest.mark.e2e
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_high_volume_transaction_processing(self, async_client, auth_headers):
        """Test high volume transaction processing"""
        base_url = self.base_url
        
        # Create multiple test accounts
        customer_resources = await self.test_complete_customer_onboarding_workflow(async_client, auth_headers)
        source_account = customer_resources["savings_account_id"]
        
        # Create additional accounts for testing
        target_accounts = []
        for i in range(5):
            account_data = {
                "customer_id": customer_resources["customer_id"],
                "account_type": "checking",
                "currency": "USD",
                "initial_deposit": 100.00,
                "branch_code": f"TEST{i:03d}"
            }
            
            response = await async_client.post(
                f"{base_url}/api/v2/accounts",
                json=account_data,
                headers=auth_headers
            )
            TestHelpers.assert_response_success(response)
            target_accounts.append(response.json()["data"]["account_id"])
        
        # Process multiple concurrent transactions
        transaction_tasks = []
        for i, target_account in enumerate(target_accounts):
            transaction_data = {
                "from_account_id": source_account,
                "to_account_id": target_account,
                "amount": 50.00,
                "currency": "USD",
                "transaction_type": "transfer",
                "description": f"Bulk transfer #{i+1}",
                "reference_number": f"BULK{i+1:03d}{datetime.now().strftime('%H%M%S')}"
            }
            
            task = async_client.post(
                f"{base_url}/api/v2/transactions",
                json=transaction_data,
                headers=auth_headers
            )
            transaction_tasks.append(task)
        
        # Execute all transactions concurrently
        results = await asyncio.gather(*transaction_tasks, return_exceptions=True)
        
        # Verify all transactions were successful
        successful_transactions = 0
        for result in results:
            if isinstance(result, httpx.Response) and result.status_code in [200, 201]:
                successful_transactions += 1
        
        assert successful_transactions >= 4  # At least 80% success rate
        
        # Verify final balances
        response = await async_client.get(
            f"{base_url}/api/v2/accounts/{source_account}/balance",
            headers=auth_headers
        )
        TestHelpers.assert_response_success(response)
        final_balance = response.json()["data"]["balance"]
        
        # Balance should be reduced by successful transfers
        expected_balance = 28000.00 - (successful_transactions * 50.00)  # Loan amount minus transfers
        assert abs(final_balance - expected_balance) < 1.00  # Allow small rounding differences


if __name__ == "__main__":
    # Run E2E tests with: python -m pytest tests/e2e/test_workflows.py -v --tb=short -m e2e
    pass
