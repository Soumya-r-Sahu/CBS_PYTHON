"""
Error Handling Utilities for Risk Compliance Module

This module provides standardized error handling utilities for the risk compliance module.
It implements a consistent approach to error handling, logging, and error response generation.

Tags: risk_compliance, error_handling, exceptions, logging, aml, regulatory
AI-Metadata:
    component_type: error_handler
    criticality: high
    purpose: standardized_error_handling
    impact_on_failure: inconsistent_error_responses
    regulatory_impact: high
"""

import logging
import traceback
from typing import Dict, Any, Optional, Union
from http import HTTPStatus
import json
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

class RiskComplianceError(Exception):
    """Base exception class for all risk compliance service errors"""
    
    def __init__(self, 
                 message: str, 
                 error_code: str = "RISK_COMPLIANCE_ERROR", 
                 status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a risk compliance error

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            status_code: HTTP status code
            details: Additional error details
        
        AI-Metadata:
            purpose: Create standardized error object
            criticality: high
            regulatory_impact: potential_reporting_requirement
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()


class ValidationError(RiskComplianceError):
    """Exception raised for validation errors in risk compliance operations"""
    
    def __init__(self, 
                 message: str, 
                 field: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a validation error

        Args:
            message: Human-readable error message
            field: The field that failed validation
            details: Additional error details
        """
        error_details = details or {}
        if field:
            error_details["field"] = field
            
        super().__init__(
            message=message,
            error_code="RISK_VALIDATION_ERROR",
            status_code=HTTPStatus.BAD_REQUEST,
            details=error_details
        )


class ComplianceViolationError(RiskComplianceError):
    """Exception raised when a compliance rule is violated"""
    
    def __init__(self, 
                 message: str,
                 rule_id: str,
                 severity: str = "high",
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a compliance violation error

        Args:
            message: Human-readable error message
            rule_id: The identifier of the violated rule
            severity: The severity of the violation (low, medium, high, critical)
            details: Additional error details
        """
        error_details = details or {}
        error_details.update({
            "rule_id": rule_id,
            "severity": severity,
            "requires_reporting": severity in ["high", "critical"],
        })
            
        super().__init__(
            message=message,
            error_code="COMPLIANCE_VIOLATION",
            status_code=HTTPStatus.FORBIDDEN,
            details=error_details
        )


class AMLAlertError(RiskComplianceError):
    """Exception raised for AML (Anti-Money Laundering) alerts"""
    
    def __init__(self, 
                 message: str,
                 alert_type: str,
                 confidence: float,
                 entity_id: str,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize an AML alert error

        Args:
            message: Human-readable error message
            alert_type: The type of AML alert
            confidence: Confidence score (0.0 to 1.0)
            entity_id: The ID of the entity (customer, account, transaction)
            details: Additional error details
        """
        error_details = details or {}
        error_details.update({
            "alert_type": alert_type,
            "confidence": confidence,
            "entity_id": entity_id,
            "requires_review": confidence > 0.7,
            "requires_reporting": confidence > 0.9
        })
            
        super().__init__(
            message=message,
            error_code="AML_ALERT",
            status_code=HTTPStatus.OK,  # Still returns OK since this is an alert, not an error
            details=error_details
        )


class RegulatoryReportingError(RiskComplianceError):
    """Exception raised for regulatory reporting errors"""
    
    def __init__(self, 
                 message: str,
                 report_type: str,
                 deadline: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize a regulatory reporting error

        Args:
            message: Human-readable error message
            report_type: The type of regulatory report
            deadline: The deadline for submission (ISO format datetime)
            details: Additional error details
        """
        error_details = details or {}
        error_details.update({
            "report_type": report_type,
            "deadline": deadline,
        })
            
        super().__init__(
            message=message,
            error_code="REGULATORY_REPORTING_ERROR",
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            details=error_details
        )


def handle_exception(exception: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Handle an exception and return a standardized error response
    
    Args:
        exception: The exception to handle
        context: Additional context information
        
    Returns:
        Dict containing standardized error information
        
    AI-Metadata:
        purpose: Provide consistent error handling
        criticality: high
        usage_frequency: high
    """
    context = context or {}
    
    # Add stack trace in development/debugging environments
    include_traceback = context.get("include_traceback", False)
    
    # Handle RiskComplianceError exceptions
    if isinstance(exception, RiskComplianceError):
        error_info = {
            "success": False,
            "error": {
                "message": exception.message,
                "code": exception.error_code,
                "status": exception.status_code,
                "timestamp": exception.timestamp,
                "details": exception.details
            }
        }
        
        # Log the error with appropriate level based on severity
        if exception.status_code >= 500:
            logger.error(f"RISK_COMPLIANCE ERROR: {str(exception)}", exc_info=True)
        elif exception.status_code >= 400:
            logger.warning(f"RISK_COMPLIANCE WARNING: {str(exception)}")
        else:
            logger.info(f"RISK_COMPLIANCE INFO: {str(exception)}")
            
    # Handle other exceptions
    else:
        error_info = {
            "success": False,
            "error": {
                "message": str(exception),
                "code": "UNEXPECTED_ERROR",
                "status": HTTPStatus.INTERNAL_SERVER_ERROR,
                "timestamp": datetime.now().isoformat()
            }
        }
        logger.error(f"RISK_COMPLIANCE UNEXPECTED ERROR: {str(exception)}", exc_info=True)
    
    # Add traceback for debugging if requested
    if include_traceback:
        error_info["error"]["traceback"] = traceback.format_exc()
        
    # Add context information if provided
    if context:
        error_info["context"] = {k: v for k, v in context.items() 
                                if k not in ["include_traceback"]}
    
    return error_info


def log_error(message: str, exception: Optional[Exception] = None, 
             severity: str = "error", context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an error with standardized formatting
    
    Args:
        message: Error message to log
        exception: Optional exception related to the error
        severity: Logging severity (debug, info, warning, error, critical)
        context: Additional context information
        
    AI-Metadata:
        purpose: Provide consistent error logging
    """
    context = context or {}
    
    # Format the log message with context
    log_data = {
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "context": context
    }
    
    if exception:
        log_data["exception"] = str(exception)
        log_data["exception_type"] = type(exception).__name__
    
    # Log at the appropriate level
    log_message = json.dumps(log_data)
    
    if severity == "debug":
        logger.debug(log_message)
    elif severity == "info":
        logger.info(log_message)
    elif severity == "warning":
        logger.warning(log_message)
    elif severity == "critical":
        logger.critical(log_message)
    else:  # default to error
        logger.error(log_message)
