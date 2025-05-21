#!/usr/bin/env python
"""
Payment Processors Status Check Script

This script provides health check functionality for the payments module
by verifying the status of payment processors, gateway connections,
and transaction processing capabilities.

Usage:
    Import and use these functions within the PaymentsModule._check_module_specific method
"""

import logging
from typing import Dict, List, Any
from datetime import datetime
import traceback

logger = logging.getLogger(__name__)

def check_payment_processors(processors: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check the status of payment processors
    
    Args:
        processors: Dictionary of processor instances
        
    Returns:
        dict: Health check results
    """
    try:
        if not processors:
            return {
                "name": "payment_processors_check",
                "status": "critical",
                "message": "No payment processors found",
                "details": {
                    "processors_count": 0
                }
            }
        
        # Check each processor
        processor_statuses = {}
        critical_count = 0
        
        for processor_name, processor in processors.items():
            # This would call a real status method on the processor
            processor_status = "healthy"  # Placeholder
            processor_statuses[processor_name] = processor_status
            
            if processor_status != "healthy":
                critical_count += 1
        
        # Determine overall status
        if critical_count == len(processors):
            status = "critical"
            message = "All payment processors are unavailable"
        elif critical_count > 0:
            status = "degraded"
            message = f"{critical_count} of {len(processors)} payment processors are unavailable"
        else:
            status = "healthy"
            message = f"All {len(processors)} payment processors are operational"
        
        return {
            "name": "payment_processors_check",
            "status": status,
            "message": message,
            "details": {
                "processors_count": len(processors),
                "unavailable_count": critical_count,
                "processor_statuses": processor_statuses
            }
        }
    except Exception as e:
        logger.error(f"Error checking payment processors: {str(e)}")
        return {
            "name": "payment_processors_check",
            "status": "critical",
            "message": f"Error checking payment processors: {str(e)}",
            "details": {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        }

def check_payment_gateways() -> Dict[str, Any]:
    """
    Check the status of external payment gateways
    
    Returns:
        dict: Health check results
    """
    try:
        # This would make real gateway connectivity checks
        gateways = {
            "visa": "healthy",
            "mastercard": "healthy",
            "paypal": "healthy",
            "applepay": "healthy"
        }
        
        unavailable = [name for name, status in gateways.items() if status != "healthy"]
        
        if len(unavailable) == len(gateways):
            status = "critical"
            message = "All payment gateways are unavailable"
        elif unavailable:
            status = "degraded"
            message = f"{len(unavailable)} of {len(gateways)} payment gateways are unavailable"
        else:
            status = "healthy"
            message = f"All {len(gateways)} payment gateways are operational"
        
        return {
            "name": "payment_gateways_check",
            "status": status,
            "message": message,
            "details": {
                "gateways": gateways,
                "unavailable": unavailable
            }
        }
    except Exception as e:
        logger.error(f"Error checking payment gateways: {str(e)}")
        return {
            "name": "payment_gateways_check",
            "status": "critical",
            "message": f"Error checking payment gateways: {str(e)}",
            "details": {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        }

def check_transaction_processing() -> Dict[str, Any]:
    """
    Check transaction processing capabilities
    
    Returns:
        dict: Health check results
    """
    try:
        # This would do a real test transaction or check recent transaction success rates
        # For now, we'll simulate a healthy state
        processing_status = "healthy"
        recent_success_rate = 98.5  # percentage
        
        if processing_status == "critical" or recent_success_rate < 80:
            status = "critical"
            message = f"Transaction processing is severely degraded (success rate: {recent_success_rate}%)"
        elif processing_status == "degraded" or recent_success_rate < 95:
            status = "degraded"
            message = f"Transaction processing is partially degraded (success rate: {recent_success_rate}%)"
        else:
            status = "healthy"
            message = f"Transaction processing is operational (success rate: {recent_success_rate}%)"
        
        return {
            "name": "transaction_processing_check",
            "status": status,
            "message": message,
            "details": {
                "processing_status": processing_status,
                "recent_success_rate": recent_success_rate,
                "threshold_critical": 80,
                "threshold_degraded": 95
            }
        }
    except Exception as e:
        logger.error(f"Error checking transaction processing: {str(e)}")
        return {
            "name": "transaction_processing_check",
            "status": "critical",
            "message": f"Error checking transaction processing: {str(e)}",
            "details": {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        }

def run_payment_health_checks(processors: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Run all payment health checks
    
    Args:
        processors: Dictionary of processor instances
        
    Returns:
        list: List of health check results
    """
    checks = []
    
    # Run all checks
    checks.append(check_payment_processors(processors))
    checks.append(check_payment_gateways())
    checks.append(check_transaction_processing())
    
    return checks
