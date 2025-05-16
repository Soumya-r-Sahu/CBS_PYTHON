"""
Core Banking Risk Compliance Unit Tests

This module contains unit tests for risk compliance components like
fraud detection, risk scoring, and regulatory reporting.
"""

import pytest
import unittest
from unittest import mock
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import risk compliance modules
from risk_compliance.fraud_detection.transaction_analyzer import analyze_transaction
from risk_compliance.risk_scoring.customer_risk import calculate_customer_risk_score
from risk_compliance.regulatory_reporting.generator import generate_regulatory_report
from risk_compliance.audit_trail.logger import log_audit_event


class TestFraudDetection(unittest.TestCase):
    """Unit tests for fraud detection system."""
    
    @mock.patch('risk_compliance.fraud_detection.transaction_analyzer.lookup_previous_transactions')
    @mock.patch('risk_compliance.fraud_detection.transaction_analyzer.check_patterns')
    def test_analyze_normal_transaction(self, mock_patterns, mock_lookup):
        """Test analyzing a normal, non-fraudulent transaction."""
        # Configure mocks
        mock_lookup.return_value = [
            {"amount": 100.00, "location": "New York", "timestamp": "2023-01-01T12:00:00"},
            {"amount": 200.00, "location": "New York", "timestamp": "2023-01-02T14:00:00"}
        ]
        mock_patterns.return_value = {"suspicious": False, "score": 0.1}
        
        # Transaction data
        transaction = {
            "transaction_id": "TRX123456",
            "account_id": "ACC123456",
            "amount": 150.00,
            "transaction_type": "PURCHASE",
            "merchant": "Local Store",
            "location": "New York",
            "timestamp": "2023-01-03T13:00:00"
        }
        
        # Analyze transaction
        result = analyze_transaction(transaction)
        
        # Check result
        self.assertFalse(result["fraud_suspected"])
        self.assertTrue(result["score"] < 0.5)
        mock_lookup.assert_called_once_with(transaction["account_id"])
        mock_patterns.assert_called_once()
    
    @mock.patch('risk_compliance.fraud_detection.transaction_analyzer.lookup_previous_transactions')
    @mock.patch('risk_compliance.fraud_detection.transaction_analyzer.check_patterns')
    def test_analyze_suspicious_transaction(self, mock_patterns, mock_lookup):
        """Test analyzing a suspicious transaction."""
        # Configure mocks
        mock_lookup.return_value = [
            {"amount": 100.00, "location": "New York", "timestamp": "2023-01-01T12:00:00"},
            {"amount": 200.00, "location": "New York", "timestamp": "2023-01-02T14:00:00"}
        ]
        mock_patterns.return_value = {"suspicious": True, "score": 0.8}
        
        # Transaction data - unusual location
        transaction = {
            "transaction_id": "TRX123456",
            "account_id": "ACC123456",
            "amount": 5000.00,  # Unusual amount
            "transaction_type": "PURCHASE",
            "merchant": "Unknown Store",
            "location": "Moscow",  # Different location
            "timestamp": "2023-01-03T03:00:00"  # Unusual time
        }
        
        # Analyze transaction
        result = analyze_transaction(transaction)
        
        # Check result
        self.assertTrue(result["fraud_suspected"])
        self.assertTrue(result["score"] > 0.5)
        self.assertIn("unusual_location", result["factors"])
        self.assertIn("unusual_amount", result["factors"])
        mock_lookup.assert_called_once_with(transaction["account_id"])
        mock_patterns.assert_called_once()


class TestRiskScoring(unittest.TestCase):
    """Unit tests for risk scoring system."""
    
    @mock.patch('risk_compliance.risk_scoring.customer_risk.get_customer_data')
    @mock.patch('risk_compliance.risk_scoring.customer_risk.get_transaction_history')
    def test_calculate_low_risk_customer(self, mock_transactions, mock_customer):
        """Test calculating risk score for a low-risk customer."""
        # Configure mocks
        mock_customer.return_value = {
            "customer_id": "CUS123456",
            "account_type": "SAVINGS",
            "residence_country": "US",
            "occupation": "Teacher",
            "politically_exposed": False,
            "account_age_years": 5
        }
        
        mock_transactions.return_value = [
            {"amount": 1000.00, "type": "DEPOSIT", "date": "2023-01-01"},
            {"amount": 500.00, "type": "WITHDRAWAL", "date": "2023-01-15"},
            {"amount": 200.00, "type": "PAYMENT", "date": "2023-01-20"}
        ]
        
        # Calculate risk score
        result = calculate_customer_risk_score("CUS123456")
        
        # Check result
        self.assertTrue(result["score"] < 0.3)  # Low risk
        self.assertEqual(result["risk_level"], "LOW")
        mock_customer.assert_called_once_with("CUS123456")
        mock_transactions.assert_called_once_with("CUS123456")
    
    @mock.patch('risk_compliance.risk_scoring.customer_risk.get_customer_data')
    @mock.patch('risk_compliance.risk_scoring.customer_risk.get_transaction_history')
    def test_calculate_high_risk_customer(self, mock_transactions, mock_customer):
        """Test calculating risk score for a high-risk customer."""
        # Configure mocks
        mock_customer.return_value = {
            "customer_id": "CUS654321",
            "account_type": "CURRENT",
            "residence_country": "Cayman Islands",  # Tax haven
            "occupation": "Consultant",
            "politically_exposed": True,  # PEP
            "account_age_years": 0.5  # New account
        }
        
        mock_transactions.return_value = [
            {"amount": 100000.00, "type": "DEPOSIT", "date": "2023-01-01"},  # Large deposit
            {"amount": 95000.00, "type": "INTERNATIONAL_TRANSFER", "date": "2023-01-02"},  # International
            {"amount": 5000.00, "type": "WITHDRAWAL", "date": "2023-01-03"}
        ]
        
        # Calculate risk score
        result = calculate_customer_risk_score("CUS654321")
        
        # Check result
        self.assertTrue(result["score"] > 0.7)  # High risk
        self.assertEqual(result["risk_level"], "HIGH")
        self.assertIn("politically_exposed", result["factors"])
        self.assertIn("high_risk_jurisdiction", result["factors"])
        self.assertIn("large_transactions", result["factors"])
        mock_customer.assert_called_once_with("CUS654321")
        mock_transactions.assert_called_once_with("CUS654321")


class TestRegulatoryReporting(unittest.TestCase):
    """Unit tests for regulatory reporting system."""
    
    @mock.patch('risk_compliance.regulatory_reporting.generator.fetch_transaction_data')
    @mock.patch('risk_compliance.regulatory_reporting.generator.fetch_customer_data')
    def test_generate_regulatory_report(self, mock_customers, mock_transactions):
        """Test generating a regulatory report."""
        # Configure mocks
        mock_transactions.return_value = [
            {
                "transaction_id": "TRX123456",
                "account_id": "ACC123456",
                "amount": 12000.00,
                "transaction_type": "DEPOSIT",
                "timestamp": "2023-01-01T12:00:00"
            },
            {
                "transaction_id": "TRX123457",
                "account_id": "ACC654321",
                "amount": 15000.00,
                "transaction_type": "INTERNATIONAL_TRANSFER",
                "timestamp": "2023-01-02T14:00:00"
            }
        ]
        
        mock_customers.return_value = {
            "ACC123456": {
                "customer_id": "CUS123456",
                "name": "John Doe",
                "address": "123 Main St",
                "id_type": "SSN",
                "id_number": "123-45-6789"
            },
            "ACC654321": {
                "customer_id": "CUS654321",
                "name": "Jane Smith",
                "address": "456 Oak Ave",
                "id_type": "SSN",
                "id_number": "987-65-4321"
            }
        }
        
        # Report parameters
        params = {
            "report_type": "CTR",  # Currency Transaction Report
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
            "threshold": 10000.00,
            "format": "JSON"
        }
        
        # Generate report
        result = generate_regulatory_report(params)
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(len(result["report_data"]), 2)  # Both transactions above threshold
        self.assertEqual(result["report_type"], "CTR")
        mock_transactions.assert_called_once()
        mock_customers.assert_called_once()


class TestAuditTrail(unittest.TestCase):
    """Unit tests for audit trail logging."""
    
    @mock.patch('risk_compliance.audit_trail.logger.write_audit_log')
    def test_log_audit_event(self, mock_write):
        """Test logging an audit event."""
        # Event data
        event = {
            "user_id": "admin",
            "action": "ACCOUNT_UPDATE",
            "resource_type": "CUSTOMER",
            "resource_id": "CUS123456",
            "details": {
                "field": "address",
                "old_value": "123 Main St",
                "new_value": "456 Oak Ave"
            },
            "ip_address": "192.168.1.1"
        }
        
        # Log event
        result = log_audit_event(event)
        
        # Check result
        self.assertTrue(result["success"])
        self.assertTrue("timestamp" in result)
        self.assertTrue("audit_id" in result)
        mock_write.assert_called_once()
    
    @mock.patch('risk_compliance.audit_trail.logger.write_audit_log')
    def test_log_audit_event_missing_fields(self, mock_write):
        """Test logging an audit event with missing fields."""
        # Event with missing fields
        event = {
            "user_id": "admin",
            "action": "ACCOUNT_UPDATE",
            # Missing resource_type
            "resource_id": "CUS123456"
            # Missing details and ip_address
        }
        
        # Log event
        result = log_audit_event(event)
        
        # Check result
        self.assertFalse(result["success"])
        self.assertTrue("error" in result)
        self.assertEqual(result["error"], "Missing required fields")
        mock_write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
