"""
IMPS Payment Module Tests - Core Banking System

This module contains unit tests for IMPS payment functionality.
"""
import unittest
from datetime import datetime
from unittest import mock

from ..models.imps_model import (
    IMPSPaymentDetails, 
    IMPSTransaction, 
    IMPSStatus,
    IMPSReturnReason,
    IMPSType,
    IMPSChannel
)
from ..services.imps_service import IMPSService
from ..validators.imps_validators import IMPSValidator
from ..repositories.imps_repository import IMPSRepository
from ..exceptions.imps_exceptions import (
    IMPSValidationError, 
    IMPSLimitExceeded,
    IMPSInvalidMobileNumber,
    IMPSInvalidMMID
)
from ..utils.imps_utils import (
    generate_imps_reference,
    mask_account_number,
    mask_mobile_number
)


class TestIMPSValidation(unittest.TestCase):
    """Test cases for IMPS validation."""
    
    def test_account_number_validation(self):
        """Test account number validation."""
        validator = IMPSValidator()
        
        # Valid account numbers
        validator.validate_account_number("12345678901234")
        validator.validate_account_number("123456789012")
        
        # Invalid account numbers
        with self.assertRaises(IMPSValidationError):
            validator.validate_account_number("")
            
        with self.assertRaises(IMPSValidationError):
            validator.validate_account_number("12345")  # Too short
            
        with self.assertRaises(IMPSValidationError):
            validator.validate_account_number("12345AB78901@")  # Contains special characters
    
    def test_ifsc_code_validation(self):
        """Test IFSC code validation."""
        validator = IMPSValidator()
        
        # Valid IFSC codes
        validator.validate_ifsc_code("ABCD0123456")
        validator.validate_ifsc_code("SBIN0123456")
        
        # Invalid IFSC codes
        with self.assertRaises(IMPSValidationError):
            validator.validate_ifsc_code("")
            
        with self.assertRaises(IMPSValidationError):
            validator.validate_ifsc_code("ABCD123456")  # Missing 0
            
        with self.assertRaises(IMPSValidationError):
            validator.validate_ifsc_code("1BCD0123456")  # Starts with number
    
    def test_amount_validation(self):
        """Test amount validation."""
        validator = IMPSValidator()
        
        # Valid amounts
        validator.validate_amount(1000.0)
        validator.validate_amount(1.0)
        
        # Invalid amounts
        with self.assertRaises(IMPSValidationError):
            validator.validate_amount(0)
            
        with self.assertRaises(IMPSValidationError):
            validator.validate_amount(-100)
            
        with self.assertRaises(IMPSLimitExceeded):
            validator.validate_amount(600000.0)  # Exceeds maximum
    
    def test_mobile_number_validation(self):
        """Test mobile number validation."""
        validator = IMPSValidator()
        
        # Valid mobile numbers
        validator.validate_mobile_number("9876543210")
        validator.validate_mobile_number("+919876543210")
        validator.validate_mobile_number("09876543210")
        
        # Invalid mobile numbers
        with self.assertRaises(IMPSInvalidMobileNumber):
            validator.validate_mobile_number("")
            
        with self.assertRaises(IMPSInvalidMobileNumber):
            validator.validate_mobile_number("123456")  # Too short
            
        with self.assertRaises(IMPSInvalidMobileNumber):
            validator.validate_mobile_number("1234567890")  # Doesn't start with 6-9
            
        with self.assertRaises(IMPSInvalidMobileNumber):
            validator.validate_mobile_number("98765432a0")  # Contains letters
    
    def test_mmid_validation(self):
        """Test MMID validation."""
        validator = IMPSValidator()
        
        # Valid MMID
        validator.validate_mmid("1234567")
        
        # Invalid MMID
        with self.assertRaises(IMPSInvalidMMID):
            validator.validate_mmid("")
            
        with self.assertRaises(IMPSInvalidMMID):
            validator.validate_mmid("123456")  # Too short
            
        with self.assertRaises(IMPSInvalidMMID):
            validator.validate_mmid("12345678")  # Too long
            
        with self.assertRaises(IMPSInvalidMMID):
            validator.validate_mmid("123A567")  # Contains letters


class TestIMPSUtils(unittest.TestCase):
    """Test cases for IMPS utilities."""
    
    def test_generate_imps_reference(self):
        """Test IMPS reference generation."""
        # Test with fixed timestamp
        timestamp = "20250513120000"
        reference = generate_imps_reference("9876543210", "12345678901234", 1000.0, timestamp)
        
        # Verify format: IM-yymmddHHMMSS-HASH
        self.assertTrue(reference.startswith("IM-"))
        self.assertEqual(len(reference), 24)  # IM- + 12 digit timestamp + - + 8 char hash
        
        # Test uniqueness for different inputs
        reference1 = generate_imps_reference("9876543210", "12345678901234", 1000.0, timestamp)
        reference2 = generate_imps_reference("9876543211", "12345678901234", 1000.0, timestamp)
        self.assertNotEqual(reference1, reference2)
    
    def test_mask_account_number(self):
        """Test account number masking."""
        # Test standard account number
        masked = mask_account_number("12345678901234")
        self.assertEqual(masked, "12********1234")
        
        # Test short account number
        masked = mask_account_number("123456")
        self.assertEqual(masked, "**3456")
    
    def test_mask_mobile_number(self):
        """Test mobile number masking."""
        # Test standard mobile
        masked = mask_mobile_number("9876543210")
        self.assertEqual(masked, "98******10")
        
        # Test with country code
        masked = mask_mobile_number("+919876543210")
        self.assertEqual(masked, "98******10")


@mock.patch("payments.imps.repositories.imps_repository.IMPSRepository")
class TestIMPSService(unittest.TestCase):
    """Test cases for IMPS service."""
    
    def setUp(self):
        """Set up test environment."""
        # Create payment details for testing
        self.payment_details = IMPSPaymentDetails(
            sender_account_number="12345678901234",
            sender_ifsc_code="ABCD0123456",
            sender_mobile_number="9876543210",
            sender_mmid="1234567",
            sender_name="John Doe",
            beneficiary_account_number="98765432109876",
            beneficiary_ifsc_code="XYZW0654321",
            beneficiary_mobile_number="8765432109",
            beneficiary_mmid="7654321",
            beneficiary_name="Jane Smith",
            amount=1000.0,
            reference_number="IM-250513120000-ABCDEF12"
        )
    
    def test_create_transaction(self, mock_repo):
        """Test creating an IMPS transaction."""
        # Configure mock
        mock_repo_instance = mock_repo.return_value
        mock_repo_instance.create_transaction_id.return_value = "IMPS-20250513-ABCDEF12"
        mock_repo_instance.is_duplicate_transaction.return_value = False
        mock_repo_instance.save_transaction.return_value = IMPSTransaction(
            transaction_id="IMPS-20250513-ABCDEF12",
            payment_details=self.payment_details,
            status=IMPSStatus.INITIATED
        )
        
        # Create service instance with mocked repository
        service = IMPSService()
        service.repository = mock_repo_instance
        
        # Create transaction
        transaction = service.create_transaction(self.payment_details)
        
        # Verify results
        self.assertEqual(transaction.transaction_id, "IMPS-20250513-ABCDEF12")
        self.assertEqual(transaction.status, IMPSStatus.INITIATED)
        self.assertEqual(transaction.payment_details.amount, 1000.0)
        
        # Verify mock interactions
        mock_repo_instance.create_transaction_id.assert_called_once()
        mock_repo_instance.is_duplicate_transaction.assert_called_once()
        mock_repo_instance.save_transaction.assert_called_once()
    
    def test_process_transaction(self, mock_repo):
        """Test processing an IMPS transaction."""
        # Create transaction
        transaction = IMPSTransaction(
            transaction_id="IMPS-20250513-ABCDEF12",
            payment_details=self.payment_details,
            status=IMPSStatus.INITIATED
        )
        
        # Configure mock
        mock_repo_instance = mock_repo.return_value
        mock_repo_instance.get_transaction.return_value = transaction
        mock_repo_instance.save_transaction.return_value = transaction
        
        # Create service instance with mocked repository
        service = IMPSService()
        service.repository = mock_repo_instance
        service.mock_mode = True
        
        # Process transaction
        result = service.process_transaction("IMPS-20250513-ABCDEF12")
        
        # Verify results
        self.assertEqual(result.status, IMPSStatus.COMPLETED)
        self.assertIsNotNone(result.rrn)
        
        # Verify mock interactions
        mock_repo_instance.get_transaction.assert_called_once_with("IMPS-20250513-ABCDEF12")
        self.assertEqual(mock_repo_instance.save_transaction.call_count, 1)  # Save after processing
    
    def test_create_p2p_transaction(self, mock_repo):
        """Test P2P transaction creation."""
        # Create P2P payment details
        p2p_details = IMPSPaymentDetails(
            sender_account_number="12345678901234",
            sender_ifsc_code="ABCD0123456",
            sender_mobile_number="9876543210",
            sender_mmid="1234567",
            sender_name="John Doe",
            beneficiary_mobile_number="8765432109",
            beneficiary_mmid="7654321",
            beneficiary_name="Jane Smith",
            amount=500.0,
            reference_number="IM-250513120000-BBCDEF12",
            imps_type=IMPSType.P2P,
            channel=IMPSChannel.MOBILE
        )
        
        # Configure mock
        mock_repo_instance = mock_repo.return_value
        mock_repo_instance.create_transaction_id.return_value = "IMPS-20250513-BBCDEF12"
        mock_repo_instance.is_duplicate_transaction.return_value = False
        
        transaction = IMPSTransaction(
            transaction_id="IMPS-20250513-BBCDEF12",
            payment_details=p2p_details,
            status=IMPSStatus.INITIATED
        )
        
        mock_repo_instance.save_transaction.return_value = transaction
        mock_repo_instance.get_transaction.return_value = transaction
        
        # Create service instance with mocked repository
        service = IMPSService()
        service.repository = mock_repo_instance
        service.mock_mode = True
        
        # Create and process P2P transaction
        result = service.create_p2p_transaction(p2p_details)
        
        # Verify results
        self.assertEqual(result.payment_details.imps_type, IMPSType.P2P)
        self.assertEqual(result.status, IMPSStatus.COMPLETED)  # P2P gets processed immediately


if __name__ == "__main__":
    unittest.main()
