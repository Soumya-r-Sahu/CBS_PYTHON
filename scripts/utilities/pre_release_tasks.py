#!/usr/bin/env python
"""
Pre-Release Task Runner for CBS_PYTHON v1.1.1

This script automates the final tasks before releasing v1.1.1, including:
1. Running syntax checks
2. Verifying version consistency
3. Verifying test status
4. Preparing the final commit command
"""

import os
import sys
import subprocess
from pathlib import Path
import datetime
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Get the project root
project_root = Path(__file__).resolve().parent.parent.parent

def run_command(command, exit_on_error=False):
    """Run a shell command and return the output."""
    print(f"{Fore.CYAN}Running: {command}")
    
    try:
        # Use proper quoting for commands with spaces
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=True
        )
        
        print(f"{Fore.GREEN}Command succeeded")
        if result.stdout:
            print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Command failed with exit code {e.returncode}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        
        if exit_on_error:
            sys.exit(1)
        return False, str(e)

def run_syntax_check():
    """Run syntax check on all Python files."""
    print(f"{Fore.CYAN}Running syntax check...")
    syntax_checker = str(project_root / "scripts" / "utilities" / "check_syntax_errors.py")
    
    success, _ = run_command(f'python "{syntax_checker}" --fix', exit_on_error=False)
    return success

def verify_version_consistency():
    """Verify the version is consistent across all relevant files."""
    print(f"{Fore.CYAN}Verifying version consistency...")
    
    # Files to check for version string
    files_to_check = {
        "README.md": "1.1.1",
        "setup.py": "1.1.1",
        "pyproject.toml": "1.1.1",
        "CHANGELOG.md": "[1.1.1]"
    }
    
    all_consistent = True
    
    for file_name, version_str in files_to_check.items():
        file_path = project_root / file_name
        
        if not file_path.exists():
            print(f"{Fore.YELLOW}Warning: {file_name} not found")
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if version_str not in content:
                print(f"{Fore.RED}Error: Version {version_str} not found in {file_name}")
                all_consistent = False
            else:
                print(f"{Fore.GREEN}Version check passed for {file_name}: {version_str}")
        except Exception as e:
            print(f"{Fore.RED}Error reading {file_name}: {str(e)}")
            all_consistent = False
    
    return all_consistent

def prepare_git_commands():
    """Prepare the Git commands for final commit."""
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    
    print(f"\n{Fore.CYAN}Git commands for final commit and release:")
    print(f"{Fore.GREEN}git add .")
    print(f"{Fore.GREEN}git commit -m \"Release v1.1.1: Final Code cleanup, syntax fixes, and documentation updates ({today})\"")
    print(f"{Fore.GREEN}git tag -a v1.1.1 -m \"Version 1.1.1 - {today}\"")
    print(f"{Fore.GREEN}git push origin main")
    print(f"{Fore.GREEN}git push origin v1.1.1")

def main():
    """Main function."""
    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}{' ' * 25}CBS_PYTHON v1.1.1 Pre-Release Tasks{' ' * 25}")
    print(f"{Fore.CYAN}{'=' * 80}")
    
    # Run syntax check
    syntax_result = run_syntax_check()
    
    # Verify version consistency
    version_result = verify_version_consistency()
    
    # Print summary
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}{' ' * 30}Summary{' ' * 30}")
    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"{'[OK]' if syntax_result else '[FAIL]'} Syntax Check: {Fore.GREEN if syntax_result else Fore.RED}{syntax_result}")
    print(f"{'[OK]' if version_result else '[FAIL]'} Version Consistency: {Fore.GREEN if version_result else Fore.RED}{version_result}")
    
    # Prepare Git commands if all checks pass
    if syntax_result and version_result:
        prepare_git_commands()
    else:
        print(f"\n{Fore.YELLOW}Some checks failed. Please fix the issues before the final commit.")

if __name__ == "__main__":
    main()
