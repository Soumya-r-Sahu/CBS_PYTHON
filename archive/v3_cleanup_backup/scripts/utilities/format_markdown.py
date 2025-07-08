#!/usr/bin/env python
"""
Markdown File Formatter for CBS_PYTHON

This script formats all Markdown files in the project to ensure consistent styling.
It performs tasks like:
1. Standardizing line endings
2. Ensuring a single newline at the end of files
3. Removing trailing whitespace
4. Consistent heading formatting
"""

import os
import sys
import re
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Get the project root
project_root = Path(__file__).resolve().parent.parent.parent

def format_markdown_file(file_path):
    """Format a Markdown file for consistency."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Store original content for comparison
        original_content = content
        
        # Apply formatting rules
        
        # 1. Standardize line endings to LF
        content = content.replace('\r\n', '\n')
        
        # 2. Remove trailing whitespace
        content = '\n'.join(line.rstrip() for line in content.split('\n'))
        
        # 3. Ensure a single newline at the end of the file
        content = content.rstrip('\n') + '\n'
        
        # 4. Standardize heading levels - space after # for headings
        content = re.sub(r'^(#+)([^#\s])', r'\1 \2', content, flags=re.MULTILINE)
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
    except Exception as e:
        print(f"{Fore.RED}Error formatting {file_path}: {str(e)}")
        return False

def find_markdown_files():
    """Find all Markdown files in the project."""
    markdown_files = []
    
    for root, dirs, files in os.walk(project_root):
        root_path = Path(root)
        
        # Skip some directories
        dirs_to_skip = ['.git', '__pycache__', 'venv', '.pytest_cache']
        dirs[:] = [d for d in dirs if d not in dirs_to_skip]
        
        for file in files:
            if file.lower().endswith('.md'):
                file_path = root_path / file
                markdown_files.append(file_path)
    
    return markdown_files

def main():
    """Main function."""
    print(f"{Fore.CYAN}Finding Markdown files...")
    markdown_files = find_markdown_files()
    print(f"{Fore.CYAN}Found {len(markdown_files)} Markdown files")
    
    formatted_count = 0
    for file_path in markdown_files:
        rel_path = file_path.relative_to(project_root)
        if format_markdown_file(file_path):
            formatted_count += 1
            print(f"{Fore.GREEN}Formatted: {rel_path}")
    
    print(f"\n{Fore.CYAN}Summary:")
    print(f"{Fore.GREEN}Total Markdown files: {len(markdown_files)}")
    print(f"{Fore.GREEN}Files formatted: {formatted_count}")
    print(f"{Fore.GREEN}Files already well-formatted: {len(markdown_files) - formatted_count}")

if __name__ == "__main__":
    main()
