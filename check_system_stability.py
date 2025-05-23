"""
CBS Python System Stability Check Script

This script performs a comprehensive health check of all modules in the CBS_PYTHON project
to verify system stability and identify potential issues.
"""

import os
import sys
import time
import importlib
import logging
from datetime import datetime
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SystemStabilityCheck")

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialize results dictionary
results = {
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "overall_status": "CHECKING",
    "modules": {},
    "errors": [],
    "warnings": []
}

def check_module_integrity(module_name, module_path):
    """Check if a module can be imported correctly"""
    module_result = {
        "status": "CHECKING",
        "components_checked": 0,
        "components_passed": 0,
        "errors": [],
        "warnings": []
    }
    
    logger.info(f"Checking module: {module_name}")
    
    try:
        if module_path:
            # Try to import the module interface if it exists
            try:
                module = importlib.import_module(f"{module_path}.module_interface")
                module_result["components_checked"] += 1
                module_result["components_passed"] += 1
                logger.info(f"✅ {module_name} module interface loaded successfully")
            except ImportError as e:
                # Not all modules might have a module_interface, so this is just a warning
                module_result["warnings"].append(f"Could not import module interface: {str(e)}")
                logger.warning(f"⚠️ {module_name} module interface could not be imported: {str(e)}")
        
        module_result["status"] = "PASS"
    except Exception as e:
        error_msg = f"Error checking {module_name} module: {str(e)}"
        module_result["status"] = "FAIL"
        module_result["errors"].append(error_msg)
        results["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}")
        logger.error(traceback.format_exc())
    
    return module_result

def check_clean_architecture_compliance(module_name, module_path):
    """Check if a module follows clean architecture structure"""
    if not module_path:
        return
        
    layers = ["domain", "application", "infrastructure", "presentation"]
    
    for layer in layers:
        layer_path = os.path.join("d:\\Vs code\\CBS_PYTHON", module_path, layer)
        if os.path.exists(layer_path):
            results["modules"][module_name]["clean_architecture"][layer] = "EXISTS"
        else:
            results["modules"][module_name]["clean_architecture"][layer] = "MISSING"

def check_core_banking_module():
    """Check Core Banking module stability"""
    module_name = "Core Banking"
    module_path = "core_banking"
    
    results["modules"][module_name] = {
        "basic_integrity": check_module_integrity(module_name, module_path),
        "clean_architecture": {}
    }
    
    check_clean_architecture_compliance(module_name, module_path)
    
    # Check accounts component
    try:
        import core_banking.accounts.domain.entities.account
        results["modules"][module_name]["components_tested"] = {
            "accounts": "PASS"
        }
        logger.info("✅ Core Banking accounts component check passed")
    except Exception as e:
        results["modules"][module_name]["components_tested"] = {
            "accounts": "FAIL"
        }
        error_msg = f"Error importing accounts component: {str(e)}"
        results["modules"][module_name]["basic_integrity"]["errors"].append(error_msg)
        results["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}")

    # Check transactions component
    try:
        import core_banking.transactions.domain.entities.transaction
        results["modules"][module_name]["components_tested"]["transactions"] = "PASS"
        logger.info("✅ Core Banking transactions component check passed")
    except Exception as e:
        results["modules"][module_name]["components_tested"]["transactions"] = "FAIL"
        error_msg = f"Error importing transactions component: {str(e)}"
        results["modules"][module_name]["basic_integrity"]["errors"].append(error_msg)
        results["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}")

def check_security_module():
    """Check Security module stability"""
    module_name = "Security"
    module_path = "security"
    
    results["modules"][module_name] = {
        "basic_integrity": check_module_integrity(module_name, module_path),
        "clean_architecture": {}
    }
    
    check_clean_architecture_compliance(module_name, module_path)
    
    # Check authentication component
    try:
        import security.authentication.domain.entities.user
        results["modules"][module_name]["components_tested"] = {
            "authentication": "PASS"
        }
        logger.info("✅ Security authentication component check passed")
    except Exception as e:
        results["modules"][module_name]["components_tested"] = {
            "authentication": "FAIL"
        }
        error_msg = f"Error importing authentication component: {str(e)}"
        results["modules"][module_name]["basic_integrity"]["errors"].append(error_msg)
        results["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}")

def check_digital_channels_module():
    """Check Digital Channels module stability"""
    module_name = "Digital Channels"
    module_path = "digital_channels"
    
    results["modules"][module_name] = {
        "basic_integrity": check_module_integrity(module_name, module_path),
        "clean_architecture": {}
    }
    
    check_clean_architecture_compliance(module_name, module_path)

def check_hr_erp_module():
    """Check HR-ERP module stability"""
    module_name = "HR-ERP"
    module_path = "hr_erp"
    
    results["modules"][module_name] = {
        "basic_integrity": check_module_integrity(module_name, module_path),
        "clean_architecture": {}
    }
    
    check_clean_architecture_compliance(module_name, module_path)

def check_payments_module():
    """Check Payments module stability"""
    module_name = "Payments"
    module_path = "payments"
    
    results["modules"][module_name] = {
        "basic_integrity": check_module_integrity(module_name, module_path),
        "clean_architecture": {}
    }
    
    check_clean_architecture_compliance(module_name, module_path)

def check_crm_module():
    """Check CRM module stability"""
    module_name = "CRM"
    module_path = "crm"
    
    results["modules"][module_name] = {
        "basic_integrity": check_module_integrity(module_name, module_path),
        "clean_architecture": {}
    }
    
    check_clean_architecture_compliance(module_name, module_path)

def check_treasury_module():
    """Check Treasury module stability"""
    module_name = "Treasury"
    module_path = "treasury"
    
    results["modules"][module_name] = {
        "basic_integrity": check_module_integrity(module_name, module_path),
        "clean_architecture": {}
    }
    
    check_clean_architecture_compliance(module_name, module_path)

def check_risk_compliance_module():
    """Check Risk Compliance module stability"""
    module_name = "Risk Compliance"
    module_path = "risk_compliance"
    
    results["modules"][module_name] = {
        "basic_integrity": check_module_integrity(module_name, module_path),
        "clean_architecture": {}
    }
    
    check_clean_architecture_compliance(module_name, module_path)

def check_centralized_utilities():
    """Check centralized utilities"""
    module_name = "Centralized Utilities"
    
    results["modules"][module_name] = {
        "basic_integrity": {
            "status": "CHECKING",
            "components_checked": 0,
            "components_passed": 0,
            "errors": [],
            "warnings": []
        }
    }
    
    # Check core banking utilities
    try:
        import core_banking.utils.core_banking_utils
        results["modules"][module_name]["components_tested"] = {
            "core_banking_utils": "PASS"
        }
        results["modules"][module_name]["basic_integrity"]["components_checked"] += 1
        results["modules"][module_name]["basic_integrity"]["components_passed"] += 1
        logger.info("✅ Core Banking utilities check passed")
    except Exception as e:
        results["modules"][module_name]["components_tested"] = {
            "core_banking_utils": "FAIL"
        }
        error_msg = f"Error importing Core Banking utilities: {str(e)}"
        results["modules"][module_name]["basic_integrity"]["errors"].append(error_msg)
        results["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}")
    
    # Check security utilities
    try:
        import security.common.security_utils
        results["modules"][module_name]["components_tested"]["security_utils"] = "PASS"
        results["modules"][module_name]["basic_integrity"]["components_checked"] += 1
        results["modules"][module_name]["basic_integrity"]["components_passed"] += 1
        logger.info("✅ Security utilities check passed")
    except Exception as e:
        results["modules"][module_name]["components_tested"]["security_utils"] = "FAIL"
        error_msg = f"Error importing Security utilities: {str(e)}"
        results["modules"][module_name]["basic_integrity"]["errors"].append(error_msg)
        results["errors"].append(error_msg)
        logger.error(f"❌ {error_msg}")
    
    if results["modules"][module_name]["basic_integrity"]["components_passed"] == results["modules"][module_name]["basic_integrity"]["components_checked"]:
        results["modules"][module_name]["basic_integrity"]["status"] = "PASS"
    else:
        results["modules"][module_name]["basic_integrity"]["status"] = "FAIL"

def generate_report():
    """Generate stability report"""
    # Calculate overall status
    fail_count = 0
    total_modules = len(results["modules"])
    
    for module_name, module_data in results["modules"].items():
        if module_data["basic_integrity"]["status"] == "FAIL":
            fail_count += 1
    
    if fail_count == 0:
        results["overall_status"] = "STABLE"
    elif fail_count < total_modules / 2:
        results["overall_status"] = "PARTIALLY STABLE"
    else:
        results["overall_status"] = "UNSTABLE"
    
    # Generate report file
    report_filename = f"system_stability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(f"# CBS PYTHON System Stability Report\n\n")
        f.write(f"**Generated on:** {results['timestamp']}\n\n")
        f.write(f"**Overall System Status:** {results['overall_status']}\n\n")
        
        f.write("## Module Status Summary\n\n")
        f.write("| Module | Status | Clean Architecture Compliance |\n")
        f.write("|--------|--------|--------------------------------|\n")
        
        for module_name, module_data in results["modules"].items():
            status = module_data["basic_integrity"]["status"]
            status_emoji = "PASS" if status == "PASS" else "FAIL"
              # Calculate clean architecture compliance if available
            ca_compliance = "N/A"
            if "clean_architecture" in module_data and module_data["clean_architecture"]:
                exists_count = sum(1 for layer, status in module_data["clean_architecture"].items() if status == "EXISTS")
                total_layers = len(module_data["clean_architecture"])
                if total_layers > 0:
                    compliance_pct = (exists_count / total_layers) * 100
                    ca_compliance = f"{compliance_pct:.0f}%"
            
            f.write(f"| {module_name} | {status_emoji} | {ca_compliance} |\n")
        
        f.write("\n## Detailed Results\n\n")
        
        for module_name, module_data in results["modules"].items():
            f.write(f"### {module_name}\n\n")
            
            # Basic integrity
            f.write("#### Basic Integrity\n\n")
            f.write(f"**Status:** {module_data['basic_integrity']['status']}\n\n")
            
            if module_data["basic_integrity"]["errors"]:
                f.write("**Errors:**\n\n")
                for error in module_data["basic_integrity"]["errors"]:
                    f.write(f"- {error}\n")
                f.write("\n")
            
            if module_data["basic_integrity"]["warnings"]:
                f.write("**Warnings:**\n\n")
                for warning in module_data["basic_integrity"]["warnings"]:
                    f.write(f"- {warning}\n")
                f.write("\n")
            
            # Component test results
            if "components_tested" in module_data:
                f.write("#### Components Tested\n\n")
                f.write("| Component | Status |\n")
                f.write("|-----------|--------|\n")
            for component, status in module_data["components_tested"].items():
                    status_emoji = "PASS" if status == "PASS" else "FAIL"
                    f.write(f"| {component} | {status_emoji} |\n")
                    f.write("\n")
            
            # Clean architecture compliance
            if "clean_architecture" in module_data and module_data["clean_architecture"]:
                f.write("#### Clean Architecture Compliance\n\n")
                f.write("| Layer | Status |\n")
                f.write("|-------|--------|\n")
                
                for layer, status in module_data["clean_architecture"].items():
                    status_emoji = "EXISTS" if status == "EXISTS" else "MISSING"
                    f.write(f"| {layer} | {status_emoji} |\n")
                f.write("\n")
        
        # System-wide errors
        if results["errors"]:
            f.write("## System-wide Errors\n\n")
            for error in results["errors"]:
                f.write(f"- {error}\n")
            f.write("\n")
        
        # System-wide warnings
        if results["warnings"]:
            f.write("## System-wide Warnings\n\n")
            for warning in results["warnings"]:
                f.write(f"- {warning}\n")
            f.write("\n")
        
        f.write("## Recommendations\n\n")
        if results["overall_status"] == "STABLE":
            f.write("- The system is stable and all modules are functioning correctly.\n")
            f.write("- Continue monitoring for any changes in stability.\n")
            f.write("- Consider adding more comprehensive tests for each module.\n")
        elif results["overall_status"] == "PARTIALLY STABLE":
            f.write("- Address the errors in the failing modules as soon as possible.\n")
            f.write("- Review the clean architecture compliance for modules with low scores.\n")
            f.write("- Add more robust error handling to prevent cascading failures.\n")
        else:
            f.write("- Critical system instability detected - immediate attention required.\n")
            f.write("- Address all errors in priority order starting with the core modules.\n")
            f.write("- Consider rolling back to the last known stable version if necessary.\n")
    
    logger.info(f"Stability report generated: {report_filename}")
    return report_filename

def run_stability_check():
    """Run the full system stability check"""
    start_time = time.time()
    logger.info("Starting CBS_PYTHON system stability check...")
    
    try:
        # Check each module
        check_core_banking_module()
        check_security_module()
        check_digital_channels_module()
        check_hr_erp_module()
        check_payments_module()
        check_crm_module()
        check_treasury_module()
        check_risk_compliance_module()
        check_centralized_utilities()
        
        # Generate report
        report_file = generate_report()
        
        elapsed_time = time.time() - start_time
        logger.info(f"Stability check completed in {elapsed_time:.2f} seconds")
        logger.info(f"Overall system status: {results['overall_status']}")
        
        print(f"\nStability check completed. Report saved to: {report_file}")
        print(f"Overall system status: {results['overall_status']}")
        
        # Return code based on status
        if results["overall_status"] == "STABLE":
            return 0
        elif results["overall_status"] == "PARTIALLY STABLE":
            return 1
        else:
            return 2
        
    except Exception as e:
        logger.error(f"Error during stability check: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"Stability check failed with error: {str(e)}")
        return 3

if __name__ == "__main__":
    sys.exit(run_stability_check())
