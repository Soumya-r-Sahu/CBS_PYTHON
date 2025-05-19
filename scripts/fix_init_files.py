#!/usr/bin/env python
"""
Init File Fixer

This script adds the centralized import system to __init__.py files.

Usage:
    python fix_init_files.py [directory]

If no directory is specified, the script checks the entire project.
"""

import os
import sys
import re
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Initialize statistics
stats = {
    'files_checked': 0,
    'files_modified': 0
}

def fix_init_file(file_path):
    """Fix __init__.py file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"{Fore.RED}Error reading file {file_path}: {e}")
        return False
    
    # Skip if already has the import
    if re.search(r'from\s+utils\.lib\.packages\s+import', content):
        return False
    
    # Add import only if file is not empty and doesn't already have it
    if content.strip():
        new_content = '# Use centralized import system\nfrom utils.lib.packages import fix_path\nfix_path()  # Ensures project root is in sys.path\n\n' + content
    else:
        new_content = '# Use centralized import system\nfrom utils.lib.packages import fix_path\nfix_path()  # Ensures project root is in sys.path\n'
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        stats['files_modified'] += 1
        return True
    except Exception as e:
        print(f"{Fore.RED}Error writing file {file_path}: {e}")
        return False

def scan_and_fix_directory(directory):
    """Scan a directory for __init__.py files and fix them."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file == '__init__.py':
                file_path = os.path.join(root, file)
                stats['files_checked'] += 1
                
                fixed = fix_init_file(file_path)
                if fixed:
                    rel_path = os.path.relpath(file_path, start=directory)
                    print(f"{Fore.GREEN}✅ Fixed imports in: {rel_path}")
    
    return stats

def print_report(stats):
    """Print a summary report of fixed files."""
    print(f"\n{Fore.GREEN}=== Init File Fix Report ===")
    print(f"{Fore.CYAN}Files checked: {stats['files_checked']}")
    print(f"{Fore.GREEN}Files modified: {stats['files_modified']}")

def main():
    """Main function."""
    # Get directory from command line or use current directory
    directory = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    print(f"{Fore.CYAN}Fixing __init__.py files in {directory}...")
    stats = scan_and_fix_directory(directory)
    print_report(stats)

if __name__ == "__main__":
    main()
