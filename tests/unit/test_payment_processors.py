"""
Core Banking Payments Module Unit Tests

This module contains unit tests for payment-related functionality.
Tests in this module are focused on payment components with mocked dependencies.
"""

import pytest
import unittest
from unittest import mock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Assume these imports exist based on the project structure
from payments.neft.processor import process_neft_payment
from payments.rtgs.processor import process_rtgs_payment
from payments.imps.processor import process_imps_payment
from payments.upi.processor import process_upi_payment
from payments.bill_payments.processor import process_bill_payment


class TestNEFTPayments(unittest.TestCase):
    """Unit tests for NEFT payments."""
    
    @mock.patch('payments.neft.processor.validate_neft_details')
    @mock.patch('payments.neft.processor.send_neft_request')
    @mock.patch('payments.neft.processor.update_transaction_status')
    def test_process_neft_payment_success(self, mock_update, mock_send, mock_validate):
        """Test processing a successful NEFT payment."""
        # Configure mocks
        mock_validate.return_value = True
        mock_send.return_value = {
            "status": "SUCCESS",
            "reference_id": "NEFT123456",
            "timestamp": "2023-01-01T12:00:00"
        }
        
        # Payment details
        payment_details = {
            "source_account": "ACC123456",
            "destination_account": "ACC654321",
            "destination_ifsc": "HDFC0001234",
            "amount": 10000.00,
            "description": "Test NEFT Payment"
        }
        
        # Process payment
        result = process_neft_payment(payment_details)
        
        # Verify result
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["reference_id"], "NEFT123456")
        
        # Verify mocks were called
        mock_validate.assert_called_once_with(payment_details)
        mock_send.assert_called_once()
        mock_update.assert_called_once()
    
    @mock.patch('payments.neft.processor.validate_neft_details')
    @mock.patch('payments.neft.processor.send_neft_request')
    def test_process_neft_payment_validation_failure(self, mock_send, mock_validate):
        """Test processing a NEFT payment with validation failure."""
        # Configure mocks
        mock_validate.return_value = False
        
        # Payment details with invalid IFSC
        payment_details = {
            "source_account": "ACC123456",
            "destination_account": "ACC654321",
            "destination_ifsc": "INVALID",  # Invalid IFSC
            "amount": 10000.00,
            "description": "Test NEFT Payment"
        }
        
        # Process payment
        result = process_neft_payment(payment_details)
        
        # Verify result
        self.assertEqual(result["status"], "FAILED")
        self.assertTrue("error" in result)
        
        # Verify mocks were called
        mock_validate.assert_called_once_with(payment_details)
        mock_send.assert_not_called()


class TestRTGSPayments(unittest.TestCase):
    """Unit tests for RTGS payments."""
    
    @mock.patch('payments.rtgs.processor.validate_rtgs_details')
    @mock.patch('payments.rtgs.processor.send_rtgs_request')
    @mock.patch('payments.rtgs.processor.update_transaction_status')
    def test_process_rtgs_payment_success(self, mock_update, mock_send, mock_validate):
        """Test processing a successful RTGS payment."""
        # Configure mocks
        mock_validate.return_value = True
        mock_send.return_value = {
            "status": "SUCCESS",
            "reference_id": "RTGS123456",
            "timestamp": "2023-01-01T12:00:00"
        }
        
        # Payment details
        payment_details = {
            "source_account": "ACC123456",
            "destination_account": "ACC654321",
            "destination_ifsc": "HDFC0001234",
            "amount": 200000.00,  # RTGS typically for large amounts
            "description": "Test RTGS Payment"
        }
        
        # Process payment
        result = process_rtgs_payment(payment_details)
        
        # Verify result
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["reference_id"], "RTGS123456")
        
        # Verify mocks were called
        mock_validate.assert_called_once_with(payment_details)
        mock_send.assert_called_once()
        mock_update.assert_called_once()
    
    @mock.patch('payments.rtgs.processor.validate_rtgs_details')
    def test_process_rtgs_payment_amount_too_small(self, mock_validate):
        """Test processing a RTGS payment with amount below limit."""
        # Configure mock
        mock_validate.return_value = False
        
        # Payment details with amount below RTGS limit
        payment_details = {
            "source_account": "ACC123456",
            "destination_account": "ACC654321",
            "destination_ifsc": "HDFC0001234",
            "amount": 10000.00,  # Below typical RTGS limit
            "description": "Test RTGS Payment"
        }
        
        # Process payment
        result = process_rtgs_payment(payment_details)
        
        # Verify result
        self.assertEqual(result["status"], "FAILED")
        self.assertTrue("error" in result)
        self.assertIn("minimum amount", result["error"].lower())
        
        # Verify mock was called
        mock_validate.assert_called_once_with(payment_details)


class TestIMPSPayments(unittest.TestCase):
    """Unit tests for IMPS payments."""
    
    @mock.patch('payments.imps.processor.validate_imps_details')
    @mock.patch('payments.imps.processor.send_imps_request')
    @mock.patch('payments.imps.processor.update_transaction_status')
    def test_process_imps_payment_success(self, mock_update, mock_send, mock_validate):
        """Test processing a successful IMPS payment."""
        # Configure mocks
        mock_validate.return_value = True
        mock_send.return_value = {
            "status": "SUCCESS",
            "reference_id": "IMPS123456",
            "timestamp": "2023-01-01T12:00:00"
        }
        
        # Payment details
        payment_details = {
            "source_account": "ACC123456",
            "destination_account": "ACC654321",
            "destination_ifsc": "HDFC0001234",
            "amount": 10000.00,
            "description": "Test IMPS Payment"
        }
        
        # Process payment
        result = process_imps_payment(payment_details)
        
        # Verify result
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["reference_id"], "IMPS123456")
        
        # Verify mocks were called
        mock_validate.assert_called_once_with(payment_details)
        mock_send.assert_called_once()
        mock_update.assert_called_once()


class TestUPIPayments(unittest.TestCase):
    """Unit tests for UPI payments."""
    
    @mock.patch('payments.upi.processor.validate_upi_details')
    @mock.patch('payments.upi.processor.send_upi_request')
    @mock.patch('payments.upi.processor.update_transaction_status')
    def test_process_upi_payment_success(self, mock_update, mock_send, mock_validate):
        """Test processing a successful UPI payment."""
        # Configure mocks
        mock_validate.return_value = True
        mock_send.return_value = {
            "status": "SUCCESS",
            "reference_id": "UPI123456",
            "timestamp": "2023-01-01T12:00:00"
        }
        
        # Payment details
        payment_details = {
            "source_vpa": "source@upi",
            "destination_vpa": "destination@upi",
            "amount": 1000.00,
            "description": "Test UPI Payment"
        }
        
        # Process payment
        result = process_upi_payment(payment_details)
        
        # Verify result
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["reference_id"], "UPI123456")
        
        # Verify mocks were called
        mock_validate.assert_called_once_with(payment_details)
        mock_send.assert_called_once()
        mock_update.assert_called_once()
    
    @mock.patch('payments.upi.processor.validate_upi_details')
    def test_process_upi_payment_invalid_vpa(self, mock_validate):
        """Test processing a UPI payment with invalid VPA."""
        # Configure mock
        mock_validate.side_effect = ValueError("Invalid VPA format")
        
        # Payment details with invalid VPA
        payment_details = {
            "source_vpa": "source@upi",
            "destination_vpa": "invalid-vpa",  # Invalid VPA
            "amount": 1000.00,
            "description": "Test UPI Payment"
        }
        
        # Process payment
        result = process_upi_payment(payment_details)
        
        # Verify result
        self.assertEqual(result["status"], "FAILED")
        self.assertTrue("error" in result)
        self.assertIn("invalid vpa", result["error"].lower())
        
        # Verify mock was called
        mock_validate.assert_called_once_with(payment_details)


class TestBillPayments(unittest.TestCase):
    """Unit tests for bill payments."""
    
    @mock.patch('payments.bill_payments.processor.validate_biller')
    @mock.patch('payments.bill_payments.processor.send_bill_payment_request')
    @mock.patch('payments.bill_payments.processor.update_bill_payment_status')
    def test_process_bill_payment_success(self, mock_update, mock_send, mock_validate):
        """Test processing a successful bill payment."""
        # Configure mocks
        mock_validate.return_value = {"valid": True, "biller_id": "BILLER123"}
        mock_send.return_value = {
            "status": "SUCCESS",
            "reference_id": "BILL123456",
            "timestamp": "2023-01-01T12:00:00"
        }
        
        # Payment details
        payment_details = {
            "source_account": "ACC123456",
            "biller_name": "Electricity Board",
            "consumer_number": "123456789",
            "amount": 1500.00,
            "bill_date": "2023-01-01"
        }
        
        # Process payment
        result = process_bill_payment(payment_details)
        
        # Verify result
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["reference_id"], "BILL123456")
        
        # Verify mocks were called
        mock_validate.assert_called_once_with(
            payment_details["biller_name"], 
            payment_details["consumer_number"]
        )
        mock_send.assert_called_once()
        mock_update.assert_called_once()
    
    @mock.patch('payments.bill_payments.processor.validate_biller')
    def test_process_bill_payment_invalid_biller(self, mock_validate):
        """Test processing a bill payment with invalid biller."""
        # Configure mock
        mock_validate.return_value = {"valid": False, "error": "Biller not found"}
        
        # Payment details with invalid biller
        payment_details = {
            "source_account": "ACC123456",
            "biller_name": "Unknown Biller",  # Invalid biller
            "consumer_number": "123456789",
            "amount": 1500.00,
            "bill_date": "2023-01-01"
        }
        
        # Process payment
        result = process_bill_payment(payment_details)
        
        # Verify result
        self.assertEqual(result["status"], "FAILED")
        self.assertTrue("error" in result)
        self.assertIn("biller not found", result["error"].lower())
        
        # Verify mock was called
        mock_validate.assert_called_once_with(
            payment_details["biller_name"], 
            payment_details["consumer_number"]
        )


if __name__ == "__main__":
    unittest.main()
