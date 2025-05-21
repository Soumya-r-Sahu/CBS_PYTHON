"""
Risk Compliance Module Usage Examples

This module provides examples of how to use the risk compliance module
for common risk assessment, compliance validation, and AML screening scenarios.

Usage:
    python -m risk_compliance.examples.module_usage_examples

Tags: risk_compliance, examples, usage, tutorial, aml, regulatory
AI-Metadata:
    component_type: examples
    purpose: demonstration
    usage_pattern: reference
    regulatory_relevance: medium
"""

import logging
from datetime import datetime, timedelta
import json

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the risk compliance module
try:
    from risk_compliance.module_interface import get_module_instance
except ImportError:
    logger.error("Failed to import risk_compliance module. Make sure it's in your Python path.")
    raise

def example_customer_risk_assessment():
    """
    Example of assessing customer risk
    """
    logger.info("--- Customer Risk Assessment Example ---")
    
    # Get risk compliance module instance
    risk_module = get_module_instance()
    
    # Customer ID to assess
    customer_id = "CUST123456"
    
    # Assessment parameters
    assessment_params = {
        "customer_id": customer_id,
        "assessment_type": "comprehensive",
        "risk_factors": [
            "transaction_history",
            "geographic",
            "product_usage",
            "demographic"
        ]
    }
    
    # Assess customer risk
    logger.info(f"Assessing risk for customer: {customer_id}")
    assessment = risk_module.assess_customer_risk(assessment_params)
    
    # Display the results
    if "risk_score" in assessment:
        logger.info(f"Customer risk score: {assessment['risk_score']}")
        logger.info(f"Risk level: {assessment['risk_level']}")
        
        # Display risk factors for high risk areas
        logger.info("Risk factors breakdown:")
        for factor_type, factor_data in assessment.get('risk_factors', {}).items():
            logger.info(f"  {factor_type.title()}: {factor_data['score']} ({factor_data['level']})")
            if factor_data['level'] in ['high', 'critical'] and 'factors' in factor_data:
                factors = ", ".join(factor_data['factors'])
                logger.info(f"    - Factors: {factors}")
        
        # Display recommended actions
        if 'recommended_actions' in assessment:
            logger.info("Recommended actions:")
            for action in assessment['recommended_actions']:
                logger.info(f"  - {action['action']} (Priority: {action['priority']})")
                logger.info(f"    Rationale: {action['rationale']}")
        
        return True
    else:
        logger.error(f"Risk assessment failed: {assessment.get('error', {}).get('message', 'Unknown error')}")
        return False

def example_transaction_risk_assessment():
    """
    Example of assessing transaction risk
    """
    logger.info("--- Transaction Risk Assessment Example ---")
    
    # Get risk compliance module instance
    risk_module = get_module_instance()
    
    # Create transaction data
    transaction_data = {
        "amount": 50000.00,
        "currency": "USD",
        "source_account": "ACC123456",
        "destination_account": "ACC789012",
        "timestamp": datetime.now().isoformat(),
        "channel": "web",
        "transaction_type": "transfer"
    }
    
    # Assessment parameters
    assessment_params = {
        "transaction_id": f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "transaction_data": transaction_data,
        "assessment_type": "standard"
    }
    
    # Assess transaction risk
    logger.info(f"Assessing risk for transaction: {assessment_params['transaction_id']}")
    assessment = risk_module.assess_transaction_risk(assessment_params)
    
    # Display the results
    if "risk_score" in assessment:
        logger.info(f"Transaction risk score: {assessment['risk_score']}")
        logger.info(f"Risk level: {assessment['risk_level']}")
        
        # Check if transaction should proceed
        if assessment.get('allow_transaction', True):
            logger.info("Transaction can proceed")
        else:
            logger.warning("HIGH RISK: Transaction should not proceed!")
        
        # Display risk factors
        logger.info("Risk factors breakdown:")
        for factor_type, factor_data in assessment.get('risk_factors', {}).items():
            logger.info(f"  {factor_type.title()}: {factor_data['score']} ({factor_data['level']})")
            if 'factors' in factor_data and factor_data['factors']:
                factors = ", ".join(factor_data['factors'])
                logger.info(f"    - Factors: {factors}")
        
        # Display recommended actions
        if 'recommended_actions' in assessment:
            logger.info("Recommended actions:")
            for action in assessment['recommended_actions']:
                logger.info(f"  - {action['action']} (Priority: {action['priority']})")
                logger.info(f"    Rationale: {action['rationale']}")
        
        return True
    else:
        logger.error(f"Risk assessment failed: {assessment.get('error', {}).get('message', 'Unknown error')}")
        return False

def example_transaction_compliance_check():
    """
    Example of checking transaction compliance
    """
    logger.info("--- Transaction Compliance Check Example ---")
    
    # Get risk compliance module instance
    risk_module = get_module_instance()
    
    # Create transaction data
    transaction_data = {
        "amount": 50000.00,
        "currency": "USD",
        "source_account": "ACC123456",
        "destination_account": "ACC789012",
        "timestamp": datetime.now().isoformat(),
        "channel": "web",
        "transaction_type": "transfer"
    }
    
    # Compliance check parameters
    compliance_params = {
        "transaction_id": f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "transaction_data": transaction_data,
        "compliance_types": [
            "aml",
            "sanctions",
            "regulatory_limits",
            "internal_policy"
        ]
    }
    
    # Check transaction compliance
    logger.info(f"Checking compliance for transaction: {compliance_params['transaction_id']}")
    compliance_result = risk_module.validate_transaction_compliance(compliance_params)
    
    # Display the results
    if "compliant" in compliance_result:
        if compliance_result["compliant"]:
            logger.info("Transaction is compliant with all regulations")
        else:
            logger.warning("Transaction has compliance issues")
            
            # Print violations
            for compliance_type, result in compliance_result.get("compliance_results", {}).items():
                if not result.get("compliant", True):
                    logger.warning(f"\n{compliance_type.upper()} violations:")
                    for violation in result.get("violations", []):
                        logger.warning(f"- {violation['description']} (Severity: {violation['severity']})")
                        if 'details' in violation:
                            logger.warning(f"  Details: {json.dumps(violation['details'])}")
            
            # Print required actions
            if 'required_actions' in compliance_result:
                logger.info("\nRequired actions to achieve compliance:")
                for action in compliance_result['required_actions']:
                    required = "REQUIRED" if action.get('required', False) else "RECOMMENDED"
                    logger.info(f"- {action['description']} ({required})")
            
            # Print regulatory references
            if 'references' in compliance_result:
                logger.info("\nRegulatory references:")
                for ref_type, references in compliance_result['references'].items():
                    for reference in references:
                        logger.info(f"- {reference.get('regulation', 'Unknown')}: {reference.get('description', 'No description')}")
        
        return True
    else:
        logger.error(f"Compliance check failed: {compliance_result.get('error', {}).get('message', 'Unknown error')}")
        return False

def example_customer_compliance_check():
    """
    Example of checking customer compliance
    """
    logger.info("--- Customer Compliance Check Example ---")
    
    # Get risk compliance module instance
    risk_module = get_module_instance()
    
    # Customer ID to check
    customer_id = "CUST123456"
    
    # Compliance check parameters
    compliance_params = {
        "customer_id": customer_id,
        "compliance_types": [
            "kyc",
            "aml",
            "sanctions",
            "pep",
            "fatca",
            "crs"
        ],
        "context": {
            "trigger": "periodic_review",
            "review_date": datetime.now().strftime("%Y-%m-%d")
        }
    }
    
    # Check customer compliance
    logger.info(f"Checking compliance for customer: {customer_id}")
    compliance_result = risk_module.validate_customer_compliance(compliance_params)
    
    # Display the results
    if "compliant" in compliance_result:
        if compliance_result["compliant"]:
            logger.info("Customer is compliant with all regulations")
            
            # Print compliance details
            for compliance_type, result in compliance_result.get("compliance_results", {}).items():
                logger.info(f"\n{compliance_type.upper()} status:")
                logger.info(f"- Compliant: {result.get('compliant', False)}")
                logger.info(f"- Rules checked: {result.get('rules_checked', 0)}")
                if 'details' in result:
                    for key, value in result['details'].items():
                        logger.info(f"- {key}: {value}")
        else:
            logger.warning("Customer has compliance issues")
            
            # Print violations
            for compliance_type, result in compliance_result.get("compliance_results", {}).items():
                if not result.get("compliant", True):
                    logger.warning(f"\n{compliance_type.upper()} violations:")
                    for violation in result.get("violations", []):
                        logger.warning(f"- {violation.get('description', 'No description')}")
        
        # Print next review date
        if 'next_review_date' in compliance_result:
            logger.info(f"\nNext compliance review scheduled for: {compliance_result['next_review_date']}")
        
        return True
    else:
        logger.error(f"Compliance check failed: {compliance_result.get('error', {}).get('message', 'Unknown error')}")
        return False

def example_aml_transaction_screening():
    """
    Example of screening a transaction for AML
    """
    logger.info("--- AML Transaction Screening Example ---")
    
    # Get risk compliance module instance
    risk_module = get_module_instance()
    
    # Create transaction data
    transaction_data = {
        "amount": 50000.00,
        "currency": "USD",
        "source_account": "ACC123456",
        "source_customer_id": "CUST123456",
        "destination_account": "ACC789012",
        "destination_customer_id": "CUST789012",
        "timestamp": datetime.now().isoformat(),
        "channel": "web",
        "transaction_type": "transfer"
    }
    
    # Screening parameters
    screening_params = {
        "transaction_id": f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "transaction_data": transaction_data,
        "screening_type": "comprehensive",
        "watchlists": [
            "sanctions",
            "pep",
            "adverse_media"
        ]
    }
    
    # Screen transaction
    logger.info(f"Screening transaction: {screening_params['transaction_id']}")
    screening_result = risk_module.screen_transaction(screening_params)
    
    # Display the results
    if "result" in screening_result:
        logger.info(f"Screening result: {screening_result['result']}")
        
        if screening_result["result"] == "clear":
            logger.info("Transaction cleared AML screening")
        elif screening_result["result"] == "alert":
            logger.warning("Transaction generated AML alerts:")
            
            # Print alerts
            for alert in screening_result.get("alerts", []):
                logger.warning(f"- {alert.get('description')} (Severity: {alert.get('severity')})")
                logger.warning(f"  Type: {alert.get('type')}, Confidence: {alert.get('confidence', 0)}")
            
            # Check if transaction should proceed
            if screening_result.get("allow_transaction", True):
                logger.info("\nTransaction can proceed with additional monitoring")
            else:
                logger.warning("\nTransaction should be blocked")
                
            # Print recommended actions
            if 'recommended_actions' in screening_result:
                logger.info("\nRecommended actions:")
                for action in screening_result['recommended_actions']:
                    required = "REQUIRED" if action.get('required', False) else "RECOMMENDED"
                    logger.info(f"- {action['description']} ({required})")
        else:  # "block"
            logger.error("Transaction blocked by AML screening")
        
        # Print screening details
        logger.info("\nScreening details:")
        for list_name, details in screening_result.get("screening_details", {}).items():
            logger.info(f"- {list_name.title()}: {details.get('result', 'unknown')}")
            if details.get('result') == 'match' and 'matches' in details:
                for match in details['matches']:
                    logger.info(f"  - Match: {match.get('description', 'No description')}")
                    logger.info(f"    Confidence: {match.get('confidence', 0)}")
        
        return True
    else:
        logger.error(f"AML screening failed: {screening_result.get('error', {}).get('message', 'Unknown error')}")
        return False

def example_regulatory_report_generation():
    """
    Example of generating a regulatory report
    """
    logger.info("--- Regulatory Report Generation Example ---")
    
    # Get risk compliance module instance
    risk_module = get_module_instance()
    
    # Report parameters
    now = datetime.now()
    start_date = (now - timedelta(days=20)).replace(hour=0, minute=0, second=0).isoformat()
    end_date = now.replace(hour=23, minute=59, second=59).isoformat()
    
    report_params = {
        "report_type": "suspicious_activity",
        "time_period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "parameters": {
            "threshold": 10000.00,
            "include_pending": True,
            "jurisdiction": "US"
        },
        "format": "json"
    }
    
    # Generate report
    logger.info(f"Generating {report_params['report_type']} report")
    report_result = risk_module.generate_compliance_report(report_params)
    
    # Display the results
    if "report_id" in report_result:
        logger.info(f"Report generated successfully. Report ID: {report_result['report_id']}")
        
        # Print report summary
        if 'summary' in report_result:
            summary = report_result['summary']
            logger.info("\nReport summary:")
            logger.info(f"- Total records: {summary.get('total_records', 0)}")
            logger.info(f"- Total amount: {summary.get('total_amount', 0)} {summary.get('currency', 'USD')}")
            logger.info(f"- High risk: {summary.get('high_risk_count', 0)}")
            logger.info(f"- Medium risk: {summary.get('medium_risk_count', 0)}")
            logger.info(f"- Low risk: {summary.get('low_risk_count', 0)}")
        
        # Print regulatory filing status
        if 'regulatory_filing_status' in report_result:
            filing = report_result['regulatory_filing_status']
            logger.info("\nRegulatory filing status:")
            logger.info(f"- Required: {filing.get('required', False)}")
            if filing.get('required', False):
                logger.info(f"- Filing ID: {filing.get('filing_id', 'Not assigned')}")
                logger.info(f"- Deadline: {filing.get('deadline', 'Not specified')}")
        
        # Print report access
        if 'report_url' in report_result:
            logger.info(f"\nReport available at: {report_result['report_url']}")
        
        return True
    else:
        logger.error(f"Report generation failed: {report_result.get('error', {}).get('message', 'Unknown error')}")
        return False

def run_examples():
    """Run all risk compliance examples"""
    example_results = []
    
    # Run all examples and collect results
    example_results.append(("Customer Risk Assessment", example_customer_risk_assessment()))
    example_results.append(("Transaction Risk Assessment", example_transaction_risk_assessment()))
    example_results.append(("Transaction Compliance Check", example_transaction_compliance_check()))
    example_results.append(("Customer Compliance Check", example_customer_compliance_check()))
    example_results.append(("AML Transaction Screening", example_aml_transaction_screening()))
    example_results.append(("Regulatory Report Generation", example_regulatory_report_generation()))
    
    # Print summary
    logger.info("\n--- Examples Summary ---")
    for name, result in example_results:
        status = "SUCCESS" if result else "FAILURE"
        logger.info(f"{name}: {status}")

if __name__ == "__main__":
    # Run all examples
    run_examples()
