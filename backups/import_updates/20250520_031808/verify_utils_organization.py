"""
Script to initialize and verify the utils directory reorganization.

This script:
1. Verifies that all subdirectories exist
2. Creates any missing __init__.py files
3. Tests importing from the new structure

Usage:
    python scripts/verify_utils_organization.py

Author: cbs-core-dev AI Assistant
Date: May 20, 2025
"""

import os
import importlib
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UTILS_DIR = os.path.join(PROJECT_ROOT, 'utils')

# Define the expected structure
EXPECTED_STRUCTURE = {
    "root": [
        "error_handling.py",
        "validators.py",
        "logging.py",
        "__init__.py"
    ],
    "lib": [
        "service_registry.py",
        "module_interface.py",
        "encryption.py",
        "task_manager.py",
        "payment_utils.py",
        "__init__.py"
    ],
    "config": [
        "config.py",
        "database_type_manager.py",
        "environment.py",
        "__init__.py"
    ],
    "common": [
        "date_format.py",
        "id_formatters.py",
        "__init__.py"
    ],
    "examples": [
        "service_registry_examples.py",
        "__init__.py"
    ]
}

def verify_structure():
    """Verify the utils directory structure."""
    logger.info("Verifying utils directory structure")
    
    missing_dirs = []
    missing_files = []
    
    # Verify the root utils directory
    if not os.path.exists(UTILS_DIR):
        logger.error(f"Utils directory does not exist: {UTILS_DIR}")
        return False
    
    # Verify subdirectories
    for subdir in EXPECTED_STRUCTURE.keys():
        if subdir == "root":
            continue
        
        subdir_path = os.path.join(UTILS_DIR, subdir)
        if not os.path.exists(subdir_path):
            missing_dirs.append(subdir)
            logger.warning(f"Missing directory: {subdir_path}")
        
    # Verify files
    for subdir, files in EXPECTED_STRUCTURE.items():
        dir_path = UTILS_DIR if subdir == "root" else os.path.join(UTILS_DIR, subdir)
        
        for file in files:
            file_path = os.path.join(dir_path, file)
            if not os.path.exists(file_path):
                missing_files.append((subdir, file))
                logger.warning(f"Missing file: {file_path}")
    
    return {
        "missing_dirs": missing_dirs,
        "missing_files": missing_files
    }

def create_missing_components(missing_components):
    """Create missing directories and __init__.py files."""
    logger.info("Creating missing components")
    
    # Create missing directories
    for subdir in missing_components["missing_dirs"]:
        subdir_path = os.path.join(UTILS_DIR, subdir)
        os.makedirs(subdir_path, exist_ok=True)
        logger.info(f"Created directory: {subdir_path}")
    
    # Create missing __init__.py files
    for subdir, file in missing_components["missing_files"]:
        if file == "__init__.py":
            dir_path = UTILS_DIR if subdir == "root" else os.path.join(UTILS_DIR, subdir)
            file_path = os.path.join(dir_path, file)
            
            with open(file_path, 'w') as f:
                f.write('"""\n')
                f.write(f'Utilities for the CBS Python {subdir} module.\n\n')
                f.write(f'This package provides {subdir} utilities used throughout the system.\n')
                f.write('"""\n\n')
            
            logger.info(f"Created file: {file_path}")

def test_imports():
    """Test importing from the utils structure."""
    logger.info("Testing imports from utils structure")
    
    import_tests = [
        # Core utilities
        "from utils import error_handling",
        "from utils import validators",
        
        # Config utilities
        "from utils.config import config",
        "from utils.config import database_type_manager",
        "from utils.config import environment",
        
        # Lib utilities
        "from utils.lib import service_registry",
        "from utils.lib import module_interface",
        "from utils.lib import task_manager",
        
        # Common utilities
        "from utils.common import date_format",
        "from utils.common import id_formatters",
        
        # Examples
        "from utils.examples import service_registry_examples"
    ]
    
    results = []
    
    for import_stmt in import_tests:
        try:
            exec(import_stmt)
            results.append((import_stmt, True, "Success"))
        except ImportError as e:
            results.append((import_stmt, False, str(e)))
    
    return results

def generate_report(missing_components, import_results):
    """Generate a report of the verification results."""
    report_path = os.path.join(PROJECT_ROOT, "utils_verification_report.md")
    
    with open(report_path, 'w') as f:
        f.write("# Utils Directory Verification Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
          # Structure verification results
        f.write("## Directory Structure Verification\\n\\n")
        
        if missing_components["missing_dirs"] or missing_components["missing_files"]:
            f.write("### Missing Components\\n\\n")
            
            if missing_components["missing_dirs"]:
                f.write("#### Missing Directories\\n\\n")
                for subdir in missing_components["missing_dirs"]:
                    f.write(f"* `utils/{subdir}/`\\n")
                f.write("\\n")
            
            if missing_components["missing_files"]:
                f.write("#### Missing Files\\n\\n")
                for subdir, file in missing_components["missing_files"]:
                    dir_path = "utils" if subdir == "root" else f"utils/{subdir}"
                    f.write(f"* `{dir_path}/{file}`\\n")
                f.write("\\n")
        else:
            f.write("All expected directories and files are present.\\n\\n")
        
        # Import test results
        f.write("## Import Tests\\n\\n")
        f.write("| Import Statement | Status | Result |\\n")
        f.write("|------------------|--------|--------|\\n")
        
        for import_stmt, success, result in import_results:
            status = "Success" if success else "Failed"
            f.write(f"| `{import_stmt}` | {status} | {result} |\\n")
        
        # Summary
        f.write("\n## Summary\n\n")
        successful_imports = sum(1 for _, success, _ in import_results if success)
        f.write(f"* Successful imports: {successful_imports}/{len(import_results)}\n")
        f.write(f"* Missing directories: {len(missing_components['missing_dirs'])}\n")
        f.write(f"* Missing files: {len(missing_components['missing_files'])}\n")
        
        # Recommendations
        f.write("\n## Recommendations\n\n")
        if missing_components["missing_dirs"] or missing_components["missing_files"]:
            f.write("1. Create the missing directories and files\n")
            f.write("2. Ensure all __init__.py files are properly configured\n")
        
        if successful_imports < len(import_results):
            f.write("3. Fix the failed imports by ensuring the proper module structure\n")
        
        f.write("4. Test importing the utils modules from your application code\n")
    
    logger.info(f"Generated report at {report_path}")
    return report_path

def main():
    """Main function to verify utils directory structure."""
    logger.info("Starting utils directory verification")
    
    try:
        # Verify structure
        missing_components = verify_structure()
        
        # Create missing components
        if missing_components["missing_dirs"] or missing_components["missing_files"]:
            create_missing_components(missing_components)
        
        # Test imports
        import_results = test_imports()
        
        # Generate report
        report_path = generate_report(missing_components, import_results)
        
        logger.info("Utils directory verification completed successfully")
        logger.info(f"Report generated at {report_path}")
        
        # Return success status
        successful_imports = sum(1 for _, success, _ in import_results if success)
        return 0 if successful_imports == len(import_results) else 1
    
    except Exception as e:
        logger.error(f"Error during utils directory verification: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
