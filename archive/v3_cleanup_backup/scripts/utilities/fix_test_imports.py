#!/usr/bin/env python
"""
Test Import Path Fixer for CBS_PYTHON

This script fixes import path issues in test files,
specifically addressing the case sensitivity between 'Tests' and 'tests'.
"""

import os
import sys
import re
from pathlib import Path

def fix_import_paths(directory):
    """Fix import paths in Python files in the given directory."""
    # Get the directory content
    print(f"Processing directory: {directory}")
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                fix_file_imports(os.path.join(root, file))

def fix_file_imports(file_path):
    """Fix import paths in a specific Python file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace 'from tests.' with 'from Tests.'
    if 'from tests.' in content or 'import tests.' in content:
        print(f"Fixing imports in: {file_path}")
        new_content = re.sub(r'from\s+tests\.', 'from Tests.', content)
        new_content = re.sub(r'import\s+tests\.', 'import Tests.', new_content)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_content)

if __name__ == "__main__":
    # Get the project root
    project_root = Path(__file__).resolve().parent.parent.parent
    
    # Fix test imports in the Tests directory
    fix_import_paths(project_root / "Tests")
    
    print("\nFixed import paths in test files.")
