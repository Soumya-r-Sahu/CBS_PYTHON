#!/usr/bin/env python
"""
CBS_PYTHON Codebase Sanitizer

This script runs all the sanitization scripts to maintain a clean codebase.
It checks and fixes requirements files and import statements.

Usage:
    python sanitize_codebase.py [directory]

If no directory is specified, the script processes the current directory.
"""

import os
import sys
import subprocess
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

def run_script(script_name, *args):
    """Run a Python script with given arguments."""
    script_path = os.path.join('scripts', script_name)
    
    # Ensure the script exists
    if not os.path.exists(script_path):
        print(f"{Fore.RED}Error: Script {script_path} not found.")
        return False
    
    print(f"{Fore.CYAN}Running {script_name}...")
    
    try:
        # Construct the command
        cmd = [sys.executable, script_path]
        cmd.extend(args)
        
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print(f"{Fore.RED}{result.stderr}")
        
        # Return success based on exit code
        return result.returncode == 0
    
    except Exception as e:
        print(f"{Fore.RED}Error running {script_name}: {e}")
        return False

def sanitize_codebase(directory):
    """Run all sanitization scripts on the directory."""
    print(f"{Fore.GREEN}=== CBS_PYTHON Codebase Sanitizer ===")
    print(f"{Fore.CYAN}Target directory: {directory}")
    
    # Step 1: Check requirements files
    print(f"\n{Fore.GREEN}=== Step 1: Checking requirements files ===")
    success = run_script('check_requirements_files.py', directory)
    if not success:
        print(f"{Fore.YELLOW}⚠️ Requirements file check found issues.")
    
    # Step 2: Check for import issues
    print(f"\n{Fore.GREEN}=== Step 2: Checking for import issues ===")
    run_script('import_checker.py', directory)
    
    # Prompt to fix import issues
    fix_imports = input(f"{Fore.YELLOW}Do you want to fix import issues? (y/n): ").strip().lower()
    if fix_imports == 'y':
        print(f"\n{Fore.GREEN}=== Step 3: Fixing import issues ===")
        run_script('fix_all_imports.py', directory)
        run_script('fix_init_files.py', directory)
    
    # All done
    print(f"\n{Fore.GREEN}=== Sanitization Complete ===")
    print(f"{Fore.CYAN}For manual fixes or additional tools:")
    print(f"{Fore.WHITE}- Use scripts/standardize_imports.py for individual files")
    print(f"{Fore.WHITE}- Use scripts/manage_requirements.py to manage dependencies")
    print(f"{Fore.WHITE}- Check documentation/technical_standards/ for best practices")

def main():
    """Main function."""
    # Get directory from command line or use current directory
    directory = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    # Make sure the path is absolute
    directory = os.path.abspath(directory)
    
    sanitize_codebase(directory)

if __name__ == "__main__":
    main()
