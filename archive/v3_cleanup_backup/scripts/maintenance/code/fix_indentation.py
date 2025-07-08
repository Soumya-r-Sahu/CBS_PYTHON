"""
Script to fix indentation issues in Python files

This script automatically detects and fixes common indentation issues 
in Python code files throughout the project.
"""
import os
import sys
import re
from pathlib import Path

def format_file(file_path):
    """
    Fix indentation issues in a Python file
    
    Args:
        file_path: Path to the Python file
    
    Returns:
        bool: True if changes were made, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Fix common indentation issues
        
        # 1. Fix indentation after function definitions
        content = re.sub(r'def ([a-zA-Z0-9_]+)\(.*\).*:\n\s*(?=def)', r'def \1\2:\n\n    def', content)
        
        # 2. Fix mixed tabs and spaces
        lines = content.split('\n')
        fixed_lines = []
        for line in lines:
            # Replace tabs with 4 spaces
            if '\t' in line:
                indent_count = len(line) - len(line.lstrip('\t'))
                fixed_line = ' ' * (4 * indent_count) + line.lstrip('\t')
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
                
        fixed_content = '\n'.join(fixed_lines)
        
        # 3. Fix incorrect indentation after closing brackets
        fixed_content = re.sub(r'(^\s+]|^\s+\)|^\s+})', r'\1\n', fixed_content, flags=re.MULTILINE)
        
        # Write back if changes were made
        if content != fixed_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            return True
            
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def scan_directory(directory):
    """
    Scan a directory for Python files and fix indentation issues
    
    Args:
        directory: Directory path to scan
    
    Returns:
        tuple: (total_files, fixed_files)
    """
    py_files = list(Path(directory).rglob("*.py"))
    total_files = len(py_files)
    fixed_files = 0
    
    for i, file_path in enumerate(py_files):
        if i % 10 == 0:
            print(f"Processing files: {i}/{total_files}")
            
        if format_file(file_path):
            fixed_files += 1
            print(f"Fixed indentation in {file_path}")
    
    return total_files, fixed_files

def main():
    """
    Main entry point for the script
    """
    # Use the current directory as the default
    directory = os.getcwd()
    
    # Allow overriding the directory from command line
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    
    print(f"Scanning directory: {directory}")
    total, fixed = scan_directory(directory)
    
    print(f"\nResults:")
    print(f"- Total Python files: {total}")
    print(f"- Files with fixed indentation: {fixed}")
    print(f"- Files without issues: {total - fixed}")
    
    if fixed > 0:
        print("\n✅ Indentation issues have been fixed!")
    else:
        print("\n✅ No indentation issues found!")

if __name__ == "__main__":
    main()
