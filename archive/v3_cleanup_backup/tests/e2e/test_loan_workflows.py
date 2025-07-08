"""
Core Banking Loan End-to-End Tests

This module contains end-to-end tests for loan workflows.
These tests verify complete loan business processes from start to finish.
"""

import pytest
import unittest
import requests
import json
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Base URL for API
API_BASE_URL = "http://localhost:5000/api/v1"


@pytest.mark.skipif(
    os.environ.get("SKIP_E2E_TESTS") == "1",
    reason="E2E tests are disabled"
)
class TestLoanApplicationWorkflow(unittest.TestCase):
    """End-to-end tests for loan application workflow."""
    
    def setUp(self):
        """Set up before each test."""
        # Create a test customer
        self.customer = {
            "customer_id": "CUS_LOAN_E2E",
            "first_name": "Loan",
            "last_name": "Test",
            "email": "loan.test@example.com",
            "phone": "1234567890",
            "address": "123 Loan St, Test City",
            "date_of_birth": "1990-01-01"
        }
        
        # Create the customer
        response = requests.post(f"{API_BASE_URL}/customers", json=self.customer)
        self.assertEqual(response.status_code, 201)
        
        # Create an account for the customer
        self.account = {
            "account_id": "ACC_LOAN_E2E",
            "customer_id": "CUS_LOAN_E2E",
            "account_type": "SAVINGS",
            "balance": 10000.00,
            "currency": "USD",
            "status": "ACTIVE"
        }
        
        # Create the account
        response = requests.post(f"{API_BASE_URL}/accounts", json=self.account)
        self.assertEqual(response.status_code, 201)
    
    def tearDown(self):
        """Clean up after each test."""
        # Delete loan if it exists
        if hasattr(self, "loan_id"):
            requests.delete(f"{API_BASE_URL}/loans/{self.loan_id}")
        
        # Delete loan application if it exists
        if hasattr(self, "application_id"):
            requests.delete(f"{API_BASE_URL}/loans/applications/{self.application_id}")
        
        # Delete account
        requests.delete(f"{API_BASE_URL}/accounts/{self.account['account_id']}")
        
        # Delete customer
        requests.delete(f"{API_BASE_URL}/customers/{self.customer['customer_id']}")
    
    def test_personal_loan_application_to_disbursal(self):
        """Test the complete personal loan workflow from application to disbursal."""
        # Step 1: Submit loan application
        loan_application = {
            "customer_id": self.customer["customer_id"],
            "loan_type": "PERSONAL",
            "requested_amount": 50000.00,
            "term_months": 24,
            "purpose": "Home Renovation",
            "employment_status": "EMPLOYED",
            "monthly_income": 8000.00
        }
        
        response = requests.post(f"{API_BASE_URL}/loans/applications", json=loan_application)
        self.assertEqual(response.status_code, 201)
        
        # Get application ID
        application_data = response.json()
        self.application_id = application_data["application_id"]
        
        # Step 2: Check application status
        response = requests.get(f"{API_BASE_URL}/loans/applications/{self.application_id}")
        self.assertEqual(response.status_code, 200)
        application = response.json()
        self.assertEqual(application["status"], "PENDING")
        
        # Step 3: Submit supporting documents
        documents = {
            "application_id": self.application_id,
            "documents": [
                {
                    "document_type": "ID_PROOF",
                    "document_name": "passport.pdf",
                    "document_content": "base64encodedcontent"
                },
                {
                    "document_type": "INCOME_PROOF",
                    "document_name": "salary_slip.pdf",
                    "document_content": "base64encodedcontent"
                }
            ]
        }
        
        response = requests.post(
            f"{API_BASE_URL}/loans/applications/{self.application_id}/documents", 
            json=documents
        )
        self.assertEqual(response.status_code, 201)
        
        # Step 4: Approve the application (admin action)
        approval = {
            "status": "APPROVED",
            "interest_rate": 12.5,
            "approved_amount": loan_application["requested_amount"],
            "term_months": loan_application["term_months"],
            "comments": "Application approved after verification"
        }
        
        response = requests.put(
            f"{API_BASE_URL}/loans/applications/{self.application_id}/status", 
            json=approval
        )
        self.assertEqual(response.status_code, 200)
        
        # Step 5: Check that loan was created
        response = requests.get(f"{API_BASE_URL}/loans/applications/{self.application_id}")
        self.assertEqual(response.status_code, 200)
        approved_application = response.json()
        self.assertEqual(approved_application["status"], "APPROVED")
        
        # Get the loan ID
        self.loan_id = approved_application["loan_id"]
        
        # Step 6: Check loan details
        response = requests.get(f"{API_BASE_URL}/loans/{self.loan_id}")
        self.assertEqual(response.status_code, 200)
        loan = response.json()
        
        self.assertEqual(loan["customer_id"], self.customer["customer_id"])
        self.assertEqual(loan["loan_type"], loan_application["loan_type"])
        self.assertEqual(loan["principal_amount"], approval["approved_amount"])
        self.assertEqual(loan["interest_rate"], approval["interest_rate"])
        self.assertEqual(loan["term_months"], approval["term_months"])
        self.assertEqual(loan["status"], "APPROVED")
        
        # Step 7: Accept loan offer
        acceptance = {
            "accepted": True,
            "disbursement_account_id": self.account["account_id"]
        }
        
        response = requests.put(
            f"{API_BASE_URL}/loans/{self.loan_id}/acceptance", 
            json=acceptance
        )
        self.assertEqual(response.status_code, 200)
        
        # Step 8: Check loan status after acceptance
        response = requests.get(f"{API_BASE_URL}/loans/{self.loan_id}")
        self.assertEqual(response.status_code, 200)
        accepted_loan = response.json()
        self.assertEqual(accepted_loan["status"], "ACCEPTED")
        
        # Step 9: Disburse the loan
        disbursal = {
            "disbursement_date": "2023-01-01",
            "disbursement_reference": "DISB123456"
        }
        
        response = requests.put(
            f"{API_BASE_URL}/loans/{self.loan_id}/disbursal",
            json=disbursal
        )
        self.assertEqual(response.status_code, 200)
        
        # Step 10: Check loan status after disbursal
        response = requests.get(f"{API_BASE_URL}/loans/{self.loan_id}")
        self.assertEqual(response.status_code, 200)
        disbursed_loan = response.json()
        self.assertEqual(disbursed_loan["status"], "ACTIVE")
        self.assertEqual(disbursed_loan["disbursement_date"], disbursal["disbursement_date"])
        
        # Step 11: Check account balance after disbursal
        response = requests.get(f"{API_BASE_URL}/accounts/{self.account['account_id']}")
        self.assertEqual(response.status_code, 200)
        updated_account = response.json()
        
        # Verify account balance increased by loan amount
        self.assertEqual(
            updated_account["balance"], 
            self.account["balance"] + loan_application["requested_amount"]
        )
        
        # Step 12: Check repayment schedule
        response = requests.get(f"{API_BASE_URL}/loans/{self.loan_id}/repayment-schedule")
        self.assertEqual(response.status_code, 200)
        schedule = response.json()
        
        # Verify schedule details
        self.assertEqual(len(schedule), loan_application["term_months"])
        self.assertIsNotNone(schedule[0]["due_date"])
        self.assertIsNotNone(schedule[0]["emi_amount"])


@pytest.mark.skipif(
    os.environ.get("SKIP_E2E_TESTS") == "1",
    reason="E2E tests are disabled"
)
class TestLoanRepaymentWorkflow(unittest.TestCase):
    """End-to-end tests for loan repayment workflow."""
    
    def setUp(self):
        """Set up before each test."""
        # Create a test customer
        self.customer = {
            "customer_id": "CUS_REPAY_E2E",
            "first_name": "Repayment",
            "last_name": "Test",
            "email": "repayment.test@example.com"
        }
        
        # Create the customer
        requests.post(f"{API_BASE_URL}/customers", json=self.customer)
        
        # Create an account for the customer
        self.account = {
            "account_id": "ACC_REPAY_E2E",
            "customer_id": "CUS_REPAY_E2E",
            "account_type": "SAVINGS",
            "balance": 20000.00,
            "currency": "USD",
            "status": "ACTIVE"
        }
        
        # Create the account
        requests.post(f"{API_BASE_URL}/accounts", json=self.account)
        
        # Create a test loan directly (bypassing application process)
        self.loan = {
            "loan_id": "LNS_REPAY_E2E",
            "customer_id": "CUS_REPAY_E2E",
            "loan_type": "PERSONAL",
            "principal_amount": 24000.00,
            "interest_rate": 12.0,
            "term_months": 24,
            "monthly_installment": 1127.15,  # Pre-calculated EMI
            "disbursement_date": "2023-01-01",
            "disbursement_account_id": "ACC_REPAY_E2E",
            "status": "ACTIVE"
        }
        
        # Create the loan
        response = requests.post(f"{API_BASE_URL}/loans", json=self.loan)
        self.assertEqual(response.status_code, 201)
    
    def tearDown(self):
        """Clean up after each test."""
        # Delete payments if they exist
        if hasattr(self, "payment_ids"):
            for payment_id in self.payment_ids:
                requests.delete(f"{API_BASE_URL}/loans/payments/{payment_id}")
        
        # Delete loan
        requests.delete(f"{API_BASE_URL}/loans/{self.loan['loan_id']}")
        
        # Delete account
        requests.delete(f"{API_BASE_URL}/accounts/{self.account['account_id']}")
        
        # Delete customer
        requests.delete(f"{API_BASE_URL}/customers/{self.customer['customer_id']}")
    
    def test_loan_repayment_workflow(self):
        """Test the complete loan repayment workflow."""
        self.payment_ids = []
        
        # Step 1: Make first EMI payment
        payment_amount = self.loan["monthly_installment"]
        payment1 = {
            "loan_id": self.loan["loan_id"],
            "account_id": self.account["account_id"],
            "amount": payment_amount,
            "payment_date": "2023-02-01",
            "payment_method": "ACCOUNT_TRANSFER",
            "remarks": "EMI Payment 1"
        }
        
        response = requests.post(f"{API_BASE_URL}/loans/payments", json=payment1)
        self.assertEqual(response.status_code, 201)
        payment1_data = response.json()
        self.payment_ids.append(payment1_data["payment_id"])
        
        # Step 2: Check loan status after first payment
        response = requests.get(f"{API_BASE_URL}/loans/{self.loan['loan_id']}")
        self.assertEqual(response.status_code, 200)
        updated_loan = response.json()
        
        # Verify outstanding amount reduced
        self.assertLess(
            updated_loan["outstanding_amount"], 
            self.loan["principal_amount"]
        )
        
        # Step 3: Check account balance after payment
        response = requests.get(f"{API_BASE_URL}/accounts/{self.account['account_id']}")
        self.assertEqual(response.status_code, 200)
        updated_account = response.json()
        
        # Verify account balance decreased by payment amount
        self.assertEqual(
            updated_account["balance"], 
            self.account["balance"] - payment_amount
        )
        
        # Step 4: Get payment history
        response = requests.get(f"{API_BASE_URL}/loans/{self.loan['loan_id']}/payments")
        self.assertEqual(response.status_code, 200)
        payments = response.json()
        
        # Verify payment was recorded
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments[0]["amount"], payment_amount)
        self.assertEqual(payments[0]["status"], "COMPLETED")
        
        # Step 5: Make second EMI payment
        payment2 = {
            "loan_id": self.loan["loan_id"],
            "account_id": self.account["account_id"],
            "amount": payment_amount,
            "payment_date": "2023-03-01",
            "payment_method": "ACCOUNT_TRANSFER",
            "remarks": "EMI Payment 2"
        }
        
        response = requests.post(f"{API_BASE_URL}/loans/payments", json=payment2)
        self.assertEqual(response.status_code, 201)
        payment2_data = response.json()
        self.payment_ids.append(payment2_data["payment_id"])
        
        # Step 6: Check updated loan status
        response = requests.get(f"{API_BASE_URL}/loans/{self.loan['loan_id']}")
        self.assertEqual(response.status_code, 200)
        updated_loan2 = response.json()
        
        # Verify outstanding amount reduced further
        self.assertLess(
            updated_loan2["outstanding_amount"], 
            updated_loan["outstanding_amount"]
        )
        
        # Step 7: Get updated payment history
        response = requests.get(f"{API_BASE_URL}/loans/{self.loan['loan_id']}/payments")
        self.assertEqual(response.status_code, 200)
        updated_payments = response.json()
        
        # Verify both payments are recorded
        self.assertEqual(len(updated_payments), 2)
        
        # Step 8: Get loan statement
        response = requests.get(
            f"{API_BASE_URL}/loans/{self.loan['loan_id']}/statement?start_date=2023-01-01&end_date=2023-03-31"
        )
        self.assertEqual(response.status_code, 200)
        statement = response.json()
        
        # Verify statement includes disbursement and payments
        self.assertEqual(len(statement["transactions"]), 3)  # 1 disbursement + 2 payments
        self.assertEqual(statement["total_paid"], payment_amount * 2)
        
        # Record initial principal
        initial_principal = self.loan["principal_amount"]
        
        # Step 9: Make a partial prepayment
        prepayment_amount = 5000.00
        prepayment = {
            "loan_id": self.loan["loan_id"],
            "account_id": self.account["account_id"],
            "amount": prepayment_amount,
            "payment_date": "2023-03-15",
            "payment_method": "ACCOUNT_TRANSFER",
            "payment_type": "PARTIAL_PREPAYMENT",
            "remarks": "Partial prepayment"
        }
        
        response = requests.post(f"{API_BASE_URL}/loans/payments", json=prepayment)
        self.assertEqual(response.status_code, 201)
        prepayment_data = response.json()
        self.payment_ids.append(prepayment_data["payment_id"])
        
        # Step 10: Check loan details after prepayment
        response = requests.get(f"{API_BASE_URL}/loans/{self.loan['loan_id']}")
        self.assertEqual(response.status_code, 200)
        loan_after_prepayment = response.json()
        
        # Verify outstanding amount reduced significantly
        self.assertLess(
            loan_after_prepayment["outstanding_amount"],
            updated_loan2["outstanding_amount"] - prepayment_amount
        )
        
        # Verify either term reduced or EMI reduced
        self.assertTrue(
            loan_after_prepayment["term_months"] < self.loan["term_months"] or
            loan_after_prepayment["monthly_installment"] < self.loan["monthly_installment"]
        )


if __name__ == "__main__":
    unittest.main()
