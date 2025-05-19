#!/usr/bin/env python
"""
Requirements File Checker

This script scans the project for requirements.txt files and verifies that 
only the main requirements.txt exists at the project root.

Usage:
    python check_requirements_files.py [directory]

If no directory is specified, the script checks the current directory.
"""

import os
import sys
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

def check_requirements_files(directory):
    """
    Scan a directory recursively for requirements.txt files and report any found
    except for the main one at the project root.
    """
    root_requirements_path = os.path.join(directory, "requirements.txt")
    found_files = []
    
    print(f"{Fore.CYAN}Scanning {directory} for requirements.txt files...")
    
    # Walk through all directories recursively
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower() == "requirements.txt":
                file_path = os.path.join(root, file)
                # Skip the main requirements.txt at the project root
                if os.path.normpath(file_path) != os.path.normpath(root_requirements_path):
                    found_files.append(file_path)
    
    # Report findings
    if found_files:
        print(f"\n{Fore.YELLOW}⚠️ Found {len(found_files)} duplicate requirements.txt file(s):")
        for file_path in found_files:
            rel_path = os.path.relpath(file_path, start=directory)
            print(f"{Fore.YELLOW}  - {rel_path}")
        
        print(f"\n{Fore.RED}Recommendation: These should be removed to avoid confusion.")
        print(f"{Fore.CYAN}Consider replacing them with README.requirements.md files that point to the main requirements.txt.")
        return False
    else:
        print(f"\n{Fore.GREEN}✅ No duplicate requirements.txt files found!")
        print(f"{Fore.GREEN}Only the main requirements.txt exists at the project root.")
        return True

def check_main_requirements_exists(directory):
    """Check if the main requirements.txt exists at the project root."""
    root_requirements_path = os.path.join(directory, "requirements.txt")
    
    if os.path.exists(root_requirements_path):
        print(f"{Fore.GREEN}✅ Main requirements.txt found at project root.")
        return True
    else:
        print(f"{Fore.RED}❌ Error: Main requirements.txt not found at project root!")
        print(f"{Fore.RED}A requirements.txt file should exist at {root_requirements_path}")
        return False

def main():
    """Main function."""
    # Get directory from command line or use current directory
    directory = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    # Make sure the path is absolute
    directory = os.path.abspath(directory)
    
    # First check if the main requirements.txt exists
    main_exists = check_main_requirements_exists(directory)
    
    # Then check for duplicates
    no_duplicates = check_requirements_files(directory)
    
    # Exit with appropriate status code
    if main_exists and no_duplicates:
        print(f"\n{Fore.GREEN}✅ Requirements file check passed!")
        sys.exit(0)
    else:
        print(f"\n{Fore.YELLOW}⚠️ Requirements file check found issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()
