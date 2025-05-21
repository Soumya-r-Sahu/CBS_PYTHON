#!/usr/bin/env python
"""
Import Standardizer

This script helps standardize imports in a Python file by adding the
centralized import system (utils.lib.packages) and fixing common issues.

Usage:
    python standardize_imports.py <file_path>

Example:
    python standardize_imports.py path/to/your/file.py
"""

import sys
import re
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

def standardize_imports(file_path):
    """Standardize imports in a Python file."""
    print(f"{Fore.CYAN}Standardizing imports in {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"{Fore.RED}Error reading file: {e}")
        return False
    
    original_content = content
    modified = False
    
    # Check if file already has the centralized import system
    already_has_central_imports = re.search(r'from\s+utils\.lib\.packages\s+import', content)
    
    if not already_has_central_imports:
        # Find a good place to add the import - after other imports but before code
        import_section_end = 0
        
        # Find all import statements
        import_lines = re.findall(r'^import.*?$|^from.*?import.*?$', content, re.MULTILINE)
        if import_lines:
            last_import = import_lines[-1]
            import_section_end = content.find(last_import) + len(last_import)
        
        central_import = '\n\n# Use centralized import system\nfrom utils.lib.packages import fix_path\nfix_path()  # Ensures project root is in sys.path\n'
        
        if import_section_end > 0:
            content = content[:import_section_end] + central_import + content[import_section_end:]
        else:
            # If no imports found, add after any docstring or initial comments
            match = re.search(r'""".*?"""', content, re.DOTALL)
            if match:
                docstring_end = match.end()
                content = content[:docstring_end] + '\n' + central_import + content[docstring_end:]
            else:
                # Add after any initial comments
                if content.startswith('#'):
                    # Find first non-comment line
                    non_comment = re.search(r'^[^#]', content, re.MULTILINE)
                    if non_comment:
                        pos = non_comment.start()
                        content = content[:pos] + central_import + content[pos:]
                    else:
                        content = content + central_import
                else:
                    content = central_import + content
        
        print(f"{Fore.GREEN}✅ Added centralized import system")
        modified = True
    
    # Fix 1: Remove manual path manipulation
    path_manipulation_pattern = r'sys\.path\.(?:append|insert)\(.*?(?:__file__|os\.path).*?\).*?\n'
    if re.search(path_manipulation_pattern, content):
        content = re.sub(path_manipulation_pattern, '', content)
        print(f"{Fore.GREEN}✅ Removed manual path manipulation")
        modified = True
    
    # Fix 2: Remove duplicate DatabaseConnection fallbacks
    fallback_pattern = r'try:[\s\n]+from database\.python\.connection import DatabaseConnection[\s\n]+except ImportError:[\s\n]+# Fallback implementation[\s\n]+class DatabaseConnection:[\s\n]+.*?pass'
    if re.search(fallback_pattern, content, re.DOTALL):
        content = re.sub(fallback_pattern, 'from database.python.common.database_operations import DatabaseConnection', content, flags=re.DOTALL)
        print(f"{Fore.GREEN}✅ Removed duplicate DatabaseConnection fallback")
        modified = True
    
    # Fix 3: Update deprecated imports
    if re.search(r'from\s+app\.lib\.(import_manager|setup_imports)', content):
        content = re.sub(
            r'from\s+app\.lib\.(import_manager|setup_imports)\s+import.*?\n', 
            '# Centralized import system already included at the top of the file\n',
            content,
            flags=re.MULTILINE
        )
        print(f"{Fore.GREEN}✅ Removed deprecated app.lib imports")
        modified = True
    
    if re.search(r'from\s+utils\.lib\.setup_imports', content):
        content = re.sub(
            r'from\s+utils\.lib\.setup_imports\s+import.*?\n', 
            '# Centralized import system already included at the top of the file\n',
            content,
            flags=re.MULTILINE
        )
        print(f"{Fore.GREEN}✅ Removed deprecated utils.lib.setup_imports")
        modified = True
    
    # Write the updated content back to the file
    if modified:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"{Fore.GREEN}✅ Successfully updated {file_path}")
            return True
        except Exception as e:
            print(f"{Fore.RED}Error writing file: {e}")
            return False
    else:
        print(f"{Fore.YELLOW}No changes needed in {file_path}")
        return True

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not Path(file_path).exists():
        print(f"{Fore.RED}Error: File {file_path} does not exist.")
        sys.exit(1)
    
    if not file_path.endswith('.py'):
        print(f"{Fore.YELLOW}Warning: {file_path} does not have a .py extension. Continue anyway? (y/n)")
        choice = input().strip().lower()
        if choice != 'y':
            sys.exit(0)
    
    if standardize_imports(file_path):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
