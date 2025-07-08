"""
NEFT Payment Module Tests - Core Banking System

This module contains unit tests for NEFT payment functionality.
"""
import unittest
from datetime import datetime
from unittest import mock

from ..models.neft_model import (
    NEFTPaymentDetails, 
    NEFTTransaction, 
    NEFTStatus,
    NEFTReturnReason
)
from ..services.neft_service import NEFTService
from ..validators.neft_validators import NEFTValidator
from ..repositories.neft_repository import NEFTRepository
from ..exceptions.neft_exceptions import (
    NEFTValidationError, 
    NEFTLimitExceeded
)
from ..utils.neft_utils import (
    generate_neft_reference,
    mask_account_number
)


class TestNEFTValidation(unittest.TestCase):
    """Test cases for NEFT validation."""
    
    def test_account_number_validation(self):
        """Test account number validation."""
        validator = NEFTValidator()
        
        # Valid account numbers
        validator.validate_account_number("12345678901234")
        validator.validate_account_number("123456789012")
        
        # Invalid account numbers
        with self.assertRaises(NEFTValidationError):
            validator.validate_account_number("")
            
        with self.assertRaises(NEFTValidationError):
            validator.validate_account_number("12345")  # Too short
            
        with self.assertRaises(NEFTValidationError):
            validator.validate_account_number("12345AB78901")  # Contains letters
    
    def test_ifsc_code_validation(self):
        """Test IFSC code validation."""
        validator = NEFTValidator()
        
        # Valid IFSC codes
        validator.validate_ifsc_code("ABCD0123456")
        validator.validate_ifsc_code("SBIN0123456")
        
        # Invalid IFSC codes
        with self.assertRaises(NEFTValidationError):
            validator.validate_ifsc_code("")
            
        with self.assertRaises(NEFTValidationError):
            validator.validate_ifsc_code("ABCD123456")  # Missing 0
            
        with self.assertRaises(NEFTValidationError):
            validator.validate_ifsc_code("1BCD0123456")  # Starts with number
    
    def test_amount_validation(self):
        """Test amount validation."""
        validator = NEFTValidator()
        
        # Valid amounts
        validator.validate_amount(1000.0)
        validator.validate_amount(1.0)
        
        # Invalid amounts
        with self.assertRaises(NEFTValidationError):
            validator.validate_amount(0)
            
        with self.assertRaises(NEFTValidationError):
            validator.validate_amount(-100)
            
        with self.assertRaises(NEFTLimitExceeded):
            validator.validate_amount(3000000.0)  # Exceeds maximum


class TestNEFTUtils(unittest.TestCase):
    """Test cases for NEFT utilities."""
    
    def test_generate_neft_reference(self):
        """Test NEFT reference generation."""
        # Test with fixed timestamp
        timestamp = "20250513120000"
        reference = generate_neft_reference("12345678901234", 1000.0, timestamp)
        
        # Verify format: REFyymmddHHMMSS-HASH
        self.assertTrue(reference.startswith("REF20250513120000-"))
        self.assertEqual(len(reference), 25)  # REF + 14 digit timestamp + dash + 10 char hash
        
        # Test uniqueness for different inputs
        reference1 = generate_neft_reference("12345678901234", 1000.0, timestamp)
        reference2 = generate_neft_reference("12345678901235", 1000.0, timestamp)
        self.assertNotEqual(reference1, reference2)
    
    def test_mask_account_number(self):
        """Test account number masking."""
        # Test standard account number
        masked = mask_account_number("12345678901234")
        self.assertEqual(masked, "12********1234")
        
        # Test short account number
        masked = mask_account_number("123456")
        self.assertEqual(masked, "**3456")


@mock.patch("payments.neft.repositories.neft_repository.NEFTRepository")
class TestNEFTService(unittest.TestCase):
    """Test cases for NEFT service."""
    
    def setUp(self):
        """Set up test environment."""
        # Create payment details for testing
        self.payment_details = NEFTPaymentDetails(
            sender_account_number="12345678901234",
            sender_ifsc_code="ABCD0123456",
            sender_account_type="SAVINGS",
            sender_name="John Doe",
            beneficiary_account_number="98765432109876",
            beneficiary_ifsc_code="XYZW0654321",
            beneficiary_account_type="SAVINGS",
            beneficiary_name="Jane Smith",
            amount=1000.0,
            payment_reference="REF20250513-ABCDEF1234"
        )
    
    def test_create_transaction(self, mock_repo):
        """Test creating a NEFT transaction."""
        # Configure mock
        mock_repo_instance = mock_repo.return_value
        mock_repo_instance.create_transaction_id.return_value = "NEFT-20250513-ABCDEF12"
        mock_repo_instance.save_transaction.return_value = NEFTTransaction(
            transaction_id="NEFT-20250513-ABCDEF12",
            payment_details=self.payment_details,
            status=NEFTStatus.INITIATED
        )
        
        # Create service instance with mocked repository
        service = NEFTService()
        service.repository = mock_repo_instance
        
        # Create transaction
        transaction = service.create_transaction(self.payment_details)
        
        # Verify results
        self.assertEqual(transaction.transaction_id, "NEFT-20250513-ABCDEF12")
        self.assertEqual(transaction.status, NEFTStatus.INITIATED)
        self.assertEqual(transaction.payment_details.amount, 1000.0)
        
        # Verify mock interactions
        mock_repo_instance.create_transaction_id.assert_called_once()
        mock_repo_instance.save_transaction.assert_called_once()
    
    def test_process_transaction(self, mock_repo):
        """Test processing a NEFT transaction."""
        # Create transaction
        transaction = NEFTTransaction(
            transaction_id="NEFT-20250513-ABCDEF12",
            payment_details=self.payment_details,
            status=NEFTStatus.INITIATED
        )
        
        # Configure mock
        mock_repo_instance = mock_repo.return_value
        mock_repo_instance.get_transaction.return_value = transaction
        mock_repo_instance.save_transaction.return_value = transaction
        mock_repo_instance.create_batch_id.return_value = "NEFTBATCH-20250513-1230"
        mock_repo_instance.get_batch.return_value = None
        
        # Create service instance with mocked repository
        service = NEFTService()
        service.repository = mock_repo_instance
        
        # Process transaction
        with mock.patch.object(service, '_calculate_next_batch_time') as mock_batch_time:
            mock_batch_time.return_value = datetime(2025, 5, 13, 12, 30)
            result = service.process_transaction("NEFT-20250513-ABCDEF12")
        
        # Verify results
        self.assertEqual(result.status, NEFTStatus.VALIDATED)
        self.assertEqual(result.batch_number, "NEFTBATCH-20250513-1230")
        
        # Verify mock interactions
        mock_repo_instance.get_transaction.assert_called_once_with("NEFT-20250513-ABCDEF12")
        self.assertEqual(mock_repo_instance.save_transaction.call_count, 2)  # Initial save and batch update


if __name__ == "__main__":
    unittest.main()
