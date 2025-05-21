#!/usr/bin/env python
"""
Security References Update Script

This script updates security references across modules to use centralized security components.
It scans the codebase for security-related imports and updates them to use the new
centralized security framework.

Usage:
    python update_security_references.py [--dry-run]

Options:
    --dry-run    Only show what would be changed without making actual changes
"""

import os
import re
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Set, Optional, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"security_references_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)
logger = logging.getLogger(__name__)

# Define old and new import patterns
SECURITY_IMPORT_PATTERNS = [
    # Old pattern, new pattern
    (r'from\s+security\.encryption\s+import\s+(.*)', r'from security.common.encryption import \1'),
    (r'from\s+security\.auth\s+import\s+(.*)', r'from security.common.auth import \1'),
    (r'from\s+security\.validation\s+import\s+(.*)', r'from security.common.validation import \1'),
    (r'from\s+security\.tokens\s+import\s+(.*)', r'from security.common.tokens import \1'),
    (r'from\s+security\.password\s+import\s+(.*)', r'from security.common.password import \1'),
    (r'from\s+security\.session\s+import\s+(.*)', r'from security.common.session import \1'),
    (r'import\s+security\.encryption', r'import security.common.encryption'),
    (r'import\s+security\.auth', r'import security.common.auth'),
    (r'import\s+security\.validation', r'import security.common.validation'),
    (r'import\s+security\.tokens', r'import security.common.tokens'),
    (r'import\s+security\.password', r'import security.common.password'),
    (r'import\s+security\.session', r'import security.common.session'),
]

# Direct function reference replacements
FUNCTION_REFERENCE_PATTERNS = [
    # Old function reference, new function reference
    (r'security\.encryption\.encrypt', r'security.common.encryption.encrypt'),
    (r'security\.encryption\.decrypt', r'security.common.encryption.decrypt'),
    (r'security\.auth\.authenticate', r'security.common.auth.authenticate'),
    (r'security\.auth\.authorize', r'security.common.auth.authorize'),
    (r'security\.validation\.validate', r'security.common.validation.validate'),
    (r'security\.tokens\.generate_token', r'security.common.tokens.generate_token'),
    (r'security\.tokens\.validate_token', r'security.common.tokens.validate_token'),
    (r'security\.password\.hash_password', r'security.common.password.hash_password'),
    (r'security\.password\.verify_password', r'security.common.password.verify_password'),
    (r'security\.session\.create_session', r'security.common.session.create_session'),
    (r'security\.session\.validate_session', r'security.common.session.validate_session'),
]

# Directories to exclude from scanning
EXCLUDED_DIRS = [
    '__pycache__',
    'venv',
    'env',
    '.git',
    '.idea',
    '.vscode',
    'node_modules',
    'dump',
    'backups',
    'archive',
]

# File extensions to include in scanning
INCLUDED_EXTENSIONS = ['.py']

def scan_directory(base_dir: Path) -> List[Path]:
    """
    Scan directory recursively for Python files
    
    Args:
        base_dir: Base directory to scan
        
    Returns:
        List of file paths
    """
    python_files = []
    
    for root, dirs, files in os.walk(base_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        
        for file in files:
            if any(file.endswith(ext) for ext in INCLUDED_EXTENSIONS):
                file_path = Path(root) / file
                python_files.append(file_path)
    
    return python_files

def update_file(file_path: Path, dry_run: bool = False) -> Tuple[bool, int]:
    """
    Update security imports and references in a file
    
    Args:
        file_path: Path to file
        dry_run: If True, only show changes without applying them
        
    Returns:
        Tuple of (was_updated, number_of_changes)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = 0
        
        # Update import statements
        for old_pattern, new_pattern in SECURITY_IMPORT_PATTERNS:
            new_content, import_changes = re.subn(old_pattern, new_pattern, content)
            if import_changes > 0:
                content = new_content
                changes += import_changes
        
        # Update function references
        for old_pattern, new_pattern in FUNCTION_REFERENCE_PATTERNS:
            new_content, function_changes = re.subn(old_pattern, new_pattern, content)
            if function_changes > 0:
                content = new_content
                changes += function_changes
        
        if changes > 0:
            if not dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            return True, changes
        
        return False, 0
        
    except Exception as e:
        logger.error(f"Error updating file {file_path}: {str(e)}")
        return False, 0

def generate_report(results: Dict[Path, int], dry_run: bool = False) -> str:
    """
    Generate a report of changes
    
    Args:
        results: Dictionary mapping file paths to number of changes
        dry_run: Whether this was a dry run
        
    Returns:
        Report as string
    """
    total_files = len(results)
    updated_files = sum(1 for changes in results.values() if changes > 0)
    total_changes = sum(results.values())
    
    report = f"""
# Security References Update Report

## Summary

- **Mode**: {"Dry Run (no changes applied)" if dry_run else "Live Run (changes applied)"}
- **Files Scanned**: {total_files}
- **Files Updated**: {updated_files}
- **Total Changes**: {total_changes}
- **Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Details

| File | Changes |
|------|---------|
"""
      # Add details for each updated file
    base_dir = Path(__file__).parent.parent  # Project root
    for file_path, changes in results.items():
        if changes > 0:
            try:
                relative_path = file_path.relative_to(base_dir)
            except ValueError:
                relative_path = str(file_path)
            report += f"| {relative_path} | {changes} |\n"
    
    report += """
## Next Steps

1. Review the changes made to ensure they're correct
2. Run the test suite to verify that the changes don't break existing functionality
3. Update any remaining security references that weren't caught by this script

"""
    return report

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Update security references across modules")
    parser.add_argument('--dry-run', action='store_true', help="Only show what would be changed without making actual changes")
    args = parser.parse_args()
    
    # Get base directory (project root)
    base_dir = Path(__file__).parent.parent
    
    logger.info(f"Starting security references update in {base_dir}")
    logger.info(f"Dry run: {args.dry_run}")
    
    # Scan for Python files
    python_files = scan_directory(base_dir)
    logger.info(f"Found {len(python_files)} Python files to scan")
    
    # Update files
    results = {}
    for file_path in python_files:
        updated, changes = update_file(file_path, args.dry_run)
        results[file_path] = changes
        
        if updated:
            action = "Would update" if args.dry_run else "Updated"
            logger.info(f"{action} {file_path.relative_to(base_dir)} ({changes} changes)")
    
    # Generate report
    report = generate_report(results, args.dry_run)
    report_path = Path(f"security_references_update_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    logger.info(f"Report generated: {report_path}")
    
    # Print summary
    updated_files = sum(1 for changes in results.values() if changes > 0)
    total_changes = sum(results.values())
    
    logger.info(f"Summary: {updated_files} files updated with {total_changes} changes")
    
    if args.dry_run:
        logger.info("This was a dry run. Run without --dry-run to apply changes.")

if __name__ == "__main__":
    main()
