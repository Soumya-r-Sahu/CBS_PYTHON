"""
Quick Null Byte Fixer Script for CBS_PYTHON

This script quickly fixes the remaining null byte issues in __init__.py files
by creating new, clean files with proper docstrings.
"""

import os
from pathlib import Path

# Define directories with known null byte issues
problem_dirs = [
    r"D:\Vs code\CBS_PYTHON\app\Portals\Admin\dashboard",
    r"D:\Vs code\CBS_PYTHON\core_banking\accounts",
]

def fix_init_file(file_path):
    """Create a new, clean __init__.py file with proper docstring."""
    dir_name = Path(file_path).parent.name
    module_name = Path(file_path).parent.as_posix().replace('\\', '/')
    
    content = f'''"""
{dir_name} module

Part of the CBS_PYTHON Core Banking System.
"""

# Package initialization
'''
    
    # Use 'wb' mode to avoid any encoding issues
    with open(file_path, 'wb') as f:
        f.write(content.encode('utf-8'))
    
    print(f"Fixed: {file_path}")

def main():
    """Fix all __init__.py files in problem directories."""
    for problem_dir in problem_dirs:
        if not os.path.exists(problem_dir):
            print(f"Directory not found: {problem_dir}")
            continue
            
        print(f"Processing: {problem_dir}")
        
        # Walk through all subdirectories
        for root, dirs, files in os.walk(problem_dir):
            if "__init__.py" in files:
                init_path = os.path.join(root, "__init__.py")
                fix_init_file(init_path)

if __name__ == "__main__":
    main()
    print("Done fixing null byte issues!")
