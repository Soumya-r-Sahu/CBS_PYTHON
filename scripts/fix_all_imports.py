#!/usr/bin/env python
"""
Comprehensive Import System Fixer

This script aggressively fixes import issues across the entire project.
It adds the centralized import system to any file with functions or classes.

Usage:
    python fix_all_imports.py [directory]

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
    'files_modified': 0,
    'duplicates_removed': 0,
    'central_imports_added': 0,
    'deprecated_imports_fixed': 0
}

def fix_imports(file_path):
    """Fix import issues in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"{Fore.RED}Error reading file {file_path}: {e}")
        return False
    
    if len(content.strip()) == 0:
        return False  # Skip empty files
    
    original_content = content
    modified = False
    
    # Fix 1: Remove duplicate DatabaseConnection fallbacks
    fallback_pattern = r'try:[\s\n]+from database\.python\.connection import DatabaseConnection[\s\n]+except ImportError:[\s\n]+# Fallback implementation[\s\n]+class DatabaseConnection:[\s\n]+.*?pass'
    if re.search(fallback_pattern, content, re.DOTALL):
        content = re.sub(fallback_pattern, 'from database.python.connection import DatabaseConnection', content, flags=re.DOTALL)
        stats['duplicates_removed'] += 1
        modified = True
    
    # Fix 2: Add centralized import system if missing
    if not re.search(r'from\s+utils\.lib\.packages\s+import', content):
        # Check if this is a real Python module with functions or classes
        has_functions = re.search(r'def\s+\w+\s*\(', content)
        has_classes = re.search(r'class\s+\w+', content)
        
        if has_functions or has_classes:
            # Find a good spot to add the import
            # Look for other imports to add after them
            import_section_end = 0
            import_lines = re.findall(r'^import.*?$|^from.*?import.*?$', content, re.MULTILINE)
            if import_lines:
                last_import = import_lines[-1]
                import_section_end = content.find(last_import) + len(last_import)
            
            central_import = '\n\n# Use centralized import system\nfrom utils.lib.packages import fix_path\nfix_path()  # Ensures project root is in sys.path\n'
            
            if import_section_end > 0:
                content = content[:import_section_end] + central_import + content[import_section_end:]
            else:
                # If no imports found, add after any initial comments or at the start
                if content.startswith('#'):
                    first_non_comment_line = re.search(r'^[^#]', content, re.MULTILINE)
                    if first_non_comment_line:
                        pos = first_non_comment_line.start()
                        content = content[:pos] + central_import + content[pos:]
                    else:
                        content = content + central_import
                else:
                    content = central_import + content
            
            stats['central_imports_added'] += 1
            modified = True
    
    # Fix 3: Update deprecated import mechanisms
    if re.search(r'from\s+app\.lib\.(import_manager|setup_imports)', content):
        content = re.sub(
            r'from\s+app\.lib\.(import_manager|setup_imports)\s+import.*?$', 
            '# Use centralized import system\nfrom utils.lib.packages import fix_path\nfix_path()  # Ensures project root is in sys.path',
            content,
            flags=re.MULTILINE
        )
        stats['deprecated_imports_fixed'] += 1
        modified = True
    
    if re.search(r'from\s+utils\.lib\.setup_imports', content):
        content = re.sub(
            r'from\s+utils\.lib\.setup_imports\s+import.*?$', 
            '# Use centralized import system\nfrom utils.lib.packages import fix_path\nfix_path()  # Ensures project root is in sys.path',
            content,
            flags=re.MULTILINE
        )
        stats['deprecated_imports_fixed'] += 1
        modified = True
    
    # Only write the file if it was modified
    if modified:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            stats['files_modified'] += 1
            return True
        except Exception as e:
            print(f"{Fore.RED}Error writing file {file_path}: {e}")
            return False
    
    return False

def scan_and_fix_directory(directory):
    """Scan a directory for Python files and fix their imports."""
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                stats['files_checked'] += 1
                
                fixed = fix_imports(file_path)
                if fixed:
                    rel_path = os.path.relpath(file_path, start=directory)
                    print(f"{Fore.GREEN}✅ Fixed imports in: {rel_path}")
    
    return stats

def print_report(stats):
    """Print a summary report of import fixes."""
    print(f"\n{Fore.GREEN}=== Import System Fix Report ===")
    print(f"{Fore.CYAN}Files checked: {stats['files_checked']}")
    print(f"{Fore.GREEN}Files modified: {stats['files_modified']}")
    print(f"{Fore.GREEN}Duplicate fallbacks removed: {stats['duplicates_removed']}")
    print(f"{Fore.GREEN}Central imports added: {stats['central_imports_added']}")
    print(f"{Fore.GREEN}Deprecated imports fixed: {stats['deprecated_imports_fixed']}")

def main():
    """Main function."""
    # Get directory from command line or use current directory
    directory = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    print(f"{Fore.CYAN}Fixing imports in {directory}...")
    stats = scan_and_fix_directory(directory)
    print_report(stats)

if __name__ == "__main__":
    main()
