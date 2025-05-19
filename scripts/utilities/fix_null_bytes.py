#!/usr/bin/env python
"""
Null Byte Fixer for __init__.py Files

This script fixes __init__.py files containing null bytes 
by replacing them with proper __init__.py files with docstrings.
"""

import os
import sys
from pathlib import Path

def fix_init_files(directory):
    """Fix __init__.py files in the directory recursively."""
    fixed_count = 0
    print(f"Scanning directory: {directory}")
    
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == "__init__.py":
                file_path = os.path.join(root, file)
                if fix_init_file(file_path):
                    fixed_count += 1
    
    return fixed_count

def fix_init_file(file_path):
    """Fix a single __init__.py file."""
    try:
        # Check if file has null bytes
        with open(file_path, 'rb') as f:
            content = f.read()
            has_null_bytes = b'\x00' in content
        
        if has_null_bytes or os.path.getsize(file_path) == 0:
            # Create proper docstring based on directory
            module_path = Path(file_path).parent
            rel_path = module_path.relative_to(project_root)
            module_name = str(rel_path).replace('\\', '.')
            
            # Create new content with proper docstring
            new_content = f'''"""
{module_name} Package

This module is part of the Core Banking System.
"""

# Package initialization
'''
            
            # Write new content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"Fixed: {file_path}")
            return True
    except Exception as e:
        print(f"Error fixing {file_path}: {str(e)}")
    
    return False

if __name__ == "__main__":
    # Get the project root
    project_root = Path(__file__).resolve().parent.parent.parent
    
    # Fix all __init__.py files in the project
    total_fixed = fix_init_files(project_root)
    
    print(f"\nTotal files fixed: {total_fixed}")
