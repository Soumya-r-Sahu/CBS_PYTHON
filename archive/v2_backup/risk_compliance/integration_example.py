"""
Risk Compliance Integration Example

This file demonstrates how to integrate the risk-compliance components
into the Core Banking System.
"""

import os
import sys
import logging
import datetime
from decimal import Decimal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_audit_trail_integration():
    """Set up audit trail integration examples"""
    logger.info("Setting up audit trail integration...")
    
    try:
        # Import audit integration
        from risk_compliance.audit_trail.audit_integration import (
            audit_decorator, audit_transaction, audit_account_change,
            audit_customer_change, log_audit_event
        )
        
        # Example of manual audit logging
        log_audit_event(
            event_type="system_startup",
            user_id="SYSTEM",
            description="Risk compliance module integration started",
            metadata={"integration_time": datetime.datetime.now().isoformat()}
        )
        
        # Example functions with decorators
        @audit_transaction("Processed {amount} {currency} transaction for account {account_id}")
        def process_transaction(user_id, account_id, amount, currency="INR"):
            # Process the transaction
            logger.info(f"Processing transaction: {amount} {currency}")
            return {
                "transaction_id": f"TX-{int(datetime.datetime.now().timestamp())}",
                "status": "SUCCESS",
                "amount": amount,
                "currency": currency
            }
        
        @audit_account_change("Updated account settings for {account_id}")
        def update_account_settings(user_id, account_id, settings):
            # Update account settings
            logger.info(f"Updating settings for account: {account_id}")
            return {
                "id": account_id,
                "status": "SUCCESS"
            }
        
        # Test the decorated functions
        process_transaction("USER123", "ACCT001", 1000.0, "INR")
        update_account_settings("USER123", "ACCT001", {"overdraft_protection": True})
        
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import audit trail module: {str(e)}")
        return False


def setup_fraud_detection_integration():
    """Set up fraud detection integration examples"""
    logger.info("Setting up fraud detection integration...")
    
    try:
        # Import fraud detection
        from risk_compliance.fraud_detection.fraud_detection_system import check_transaction
        from risk_compliance.fraud_detection.transaction_monitor import (
            start_monitoring, submit_transaction, register_alert_handler
        )
        
        # Define a custom alert handler
        def handle_fraud_alert(alert):
            logger.warning(
                f"FRAUD ALERT: {alert['severity']} risk (score: {alert['risk_score']}) "
                f"for transaction {alert['transaction_id']}"
            )
        
        # Register the alert handler
        register_alert_handler(handle_fraud_alert)
        
        # Start the transaction monitoring
        start_monitoring()
        
        # Example transaction to check
        transaction = {
            "user_id": "USER123",
            "transaction_id": f"TX-{int(datetime.datetime.now().timestamp())}",
            "amount": 5000.0,
            "transaction_type": "TRANSFER",
            "recipient_id": "ACCT999",
            "channel": "INTERNET_BANKING",
            "timestamp": datetime.datetime.now().timestamp(),
            "location": {"ip": "192.168.1.1"}
        }
        
        # Check transaction directly
        result = check_transaction(transaction)
        logger.info(f"Transaction check result: {result['is_suspicious']}")
        
        # Submit transaction for monitoring
        submit_transaction(transaction)
        
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import fraud detection module: {str(e)}")
        return False


def setup_regulatory_reporting_integration():
    """Set up regulatory reporting integration examples"""
    logger.info("Setting up regulatory reporting integration...")
    
    try:
        # Import regulatory reporting
        from risk_compliance.regulatory_reporting.regulatory_reporting_system import (
            generate_report, schedule_reports
        )
        
        # Schedule all required reports
        scheduled = schedule_reports()
        logger.info(f"Scheduled reports: {scheduled}")
        
        # Generate a specific report
        report_result = generate_report(
            report_type="AML_CTR",
            report_date=datetime.date.today(),
            formats=["JSON"]
        )
        
        if report_result["status"] == "SUCCESS":
            logger.info(f"Generated report: {report_result['report_type']}")
            logger.info(f"Output files: {report_result['output_files']}")
        else:
            logger.warning(f"Failed to generate report: {report_result['message']}")
        
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import regulatory reporting module: {str(e)}")
        return False


def setup_risk_scoring_integration():
    """Set up risk scoring integration examples"""
    logger.info("Setting up risk scoring integration...")
    
    try:
        # Import risk scoring
        from risk_compliance.risk_scoring.risk_scoring_engine import (
            score_customer, score_account, score_transaction, score_loan
        )
        
        # Example customer data
        customer_data = {
            "customer_id": "CUST123",
            "age": 35,
            "credit_score": 720,
            "employment_status": "EMPLOYED",
            "employment_years": 5,
            "income": 60000,
            "address_years": 3,
            "past_delinquencies": 0,
            "banking_history_years": 10,
            "kyc_status": "VERIFIED"
        }
        
        # Score customer
        customer_risk = score_customer(customer_data)
        logger.info(f"Customer risk score: {customer_risk['risk_score']} ({customer_risk['risk_level']})")
        
        # Example transaction data
        transaction_data = {
            "transaction_id": f"TX-{int(datetime.datetime.now().timestamp())}",
            "amount": 5000.0,
            "transaction_type": "TRANSFER",
            "average_tx_amount": 1000.0
        }
        
        # Score transaction
        transaction_risk = score_transaction(transaction_data)
        logger.info(f"Transaction risk score: {transaction_risk['risk_score']} ({transaction_risk['risk_level']})")
        
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import risk scoring module: {str(e)}")
        return False


def main():
    """Main function to demonstrate integration"""
    logger.info("Starting risk compliance integration example")
    
    # Add the parent directory to the path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        # Use centralized import manager
        try:
            from utils.lib.packages import fix_path, import_module
            fix_path()  # Ensures the project root is in sys.path
        except ImportError:
            # Fallback for when the import manager is not available
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed

    # Set up components
    audit_trail_status = setup_audit_trail_integration()
    fraud_detection_status = setup_fraud_detection_integration()
    regulatory_reporting_status = setup_regulatory_reporting_integration()
    risk_scoring_status = setup_risk_scoring_integration()
    
    # Report integration status
    logger.info("\nIntegration Status:")
    logger.info(f"Audit Trail: {'SUCCESS' if audit_trail_status else 'FAILED'}")
    logger.info(f"Fraud Detection: {'SUCCESS' if fraud_detection_status else 'FAILED'}")
    logger.info(f"Regulatory Reporting: {'SUCCESS' if regulatory_reporting_status else 'FAILED'}")
    logger.info(f"Risk Scoring: {'SUCCESS' if risk_scoring_status else 'FAILED'}")
    
    
if __name__ == "__main__":
    main()