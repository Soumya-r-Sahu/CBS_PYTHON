#!/usr/bin/env python
"""
Import System Checker

This script analyzes Python files in the CBS_PYTHON project to find and report:
1. Files with duplicate import fallbacks
2. Files not using the centralized import system
3. Files using deprecated import mechanisms

Usage:
    python import_checker.py [directory]

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
    'files_with_issues': 0,
    'duplicate_fallbacks': 0,
    'missing_central_imports': 0,
    'deprecated_imports': 0
}

def check_imports(file_path):
    """Check a Python file for import issues."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    # Check for duplicate fallback implementations
    if re.search(r'class\s+DatabaseConnection.*?def\s+__init__.*?except\s+ImportError', content, re.DOTALL):
        issues.append(f"{Fore.RED}❌ Contains duplicate DatabaseConnection fallback")
        stats['duplicate_fallbacks'] += 1
    
    # Check for missing central import system
    if not re.search(r'from\s+utils\.lib\.packages\s+import', content):
        issues.append(f"{Fore.YELLOW}⚠️ Not using centralized import system (utils.lib.packages)")
        stats['missing_central_imports'] += 1
    
    # Check for deprecated import mechanisms
    if re.search(r'from\s+app\.lib\.(import_manager|setup_imports)', content):
        issues.append(f"{Fore.YELLOW}⚠️ Using deprecated import manager (app.lib.import_manager/setup_imports)")
        stats['deprecated_imports'] += 1
    
    if re.search(r'from\s+utils\.lib\.setup_imports', content):
        issues.append(f"{Fore.YELLOW}⚠️ Using deprecated setup_imports (utils.lib.setup_imports)")
        stats['deprecated_imports'] += 1
    
    # Return issues if found
    if issues:
        stats['files_with_issues'] += 1
        return issues
    return None

def scan_directory(directory):
    """Scan a directory for Python files and check their imports."""
    file_counter = 0
    files_with_issues = 0
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                stats['files_checked'] += 1
                
                issues = check_imports(file_path)
                if issues:
                    rel_path = os.path.relpath(file_path, start=directory)
                    print(f"\n{Fore.CYAN}File: {rel_path}")
                    for issue in issues:
                        print(f"  {issue}")
    
    return stats

def print_report(stats):
    """Print a summary report of import issues."""
    print(f"\n{Fore.GREEN}=== Import System Check Report ===")
    print(f"{Fore.GREEN}Files checked: {stats['files_checked']}")
    print(f"{Fore.YELLOW}Files with issues: {stats['files_with_issues']}")
    print(f"{Fore.RED}Duplicate fallbacks found: {stats['duplicate_fallbacks']}")
    print(f"{Fore.YELLOW}Missing central imports: {stats['missing_central_imports']}")
    print(f"{Fore.YELLOW}Deprecated import mechanisms: {stats['deprecated_imports']}")
    print(f"\n{Fore.GREEN}Recommendation: Run the import cleanup script to fix these issues.")

def main():
    """Main function."""
    # Get directory from command line or use current directory
    directory = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    print(f"{Fore.CYAN}Checking imports in {directory}...")
    stats = scan_directory(directory)
    print_report(stats)

if __name__ == "__main__":
    main()
