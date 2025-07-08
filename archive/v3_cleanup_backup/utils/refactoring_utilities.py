"""
Refactoring Utility for CBS_PYTHON

This script helps identify redundant utility functions and files 
that have been consolidated into the common utilities.
"""
import os
import re
import argparse
from typing import List, Dict, Set

def find_function_references(directory: str, function_name: str) -> List[str]:
    """
    Find all files that reference a specific function.
    
    Args:
        directory: The directory to search in
        function_name: The function name to search for
        
    Returns:
        List of files that reference the function
    """
    references = []
    pattern = re.compile(r'[^a-zA-Z0-9_]{}[^a-zA-Z0-9_]'.format(function_name))
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if pattern.search(content):
                            references.append(file_path)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return references

def find_consolidation_candidates(directory: str) -> Dict[str, List[str]]:
    """
    Find utility functions that might be candidates for consolidation.
    
    Args:
        directory: The directory to search in
        
    Returns:
        Dictionary of function names to files containing similar implementations
    """
    function_patterns = [
        r'def\s+(?P<name>format_[a-zA-Z0-9_]+)',
        r'def\s+(?P<name>generate_[a-zA-Z0-9_]+_reference)',
        r'def\s+(?P<name>mask_[a-zA-Z0-9_]+)',
        r'def\s+(?P<name>sanitize_[a-zA-Z0-9_]+)',
        r'def\s+(?P<name>validate_[a-zA-Z0-9_]+)',
    ]
    
    candidates = {}
    
    for root, _, files in os.walk(directory):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    for pattern in function_patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            function_name = match.group('name')
                            if function_name not in candidates:
                                candidates[function_name] = []
                            candidates[function_name].append(file_path)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
    
    # Filter to only include functions found in multiple files
    return {name: files for name, files in candidates.items() if len(files) > 1}

def identify_consolidated_functions(directory: str) -> Set[str]:
    """
    Identify functions that have been migrated to use common implementations.
    
    Args:
        directory: The directory to search in
        
    Returns:
        Set of file paths that contain functions using common implementations
    """
    pattern = re.compile(r'return\s+common_[a-zA-Z0-9_]+\(')
    consolidated = set()
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if pattern.search(content):
                            consolidated.add(file_path)
                except Exception as e:
                    print(f"Error reading {file_path}: {e}")
    
    return consolidated

def main():
    parser = argparse.ArgumentParser(description='Find candidates for function consolidation')
    parser.add_argument('--dir', type=str, default='.', help='Directory to search')
    args = parser.parse_args()
    
    print("Finding consolidation candidates...")
    candidates = find_consolidation_candidates(args.dir)
    
    print("\nPotential functions to consolidate:")
    for function_name, files in candidates.items():
        print(f"\n{function_name} (found in {len(files)} files):")
        for file in files:
            print(f"  - {file}")
    
    print("\nIdentifying already consolidated functions...")
    consolidated = identify_consolidated_functions(args.dir)
    
    print("\nFiles using consolidated functions:")
    for file in consolidated:
        print(f"  - {file}")
    
    print("\nDone!")

if __name__ == "__main__":
    main()
