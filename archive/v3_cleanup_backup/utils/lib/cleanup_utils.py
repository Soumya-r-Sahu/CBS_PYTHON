#!/usr/bin/env python3
"""
Clean Up Utility for CBS_PYTHON Codebase

This script identifies and helps remove unnecessary duplicate files/functions
after the refactoring to consolidated utilities is complete.

Usage:
    python cleanup_utils.py --check
    python cleanup_utils.py --scan
    python cleanup_utils.py --remove
"""

import os
import sys
import re
import argparse
import shutil
from typing import List, Dict, Set, Tuple

# Define consolidated utilities modules
CONSOLIDATED_MODULES = [
    'utils.common.id_utils',
    'utils.common.validators',
    'utils.common.encryption',
    'utils.common.date_format',
    'utils.common.cross_cutting',
    'utils.common.design_patterns',
    'utils.common.gdpr_compliance',
    'utils.common.xss_protection',
    'utils.config.config',
    'utils.config.config_manager',
    'utils.config.database_type_manager',
    'utils.lib.cleanup_utils',
    'utils.lib.encryption',
    'utils.lib.framework_compatibility',
    'utils.lib.payment_utils',
    'utils.lib.refactoring_utilities',
    'utils.lib.sql_security'
]

# Define patterns for functions that have been consolidated
CONSOLIDATED_PATTERNS = [
    r'import\s+utils\.common',
    r'import\s+utils\.config',
    r'import\s+utils\.lib',
    r'from\s+utils\.common\s+import',
    r'from\s+utils\.config\s+import',
    r'from\s+utils\.lib\s+import'
]

def find_python_files(directory: str) -> List[str]:
    """
    Find all Python files in the given directory and its subdirectories.
    
    Args:
        directory: The directory to search in
        
    Returns:
        List of file paths
    """
    python_files = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def check_imports(file_path: str) -> Set[str]:
    """
    Check a file for imports of consolidated utility modules.
    
    Args:
        file_path: The file to check
        
    Returns:
        Set of imported consolidated modules
    """
    imported_modules = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            for module in CONSOLIDATED_MODULES:
                # Check for direct imports
                if f"import {module}" in content or f"from {module} import" in content:
                    imported_modules.add(module)
                
                # Check for wildcard imports from parent packages
                base_module = '.'.join(module.split('.')[:2])  # e.g., utils.common
                if f"from {base_module} import *" in content:
                    imported_modules.add(module)
    
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return imported_modules

def find_duplicate_code(directory: str) -> Dict[str, List[str]]:
    """
    Find files with duplicate functionality that has been consolidated.
    
    Args:
        directory: The directory to search in
        
    Returns:
        Dictionary mapping consolidated modules to lists of potential duplicate files
    """
    python_files = find_python_files(directory)
    duplicates = {module: [] for module in CONSOLIDATED_MODULES}
    
    # Map module name to its base name for easier matching
    module_base_names = {module: module.split('.')[-1] for module in CONSOLIDATED_MODULES}
    
    for file_path in python_files:
        # Skip the consolidated modules themselves
        if any(module.replace('.', os.sep) + '.py' in file_path for module in CONSOLIDATED_MODULES):
            continue
        
        # Check if the file name suggests a duplicate
        file_name = os.path.basename(file_path)
        file_base = os.path.splitext(file_name)[0]
        
        for module, base_name in module_base_names.items():
            if file_base == base_name or file_base.replace('_', '') == base_name.replace('_', ''):
                duplicates[module].append(file_path)
                break
    
    return duplicates

def can_safely_remove(file_path: str) -> bool:
    """
    Check if a file can be safely removed after refactoring.
    
    Args:
        file_path: The file to check
        
    Returns:
        Boolean indicating if the file can be safely removed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Check if the file contains a deprecation warning
            if '# DEPRECATED' in content or '# Deprecated' in content:
                return True
            
            # Check if file only contains imports and no actual implementation
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            code_lines = [line for line in lines if not line.startswith('#') and not line.startswith('import') and not line.startswith('from')]
            
            return len(code_lines) == 0
    
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return False

def generate_report(duplicates: Dict[str, List[str]]) -> None:
    """
    Generate a report of potential duplicate files.
    
    Args:
        duplicates: Dictionary mapping consolidated modules to lists of potential duplicate files
    """
    print("\n=== Potential Duplicate Files Report ===\n")
    
    total_duplicates = 0
    for module, files in duplicates.items():
        if files:
            total_duplicates += len(files)
            print(f"Files potentially duplicating {module}:")
            for file_path in files:
                safe_to_remove = can_safely_remove(file_path)
                status = "SAFE TO REMOVE" if safe_to_remove else "NEEDS REVIEW"
                print(f"  {file_path} [{status}]")
            print()
    
    print(f"Total potential duplicates: {total_duplicates}")

def remove_duplicates(duplicates: Dict[str, List[str]], backup: bool = True) -> None:
    """
    Remove duplicate files after confirmation.
    
    Args:
        duplicates: Dictionary mapping consolidated modules to lists of potential duplicate files
        backup: Whether to create backup files before removal
    """
    files_to_remove = []
    
    for files in duplicates.values():
        for file_path in files:
            if can_safely_remove(file_path):
                files_to_remove.append(file_path)
    
    if not files_to_remove:
        print("No files safe to remove automatically.")
        return
    
    print("\n=== Files to Remove ===\n")
    for file_path in files_to_remove:
        print(f"  {file_path}")
    
    confirmation = input("\nDo you want to remove these files? (yes/no): ")
    if confirmation.lower() != 'yes':
        print("Operation cancelled.")
        return
    
    for file_path in files_to_remove:
        try:
            if backup:
                backup_path = file_path + '.bak'
                shutil.copy2(file_path, backup_path)
                print(f"Backup created: {backup_path}")
            
            os.remove(file_path)
            print(f"Removed: {file_path}")
        except Exception as e:
            print(f"Error removing {file_path}: {e}")

def main() -> None:
    """Main function to parse arguments and execute the utility."""
    parser = argparse.ArgumentParser(description='Clean Up Utility for CBS_PYTHON Codebase')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--check', action='store_true', help='Check for imports of consolidated modules')
    group.add_argument('--scan', action='store_true', help='Scan for potential duplicate files')
    group.add_argument('--remove', action='store_true', help='Remove duplicate files (with confirmation)')
    parser.add_argument('--no-backup', action='store_true', help='Do not create backup files when removing')
    parser.add_argument('--directory', default='.', help='Directory to scan (default: current directory)')
    
    args = parser.parse_args()
    directory = os.path.abspath(args.directory)
    
    if args.check:
        print(f"Checking imports in {directory}...")
        python_files = find_python_files(directory)
        for file_path in python_files:
            imported_modules = check_imports(file_path)
            if imported_modules:
                print(f"\n{file_path} imports:")
                for module in imported_modules:
                    print(f"  - {module}")
    
    elif args.scan:
        print(f"Scanning for potential duplicates in {directory}...")
        duplicates = find_duplicate_code(directory)
        generate_report(duplicates)
    
    elif args.remove:
        print(f"Finding duplicates to remove in {directory}...")
        duplicates = find_duplicate_code(directory)
        remove_duplicates(duplicates, not args.no_backup)

if __name__ == "__main__":
    main()
