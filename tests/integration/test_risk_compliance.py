"""
Core Banking Risk Compliance Integration Tests

This module contains integration tests for risk compliance components including
fraud detection, risk scoring, and regulatory reporting.
"""

import pytest
import unittest
from unittest import mock
import sys
import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import risk compliance modules
from risk_compliance.fraud_detection.transaction_analyzer import analyze_transaction
from risk_compliance.risk_scoring.customer_risk import calculate_customer_risk_score
from risk_compliance.regulatory_reporting.generator import generate_regulatory_report
from risk_compliance.audit_trail.logger import log_audit_event

# Import database modules
from database.python.common.database_operations import Account, Transaction, Customer
from database.db_manager import get_db_session


class TestFraudDetectionIntegration(unittest.TestCase):
    """Integration tests for fraud detection system."""
    
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
        
        # Create test customer and account
        self.customer = Customer(
            customer_id="CUS_FRAUD_TEST",
            first_name="Fraud",
            last_name="Test",
            email="fraud.test@example.com",
            status="ACTIVE"
        )
        
        self.account = Account(
            account_id="ACC_FRAUD_TEST",
            customer_id="CUS_FRAUD_TEST",
            account_type="SAVINGS",
            balance=10000.00,
            currency="USD",
            status="ACTIVE"
        )
        
        # Add to database
        self.db_session.add(self.customer)
        self.db_session.add(self.account)
        
        # Add historical transactions
        now = datetime.datetime.now()
        
        # Normal transaction patterns in New York
        for i in range(5):
            day_offset = i * 3  # Every 3 days
            trans = Transaction(
                transaction_id=f"HIST_TRX_{i}",
                account_id="ACC_FRAUD_TEST",
                transaction_type="PURCHASE",
                amount=100.00 + (i * 10),  # Small variations
                currency="USD",
                description=f"Regular purchase {i}",
                location="New York",
                status="COMPLETED",
                timestamp=(now - datetime.timedelta(days=day_offset)).isoformat()
            )
            self.db_session.add(trans)
        
        self.db_session.flush()
    
    def tearDown(self):
        """Clean up after each test."""
        # Roll back the transaction
        self.transaction.rollback()
    
    def test_normal_transaction_detection(self):
        """Test fraud detection with a normal transaction pattern."""
        # Create a transaction similar to historical pattern
        normal_transaction = {
            "transaction_id": "TRX_NORMAL",
            "account_id": "ACC_FRAUD_TEST",
            "amount": 120.00,
            "transaction_type": "PURCHASE",
            "merchant": "Local Store",
            "location": "New York",
            "timestamp": datetime.datetime.now().isoformat(),
            "db_session": self.db_session  # For testing
        }
        
        # Analyze transaction
        result = analyze_transaction(normal_transaction)
        
        # Verify not flagged as fraudulent
        self.assertFalse(result["fraud_suspected"])
        self.assertTrue(result["score"] < 0.5)
    
    def test_suspicious_transaction_detection(self):
        """Test fraud detection with a suspicious transaction pattern."""
        # Create a transaction with unusual pattern
        suspicious_transaction = {
            "transaction_id": "TRX_SUSPICIOUS",
            "account_id": "ACC_FRAUD_TEST",
            "amount": 5000.00,  # Unusually large
            "transaction_type": "PURCHASE",
            "merchant": "Unknown Store",
            "location": "Bangkok",  # Different location
            "timestamp": datetime.datetime.now().isoformat(),
            "db_session": self.db_session  # For testing
        }
        
        # Analyze transaction
        result = analyze_transaction(suspicious_transaction)
        
        # Verify flagged as potentially fraudulent
        self.assertTrue(result["fraud_suspected"])
        self.assertTrue(result["score"] > 0.5)
        self.assertIn("unusual_location", result["factors"])
        self.assertIn("unusual_amount", result["factors"])
        
        # Verify alert was created
        from risk_compliance.fraud_detection.alert import get_alerts
        
        alerts = get_alerts("ACC_FRAUD_TEST", self.db_session)
        
        self.assertGreaterEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["transaction_id"], "TRX_SUSPICIOUS")


class TestRiskScoringIntegration(unittest.TestCase):
    """Integration tests for risk scoring system."""
    
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
        
        # Create low risk customer
        self.low_risk_customer = Customer(
            customer_id="CUS_LOW_RISK",
            first_name="Low",
            last_name="Risk",
            email="low.risk@example.com",
            nationality="US",
            residence_country="US",
            occupation="Teacher",
            politically_exposed=False,
            registration_date=(datetime.datetime.now() - datetime.timedelta(days=365*5)).isoformat(),  # 5 years ago
            status="ACTIVE"
        )
        
        # Create high risk customer
        self.high_risk_customer = Customer(
            customer_id="CUS_HIGH_RISK",
            first_name="High",
            last_name="Risk",
            email="high.risk@example.com",
            nationality="RU",
            residence_country="CY",  # Cyprus - higher risk
            occupation="Consultant",
            politically_exposed=True,
            registration_date=(datetime.datetime.now() - datetime.timedelta(days=30)).isoformat(),  # 30 days ago
            status="ACTIVE"
        )
        
        # Add customers
        self.db_session.add(self.low_risk_customer)
        self.db_session.add(self.high_risk_customer)
        
        # Create accounts
        self.low_risk_account = Account(
            account_id="ACC_LOW_RISK",
            customer_id="CUS_LOW_RISK",
            account_type="SAVINGS",
            balance=5000.00,
            currency="USD",
            status="ACTIVE"
        )
        
        self.high_risk_account = Account(
            account_id="ACC_HIGH_RISK",
            customer_id="CUS_HIGH_RISK",
            account_type="CURRENT",
            balance=100000.00,
            currency="USD",
            status="ACTIVE"
        )
        
        # Add accounts
        self.db_session.add(self.low_risk_account)
        self.db_session.add(self.high_risk_account)
        
        # Add transactions for low risk
        for i in range(5):
            day_offset = i * 7  # Weekly transactions
            trans = Transaction(
                transaction_id=f"LR_TRX_{i}",
                account_id="ACC_LOW_RISK",
                transaction_type="DEPOSIT" if i % 2 == 0 else "WITHDRAWAL",
                amount=500.00,
                currency="USD",
                description=f"Regular transaction {i}",
                status="COMPLETED",
                timestamp=(datetime.datetime.now() - datetime.timedelta(days=day_offset)).isoformat()
            )
            self.db_session.add(trans)
        
        # Add transactions for high risk
        for i in range(3):
            day_offset = i * 3  # Frequent transactions
            trans = Transaction(
                transaction_id=f"HR_TRX_{i}",
                account_id="ACC_HIGH_RISK",
                transaction_type="INTERNATIONAL_TRANSFER" if i == 0 else "DEPOSIT",
                amount=30000.00 if i == 0 else 50000.00,
                currency="USD",
                description=f"High value transaction {i}",
                status="COMPLETED",
                timestamp=(datetime.datetime.now() - datetime.timedelta(days=day_offset)).isoformat()
            )
            self.db_session.add(trans)
        
        self.db_session.flush()
    
    def tearDown(self):
        """Clean up after each test."""
        # Roll back the transaction
        self.transaction.rollback()
    
    def test_low_risk_customer_scoring(self):
        """Test risk scoring for a low-risk customer."""
        # Calculate risk score
        result = calculate_customer_risk_score("CUS_LOW_RISK", self.db_session)
        
        # Verify low risk score
        self.assertTrue(result["score"] < 0.3)  # Low risk
        self.assertEqual(result["risk_level"], "LOW")
    
    def test_high_risk_customer_scoring(self):
        """Test risk scoring for a high-risk customer."""
        # Calculate risk score
        result = calculate_customer_risk_score("CUS_HIGH_RISK", self.db_session)
        
        # Verify high risk score
        self.assertTrue(result["score"] > 0.7)  # High risk
        self.assertEqual(result["risk_level"], "HIGH")
        self.assertIn("politically_exposed", result["factors"])
        self.assertIn("high_risk_jurisdiction", result["factors"])
        self.assertIn("large_transactions", result["factors"])
        
        # Verify customer is added to high risk register
        from risk_compliance.risk_scoring.high_risk_register import get_high_risk_customers
        
        high_risk_customers = get_high_risk_customers(self.db_session)
        high_risk_ids = [c["customer_id"] for c in high_risk_customers]
        
        self.assertIn("CUS_HIGH_RISK", high_risk_ids)


class TestRegulatoryReportingIntegration(unittest.TestCase):
    """Integration tests for regulatory reporting."""
    
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
        
        # Create test customer and account
        self.customer = Customer(
            customer_id="CUS_REG_TEST",
            first_name="Regulatory",
            last_name="Test",
            email="regulatory.test@example.com",
            address="123 Test St, Test City",
            id_type="SSN",
            id_number="123-45-6789",
            status="ACTIVE"
        )
        
        self.account = Account(
            account_id="ACC_REG_TEST",
            customer_id="CUS_REG_TEST",
            account_type="SAVINGS",
            balance=20000.00,
            currency="USD",
            status="ACTIVE"
        )
        
        # Add to database
        self.db_session.add(self.customer)
        self.db_session.add(self.account)
        
        # Add large transactions for CTR reporting
        now = datetime.datetime.now()
        for i in range(3):
            day_offset = i * 1  # Daily transactions
            trans = Transaction(
                transaction_id=f"REG_TRX_{i}",
                account_id="ACC_REG_TEST",
                transaction_type="DEPOSIT",
                amount=12000.00,  # Above CTR threshold
                currency="USD",
                description=f"Large deposit {i}",
                status="COMPLETED",
                timestamp=(now - datetime.timedelta(days=day_offset)).isoformat()
            )
            self.db_session.add(trans)
        
        self.db_session.flush()
    
    def tearDown(self):
        """Clean up after each test."""
        # Roll back the transaction
        self.transaction.rollback()
    
    def test_currency_transaction_report_generation(self):
        """Test generating a Currency Transaction Report (CTR)."""
        # Report parameters
        today = datetime.datetime.now()
        start_date = (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        
        params = {
            "report_type": "CTR",  # Currency Transaction Report
            "start_date": start_date,
            "end_date": end_date,
            "threshold": 10000.00,
            "format": "JSON",
            "db_session": self.db_session  # For testing
        }
        
        # Generate report
        result = generate_regulatory_report(params)
        
        # Verify report generation
        self.assertTrue(result["success"])
        self.assertEqual(result["report_type"], "CTR")
        self.assertGreaterEqual(len(result["report_data"]), 3)  # All 3 transactions
        
        # Verify report includes customer information
        for entry in result["report_data"]:
            self.assertTrue("customer_info" in entry)
            self.assertEqual(entry["customer_info"]["customer_id"], "CUS_REG_TEST")
            self.assertEqual(entry["customer_info"]["name"], "Regulatory Test")
            self.assertEqual(entry["customer_info"]["id_type"], "SSN")
            self.assertEqual(entry["customer_info"]["id_number"], "123-45-6789")
        
        # Verify report was saved
        from risk_compliance.regulatory_reporting.storage import get_report
        
        saved_report = get_report(result["report_id"], self.db_session)
        
        self.assertIsNotNone(saved_report)
        self.assertEqual(saved_report["report_type"], "CTR")
        self.assertEqual(saved_report["status"], "GENERATED")


class TestAuditTrailIntegration(unittest.TestCase):
    """Integration tests for audit trail logging."""
    
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
    
    def tearDown(self):
        """Clean up after each test."""
        # Roll back the transaction
        self.transaction.rollback()
    
    def test_audit_logging_and_retrieval(self):
        """Test logging audit events and retrieving them."""
        # Log various audit events
        events = [
            {
                "user_id": "admin",
                "action": "CUSTOMER_CREATE",
                "resource_type": "CUSTOMER",
                "resource_id": "CUS123456",
                "details": {"operation": "create"},
                "ip_address": "192.168.1.1"
            },
            {
                "user_id": "admin",
                "action": "ACCOUNT_UPDATE",
                "resource_type": "ACCOUNT",
                "resource_id": "ACC123456",
                "details": {
                    "field": "status",
                    "old_value": "ACTIVE",
                    "new_value": "INACTIVE"
                },
                "ip_address": "192.168.1.1"
            },
            {
                "user_id": "teller1",
                "action": "TRANSACTION_CREATE",
                "resource_type": "TRANSACTION",
                "resource_id": "TRX123456",
                "details": {"amount": 1000.00},
                "ip_address": "192.168.1.2"
            }
        ]
        
        audit_ids = []
        for event in events:
            event["db_session"] = self.db_session  # For testing
            result = log_audit_event(event)
            self.assertTrue(result["success"])
            audit_ids.append(result["audit_id"])
        
        # Retrieve audit log by user
        from risk_compliance.audit_trail.retrieval import get_audit_logs
        
        admin_logs = get_audit_logs(
            {"user_id": "admin"},
            self.db_session
        )
        
        self.assertEqual(len(admin_logs), 2)  # Two actions by admin
        
        # Retrieve by resource type
        account_logs = get_audit_logs(
            {"resource_type": "ACCOUNT"},
            self.db_session
        )
        
        self.assertEqual(len(account_logs), 1)  # One account action
        self.assertEqual(account_logs[0]["action"], "ACCOUNT_UPDATE")
        
        # Retrieve by date range
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        all_logs = get_audit_logs(
            {"from_date": today, "to_date": today},
            self.db_session
        )
        
        self.assertEqual(len(all_logs), 3)  # All actions today
        
        # Verify specific audit record
        specific_log = get_audit_logs(
            {"audit_id": audit_ids[0]},
            self.db_session
        )
        
        self.assertEqual(len(specific_log), 1)
        self.assertEqual(specific_log[0]["action"], "CUSTOMER_CREATE")


if __name__ == "__main__":
    unittest.main()
