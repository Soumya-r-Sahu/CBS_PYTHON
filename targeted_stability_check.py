"""
Targeted stability check for Core Banking and Security modules
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
logger = logging.getLogger("TargetedCheck")

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_component(component_path):
    """Try to import a component and return its status"""
    try:
        importlib.import_module(component_path)
        return "PASS"
    except Exception as e:
        logger.error(f"Error importing {component_path}: {str(e)}")
        return f"FAIL: {str(e)}"

def check_directory_exists(base_dir, subdir):
    """Check if a directory exists"""
    full_path = os.path.join(base_dir, subdir)
    return os.path.isdir(full_path)

def list_directory_contents(directory):
    """List contents of a directory"""
    try:
        return os.listdir(directory)
    except Exception as e:
        return [f"ERROR: {str(e)}"]

def main():
    base_dir = "d:\\Vs code\\CBS_PYTHON"
    
    # Components to check
    core_banking_components = [
        "core_banking.utils.core_banking_utils",
        "core_banking.accounts.domain.entities.account",
        "core_banking.transactions.domain.entities.transaction",
        "core_banking.accounts.application.interfaces.account_repository",
        "core_banking.transactions.application.services.transaction_service",
        "core_banking.accounts.presentation.controllers.account_controller"
    ]
    
    security_components = [
        "security.common.security_utils",
        "security.authentication.domain.entities.user",
        "security.authentication.domain.services.password_policy_service",
        "security.authentication.infrastructure.repositories.sqlite_user_repository",
        "security.authentication.presentation.controllers.authentication_controller"
    ]
    
    print("=== TARGETED STABILITY CHECK FOR CORE BANKING AND SECURITY MODULES ===\n")
    
    # Check Core Banking module
    print("CORE BANKING MODULE:")
    print("-" * 50)
    
    # 1. Check directory structure
    print("\nDirectory Structure:")
    core_banking_dir = os.path.join(base_dir, "core_banking")
    core_dirs = list_directory_contents(core_banking_dir)
    print(f"Root Contents: {', '.join(core_dirs)}")
    
    # Check clean architecture directories in accounts module
    accounts_dir = os.path.join(core_banking_dir, "accounts")
    if check_directory_exists(core_banking_dir, "accounts"):
        accounts_dirs = list_directory_contents(accounts_dir)
        print(f"Accounts Contents: {', '.join(accounts_dirs)}")
        
        # Check for clean architecture layers
        for layer in ["domain", "application", "infrastructure", "presentation"]:
            layer_exists = check_directory_exists(accounts_dir, layer)
            print(f"  - accounts/{layer}: {'EXISTS' if layer_exists else 'MISSING'}")
    else:
        print("Accounts directory not found")
    
    # 2. Check component imports
    print("\nComponent Imports:")
    for component in core_banking_components:
        status = check_component(component)
        print(f"  - {component}: {status}")
    
    # Check Security module
    print("\n\nSECURITY MODULE:")
    print("-" * 50)
    
    # 1. Check directory structure
    print("\nDirectory Structure:")
    security_dir = os.path.join(base_dir, "security")
    security_dirs = list_directory_contents(security_dir)
    print(f"Root Contents: {', '.join(security_dirs)}")
    
    # Check clean architecture directories in authentication module
    auth_dir = os.path.join(security_dir, "authentication")
    if check_directory_exists(security_dir, "authentication"):
        auth_dirs = list_directory_contents(auth_dir)
        print(f"Authentication Contents: {', '.join(auth_dirs)}")
        
        # Check for clean architecture layers
        for layer in ["domain", "application", "infrastructure", "presentation"]:
            layer_exists = check_directory_exists(auth_dir, layer)
            print(f"  - authentication/{layer}: {'EXISTS' if layer_exists else 'MISSING'}")
    else:
        print("Authentication directory not found")
    
    # 2. Check component imports
    print("\nComponent Imports:")
    for component in security_components:
        status = check_component(component)
        print(f"  - {component}: {status}")
    
    # Generate summary report
    print("\n\nSUMMARY:")
    print("-" * 50)
    
    core_banking_status = "STABLE" if all(check_component(c) == "PASS" for c in core_banking_components) else "ISSUES DETECTED"
    security_status = "STABLE" if all(check_component(c) == "PASS" for c in security_components) else "ISSUES DETECTED"
    
    print(f"Core Banking Module: {core_banking_status}")
    print(f"Security Module: {security_status}")
    
    # Write report to file
    with open(f"targeted_stability_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md", "w", encoding="utf-8") as f:
        f.write(f"# Targeted Stability Check - Core Banking and Security Modules\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Core Banking Module\n\n")
        f.write(f"**Overall Status:** {core_banking_status}\n\n")
        
        f.write("### Component Status\n\n")
        f.write("| Component | Status |\n")
        f.write("|-----------|--------|\n")
        for component in core_banking_components:
            status = check_component(component)
            status_short = "PASS" if status == "PASS" else "FAIL"
            f.write(f"| {component} | {status_short} |\n")
        
        f.write("\n## Security Module\n\n")
        f.write(f"**Overall Status:** {security_status}\n\n")
        
        f.write("### Component Status\n\n")
        f.write("| Component | Status |\n")
        f.write("|-----------|--------|\n")
        for component in security_components:
            status = check_component(component)
            status_short = "PASS" if status == "PASS" else "FAIL"
            f.write(f"| {component} | {status_short} |\n")

if __name__ == "__main__":
    main()
