# Risk Compliance Module API Reference

This document provides a comprehensive reference for the Risk Compliance Module API. It details all available services, their inputs, outputs, and usage examples.

## Table of Contents

1. [Risk Assessment APIs](#risk-assessment-apis)
   - [Assess Customer Risk](#assess-customer-risk)
   - [Assess Transaction Risk](#assess-transaction-risk)
   - [Assess Account Risk](#assess-account-risk)
2. [Compliance APIs](#compliance-apis)
   - [Validate Transaction Compliance](#validate-transaction-compliance)
   - [Validate Customer Compliance](#validate-customer-compliance)
   - [Generate Compliance Report](#generate-compliance-report)
3. [AML Screening APIs](#aml-screening-apis)
   - [Screen Transaction](#screen-transaction)
   - [Screen Customer](#screen-customer)
   - [Generate AML Alert](#generate-aml-alert)
4. [Error Handling](#error-handling)
   - [Error Response Format](#error-response-format)
   - [Common Error Codes](#common-error-codes)
5. [Data Types](#data-types)
   - [Risk Assessment Result](#risk-assessment-result)
   - [Compliance Validation Result](#compliance-validation-result)
   - [AML Screening Result](#aml-screening-result)

---

## Risk Assessment APIs

### Assess Customer Risk

Assesses the risk level associated with a customer.

**Service Name**: `risk.customer.assess`

**Input**:
```json
{
  "customer_id": "CUST123456",       // Required: Customer identifier
  "assessment_type": "comprehensive", // Optional: basic, comprehensive, enhanced
  "risk_factors": [                   // Optional: Specific risk factors to assess
    "transaction_history",
    "geographic",
    "product_usage",
    "demographic"
  ],
  "context": {                        // Optional: Additional context
    "trigger": "new_account",
    "requested_by": "onboarding_team"
  }
}
```

**Output**:
```json
{
  "customer_id": "CUST123456",
  "risk_score": 65,                   // Overall risk score (0-100)
  "risk_level": "medium",             // risk level: low, medium, high, critical
  "assessment_id": "RA987654321",     // Unique assessment identifier
  "timestamp": "2025-05-20T10:15:35Z",
  "expiry": "2025-08-20T10:15:35Z",   // Expiry of this assessment
  "risk_factors": {                   // Breakdown of risk factors
    "transaction_history": {
      "score": 45,
      "level": "medium",
      "factors": ["high_value_transactions", "frequent_cash_deposits"]
    },
    "geographic": {
      "score": 75,
      "level": "high",
      "factors": ["high_risk_jurisdiction"]
    },
    "product_usage": {
      "score": 25,
      "level": "low",
      "factors": []
    },
    "demographic": {
      "score": 30,
      "level": "low",
      "factors": []
    }
  },
  "recommended_actions": [            // Recommended follow-up actions
    {
      "action": "enhanced_due_diligence",
      "rationale": "Customer has transactions in high-risk jurisdictions",
      "priority": "high"
    },
    {
      "action": "transaction_monitoring",
      "rationale": "Frequent high-value transactions",
      "priority": "medium"
    }
  ],
  "next_assessment_date": "2025-08-20T10:15:35Z" // Recommended next assessment
}
```

**Error Responses**:

* Customer not found:
```json
{
  "success": false,
  "error": {
    "code": "CUSTOMER_NOT_FOUND",
    "message": "Customer not found",
    "details": {
      "customer_id": "CUST123456"
    }
  }
}
```

* Risk assessment failed:
```json
{
  "success": false,
  "error": {
    "code": "RISK_ASSESSMENT_ERROR",
    "message": "Unable to complete risk assessment",
    "details": {
      "reason": "Insufficient customer data for assessment"
    }
  }
}
```

**Usage Example**:

```python
from risk_compliance.module_interface import get_module_instance

risk_module = get_module_instance()

# Assess customer risk
assessment = risk_module.assess_customer_risk("CUST123456")

if "risk_score" in assessment:
    print(f"Customer risk score: {assessment['risk_score']}")
    print(f"Risk level: {assessment['risk_level']}")
    
    if assessment['risk_level'] in ['high', 'critical']:
        print("High risk customer! Recommended actions:")
        for action in assessment['recommended_actions']:
            print(f"- {action['action']}: {action['rationale']}")
else:
    print(f"Risk assessment failed: {assessment.get('error', {}).get('message')}")
```

### Assess Transaction Risk

Assesses the risk level associated with a transaction.

**Service Name**: `risk.transaction.assess`

**Input**:
```json
{
  "transaction_id": "TXN987654321",   // Required: Transaction identifier
  "transaction_data": {                // Required: Transaction details
    "amount": 50000.00,
    "currency": "USD",
    "source_account": "ACC123456",
    "destination_account": "ACC789012",
    "timestamp": "2025-05-20T10:15:30Z",
    "channel": "web",
    "transaction_type": "transfer"
  },
  "assessment_type": "standard",       // Optional: quick, standard, enhanced
  "context": {                         // Optional: Additional context
    "user_ip": "192.168.1.1",
    "user_device": "mobile_ios"
  }
}
```

**Output**:
```json
{
  "transaction_id": "TXN987654321",
  "risk_score": 82,                    // Overall risk score (0-100)
  "risk_level": "high",                // risk level: low, medium, high, critical
  "assessment_id": "RA123456789",      // Unique assessment identifier
  "timestamp": "2025-05-20T10:15:35Z",
  "risk_factors": {                    // Breakdown of risk factors
    "amount": {
      "score": 85,
      "level": "high",
      "factors": ["unusually_high_amount"]
    },
    "destination": {
      "score": 70,
      "level": "high",
      "factors": ["new_counterparty", "high_risk_jurisdiction"]
    },
    "timing": {
      "score": 50,
      "level": "medium",
      "factors": ["outside_normal_hours"]
    },
    "behavior": {
      "score": 60,
      "level": "medium",
      "factors": ["unusual_for_customer"]
    }
  },
  "recommended_actions": [
    {
      "action": "additional_authentication",
      "rationale": "High-value transaction to new counterparty",
      "priority": "high"
    },
    {
      "action": "manual_review",
      "rationale": "Multiple high-risk factors identified",
      "priority": "high"
    }
  ],
  "allow_transaction": false,          // Whether transaction should proceed
  "additional_info": {
    "threshold_breached": "single_transaction_limit",
    "expected_range": "0-25000"
  }
}
```

**Usage Example**:

```python
# Transaction data
transaction_data = {
    "amount": 50000.00,
    "currency": "USD",
    "source_account": "ACC123456",
    "destination_account": "ACC789012",
    "timestamp": "2025-05-20T10:15:30Z",
    "channel": "web",
    "transaction_type": "transfer"
}

# Assess transaction risk
risk_data = {
    "transaction_id": "TXN987654321",
    "transaction_data": transaction_data
}

assessment = risk_module.assess_transaction_risk(risk_data)

if "risk_score" in assessment:
    print(f"Transaction risk score: {assessment['risk_score']}")
    print(f"Risk level: {assessment['risk_level']}")
    
    if not assessment.get('allow_transaction', True):
        print("HIGH RISK: Transaction should not proceed!")
        print("Reasons:")
        for factor_type, factor_data in assessment['risk_factors'].items():
            if factor_data['level'] in ['high', 'critical']:
                factors = ", ".join(factor_data['factors'])
                print(f"- {factor_type.title()}: {factors}")
```

### Assess Account Risk

Assesses the risk level associated with an account.

**Service Name**: `risk.account.assess`

**Input**:
```json
{
  "account_id": "ACC123456",          // Required: Account identifier
  "assessment_type": "standard",       // Optional: quick, standard, enhanced
  "time_period": {                     // Optional: Assessment time period
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-05-20T23:59:59Z"
  }
}
```

**Output**:
```json
{
  "account_id": "ACC123456",
  "risk_score": 42,                    // Overall risk score (0-100)
  "risk_level": "medium",              // risk level: low, medium, high, critical
  "assessment_id": "RA567890123",      // Unique assessment identifier
  "timestamp": "2025-05-20T10:20:35Z",
  "account_type": "savings",
  "risk_factors": {                    // Breakdown of risk factors
    "transaction_pattern": {
      "score": 30,
      "level": "low",
      "factors": []
    },
    "balance_volatility": {
      "score": 65,
      "level": "medium",
      "factors": ["sudden_balance_changes"]
    },
    "dormancy": {
      "score": 20,
      "level": "low",
      "factors": []
    },
    "customer_profile": {
      "score": 55,
      "level": "medium",
      "factors": ["mid_risk_customer_association"]
    }
  },
  "recommended_actions": [
    {
      "action": "regular_monitoring",
      "rationale": "Medium risk account with some balance volatility",
      "priority": "medium"
    }
  ],
  "next_assessment_date": "2025-08-20T10:20:35Z"
}
```

## Compliance APIs

### Validate Transaction Compliance

Validates if a transaction complies with relevant regulations.

**Service Name**: `compliance.transaction.validate`

**Input**:
```json
{
  "transaction_id": "TXN987654321",   // Required: Transaction identifier
  "transaction_data": {                // Required: Transaction details
    "amount": 50000.00,
    "currency": "USD",
    "source_account": "ACC123456",
    "destination_account": "ACC789012",
    "timestamp": "2025-05-20T10:15:30Z",
    "channel": "web",
    "transaction_type": "transfer"
  },
  "compliance_types": [                // Optional: Specific compliance types to check
    "aml",
    "sanctions",
    "regulatory_limits",
    "internal_policy"
  ]
}
```

**Output**:
```json
{
  "transaction_id": "TXN987654321",
  "compliant": false,                  // Overall compliance result
  "validation_id": "CV123456789",      // Unique validation identifier
  "timestamp": "2025-05-20T10:15:40Z",
  "compliance_results": {              // Detailed compliance results
    "aml": {
      "compliant": true,
      "rules_checked": 12,
      "details": {}
    },
    "sanctions": {
      "compliant": true,
      "rules_checked": 5,
      "details": {}
    },
    "regulatory_limits": {
      "compliant": false,
      "rules_checked": 8,
      "violations": [
        {
          "rule_id": "REG_LIMIT_01",
          "description": "Single transaction limit exceeded",
          "severity": "high",
          "details": {
            "limit": 25000.00,
            "actual": 50000.00
          }
        }
      ]
    },
    "internal_policy": {
      "compliant": true,
      "rules_checked": 10,
      "details": {}
    }
  },
  "required_actions": [                // Required actions to achieve compliance
    {
      "action": "obtain_approval",
      "description": "Obtain senior management approval for exceeding transaction limit",
      "required": true
    },
    {
      "action": "document_purpose",
      "description": "Document purpose of high-value transaction",
      "required": true
    }
  ],
  "references": {                      // Regulatory references
    "regulatory_limits": [
      {
        "regulation": "Bank Secrecy Act",
        "section": "Section 5318(g)",
        "description": "Reporting requirements for large currency transactions"
      }
    ]
  }
}
```

**Usage Example**:

```python
# Validate transaction compliance
transaction_data = {
    "amount": 50000.00,
    "currency": "USD",
    "source_account": "ACC123456",
    "destination_account": "ACC789012",
    "timestamp": "2025-05-20T10:15:30Z",
    "channel": "web",
    "transaction_type": "transfer"
}

compliance_data = {
    "transaction_id": "TXN987654321",
    "transaction_data": transaction_data
}

compliance_result = risk_module.validate_transaction_compliance(compliance_data)

if compliance_result.get("compliant"):
    print("Transaction is compliant with all regulations")
else:
    print("Transaction has compliance issues:")
    
    # Print all violations
    for compliance_type, result in compliance_result.get("compliance_results", {}).items():
        if not result.get("compliant"):
            print(f"\n{compliance_type.upper()} violations:")
            for violation in result.get("violations", []):
                print(f"- {violation['description']} (Severity: {violation['severity']})")
    
    # Print required actions
    print("\nRequired actions:")
    for action in compliance_result.get("required_actions", []):
        print(f"- {action['description']}")
```

### Validate Customer Compliance

Validates if a customer's profile and activities comply with relevant regulations.

**Service Name**: `compliance.customer.validate`

**Input**:
```json
{
  "customer_id": "CUST123456",        // Required: Customer identifier
  "compliance_types": [                // Optional: Specific compliance types to check
    "kyc",
    "aml",
    "sanctions",
    "pep",
    "fatca",
    "crs"
  ],
  "context": {                         // Optional: Additional context
    "trigger": "periodic_review",
    "review_date": "2025-05-20"
  }
}
```

**Output**:
```json
{
  "customer_id": "CUST123456",
  "compliant": true,                   // Overall compliance result
  "validation_id": "CV987654321",      // Unique validation identifier
  "timestamp": "2025-05-20T10:25:40Z",
  "compliance_results": {              // Detailed compliance results
    "kyc": {
      "compliant": true,
      "rules_checked": 15,
      "details": {
        "kyc_status": "verified",
        "last_verified": "2025-01-15T14:30:22Z",
        "documentation_status": "complete"
      }
    },
    "aml": {
      "compliant": true,
      "rules_checked": 8,
      "details": {}
    },
    "sanctions": {
      "compliant": true,
      "rules_checked": 6,
      "details": {
        "lists_checked": ["UN", "OFAC", "EU", "UK"],
        "last_checked": "2025-05-19T08:15:30Z"
      }
    },
    "pep": {
      "compliant": true,
      "rules_checked": 3,
      "details": {
        "pep_status": "not_pep",
        "last_checked": "2025-05-19T08:15:30Z"
      }
    },
    "fatca": {
      "compliant": true,
      "rules_checked": 5,
      "details": {
        "fatca_status": "non_us_person",
        "documentation": "self_certification"
      }
    },
    "crs": {
      "compliant": true,
      "rules_checked": 4,
      "details": {
        "crs_status": "reported",
        "last_reported": "2025-01-31T23:59:59Z"
      }
    }
  },
  "next_review_date": "2025-11-20T10:25:40Z"  // Next scheduled review date
}
```

### Generate Compliance Report

Generates a compliance report for regulatory or internal purposes.

**Service Name**: `compliance.reporting.generate`

**Input**:
```json
{
  "report_type": "suspicious_activity",  // Required: Report type
  "time_period": {                       // Required: Reporting period
    "start_date": "2025-05-01T00:00:00Z",
    "end_date": "2025-05-20T23:59:59Z"
  },
  "parameters": {                        // Optional: Report parameters
    "threshold": 10000.00,
    "include_pending": true,
    "jurisdiction": "US"
  },
  "format": "json"                       // Optional: Report format (json, csv, pdf)
}
```

**Output**:
```json
{
  "report_id": "RPT123456789",           // Unique report identifier
  "report_type": "suspicious_activity",
  "generation_timestamp": "2025-05-20T10:35:40Z",
  "time_period": {
    "start_date": "2025-05-01T00:00:00Z",
    "end_date": "2025-05-20T23:59:59Z"
  },
  "summary": {                           // Report summary
    "total_records": 3,
    "total_amount": 175000.00,
    "currency": "USD",
    "high_risk_count": 2,
    "medium_risk_count": 1,
    "low_risk_count": 0
  },
  "records": [                           // Detailed records
    {
      "transaction_id": "TXN987654321",
      "timestamp": "2025-05-20T10:15:30Z",
      "amount": 50000.00,
      "currency": "USD",
      "source_account": "ACC123456",
      "destination_account": "ACC789012",
      "risk_level": "high",
      "risk_factors": ["unusually_high_amount", "new_counterparty"],
      "alert_id": "ALT123456"
    },
    {
      "transaction_id": "TXN987654320",
      "timestamp": "2025-05-15T14:30:22Z",
      "amount": 100000.00,
      "currency": "USD",
      "source_account": "ACC123457",
      "destination_account": "ACC789013",
      "risk_level": "high",
      "risk_factors": ["high_risk_jurisdiction", "structuring_pattern"],
      "alert_id": "ALT123457"
    },
    {
      "transaction_id": "TXN987654319",
      "timestamp": "2025-05-10T09:45:12Z",
      "amount": 25000.00,
      "currency": "USD",
      "source_account": "ACC123458",
      "destination_account": "ACC789014",
      "risk_level": "medium",
      "risk_factors": ["unusual_for_customer"],
      "alert_id": "ALT123458"
    }
  ],
  "regulatory_filing_status": {          // Regulatory filing information
    "required": true,
    "deadline": "2025-06-19T23:59:59Z",
    "filing_id": "SAR-2025-123456"
  },
  "report_url": "https://example.com/reports/RPT123456789.pdf"  // Report download URL (if format != json)
}
```

## AML Screening APIs

### Screen Transaction

Screens a transaction against AML rules and watchlists.

**Service Name**: `aml.transaction.screen`

**Input**:
```json
{
  "transaction_id": "TXN987654321",   // Required: Transaction identifier
  "transaction_data": {                // Required: Transaction details
    "amount": 50000.00,
    "currency": "USD",
    "source_account": "ACC123456",
    "source_customer_id": "CUST123456",
    "destination_account": "ACC789012",
    "destination_customer_id": "CUST789012",
    "timestamp": "2025-05-20T10:15:30Z",
    "channel": "web",
    "transaction_type": "transfer"
  },
  "screening_type": "comprehensive",   // Optional: quick, standard, comprehensive
  "watchlists": [                      // Optional: Specific watchlists to check
    "sanctions",
    "pep",
    "adverse_media"
  ]
}
```

**Output**:
```json
{
  "transaction_id": "TXN987654321",
  "screening_id": "SCR123456789",      // Unique screening identifier
  "timestamp": "2025-05-20T10:15:45Z",
  "result": "alert",                   // result: clear, alert, block
  "alerts": [                          // Alerts generated during screening
    {
      "alert_id": "ALT123456",
      "type": "pattern_match",
      "severity": "high",
      "description": "Transaction pattern matches money laundering typology",
      "rule_id": "AML-PATTERN-023",
      "confidence": 0.85
    },
    {
      "alert_id": "ALT123457",
      "type": "destination_risk",
      "severity": "medium",
      "description": "Destination account in high-risk jurisdiction",
      "rule_id": "AML-DEST-008",
      "confidence": 0.72
    }
  ],
  "screening_details": {               // Detailed screening results
    "sanctions": {
      "result": "clear",
      "lists_checked": ["UN", "OFAC", "EU", "UK"],
      "timestamp": "2025-05-20T10:15:42Z"
    },
    "pep": {
      "result": "clear",
      "lists_checked": ["Global PEP Database"],
      "timestamp": "2025-05-20T10:15:43Z"
    },
    "adverse_media": {
      "result": "clear",
      "sources_checked": 15,
      "timestamp": "2025-05-20T10:15:44Z"
    },
    "typologies": {
      "result": "match",
      "matches": [
        {
          "typology_id": "ML-TYP-023",
          "description": "Structured transfers to high-risk jurisdictions",
          "confidence": 0.85
        }
      ],
      "timestamp": "2025-05-20T10:15:45Z"
    }
  },
  "recommended_actions": [
    {
      "action": "enhanced_due_diligence",
      "description": "Conduct enhanced due diligence on transaction purpose",
      "required": true
    },
    {
      "action": "file_sar",
      "description": "File Suspicious Activity Report",
      "required": true
    }
  ],
  "allow_transaction": false           // Whether transaction should proceed
}
```

**Usage Example**:

```python
# Screen transaction for AML
transaction_data = {
    "amount": 50000.00,
    "currency": "USD",
    "source_account": "ACC123456",
    "source_customer_id": "CUST123456",
    "destination_account": "ACC789012",
    "destination_customer_id": "CUST789012",
    "timestamp": "2025-05-20T10:15:30Z",
    "channel": "web",
    "transaction_type": "transfer"
}

screening_data = {
    "transaction_id": "TXN987654321",
    "transaction_data": transaction_data,
    "screening_type": "comprehensive"
}

screening_result = risk_module.screen_transaction(screening_data)

if screening_result.get("result") == "clear":
    print("Transaction cleared AML screening")
elif screening_result.get("result") == "alert":
    print("Transaction generated AML alerts:")
    for alert in screening_result.get("alerts", []):
        print(f"- {alert['description']} (Severity: {alert['severity']})")
    
    if not screening_result.get("allow_transaction", True):
        print("\nTransaction should be blocked.")
else:  # "block"
    print("Transaction blocked by AML screening")
```

### Screen Customer

Screens a customer against AML/KYC watchlists.

**Service Name**: `aml.customer.screen`

**Input**:
```json
{
  "customer_id": "CUST123456",        // Required: Customer identifier
  "screening_type": "comprehensive",   // Optional: quick, standard, comprehensive
  "watchlists": [                      // Optional: Specific watchlists to check
    "sanctions",
    "pep",
    "adverse_media",
    "fatf_blacklist"
  ]
}
```

**Output**:
```json
{
  "customer_id": "CUST123456",
  "screening_id": "SCR987654321",      // Unique screening identifier
  "timestamp": "2025-05-20T10:20:45Z",
  "result": "clear",                   // result: clear, alert, block
  "screening_details": {               // Detailed screening results
    "sanctions": {
      "result": "clear",
      "lists_checked": ["UN", "OFAC", "EU", "UK"],
      "timestamp": "2025-05-20T10:20:42Z"
    },
    "pep": {
      "result": "clear",
      "lists_checked": ["Global PEP Database"],
      "timestamp": "2025-05-20T10:20:43Z"
    },
    "adverse_media": {
      "result": "clear",
      "sources_checked": 15,
      "timestamp": "2025-05-20T10:20:44Z"
    },
    "fatf_blacklist": {
      "result": "clear",
      "countries_checked": ["high_risk_countries"],
      "timestamp": "2025-05-20T10:20:45Z"
    }
  },
  "next_screening_date": "2025-11-20T10:20:45Z" // Next scheduled screening date
}
```

### Generate AML Alert

Generates an AML alert for suspicious activity.

**Service Name**: `aml.alert.generate`

**Input**:
```json
{
  "alert_type": "suspicious_activity", // Required: Alert type
  "entity_type": "transaction",        // Required: Entity type (transaction, customer, account)
  "entity_id": "TXN987654321",         // Required: Entity identifier
  "detection_source": "automated",     // Required: automated, manual
  "confidence": 0.85,                  // Required: Confidence score (0.0-1.0)
  "details": {                         // Required: Alert details
    "description": "Transaction pattern matches money laundering typology",
    "rule_id": "AML-PATTERN-023",
    "detection_time": "2025-05-20T10:15:45Z"
  },
  "related_entities": [                // Optional: Related entities
    {
      "entity_type": "customer",
      "entity_id": "CUST123456",
      "relationship": "transaction_source"
    },
    {
      "entity_type": "account",
      "entity_id": "ACC123456",
      "relationship": "source_account"
    }
  ]
}
```

**Output**:
```json
{
  "alert_id": "ALT123456",             // Unique alert identifier
  "status": "open",                    // Status: open, under_review, closed
  "creation_timestamp": "2025-05-20T10:25:45Z",
  "alert_type": "suspicious_activity",
  "entity_type": "transaction",
  "entity_id": "TXN987654321",
  "detection_source": "automated",
  "confidence": 0.85,
  "priority": "high",                  // Priority based on confidence and type
  "details": {
    "description": "Transaction pattern matches money laundering typology",
    "rule_id": "AML-PATTERN-023",
    "detection_time": "2025-05-20T10:15:45Z"
  },
  "related_entities": [
    {
      "entity_type": "customer",
      "entity_id": "CUST123456",
      "relationship": "transaction_source"
    },
    {
      "entity_type": "account",
      "entity_id": "ACC123456",
      "relationship": "source_account"
    }
  ],
  "required_actions": [                // Required follow-up actions
    {
      "action": "review",
      "description": "Review alert details",
      "deadline": "2025-05-21T10:25:45Z",
      "assigned_to": "aml_team"
    },
    {
      "action": "decision",
      "description": "Decide on alert disposition",
      "deadline": "2025-05-22T10:25:45Z",
      "assigned_to": "aml_team"
    }
  ],
  "regulatory_filing": {               // Regulatory filing information
    "required": true,
    "filing_type": "SAR",
    "deadline": "2025-06-19T23:59:59Z"
  }
}
```

## Error Handling

### Error Response Format

All error responses follow this standard format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",              // Machine-readable error code
    "message": "Human-readable error message", // User-friendly error message
    "details": {                       // Optional error details
      "field": "field_name",           // Field causing the error (if applicable)
      "value": "invalid_value",        // Invalid value (if applicable)
      "additional_info": "Additional error information"
    },
    "timestamp": "2025-05-20T10:15:35Z" // Error timestamp
  },
  "request_id": "REQ123456789"         // Request identifier for support reference
}
```

### Common Error Codes

| Error Code | Description | HTTP Status |
|------------|-------------|------------|
| `CUSTOMER_NOT_FOUND` | Customer not found | 404 |
| `ACCOUNT_NOT_FOUND` | Account not found | 404 |
| `TRANSACTION_NOT_FOUND` | Transaction not found | 404 |
| `RISK_ASSESSMENT_ERROR` | Error during risk assessment | 500 |
| `COMPLIANCE_VALIDATION_ERROR` | Error during compliance validation | 500 |
| `AML_SCREENING_ERROR` | Error during AML screening | 500 |
| `REGULATORY_REPORTING_ERROR` | Error generating regulatory report | 500 |
| `VALIDATION_ERROR` | Invalid input data | 400 |
| `COMPLIANCE_VIOLATION` | Compliance rule violation | 403 |
| `AML_ALERT` | AML alert generated | 200 |
| `SERVICE_UNAVAILABLE` | Risk compliance service unavailable | 503 |

## Data Types

### Risk Assessment Result

| Field | Type | Description |
|-------|------|------------|
| `risk_score` | Integer | Overall risk score (0-100) |
| `risk_level` | String | Risk level: low, medium, high, critical |
| `assessment_id` | String | Unique assessment identifier |
| `timestamp` | String | Assessment timestamp (ISO format) |
| `risk_factors` | Object | Breakdown of risk factors by category |
| `recommended_actions` | Array | Recommended follow-up actions |
| `next_assessment_date` | String | Next scheduled assessment date |

### Compliance Validation Result

| Field | Type | Description |
|-------|------|------------|
| `compliant` | Boolean | Overall compliance result |
| `validation_id` | String | Unique validation identifier |
| `timestamp` | String | Validation timestamp (ISO format) |
| `compliance_results` | Object | Detailed compliance results by category |
| `required_actions` | Array | Required actions to achieve compliance |
| `references` | Object | Regulatory references |
| `next_review_date` | String | Next scheduled review date |

### AML Screening Result

| Field | Type | Description |
|-------|------|------------|
| `screening_id` | String | Unique screening identifier |
| `timestamp` | String | Screening timestamp (ISO format) |
| `result` | String | Screening result: clear, alert, block |
| `alerts` | Array | Alerts generated during screening |
| `screening_details` | Object | Detailed screening results by category |
| `recommended_actions` | Array | Recommended follow-up actions |
| `allow_transaction` | Boolean | Whether transaction should proceed |
| `next_screening_date` | String | Next scheduled screening date |
