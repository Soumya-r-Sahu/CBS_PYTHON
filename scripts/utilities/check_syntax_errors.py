#!/usr/bin/env python
"""
Syntax Error Checker for CBS_PYTHON

This script checks all Python files in the CBS_PYTHON project for syntax errors.
It outputs a report of files with syntax errors, making it easy to identify and
fix issues before they cause problems.

Usage:
    python scripts/utilities/check_syntax_errors.py [--verbose] [--fix]

Options:
    --verbose  Show detailed information about each file checked
    --fix      Attempt to fix common syntax issues
"""

import os
import sys
import argparse
import subprocess
import tempfile
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Get the project root
project_root = Path(__file__).resolve().parent.parent.parent

def check_file(file_path, verbose=False, fix=False):
    """
    Check a single file for syntax errors.
    Returns True if file is valid, False if it has syntax errors.
    """
    abs_path = Path(file_path).resolve()
    rel_path = abs_path.relative_to(project_root)
    
    if verbose:
        print(f"Checking {rel_path}...")
    
    # Try to compile the file to check for syntax errors
    try:
        with open(abs_path, 'rb') as file:
            content = file.read()
            try:
                compile(content, str(abs_path), 'exec')
            except SyntaxError as e:
                line_num = e.lineno
                line = e.text.strip() if e.text else "<unknown>"
                error_msg = str(e)
                
                print(f"{Fore.RED}X {rel_path} (line {line_num}): {error_msg}")
                print(f"  {line}")
                
                if fix:
                    try_to_fix(abs_path, line_num, error_msg)
                
                return False
            except Exception as e:
                print(f"{Fore.RED}Error compiling {rel_path}: {str(e)}")
                return False
        
        if verbose:
            print(f"{Fore.GREEN}✓ {rel_path}")
        
        return True
    except Exception as e:
        print(f"{Fore.RED}Error reading {rel_path}: {str(e)}")
        return False

def try_to_fix(file_path, line_num, error_msg):
    """Attempt to fix common syntax errors."""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # Only fix if we have enough lines
    if 0 <= line_num - 1 < len(lines):
        line = lines[line_num - 1]
        fixed = False
        
        # Fix common issues
        if "unexpected EOF" in error_msg:
            if line.rstrip().endswith('(') or line.rstrip().endswith('[') or line.rstrip().endswith('{'):
                # Add closing parenthesis/bracket/brace
                if line.rstrip().endswith('('):
                    lines[line_num - 1] = line.rstrip() + ")\n"
                elif line.rstrip().endswith('['):
                    lines[line_num - 1] = line.rstrip() + "]\n"
                elif line.rstrip().endswith('{'):
                    lines[line_num - 1] = line.rstrip() + "}\n"
                fixed = True
        
        elif "invalid syntax" in error_msg and ":" in line:
            if not line.strip().endswith(':'):
                # Fix missing colon at end of control statements
                indent = len(line) - len(line.lstrip())
                parts = line.split(':')
                if len(parts) > 1:
                    # Fix indentation if it's the issue
                    next_line_num = line_num
                    if next_line_num < len(lines):
                        next_line = lines[next_line_num]
                        next_indent = len(next_line) - len(next_line.lstrip())
                        if next_indent <= indent:
                            lines.insert(next_line_num, ' ' * (indent + 4) + "pass\n")
                            fixed = True
        
        # Write fixed file
        if fixed:
            print(f"{Fore.YELLOW}  Attempted to fix {file_path}")
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(lines)

def is_excluded(path):
    """Check if a path should be excluded from checking."""
    excludes = [
        "__pycache__",
        ".git",
        "venv",
        ".pytest_cache",
        ".mypy_cache",
        ".vscode",
        "migrations"
    ]
    
    for exclude in excludes:
        if exclude in path.parts:
            return True
    
    return False

def find_python_files(start_dir=project_root):
    """Find all Python files in the project."""
    python_files = []
    
    for root, dirs, files in os.walk(start_dir):
        root_path = Path(root)
        
        if is_excluded(root_path):
            continue
        
        for file in files:
            if file.endswith('.py'):
                file_path = root_path / file
                python_files.append(file_path)
    
    return python_files

def main():
    parser = argparse.ArgumentParser(description='Check Python files for syntax errors')
    parser.add_argument('--verbose', action='store_true', help='Show verbose output')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix common syntax errors')
    args = parser.parse_args()
    
    print(f"{Fore.CYAN}Checking Python files for syntax errors...")
    
    # Find all Python files
    python_files = find_python_files()
    
    # Sort files by path for consistent output
    python_files.sort()
    
    # Check each file
    valid_count = 0
    error_count = 0
    
    for file_path in python_files:
        if check_file(file_path, args.verbose, args.fix):
            valid_count += 1
        else:
            error_count += 1
    
    # Print summary
    total = valid_count + error_count
    print(f"\n{Fore.CYAN}Syntax Check Summary:")
    print(f"{Fore.GREEN}Valid files: {valid_count}/{total} ({valid_count / total * 100:.1f}%)")
    
    if error_count > 0:
        print(f"{Fore.RED}Files with errors: {error_count}/{total} ({error_count / total * 100:.1f}%)")
        sys.exit(1)
    else:
        print(f"{Fore.GREEN}No syntax errors found! 🎉")
        sys.exit(0)

if __name__ == "__main__":
    main()
