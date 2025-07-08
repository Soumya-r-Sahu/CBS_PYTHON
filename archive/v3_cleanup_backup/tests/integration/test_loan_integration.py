"""
Core Banking Loan Integration Tests

This module contains integration tests for loan-related functionality.
These tests verify that loan components work together correctly.
"""

import pytest
import unittest
import sys
from pathlib import Path
from unittest import mock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import loan modules
from core_banking.loans.domain.models import Loan, LoanApplication
from core_banking.loans.emi_calculation.calculator import calculate_emi
from core_banking.loans.loan_origination.service import process_loan_application

# Import database modules
from database.db_manager import get_db_session


class TestLoanOriginationFlow(unittest.TestCase):
    """Integration tests for loan origination flow."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database session."""
        # Use a real session but with transaction rollback
        cls.db_session = get_db_session()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database session."""
        cls.db_session.close()
    
    def setUp(self):
        """Set up before each test."""
        # Begin a transaction
        self.transaction = self.db_session.begin_nested()
    
    def tearDown(self):
        """Clean up after each test."""
        # Roll back the transaction
        self.transaction.rollback()
    
    @mock.patch('core_banking.loans.loan_origination.service.check_credit_score')
    def test_loan_application_to_approval(self, mock_credit_score):
        """Test the full flow from loan application to approval."""
        # Mock credit score to ensure approval
        mock_credit_score.return_value = 800  # Excellent credit score
        
        # Create a loan application
        application = LoanApplication(
            application_id="APP_INT_TEST",
            customer_id="CUS_INT_TEST",
            loan_type="PERSONAL",
            requested_amount=50000.00,
            term_months=24,
            application_date="2023-01-01",
            status="PENDING"
        )
        
        # Add application to database
        self.db_session.add(application)
        self.db_session.flush()
        
        # Process the application
        result = process_loan_application(application, self.db_session)
        
        # Verify result
        self.assertEqual(result["status"], "APPROVED")
        self.assertTrue("loan_id" in result)
        
        # Retrieve the created loan
        loan = self.db_session.query(Loan).filter_by(
            loan_id=result["loan_id"]
        ).first()
        
        # Verify loan was created
        self.assertIsNotNone(loan)
        self.assertEqual(loan.customer_id, application.customer_id)
        self.assertEqual(loan.loan_type, application.loan_type)
        self.assertEqual(loan.principal_amount, application.requested_amount)
        self.assertEqual(loan.term_months, application.term_months)
        self.assertEqual(loan.status, "APPROVED")
        
        # Verify EMI calculation
        expected_emi = calculate_emi(
            loan.principal_amount,
            loan.interest_rate,
            loan.term_months
        )
        
        self.assertAlmostEqual(loan.monthly_installment, expected_emi, places=2)
    
    @mock.patch('core_banking.loans.loan_origination.service.check_credit_score')
    def test_loan_application_to_rejection(self, mock_credit_score):
        """Test the full flow from loan application to rejection."""
        # Mock credit score to ensure rejection
        mock_credit_score.return_value = 500  # Poor credit score
        
        # Create a loan application
        application = LoanApplication(
            application_id="APP_INT_TEST_REJ",
            customer_id="CUS_INT_TEST",
            loan_type="PERSONAL",
            requested_amount=100000.00,
            term_months=36,
            application_date="2023-01-01",
            status="PENDING"
        )
        
        # Add application to database
        self.db_session.add(application)
        self.db_session.flush()
        
        # Process the application
        result = process_loan_application(application, self.db_session)
        
        # Verify result
        self.assertEqual(result["status"], "REJECTED")
        self.assertTrue("reason" in result)
        
        # Verify application status was updated
        updated_application = self.db_session.query(LoanApplication).filter_by(
            application_id="APP_INT_TEST_REJ"
        ).first()
        
        self.assertEqual(updated_application.status, "REJECTED")
        
        # Verify no loan was created
        loan = self.db_session.query(Loan).filter_by(
            customer_id="CUS_INT_TEST"
        ).first()
        
        self.assertIsNone(loan)


class TestLoanRepaymentFlow(unittest.TestCase):
    """Integration tests for loan repayment flow."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database session."""
        cls.db_session = get_db_session()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database session."""
        cls.db_session.close()
    
    def setUp(self):
        """Set up before each test."""
        # Begin a transaction
        self.transaction = self.db_session.begin_nested()
        
        # Create a test loan
        self.test_loan = Loan(
            loan_id="LNS_INT_TEST",
            customer_id="CUS_INT_TEST",
            loan_type="PERSONAL",
            principal_amount=50000.00,
            interest_rate=12.5,
            term_months=24,
            monthly_installment=2355.68,  # Pre-calculated EMI
            disbursement_date="2023-01-01",
            status="ACTIVE"
        )
        
        # Add loan to database
        self.db_session.add(self.test_loan)
        self.db_session.flush()
    
    def tearDown(self):
        """Clean up after each test."""
        # Roll back the transaction
        self.transaction.rollback()
    
    def test_loan_payment_processing(self):
        """Test processing a loan payment."""
        from core_banking.loans.domain.services import process_loan_payment
        
        # Initial outstanding amount
        initial_outstanding = self.test_loan.outstanding_amount
        
        # Process payment
        payment_amount = self.test_loan.monthly_installment
        result = process_loan_payment(
            self.test_loan.loan_id,
            payment_amount,
            "EMI Payment",
            self.db_session
        )
        
        # Verify result
        self.assertEqual(result["status"], "SUCCESS")
        
        # Get updated loan
        updated_loan = self.db_session.query(Loan).filter_by(
            loan_id="LNS_INT_TEST"
        ).first()
        
        # Verify outstanding amount was reduced
        self.assertLess(updated_loan.outstanding_amount, initial_outstanding)
        self.assertAlmostEqual(
            updated_loan.outstanding_amount,
            initial_outstanding - payment_amount,
            places=2
        )
        
        # Verify payment was recorded
        from core_banking.loans.domain.models import LoanPayment
        
        payment = self.db_session.query(LoanPayment).filter_by(
            loan_id="LNS_INT_TEST"
        ).first()
        
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount, payment_amount)
        self.assertEqual(payment.status, "COMPLETED")


if __name__ == "__main__":
    unittest.main()
