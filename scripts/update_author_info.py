"""
Update Author Information

This script updates the author information in all files with the standard format.
"""
import os
import re
from pathlib import Path

# GitHub username to use
GITHUB_USERNAME = "cbs-core-dev"

# Project root directory
PROJECT_ROOT = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# File patterns to include
INCLUDE_PATTERNS = [
    "*.py",
    "*.md"
]

# Regex patterns for author lines
AUTHOR_PATTERNS = [
    r'Author: *your-github-username',
    r'Author: *[a-zA-Z0-9_-]+'
]

def update_author_in_file(file_path):
    """Update author information in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if any author pattern matches
        updated = False
        for pattern in AUTHOR_PATTERNS:
            if re.search(pattern, content):
                content = re.sub(pattern, f"Author: {GITHUB_USERNAME}", content)
                updated = True
        
        if updated:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated author in {file_path.relative_to(PROJECT_ROOT)}")
            return True
    except Exception as e:
        print(f"Error updating {file_path}: {str(e)}")
    
    return False

def find_and_update_files():
    """Find and update files with author information"""
    updated_count = 0
    
    for pattern in INCLUDE_PATTERNS:
        for file_path in PROJECT_ROOT.glob(f"**/{pattern}"):
            if update_author_in_file(file_path):
                updated_count += 1
    
    return updated_count

if __name__ == "__main__":
    print(f"Updating author information to '{GITHUB_USERNAME}'")
    updated = find_and_update_files()
    print(f"Updated author information in {updated} files")
