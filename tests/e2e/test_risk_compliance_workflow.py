"""
Core Banking Risk Compliance End-to-End Tests

This module contains E2E tests for risk compliance workflows including
fraud detection, risk scoring, regulatory reporting, and audit trails.
"""

import unittest
import sys
import time
import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import utility modules
from database.python.models import Customer, Account, Transaction
from database.db_manager import get_db_session

# Import risk compliance modules
from risk_compliance.fraud_detection.transaction_analyzer import analyze_transaction
from risk_compliance.fraud_detection.alert import get_alerts, resolve_alert
from risk_compliance.risk_scoring.customer_risk import calculate_customer_risk_score
from risk_compliance.regulatory_reporting.generator import generate_regulatory_report
from risk_compliance.audit_trail.logger import log_audit_event
from risk_compliance.audit_trail.retrieval import get_audit_logs

# Import from utils
from tests.e2e.db_workflow_utils import (
    create_test_customer,
    create_test_account,
    clean_up_test_data
)


class TestFraudDetectionWorkflow(unittest.TestCase):
    """End-to-end tests for fraud detection workflows."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data for all test methods."""
        cls.db_session = get_db_session()
        
        # Create test customer
        cls.customer = create_test_customer(
            cls.db_session,
            customer_id="E2E_FD_CUST",
            first_name="E2E",
            last_name="Fraud_Test",
            email="e2e.fraud@example.com"
        )
        
        # Create account
        cls.account = create_test_account(
            cls.db_session,
            account_id="E2E_FD_ACC",
            customer_id="E2E_FD_CUST",
            account_type="SAVINGS",
            balance=10000.00
        )
        
        # Create normal transaction pattern
        now = datetime.datetime.now()
        
        # Add historical transactions in New York
        for i in range(5):
            day_offset = i * 3  # Every 3 days
            timestamp = (now - datetime.timedelta(days=day_offset)).isoformat()
            
            transaction = Transaction(
                transaction_id=f"E2E_FD_TRX_{i}",
                account_id="E2E_FD_ACC",
                transaction_type="PURCHASE",
                amount=100.00 + (i * 10),  # Small variations
                currency="USD",
                description=f"Regular purchase {i}",
                location="New York",
                status="COMPLETED",
                timestamp=timestamp
            )
            cls.db_session.add(transaction)
        
        cls.db_session.flush()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Clean up test data
        clean_up_test_data(cls.db_session, "E2E_FD_CUST")
        cls.db_session.close()
    
    def test_01_normal_transaction_analysis(self):
        """Test analyzing a normal transaction."""
        # Create a transaction similar to normal pattern
        normal_transaction = {
            "transaction_id": "E2E_FD_NORMAL",
            "account_id": "E2E_FD_ACC",
            "amount": 120.00,
            "transaction_type": "PURCHASE",
            "merchant": "Local Store",
            "location": "New York",
            "timestamp": datetime.datetime.now().isoformat(),
            "db_session": self.db_session
        }
        
        # Analyze transaction
        analysis_result = analyze_transaction(normal_transaction)
        
        # Verify analysis
        self.assertFalse(analysis_result["fraud_suspected"])
        self.assertTrue(analysis_result["score"] < 0.5)
        
        # Check database for the transaction
        transaction = self.db_session.query(Transaction).filter_by(
            transaction_id="E2E_FD_NORMAL"
        ).first()
        
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.status, "COMPLETED")
    
    def test_02_suspicious_transaction_analysis(self):
        """Test analyzing a suspicious transaction."""
        # Create a transaction with unusual pattern
        suspicious_transaction = {
            "transaction_id": "E2E_FD_SUSPICIOUS",
            "account_id": "E2E_FD_ACC",
            "amount": 5000.00,  # Unusually large
            "transaction_type": "PURCHASE",
            "merchant": "Unknown Store",
            "location": "Moscow",  # Different location
            "timestamp": datetime.datetime.now().isoformat(),
            "db_session": self.db_session
        }
        
        # Analyze transaction
        analysis_result = analyze_transaction(suspicious_transaction)
        
        # Verify analysis
        self.assertTrue(analysis_result["fraud_suspected"])
        self.assertTrue(analysis_result["score"] > 0.5)
        self.assertIn("unusual_location", analysis_result["factors"])
        self.assertIn("unusual_amount", analysis_result["factors"])
        
        # Check alerts
        alerts = get_alerts("E2E_FD_ACC", self.db_session)
        
        self.assertGreaterEqual(len(alerts), 1)
        
        # Find our alert
        alert = None
        for a in alerts:
            if a["transaction_id"] == "E2E_FD_SUSPICIOUS":
                alert = a
                break
        
        self.assertIsNotNone(alert, "Alert not found")
        self.assertEqual(alert["status"], "OPEN")
        
        # Check database for the transaction
        transaction = self.db_session.query(Transaction).filter_by(
            transaction_id="E2E_FD_SUSPICIOUS"
        ).first()
        
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.status, "PENDING_REVIEW")
    
    def test_03_alert_resolution_workflow(self):
        """Test the alert resolution workflow."""
        # Get alerts
        alerts = get_alerts("E2E_FD_ACC", self.db_session)
        
        # Find our alert
        alert_id = None
        for a in alerts:
            if a["transaction_id"] == "E2E_FD_SUSPICIOUS":
                alert_id = a["alert_id"]
                break
        
        self.assertIsNotNone(alert_id, "Alert not found")
        
        # Resolve alert as false positive
        resolution_result = resolve_alert({
            "alert_id": alert_id,
            "resolution": "FALSE_POSITIVE",
            "notes": "Customer verified transaction",
            "resolved_by": "test_user",
            "db_session": self.db_session
        })
        
        # Verify resolution
        self.assertTrue(resolution_result["success"])
        
        # Check alert status
        alerts = get_alerts("E2E_FD_ACC", self.db_session)
        
        # Find our alert
        alert = None
        for a in alerts:
            if a["alert_id"] == alert_id:
                alert = a
                break
        
        self.assertIsNotNone(alert, "Alert not found")
        self.assertEqual(alert["status"], "RESOLVED")
        self.assertEqual(alert["resolution"], "FALSE_POSITIVE")
        
        # Check transaction status was updated
        transaction = self.db_session.query(Transaction).filter_by(
            transaction_id="E2E_FD_SUSPICIOUS"
        ).first()
        
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.status, "COMPLETED")


class TestRiskScoringWorkflow(unittest.TestCase):
    """End-to-end tests for customer risk scoring workflows."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data for all test methods."""
        cls.db_session = get_db_session()
        
        # Create low risk customer
        cls.low_risk_customer = create_test_customer(
            cls.db_session,
            customer_id="E2E_LOW_RISK",
            first_name="Low",
            last_name="Risk",
            email="low.risk@example.com",
            nationality="US",
            residence_country="US",
            occupation="Teacher",
            politically_exposed=False,
            account_age_years=5
        )
        
        # Create low risk account
        cls.low_risk_account = create_test_account(
            cls.db_session,
            account_id="E2E_LOW_RISK_ACC",
            customer_id="E2E_LOW_RISK",
            account_type="SAVINGS",
            balance=5000.00
        )
        
        # Create high risk customer
        cls.high_risk_customer = create_test_customer(
            cls.db_session,
            customer_id="E2E_HIGH_RISK",
            first_name="High",
            last_name="Risk",
            email="high.risk@example.com",
            nationality="RU",
            residence_country="CY",  # Cyprus - higher risk
            occupation="Consultant",
            politically_exposed=True,
            account_age_years=0.5
        )
        
        # Create high risk account
        cls.high_risk_account = create_test_account(
            cls.db_session,
            account_id="E2E_HIGH_RISK_ACC",
            customer_id="E2E_HIGH_RISK",
            account_type="CURRENT",
            balance=100000.00
        )
        
        # Add normal transactions for low risk
        now = datetime.datetime.now()
        for i in range(5):
            day_offset = i * 7  # Weekly transactions
            timestamp = (now - datetime.timedelta(days=day_offset)).isoformat()
            
            transaction = Transaction(
                transaction_id=f"E2E_LR_TRX_{i}",
                account_id="E2E_LOW_RISK_ACC",
                transaction_type="DEPOSIT" if i % 2 == 0 else "WITHDRAWAL",
                amount=500.00,
                currency="USD",
                description=f"Regular transaction {i}",
                status="COMPLETED",
                timestamp=timestamp
            )
            cls.db_session.add(transaction)
        
        # Add suspicious transactions for high risk
        for i in range(3):
            day_offset = i * 3  # Frequent transactions
            timestamp = (now - datetime.timedelta(days=day_offset)).isoformat()
            
            transaction = Transaction(
                transaction_id=f"E2E_HR_TRX_{i}",
                account_id="E2E_HIGH_RISK_ACC",
                transaction_type="INTERNATIONAL_TRANSFER" if i == 0 else "DEPOSIT",
                amount=30000.00 if i == 0 else 50000.00,
                currency="USD",
                description=f"High value transaction {i}",
                status="COMPLETED",
                timestamp=timestamp
            )
            cls.db_session.add(transaction)
        
        cls.db_session.flush()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Clean up test data
        clean_up_test_data(cls.db_session, "E2E_LOW_RISK")
        clean_up_test_data(cls.db_session, "E2E_HIGH_RISK")
        cls.db_session.close()
    
    def test_01_low_risk_customer_scoring(self):
        """Test risk scoring for a low-risk customer."""
        # Calculate risk score
        risk_result = calculate_customer_risk_score("E2E_LOW_RISK", self.db_session)
        
        # Verify risk level
        self.assertTrue(risk_result["score"] < 0.3)
        self.assertEqual(risk_result["risk_level"], "LOW")
        
        # Check high risk register - should not be present
        from risk_compliance.risk_scoring.high_risk_register import get_high_risk_customers
        
        high_risk_customers = get_high_risk_customers(self.db_session)
        high_risk_ids = [c["customer_id"] for c in high_risk_customers]
        
        self.assertNotIn("E2E_LOW_RISK", high_risk_ids)
    
    def test_02_high_risk_customer_scoring(self):
        """Test risk scoring for a high-risk customer."""
        # Calculate risk score
        risk_result = calculate_customer_risk_score("E2E_HIGH_RISK", self.db_session)
        
        # Verify risk level
        self.assertTrue(risk_result["score"] > 0.7)
        self.assertEqual(risk_result["risk_level"], "HIGH")
        self.assertIn("politically_exposed", risk_result["factors"])
        self.assertIn("high_risk_jurisdiction", risk_result["factors"])
        
        # Check high risk register - should be present
        from risk_compliance.risk_scoring.high_risk_register import get_high_risk_customers
        
        high_risk_customers = get_high_risk_customers(self.db_session)
        high_risk_ids = [c["customer_id"] for c in high_risk_customers]
        
        self.assertIn("E2E_HIGH_RISK", high_risk_ids)
    
    def test_03_enhanced_due_diligence_workflow(self):
        """Test enhanced due diligence workflow for high-risk customers."""
        # Get high risk customer details
        from risk_compliance.risk_scoring.high_risk_register import get_high_risk_customer_details
        
        customer_details = get_high_risk_customer_details("E2E_HIGH_RISK", self.db_session)
        
        # Verify customer details
        self.assertEqual(customer_details["customer_id"], "E2E_HIGH_RISK")
        self.assertEqual(customer_details["risk_level"], "HIGH")
        self.assertTrue("factors" in customer_details)
        self.assertTrue("politically_exposed" in customer_details["factors"])
        
        # Perform enhanced due diligence
        from risk_compliance.risk_scoring.due_diligence import perform_enhanced_due_diligence
        
        edd_result = perform_enhanced_due_diligence({
            "customer_id": "E2E_HIGH_RISK",
            "verification_documents": ["ID_VERIFICATION", "ADDRESS_PROOF", "INCOME_PROOF"],
            "verification_notes": "Customer documents verified",
            "reviewer": "test_user",
            "db_session": self.db_session
        })
        
        # Verify EDD result
        self.assertTrue(edd_result["success"])
        self.assertEqual(edd_result["status"], "COMPLETED")
        
        # Check customer monitoring status
        from risk_compliance.risk_scoring.monitoring import get_monitoring_status
        
        monitoring_status = get_monitoring_status("E2E_HIGH_RISK", self.db_session)
        
        self.assertEqual(monitoring_status["customer_id"], "E2E_HIGH_RISK")
        self.assertEqual(monitoring_status["monitoring_level"], "ENHANCED")
        self.assertTrue("last_review_date" in monitoring_status)


class TestRegulatoryReportingWorkflow(unittest.TestCase):
    """End-to-end tests for regulatory reporting workflows."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data for all test methods."""
        cls.db_session = get_db_session()
        
        # Create test customer
        cls.customer = create_test_customer(
            cls.db_session,
            customer_id="E2E_REG_CUST",
            first_name="Regulatory",
            last_name="Testing",
            email="regulatory.test@example.com",
            address="123 Test St, Test City",
            id_type="SSN",
            id_number="123-45-6789"
        )
        
        # Create account
        cls.account = create_test_account(
            cls.db_session,
            account_id="E2E_REG_ACC",
            customer_id="E2E_REG_CUST",
            account_type="SAVINGS",
            balance=50000.00
        )
        
        # Add large transactions for CTR reporting
        now = datetime.datetime.now()
        for i in range(3):
            day_offset = i  # Daily transactions
            timestamp = (now - datetime.timedelta(days=day_offset)).isoformat()
            
            transaction = Transaction(
                transaction_id=f"E2E_REG_TRX_{i}",
                account_id="E2E_REG_ACC",
                transaction_type="DEPOSIT",
                amount=12000.00,  # Above CTR threshold
                currency="USD",
                description=f"Large deposit {i}",
                status="COMPLETED",
                timestamp=timestamp
            )
            cls.db_session.add(transaction)
        
        cls.db_session.flush()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        # Clean up test data
        clean_up_test_data(cls.db_session, "E2E_REG_CUST")
        cls.db_session.close()
    
    def test_01_currency_transaction_report_generation(self):
        """Test generating a Currency Transaction Report (CTR)."""
        # Define report parameters
        today = datetime.datetime.now()
        end_date = today.strftime("%Y-%m-%d")
        start_date = (today - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        
        params = {
            "report_type": "CTR",  # Currency Transaction Report
            "start_date": start_date,
            "end_date": end_date,
            "threshold": 10000.00,
            "format": "JSON",
            "db_session": self.db_session
        }
        
        # Generate report
        report_result = generate_regulatory_report(params)
        
        # Verify report generation
        self.assertTrue(report_result["success"])
        self.assertEqual(report_result["report_type"], "CTR")
        self.assertTrue("report_id" in report_result)
        
        # Save report ID for next test
        self.report_id = report_result["report_id"]
        
        # Verify report data includes our transactions
        report_data = report_result["report_data"]
        self.assertGreaterEqual(len(report_data), 3)  # Should include our 3 transactions
        
        # Verify customer information in report
        transaction_found = False
        for entry in report_data:
            if entry["transaction_id"].startswith("E2E_REG_TRX_"):
                transaction_found = True
                self.assertEqual(entry["customer_info"]["customer_id"], "E2E_REG_CUST")
                self.assertEqual(entry["customer_info"]["name"], "Regulatory Testing")
                self.assertEqual(entry["customer_info"]["id_type"], "SSN")
        
        self.assertTrue(transaction_found, "Test transactions not found in report")
    
    def test_02_report_submission_workflow(self):
        """Test the regulatory report submission workflow."""
        # Check that we have a report ID from previous test
        self.assertTrue(hasattr(self, 'report_id'), "No report ID available from previous test")
        
        # Submit report
        from risk_compliance.regulatory_reporting.submission import submit_report
        
        submission_result = submit_report({
            "report_id": self.report_id,
            "submission_method": "API",
            "submission_notes": "Test submission",
            "submitted_by": "test_user",
            "db_session": self.db_session
        })
        
        # Verify submission
        self.assertTrue(submission_result["success"])
        self.assertEqual(submission_result["status"], "SUBMITTED")
        
        # Check report status
        from risk_compliance.regulatory_reporting.storage import get_report
        
        report = get_report(self.report_id, self.db_session)
        
        self.assertIsNotNone(report)
        self.assertEqual(report["status"], "SUBMITTED")
        self.assertTrue("submission_date" in report)


class TestAuditTrailWorkflow(unittest.TestCase):
    """End-to-end tests for audit trail workflows."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        cls.db_session = get_db_session()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        cls.db_session.close()
    
    def test_01_audit_logging_and_retrieval(self):
        """Test logging audit events and retrieving them."""
        # Log various audit events
        audit_events = [
            {
                "user_id": "admin",
                "action": "CUSTOMER_CREATE",
                "resource_type": "CUSTOMER",
                "resource_id": "CUS123456",
                "details": {"operation": "create"},
                "ip_address": "192.168.1.1",
                "db_session": self.db_session
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
                "ip_address": "192.168.1.1",
                "db_session": self.db_session
            },
            {
                "user_id": "teller1",
                "action": "TRANSACTION_CREATE",
                "resource_type": "TRANSACTION",
                "resource_id": "TRX123456",
                "details": {"amount": 1000.00},
                "ip_address": "192.168.1.2",
                "db_session": self.db_session
            }
        ]
        
        # Log each event
        audit_ids = []
        for event in audit_events:
            result = log_audit_event(event)
            self.assertTrue(result["success"])
            audit_ids.append(result["audit_id"])
        
        # Get audit logs by user
        admin_logs = get_audit_logs(
            {"user_id": "admin"},
            self.db_session
        )
        
        self.assertEqual(len(admin_logs), 2)  # Two actions by admin
        
        # Get audit logs by resource type
        account_logs = get_audit_logs(
            {"resource_type": "ACCOUNT"},
            self.db_session
        )
        
        self.assertEqual(len(account_logs), 1)  # One account action
        self.assertEqual(account_logs[0]["action"], "ACCOUNT_UPDATE")
        
        # Get specific audit record
        specific_log = get_audit_logs(
            {"audit_id": audit_ids[0]},
            self.db_session
        )
        
        self.assertEqual(len(specific_log), 1)
        self.assertEqual(specific_log[0]["action"], "CUSTOMER_CREATE")
    
    def test_02_security_incident_workflow(self):
        """Test security incident logging and investigation workflow."""
        # Create a security incident
        from risk_compliance.audit_trail.security_incident import create_security_incident
        
        incident_data = {
            "incident_type": "UNAUTHORIZED_ACCESS",
            "description": "Suspicious login attempts detected",
            "severity": "HIGH",
            "reported_by": "system",
            "related_logs": [],  # Would normally include audit log IDs
            "db_session": self.db_session
        }
        
        incident_result = create_security_incident(incident_data)
        
        # Verify incident creation
        self.assertTrue(incident_result["success"])
        self.assertTrue("incident_id" in incident_result)
        
        # Get incident details
        from risk_compliance.audit_trail.security_incident import get_incident
        
        incident = get_incident(incident_result["incident_id"], self.db_session)
        
        self.assertIsNotNone(incident)
        self.assertEqual(incident["incident_type"], "UNAUTHORIZED_ACCESS")
        self.assertEqual(incident["status"], "OPEN")
        
        # Investigate and resolve the incident
        from risk_compliance.audit_trail.security_incident import update_incident
        
        update_result = update_incident({
            "incident_id": incident_result["incident_id"],
            "status": "RESOLVED",
            "resolution": "False alarm - system testing",
            "resolution_date": datetime.datetime.now().isoformat(),
            "resolved_by": "test_user",
            "db_session": self.db_session
        })
        
        # Verify update
        self.assertTrue(update_result["success"])
        
        # Check updated incident
        incident = get_incident(incident_result["incident_id"], self.db_session)
        
        self.assertEqual(incident["status"], "RESOLVED")
        self.assertTrue("resolution" in incident)


if __name__ == "__main__":
    unittest.main()
