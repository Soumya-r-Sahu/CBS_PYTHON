"""
Core Banking Loan Module Unit Tests

This module contains unit tests for loan-related functionality.
Tests in this module are focused on loan components with mocked dependencies.
"""

import pytest
import unittest
from unittest import mock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import loan modules
from core_banking.loans.emi_calculation.calculator import calculate_emi
from core_banking.loans.domain.models import Loan, LoanApplication
from core_banking.loans.loan_origination.service import process_loan_application


class TestLoanModels(unittest.TestCase):
    """Unit tests for loan models."""
    
    def test_loan_creation(self):
        """Test creating a Loan instance."""
        loan = Loan(
            loan_id="LNS123456",
            customer_id="CUS123456",
            loan_type="PERSONAL",
            principal_amount=100000.00,
            interest_rate=12.5,
            term_months=36,
            disbursement_date="2023-01-01",
            status="ACTIVE"
        )
        
        self.assertEqual(loan.loan_id, "LNS123456")
        self.assertEqual(loan.customer_id, "CUS123456")
        self.assertEqual(loan.loan_type, "PERSONAL")
        self.assertEqual(loan.principal_amount, 100000.00)
        self.assertEqual(loan.interest_rate, 12.5)
        self.assertEqual(loan.term_months, 36)
        self.assertEqual(loan.disbursement_date, "2023-01-01")
        self.assertEqual(loan.status, "ACTIVE")
    
    def test_loan_application_creation(self):
        """Test creating a LoanApplication instance."""
        application = LoanApplication(
            application_id="APP123456",
            customer_id="CUS123456",
            loan_type="PERSONAL",
            requested_amount=100000.00,
            term_months=36,
            application_date="2023-01-01",
            status="PENDING"
        )
        
        self.assertEqual(application.application_id, "APP123456")
        self.assertEqual(application.customer_id, "CUS123456")
        self.assertEqual(application.loan_type, "PERSONAL")
        self.assertEqual(application.requested_amount, 100000.00)
        self.assertEqual(application.term_months, 36)
        self.assertEqual(application.application_date, "2023-01-01")
        self.assertEqual(application.status, "PENDING")


class TestEMICalculation(unittest.TestCase):
    """Unit tests for EMI calculation."""
    
    def test_calculate_emi(self):
        """Test calculating EMI."""
        # Test cases with expected EMI values
        test_cases = [
            # (principal, rate, term, expected_emi)
            (100000, 12, 12, 8884.88),  # 1 year
            (100000, 12, 24, 4707.35),  # 2 years
            (100000, 12, 36, 3321.85),  # 3 years
            (500000, 10, 60, 10624.28)   # 5 years
        ]
        
        for principal, rate, term, expected_emi in test_cases:
            emi = calculate_emi(principal, rate, term)
            self.assertAlmostEqual(emi, expected_emi, places=2)
    
    def test_calculate_emi_edge_cases(self):
        """Test calculating EMI with edge cases."""
        # Zero principal
        self.assertEqual(calculate_emi(0, 12, 12), 0)
        
        # Zero interest rate (should be principal / term)
        self.assertEqual(calculate_emi(12000, 0, 12), 1000)
        
        # Zero term (should raise ValueError)
        with self.assertRaises(ValueError):
            calculate_emi(100000, 12, 0)
        
        # Negative values (should raise ValueError)
        with self.assertRaises(ValueError):
            calculate_emi(-100000, 12, 12)
        
        with self.assertRaises(ValueError):
            calculate_emi(100000, -12, 12)


class TestLoanOrigination(unittest.TestCase):
    """Unit tests for loan origination process."""
    
    @mock.patch('core_banking.loans.loan_origination.service.validate_application')
    @mock.patch('core_banking.loans.loan_origination.service.check_credit_score')
    @mock.patch('core_banking.loans.loan_origination.service.calculate_risk_score')
    def test_process_loan_application_approval(self, mock_risk, mock_credit, mock_validate):
        """Test processing a loan application that gets approved."""
        # Configure mocks
        mock_validate.return_value = True
        mock_credit.return_value = 750  # Good credit score
        mock_risk.return_value = 85  # Low risk
        
        # Create application
        application = LoanApplication(
            application_id="APP123456",
            customer_id="CUS123456",
            loan_type="PERSONAL",
            requested_amount=100000.00,
            term_months=36,
            application_date="2023-01-01",
            status="PENDING"
        )
        
        # Process application
        result = process_loan_application(application)
        
        # Verify result
        self.assertEqual(result["status"], "APPROVED")
        self.assertTrue("loan_id" in result)
        self.assertEqual(result["interest_rate"], 12.5)  # Default rate
        
        # Verify mocks were called
        mock_validate.assert_called_once_with(application)
        mock_credit.assert_called_once_with(application.customer_id)
        mock_risk.assert_called_once()
    
    @mock.patch('core_banking.loans.loan_origination.service.validate_application')
    @mock.patch('core_banking.loans.loan_origination.service.check_credit_score')
    @mock.patch('core_banking.loans.loan_origination.service.calculate_risk_score')
    def test_process_loan_application_rejection(self, mock_risk, mock_credit, mock_validate):
        """Test processing a loan application that gets rejected."""
        # Configure mocks
        mock_validate.return_value = True
        mock_credit.return_value = 550  # Poor credit score
        mock_risk.return_value = 35  # High risk
        
        # Create application
        application = LoanApplication(
            application_id="APP123456",
            customer_id="CUS123456",
            loan_type="PERSONAL",
            requested_amount=100000.00,
            term_months=36,
            application_date="2023-01-01",
            status="PENDING"
        )
        
        # Process application
        result = process_loan_application(application)
        
        # Verify result
        self.assertEqual(result["status"], "REJECTED")
        self.assertTrue("reason" in result)
        
        # Verify mocks were called
        mock_validate.assert_called_once_with(application)
        mock_credit.assert_called_once_with(application.customer_id)
        mock_risk.assert_called_once()


if __name__ == "__main__":
    unittest.main()
