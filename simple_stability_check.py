"""
CBS Python System Stability Check Script - Simplified Version

This script performs a basic health check of all modules in the CBS_PYTHON project
to verify system stability and identify potential issues.
"""

import os
import sys
import importlib
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("StabilityCheck")

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_module_importable(module_name):
    """Check if a module can be imported correctly"""
    try:
        importlib.import_module(module_name)
        logger.info(f"{module_name} imported successfully")
        return True
    except Exception as e:
        logger.error(f"Error importing {module_name}: {str(e)}")
        return False

def check_clean_architecture(module_path):
    """Check if a module follows clean architecture structure"""
    layers = ["domain", "application", "infrastructure", "presentation"]
    results = {}
    base_path = "d:\\Vs code\\CBS_PYTHON"
    
    # Check if module exists
    module_full_path = os.path.join(base_path, module_path)
    if not os.path.exists(module_full_path):
        logger.warning(f"Module path does not exist: {module_full_path}")
        for layer in layers:
            results[layer] = "MISSING"
        return results
    
    # List all subdirectories
    try:
        subdirs = [d for d in os.listdir(module_full_path) 
                  if os.path.isdir(os.path.join(module_full_path, d))]
        logger.info(f"Found subdirectories in {module_path}: {subdirs}")
        
        # Check each layer
        for layer in layers:
            if layer in subdirs:
                results[layer] = "EXISTS"
            else:
                results[layer] = "MISSING"
    except Exception as e:
        logger.error(f"Error checking architecture for {module_path}: {str(e)}")
        for layer in layers:
            results[layer] = "ERROR"
    
    return results

def run_system_check():
    """Run a basic system stability check"""
    # Track results
    results = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "module_status": {},
        "clean_architecture": {},
    }
    
    # Core modules to check
    modules = {
        "Core Banking": "core_banking",
        "Security": "security",
        "HR-ERP": "hr_erp",
        "Digital Channels": "digital_channels",
        "Payments": "payments",
        "CRM": "crm", 
        "Treasury": "treasury",
        "Risk Compliance": "risk_compliance"
    }
    
    # Critical components to test
    critical_components = [
        "core_banking.utils.core_banking_utils",
        "security.common.security_utils",
        "core_banking.accounts.domain.entities.account",
        "core_banking.transactions.domain.entities.transaction",
        "security.authentication.domain.entities.user"
    ]
    
    print("Starting CBS_PYTHON system stability check...")
    print("-" * 50)
    
    # Check module interfaces
    print("\nChecking module interfaces:")
    for name, path in modules.items():
        try:
            interface_path = f"{path}.module_interface"
            status = check_module_importable(interface_path)
            results["module_status"][name] = "PASS" if status else "FAIL"
            
            # Also check clean architecture
            results["clean_architecture"][name] = check_clean_architecture(path)
            
            # Print status
            print(f"  {name}: {'PASS' if status else 'FAIL'}")
        except Exception as e:
            results["module_status"][name] = "ERROR"
            print(f"  {name}: ERROR - {str(e)}")
    
    # Check critical components
    print("\nChecking critical components:")
    for component in critical_components:
        status = check_module_importable(component)
        if component not in results:
            results[component] = {}
        results[component] = "PASS" if status else "FAIL"
        print(f"  {component}: {'PASS' if status else 'FAIL'}")
    
    # Generate report
    report_filename = f"system_stability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(f"# CBS PYTHON System Stability Report\n\n")
        f.write(f"**Generated on:** {results['timestamp']}\n\n")
        
        # Module status summary
        f.write("## Module Status Summary\n\n")
        f.write("| Module | Status | Clean Architecture Compliance |\n")
        f.write("|--------|--------|--------------------------------|\n")
        
        for module_name, status in results["module_status"].items():
            ca_data = results["clean_architecture"].get(module_name, {})
            if ca_data:
                exists_count = sum(1 for _, status in ca_data.items() if status == "EXISTS")
                total_layers = len(ca_data)
                compliance = f"{int((exists_count / total_layers) * 100)}%" if total_layers > 0 else "N/A"
            else:
                compliance = "N/A"
                
            f.write(f"| {module_name} | {status} | {compliance} |\n")
        
        # Critical components
        f.write("\n## Critical Components Status\n\n")
        f.write("| Component | Status |\n")
        f.write("|-----------|--------|\n")
        
        for component in critical_components:
            status = results.get(component, "UNKNOWN")
            f.write(f"| {component} | {status} |\n")
        
        # Clean architecture details
        f.write("\n## Clean Architecture Compliance Details\n\n")
        
        for module_name, layers in results["clean_architecture"].items():
            f.write(f"### {module_name}\n\n")
            f.write("| Layer | Status |\n")
            f.write("|-------|--------|\n")
            
            for layer, status in layers.items():
                f.write(f"| {layer} | {status} |\n")
            
            f.write("\n")
    
    print(f"\nStability check completed. Report saved to: {report_filename}")
    return report_filename

if __name__ == "__main__":
    run_system_check()
