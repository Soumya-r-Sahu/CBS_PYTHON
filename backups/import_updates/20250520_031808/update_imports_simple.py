"""
Script to update import statements across the codebase.

This script:
1. Finds Python files with utils imports
2. Updates the imports to match the new structure
3. Creates a backup of each modified file

Usage:
    python scripts/update_imports_simple.py [--apply]

Author: cbs-core-dev Assistant
Date: May 20, 2025
"""

import os
import re
import logging
import argparse
import shutil
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
BACKUP_DIR = os.path.join(PROJECT_ROOT, "backups", "import_updates")

# Import patterns to search for and their replacements
IMPORT_PATTERNS = [
    # Config imports
    (r"from utils import (config|database_type_manager|environment|api|compatibility)", r"from utils.config import \1"),
    (r"from utils\.(config|database_type_manager|environment|api|compatibility) import", r"from utils.config.\1 import"),
    
    # Lib imports
    (r"from utils import (service_registry|module_interface|encryption|task_manager|payment_utils|notification_service|packages|cleanup_utils|framework_compatibility|setup_imports|refactoring_utilities)", r"from utils.lib import \1"),
    (r"from utils\.(service_registry|module_interface|encryption|task_manager|payment_utils|notification_service|packages|cleanup_utils|framework_compatibility|setup_imports|refactoring_utilities) import", r"from utils.lib.\1 import"),
    
    # Common imports
    (r"from utils import (date_format|id_formatters)", r"from utils.common import \1"),
    (r"from utils\.(date_format|id_formatters) import", r"from utils.common.\1 import"),
    
    # Example imports
    (r"from utils import (service_registry_examples)", r"from utils.examples import \1"),
    (r"from utils\.(service_registry_examples) import", r"from utils.examples.\1 import")
]

def find_python_files():
    """Find all Python files in the project."""
    logger.info("Finding Python files")
    
    python_files = []
    
    for root, _, files in os.walk(PROJECT_ROOT):
        if "dump" in root or "backups" in root or "__pycache__" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    logger.info(f"Found {len(python_files)} Python files")
    return python_files

def backup_file(file_path):
    """Create a backup of a file."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join(BACKUP_DIR, timestamp)
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    backup_path = os.path.join(backup_dir, os.path.basename(file_path))
    shutil.copy2(file_path, backup_path)
    
    logger.info(f"Created backup: {backup_path}")
    return backup_path

def update_imports(file_path, apply=False):
    """Update imports in a file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    original_content = content
    changes = []
    
    # Apply each pattern
    for pattern, replacement in IMPORT_PATTERNS:
        # Find all matches
        matches = re.finditer(pattern, content, re.MULTILINE)
        
        for match in matches:
            old_import = match.group(0)
            new_import = re.sub(pattern, replacement, old_import)
            
            if old_import != new_import:
                changes.append((old_import, new_import))
    
    # Apply changes
    for old_import, new_import in changes:
        content = content.replace(old_import, new_import)
    
    # If changes were made and apply is True, update the file
    if content != original_content and apply:
        backup_file(file_path)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Updated imports in {file_path}")
    
    return changes

def create_report(file_changes):
    """Create a report of the changes."""
    report_path = os.path.join(PROJECT_ROOT, "import_updates_simple_report.md")
    
    with open(report_path, 'w') as f:
        f.write("# Import Updates Report\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Files to Update\n\n")
        
        total_changes = 0
        
        for file_path, changes in file_changes.items():
            if not changes:
                continue
                
            rel_path = os.path.relpath(file_path, PROJECT_ROOT)
            f.write(f"### {rel_path}\n\n")
            
            f.write("| Old Import | New Import |\n")
            f.write("|------------|------------|\n")
            
            for old_import, new_import in changes:
                f.write(f"| `{old_import}` | `{new_import}` |\n")
            
            f.write("\n")
            total_changes += len(changes)
        
        f.write(f"\n## Summary\n\n")
        f.write(f"* Files to update: {len([f for f, c in file_changes.items() if c])}\n")
        f.write(f"* Total import statements to change: {total_changes}\n")
        
        f.write("\n## How to Apply Changes\n\n")
        f.write("To apply these changes, run the script with the `--apply` flag:\n\n")
        f.write("```\npython scripts/update_imports_simple.py --apply\n```\n")
    
    logger.info(f"Created report at {report_path}")
    return report_path

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Update import statements in Python files.')
    parser.add_argument('--apply', action='store_true', help='Apply the changes to the files.')
    args = parser.parse_args()
    
    logger.info("Starting import updates")
    
    # Create backup directory if it doesn't exist
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    # Find Python files
    python_files = find_python_files()
    
    # Update imports
    file_changes = {}
    
    for file_path in python_files:
        changes = update_imports(file_path, apply=args.apply)
        file_changes[file_path] = changes
    
    # Create report
    report_path = create_report(file_changes)
    
    # Summary
    files_to_update = len([f for f, c in file_changes.items() if c])
    total_changes = sum(len(c) for c in file_changes.values())
    
    if args.apply:
        logger.info(f"Applied changes to {files_to_update} files ({total_changes} import statements)")
    else:
        logger.info(f"Found {files_to_update} files to update ({total_changes} import statements)")
        logger.info(f"Run with --apply to apply the changes")
    
    logger.info(f"See the report at {report_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
