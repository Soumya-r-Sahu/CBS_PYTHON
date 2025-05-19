#!/usr/bin/env python
"""
Requirements Manager

This script helps manage dependencies in the main requirements.txt file.
It can add new dependencies to the appropriate section, ensuring they're
properly formatted with version constraints.

Usage:
    python manage_requirements.py add <package_name> [version] [section] [comment]
    python manage_requirements.py list
    python manage_requirements.py sections

Examples:
    python manage_requirements.py add requests ">=2.31.0" "Core Dependencies" "HTTP client"
    python manage_requirements.py add pytest ">=7.0.0" "Development and Testing"
    python manage_requirements.py list
    python manage_requirements.py sections
"""

import os
import sys
import re
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Path to the main requirements file
REQUIREMENTS_PATH = "requirements.txt"

def get_sections():
    """Get all sections from the requirements file."""
    sections = []
    
    with open(REQUIREMENTS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Match section headings (lines starting with # that aren't file path comments)
    section_pattern = r'^# ([^/][^:].*?)$'
    for match in re.finditer(section_pattern, content, re.MULTILINE):
        section = match.group(1).strip()
        # Skip filepath comments and certain metadata sections
        if not section.startswith('filepath:') and not any(keyword in section.lower() for keyword in 
                                           ["this is", "includes", "note:", "last updated"]):
            sections.append(section)
    
    return sections

def list_requirements():
    """List all requirements by section."""
    with open(REQUIREMENTS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    current_section = None
    packages = {}
    
    for line in content.split('\n'):
        if line.startswith('# ') and not line.startswith('// '):
            # This is a section header
            section = line[2:].strip()
            if not section.startswith('filepath:'):
                current_section = section
                if current_section not in packages:
                    packages[current_section] = []
        elif line.strip() and not line.startswith('#') and not line.startswith('//'):
            # This is a package
            if current_section:
                packages[current_section].append(line.strip())
    
    # Print packages by section
    print(f"{Fore.CYAN}Current requirements by section:")
    for section, pkg_list in packages.items():
        print(f"\n{Fore.GREEN}{section}:")
        for pkg in pkg_list:
            print(f"  {Fore.WHITE}{pkg}")
    
    return packages

def add_requirement(package, version=None, section=None, comment=None):
    """Add a new requirement to the appropriate section."""
    # Validate inputs
    if not package:
        print(f"{Fore.RED}Error: Package name is required.")
        return False
    
    # Get all sections if not specified
    available_sections = get_sections()
    if not available_sections:
        print(f"{Fore.RED}Error: Could not find any sections in {REQUIREMENTS_PATH}")
        return False
    
    # Default to Development and Testing section if not specified
    if not section:
        section = "Development and Testing"
    
    # Validate section
    if section not in available_sections:
        print(f"{Fore.YELLOW}Warning: Section '{section}' not found in requirements file.")
        print(f"{Fore.YELLOW}Available sections:")
        for s in available_sections:
            print(f"  {Fore.CYAN}{s}")
        
        use_anyway = input(f"{Fore.YELLOW}Use this section anyway? (y/n): ").strip().lower()
        if use_anyway != 'y':
            return False
    
    # Format the package line
    if version:
        package_line = f"{package}{version}"
    else:
        package_line = f"{package}"
    
    if comment:
        package_line = f"{package_line}  # {comment}"
    
    # Read the current file
    with open(REQUIREMENTS_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the section and add the package
    new_lines = []
    current_section = None
    package_added = False
    
    for line in lines:
        new_lines.append(line)
        
        # Track the current section
        if line.startswith('# ') and not line.startswith('// '):
            section_name = line[2:].strip()
            if not section_name.startswith('filepath:'):
                current_section = section_name
        
        # Add the package after the last package in the section
        if current_section == section and not package_added:
            # If this is a blank line and the next line starts a new section, add here
            if line.strip() == '' and len(new_lines) < len(lines):
                next_line = lines[len(new_lines)]
                if next_line.startswith('# ') and not next_line.startswith('// '):
                    new_lines.append(f"{package_line}\n")
                    package_added = True
    
    # If the package wasn't added (section might be the last one), add it now
    if not package_added:
        for i in range(len(new_lines) - 1, -1, -1):
            if new_lines[i].strip() == '' and current_section == section:
                new_lines.insert(i, f"{package_line}\n")
                package_added = True
                break
    
    # If still not added, append to the end
    if not package_added:
        print(f"{Fore.YELLOW}Warning: Could not determine where to add the package. Appending to end.")
        new_lines.append(f"\n# {section}\n{package_line}\n")
    
    # Write the updated file
    with open(REQUIREMENTS_PATH, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"{Fore.GREEN}✅ Added {package_line} to section '{section}'")
    return True

def print_sections():
    """Print all available sections in the requirements file."""
    sections = get_sections()
    
    print(f"{Fore.CYAN}Available sections in {REQUIREMENTS_PATH}:")
    for section in sections:
        print(f"  {Fore.GREEN}{section}")

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_requirements()
    
    elif command == "sections":
        print_sections()
    
    elif command == "add":
        if len(sys.argv) < 3:
            print(f"{Fore.RED}Error: Package name is required.")
            print("Usage: python manage_requirements.py add <package_name> [version] [section] [comment]")
            sys.exit(1)
        
        package = sys.argv[2]
        version = sys.argv[3] if len(sys.argv) > 3 else ">=0.0.1"
        section = sys.argv[4] if len(sys.argv) > 4 else None
        comment = sys.argv[5] if len(sys.argv) > 5 else None
        
        if add_requirement(package, version, section, comment):
            sys.exit(0)
        else:
            sys.exit(1)
    
    else:
        print(f"{Fore.RED}Error: Unknown command '{command}'")
        print(__doc__)
        sys.exit(1)

if __name__ == "__main__":
    main()
