#!/usr/bin/env python
"""
Version Verification Script for CBS_PYTHON

This script verifies that all version references in the codebase
have been updated to 1.1.1 for the v1.1.1 release.
"""

import os
import re
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Get the project root
project_root = Path(__file__).resolve().parent.parent.parent
current_version = "1.1.1"

def check_file(file_path, patterns):
    """
    Check a file for version patterns.
    Returns a dictionary of patterns found and whether the version matches.
    """
    results = {}
    
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    for name, pattern in patterns.items():
        matches = re.findall(pattern, content)
        
        if matches:
            # Only check patterns relevant to this file type
            if file_path.name == 'pyproject.toml' and name != 'pyproject.toml version':
                continue
            if file_path.name == 'setup.py' and name != 'setup.py version':
                continue
            if file_path.name.endswith('.md') and name not in ['Version badge', 'README version', 'CHANGELOG']:
                continue
            
            for match in matches:
                version = match.strip() if isinstance(match, str) else match[0].strip()
                is_current = version == current_version
                
                if not is_current:
                    results[name] = {
                        "found": version,
                        "should_be": current_version,
                        "is_current": False
                    }
                    break
    
    return results

def find_version_references():
    """
    Find and check version references in the codebase.
    """
    version_patterns = {
        "Version badge": r'Version-([0-9.]+)-brightgreen',
        "setup.py version": r'version="([0-9.]+)"',
        "pyproject.toml version": r'version = "([0-9.]+)"',
        "CHANGELOG": r'## \[([0-9.]+)\] - 2025-05-19',
        "README version": r'![Version ([0-9.]+)]',
    }
    
    files_to_check = [
        project_root / "README.md",
        project_root / "setup.py",
        project_root / "pyproject.toml",
        project_root / "CHANGELOG.md",
        project_root / "Documentation" / "CHANGELOG.md",
    ]
    
    inconsistent_versions = {}
    
    for file_path in files_to_check:
        if file_path.exists():
            results = check_file(file_path, version_patterns)
            
            if results:
                inconsistent_versions[str(file_path)] = results
    
    return inconsistent_versions

def main():
    """Main function."""
    print(f"{Fore.CYAN}Checking for version references in the codebase...")
    inconsistent_versions = find_version_references()
    
    if inconsistent_versions:
        print(f"\n{Fore.RED}Found inconsistent version references:")
        
        for file_path, results in inconsistent_versions.items():
            print(f"\n{Fore.YELLOW}File: {file_path}")
            
            for pattern_name, result in results.items():
                print(f"  {Fore.RED}- {pattern_name}: found {result['found']}, should be {result['should_be']}")
        
        print(f"\n{Fore.RED}Please update these version references to {current_version} before releasing.")
        return False
    else:
        print(f"\n{Fore.GREEN}All version references are consistent with {current_version}. ✓")
        return True

if __name__ == "__main__":
    main()
