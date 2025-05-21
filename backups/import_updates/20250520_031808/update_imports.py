"""
Script to help migrate import statements throughout the codebase.

This script analyzes Python files in the project and suggests import
statement changes based on the new utils directory structure.

Usage:
    python scripts/update_imports.py [--dry-run] [--apply]

Options:
    --dry-run  Show changes without making them
    --apply    Apply the suggested changes

Author: cbs-core-dev AI Assistant
Date: May 20, 2025
"""

import os
import re
import logging
import argparse
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
UTILS_DIR = os.path.join(PROJECT_ROOT, 'utils')
DUMP_DIR = os.path.join(PROJECT_ROOT, 'dump')

# Utility modules mapping
UTILITY_MAPPINGS = {
    # Root utilities - direct imports from utils
    "error_handling": "utils.error_handling",
    "validators": "utils.validators",
    "logging": "utils.logging",
    
    # Lib utilities - import from utils.lib
    "service_registry": "utils.lib.service_registry",
    "module_interface": "utils.lib.module_interface",
    "encryption": "utils.lib.encryption",
    "logging_utils": "utils.lib.logging_utils",
    "task_manager": "utils.lib.task_manager",
    "payment_utils": "utils.lib.payment_utils",
    "notification_service": "utils.lib.notification_service",
    "packages": "utils.lib.packages",
    "framework_compatibility": "utils.lib.framework_compatibility",
    "setup_imports": "utils.lib.setup_imports",
    "refactoring_utilities": "utils.lib.refactoring_utilities",
    "cleanup_utils": "utils.lib.cleanup_utils",
    
    # Config utilities - import from utils.config
    "config": "utils.config.config",
    "config_manager": "utils.config.config_manager",
    "database_type_manager": "utils.config.database_type_manager",
    "environment": "utils.config.environment",
    "api": "utils.config.api",
    "compatibility": "utils.config.compatibility",
    
    # Common utilities - import from utils.common
    "date_format": "utils.common.date_format",
    "id_formatters": "utils.common.id_formatters",
    
    # Examples - import from utils.examples
    "service_registry_examples": "utils.examples.service_registry_examples",
}

# More complex mappings for old paths to new paths
PATH_MAPPINGS = {
    # Common to new locations
    r"utils\.common\.": "utils.common.",
    
    # Root utils to lib
    r"^from utils import (service_registry|module_interface|encryption|logging_utils|task_manager|payment_utils|notification_service|packages|framework_compatibility|setup_imports|refactoring_utilities|cleanup_utils)": 
        lambda match: f"from utils.lib import {match.group(1)}",
    
    # Root utils to config
    r"^from utils import (config|config_manager|database_type_manager|environment|api|compatibility)": 
        lambda match: f"from utils.config import {match.group(1)}",
    
    # Direct imports from utils submodules
    r"^from utils\.(service_registry|module_interface|encryption|logging_utils|task_manager|payment_utils|notification_service|packages|framework_compatibility|setup_imports|refactoring_utilities|cleanup_utils) import": 
        lambda match: f"from utils.lib.{match.group(1)} import",
        
    r"^from utils\.(config|config_manager|database_type_manager|environment|api|compatibility) import": 
        lambda match: f"from utils.config.{match.group(1)} import",
        
    r"^from utils\.(date_format|id_formatters) import": 
        lambda match: f"from utils.common.{match.group(1)} import",
        
    r"^from utils\.(service_registry_examples) import": 
        lambda match: f"from utils.examples.{match.group(1)} import",
    
    # Import directly from utils
    r"^from utils\.(error_handling|validators|logging) import": 
        lambda match: f"from utils.{match.group(1)} import",
    
    # Import * cases
    r"^from utils import \*": "from utils import *",
    r"^from utils\.common import \*": "from utils.common import *",
    r"^from utils\.lib import \*": "from utils.lib import *",
    r"^from utils\.config import \*": "from utils.config import *",
}

def find_python_files(directory, exclude_dirs=None):
    """Find all Python files in the given directory and subdirectories."""
    if exclude_dirs is None:
        exclude_dirs = ['venv', 'env', '.env', '.venv', '__pycache__', 'dump']
    
    python_files = []
    
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def analyze_imports(file_path):
    """Analyze import statements in a Python file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Find import statements
    import_lines = []
    line_numbers = []
    
    for i, line in enumerate(content.splitlines()):
        line = line.strip()
        if (line.startswith('import utils') or line.startswith('from utils')):
            import_lines.append(line)
            line_numbers.append(i + 1)
    
    return import_lines, line_numbers, content

def suggest_import_changes(import_line):
    """Suggest changes to an import statement based on mappings."""
    for pattern, replacement in PATH_MAPPINGS.items():
        if callable(replacement):
            match = re.match(pattern, import_line)
            if match:
                return replacement(match)
        else:
            new_line = re.sub(pattern, replacement, import_line)
            if new_line != import_line:
                return new_line
    
    # If no patterns matched, return the original line
    return import_line

def apply_changes(file_path, content, old_imports, new_imports):
    """Apply the suggested changes to the file."""
    new_content = content
    
    # Replace each old import with the new one
    for old_import, new_import in zip(old_imports, new_imports):
        if old_import != new_import:
            new_content = new_content.replace(old_import, new_import)
    
    # Write the updated content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    logger.info(f"Updated {file_path}")

def generate_report(changes, applied=False):
    """Generate a report of suggested import changes."""
    report_path = os.path.join(PROJECT_ROOT, "import_migration_report.md")
    
    with open(report_path, 'w') as f:
        f.write("# Import Migration Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        if applied:
            f.write("## Changes Applied\n\n")
        else:
            f.write("## Suggested Changes\n\n")
        
        files_with_changes = 0
        total_changes = 0
        
        for file_path, file_changes in changes.items():
            if not file_changes:
                continue
                
            files_with_changes += 1
            total_changes += len(file_changes)
            
            rel_path = os.path.relpath(file_path, PROJECT_ROOT)
            f.write(f"### {rel_path}\n\n")
            
            f.write("| Line | Old Import | New Import |\n")
            f.write("|------|------------|------------|\n")
            
            for line_num, old_import, new_import in file_changes:
                if old_import != new_import:
                    f.write(f"| {line_num} | `{old_import}` | `{new_import}` |\n")
            
            f.write("\n")
        
        f.write(f"\n## Summary\n\n")
        f.write(f"* Files with import changes: {files_with_changes}\n")
        f.write(f"* Total import statements changed: {total_changes}\n")
        
        if not applied:
            f.write("\n## How to Apply Changes\n\n")
            f.write("To apply these changes, run the script with the `--apply` flag:\n\n")
            f.write("```\npython scripts/update_imports.py --apply\n```\n")
    
    logger.info(f"Generated report at {report_path}")
    return report_path, files_with_changes, total_changes

def main():
    """Main function to scan for utils imports and suggest changes."""
    parser = argparse.ArgumentParser(description='Update utils import statements.')
    parser.add_argument('--dry-run', action='store_true', help='Show changes without making them')
    parser.add_argument('--apply', action='store_true', help='Apply the suggested changes')
    args = parser.parse_args()
    
    logger.info("Starting import analysis for utils modules")
    
    # Find all Python files
    python_files = find_python_files(PROJECT_ROOT, exclude_dirs=['venv', 'env', '.env', '.venv', '__pycache__', 'dump'])
    logger.info(f"Found {len(python_files)} Python files to analyze")
    
    # Analyze imports and suggest changes
    changes = {}
    
    for file_path in python_files:
        import_lines, line_numbers, content = analyze_imports(file_path)
        
        if not import_lines:
            continue
        
        file_changes = []
        
        for i, (line, line_num) in enumerate(zip(import_lines, line_numbers)):
            new_line = suggest_import_changes(line)
            
            if new_line != line:
                file_changes.append((line_num, line, new_line))
        
        if file_changes:
            changes[file_path] = file_changes
            
            if args.apply and not args.dry_run:
                new_imports = [new_line for _, _, new_line in file_changes]
                old_imports = [old_line for _, old_line, _ in file_changes]
                apply_changes(file_path, content, old_imports, new_imports)
    
    # Generate report
    report_path, files_with_changes, total_changes = generate_report(changes, applied=args.apply and not args.dry_run)
    
    # Output summary
    if args.dry_run:
        logger.info(f"Dry run completed. {files_with_changes} files would be changed with {total_changes} import updates.")
        logger.info(f"Check {report_path} for details.")
    elif args.apply:
        logger.info(f"Applied changes to {files_with_changes} files, updating {total_changes} import statements.")
        logger.info(f"Check {report_path} for a summary of the changes made.")
    else:
        logger.info(f"Analysis completed. {files_with_changes} files need changes with {total_changes} import updates.")
        logger.info(f"To apply these changes, run with --apply")
        logger.info(f"Check {report_path} for details.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
