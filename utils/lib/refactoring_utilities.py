"""
Refactoring Utilities for CBS_PYTHON Codebase

This module provides utilities to help with code refactoring tasks
within the CBS_PYTHON codebase. It offers tools to identify code duplication,
track dependencies, and assist in safely moving code to new locations.
"""

import os
import sys
import re
import ast
import logging
from typing import List, Dict, Set, Tuple, Optional, Any
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)

def find_imports(file_path: str) -> Dict[str, List[str]]:
    """
    Find all imports in a Python file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Dictionary mapping import types to lists of imported modules
    """
    result = {
        'import': [],  # Direct imports (import x)
        'from': {}     # From imports (from x import y)
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            tree = ast.parse(file.read(), filename=file_path)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        result['import'].append(name.name)
                
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    if module not in result['from']:
                        result['from'][module] = []
                    
                    for name in node.names:
                        if name.name != '*':
                            result['from'][module].append(name.name)
                        else:
                            result['from'][module].append('*')
    
    except Exception as e:
        logger.error(f"Error analyzing imports in {file_path}: {str(e)}")
    
    return result

def find_function_calls(file_path: str) -> Dict[str, List[Tuple[int, str]]]:
    """
    Find all function calls in a Python file.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Dictionary mapping module names to lists of (line_number, function_name) tuples
    """
    result = defaultdict(list)
    
    class FunctionCallVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                module = node.func.value.id
                function = node.func.attr
                result[module].append((node.lineno, function))
            elif isinstance(node.func, ast.Name):
                result[''].append((node.lineno, node.func.id))
            
            self.generic_visit(node)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            tree = ast.parse(file.read(), filename=file_path)
            visitor = FunctionCallVisitor()
            visitor.visit(tree)
    
    except Exception as e:
        logger.error(f"Error analyzing function calls in {file_path}: {str(e)}")
    
    return dict(result)

def trace_function_usage(function_name: str, module_name: str, directory: str) -> List[Dict[str, Any]]:
    """
    Trace where a function is used throughout the codebase.
    
    Args:
        function_name: Name of the function to trace
        module_name: Name of the module containing the function
        directory: Directory to search in
        
    Returns:
        List of dictionaries with usage information
    """
    usages = []
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Check for imports of the module
                        imports = find_imports(file_path)
                        
                        # Check if the module is imported
                        module_imported = False
                        if module_name in imports['import']:
                            module_imported = True
                        elif module_name in imports['from'] and (function_name in imports['from'][module_name] or '*' in imports['from'][module_name]):
                            module_imported = True
                        
                        # If module is imported, check for function calls
                        if module_imported:
                            function_calls = find_function_calls(file_path)
                            
                            # Check for direct calls
                            if module_name in function_calls and any(func == function_name for _, func in function_calls[module_name]):
                                for line_num, func in function_calls[module_name]:
                                    if func == function_name:
                                        usages.append({
                                            'file': file_path,
                                            'line': line_num,
                                            'type': 'direct_call'
                                        })
                            
                            # Check for unqualified calls (if imported using from)
                            if module_name in imports['from'] and (function_name in imports['from'][module_name] or '*' in imports['from'][module_name]):
                                if '' in function_calls and any(func == function_name for _, func in function_calls['']):
                                    for line_num, func in function_calls['']:
                                        if func == function_name:
                                            usages.append({
                                                'file': file_path,
                                                'line': line_num,
                                                'type': 'unqualified_call'
                                            })
                
                except Exception as e:
                    logger.error(f"Error tracing function usage in {file_path}: {str(e)}")
    
    return usages

def update_import_paths(old_path: str, new_path: str, directory: str) -> List[str]:
    """
    Update import statements in Python files to reflect moved modules.
    
    Args:
        old_path: Old import path (e.g., 'utils.encryption')
        new_path: New import path (e.g., 'utils.common.encryption')
        directory: Directory to search in
        
    Returns:
        List of modified files
    """
    modified_files = []
    
    # Build regular expressions for finding imports
    import_pattern = re.compile(rf'import\s+{re.escape(old_path)}(?:\s+as\s+(\w+))?')
    from_pattern = re.compile(rf'from\s+{re.escape(old_path)}\s+import\s+(.*)')
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Replace direct imports
                    new_content = import_pattern.sub(lambda m: f"import {new_path}" + (f" as {m.group(1)}" if m.group(1) else ""), content)
                    
                    # Replace from imports
                    new_content = from_pattern.sub(f"from {new_path} import \\1", new_content)
                    
                    # Update the file if changes were made
                    if new_content != content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        modified_files.append(file_path)
                
                except Exception as e:
                    logger.error(f"Error updating imports in {file_path}: {str(e)}")
    
    return modified_files

def create_backwards_compatibility(old_path: str, new_path: str, file_path: str) -> bool:
    """
    Create a backwards compatibility module at the old location.
    
    Args:
        old_path: Old import path (e.g., 'utils.encryption')
        new_path: New import path (e.g., 'utils.common.encryption')
        file_path: Path where the backwards compatibility module should be created
        
    Returns:
        Boolean indicating success
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Create the backwards compatibility module
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"""# DEPRECATED: This module is deprecated and will be removed in a future release.
# Please update your imports to use {new_path} instead.

import warnings

warnings.warn(
    f"The module {old_path} is deprecated. "
    f"Please use {new_path} instead.",
    DeprecationWarning,
    stacklevel=2
)

from {new_path} import *
""")
        
        return True
    
    except Exception as e:
        logger.error(f"Error creating backwards compatibility module at {file_path}: {str(e)}")
        return False
