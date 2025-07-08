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
    'utils.common.id_formatters',
    'utils.common.validators',
    'utils.common.encryption',
    'utils.payment_utils'
]

# Define patterns for functions that have been consolidated
CONSOLIDATED_PATTERNS = [
    r'import\s+utils\.common',
    r'from\s+utils\.common\s+import',
    r'from\s+utils\.payment_utils\s+import',
    r'common_[a-zA-Z0-9_]+\s*\(',
]

def scan_for_unused_utilities(directory: str) -> Tuple[Dict[str, List[str]], List[str]]:
    """
    Scan for potentially unused utility files and functions.
    
    Args:
        directory: Directory to scan
        
    Returns:
        Tuple of:
            - Dictionary mapping file paths to lists of unused functions
            - List of files that might be completely removable
    """
    # Find all imports of the consolidated modules
    import_pattern = re.compile(r'(from|import)\s+([a-zA-Z0-9_.]+)\s+import\s+([a-zA-Z0-9_, ]+)')
    
    # Track imports and their usage
    imports_by_file = {}
    function_usages = {}
    wrapped_functions = set()
    
    # First pass: find all imports and wrapped functions
    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Find imports
                    imports = []
                    for match in import_pattern.finditer(content):
                        module = match.group(2)
                        if any(module.startswith(m) for m in CONSOLIDATED_MODULES):
                            imported_items = match.group(3).split(',')
                            imported_items = [item.strip() for item in imported_items]
                            imports.extend(imported_items)
                    
                    if imports:
                        imports_by_file[file_path] = imports
                    
                    # Find wrapper functions (functions that return common_X)
                    wrapper_pattern = re.compile(r'def\s+([a-zA-Z0-9_]+).*?return\s+common_([a-zA-Z0-9_]+)', re.DOTALL)
                    for match in wrapper_pattern.finditer(content):
                        wrapped_functions.add(match.group(1))
                        
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    # Second pass: find function usages
    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check each function
                    for func in wrapped_functions:
                        pattern = re.compile(r'[^a-zA-Z0-9_]{}[^a-zA-Z0-9_]'.format(func))
                        if pattern.search(content):
                            if func not in function_usages:
                                function_usages[func] = []
                            function_usages[func].append(file_path)
                        
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    # Identify unused wrapper functions
    unused_functions = {}
    for file_path, imports in imports_by_file.items():
        unused = []
        for func in wrapped_functions:
            if func in imports and (func not in function_usages or len(function_usages[func]) <= 1):
                unused.append(func)
        
        if unused:
            unused_functions[file_path] = unused
    
    # Identify completely wrapped utility files
    removable_files = []
    for file_path in unused_functions.keys():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Count non-wrapper functions
                non_wrapper_pattern = re.compile(r'def\s+([a-zA-Z0-9_]+).*?(?!return\s+common_[a-zA-Z0-9_]+)', re.DOTALL)
                non_wrapper_matches = non_wrapper_pattern.finditer(content)
                non_wrapper_count = sum(1 for _ in non_wrapper_matches)
                
                # If all functions are wrappers, file might be removable
                if non_wrapper_count == 0:
                    removable_files.append(file_path)
                
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
    
    return unused_functions, removable_files

def check_for_consolidated_usage(directory: str) -> Dict[str, List[str]]:
    """
    Check which files are using consolidated utilities.
    
    Args:
        directory: Directory to check
        
    Returns:
        Dictionary mapping consolidated pattern to files using it
    """
    usage = {}
    
    for pattern_str in CONSOLIDATED_PATTERNS:
        pattern = re.compile(pattern_str)
        usage[pattern_str] = []
        
        for root, _, files in os.walk(directory):
            for file in files:
                if not file.endswith('.py'):
                    continue
                    
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if pattern.search(content):
                            usage[pattern_str].append(file_path)
                        
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return usage

def main():
    parser = argparse.ArgumentParser(description='Clean up utility for CBS_PYTHON codebase')
    parser.add_argument('--check', action='store_true', help='Check for files using consolidated utilities')
    parser.add_argument('--scan', action='store_true', help='Scan for potentially unused utilities')
    parser.add_argument('--remove', action='store_true', help='Remove unused utilities (DANGEROUS, backup first)')
    parser.add_argument('--dir', type=str, default='.', help='Directory to scan')
    args = parser.parse_args()
    
    if not (args.check or args.scan or args.remove):
        parser.print_help()
        sys.exit(1)
    
    if args.check:
        print("Checking for consolidated utilities usage...")
        usage = check_for_consolidated_usage(args.dir)
        
        for pattern, files in usage.items():
            print(f"\nPattern: {pattern}")
            print(f"Found in {len(files)} files:")
            for file in sorted(files)[:5]:  # Show only first 5 to avoid cluttering output
                print(f"  - {file}")
            if len(files) > 5:
                print(f"  - ... and {len(files) - 5} more")
        
        print("\nDone!")
    
    if args.scan:
        print("Scanning for unused utilities...")
        unused_functions, removable_files = scan_for_unused_utilities(args.dir)
        
        print("\nPotentially unused wrapper functions:")
        for file, functions in unused_functions.items():
            print(f"\n{file}:")
            for func in functions:
                print(f"  - {func}")
        
        print("\nPotentially removable files:")
        for file in removable_files:
            print(f"  - {file}")
        
        print("\nDone!")
    
    if args.remove:
        print("WARNING: This will remove unused utilities. Make sure you have a backup!")
        confirm = input("Are you sure you want to continue? (y/N): ")
        
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            sys.exit(0)
        
        print("Scanning for unused utilities...")
        unused_functions, removable_files = scan_for_unused_utilities(args.dir)
        
        print("\nRemoving unused files...")
        for file in removable_files:
            try:
                # Create a backup
                backup_path = file + '.bak'
                shutil.copy2(file, backup_path)
                print(f"Backed up {file} to {backup_path}")
                
                # Remove the file
                os.remove(file)
                print(f"Removed {file}")
            except Exception as e:
                print(f"Error removing {file}: {e}")
        
        print("\nDone!")

if __name__ == "__main__":
    main()
