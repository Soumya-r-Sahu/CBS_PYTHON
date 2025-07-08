#!/usr/bin/env python
"""
GitHub Preparation Script for CBS_PYTHON

This script performs final checks and preparations before pushing to GitHub.
It checks for syntax errors, validates version consistency, and runs tests.
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Get the project root
project_root = Path(__file__).resolve().parent.parent.parent

def run_command(command, exit_on_error=True):
    """Run a shell command and return the output."""
    print(f"{Fore.CYAN}Running: {command}")
    
    try:
        # Use subprocess.run with shell=False for better security and path handling
        if sys.platform == 'win32':
            # Windows needs special handling
            result = subprocess.run(
                command,
                shell=True,  # Use shell on Windows to handle quotes properly
                check=True,
                text=True,
                capture_output=True
            )
        else:
            # Unix systems
            args = command.split()
            result = subprocess.run(
                args,
                shell=False,
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

def check_version_consistency():
    """Check that the version is consistent across all files."""
    print(f"{Fore.CYAN}Checking version consistency...")
    
    version = "1.1.1"
    files_to_check = {
        "README.md": r"Version (\d+\.\d+\.\d+)",
        "setup.py": r'version="(\d+\.\d+\.\d+)"',
        "pyproject.toml": r'version = "(\d+\.\d+\.\d+)"',
        "CHANGELOG.md": r"## \[(\d+\.\d+\.\d+)\]"
    }
    
    inconsistent_files = []
    
    for file_name, pattern in files_to_check.items():
        file_path = project_root / file_name
        
        if not file_path.exists():
            print(f"{Fore.YELLOW}Warning: {file_name} not found at expected path: {file_path}")
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            matches = re.findall(pattern, content)
            if not matches:
                print(f"{Fore.YELLOW}Warning: Could not find version in {file_name}")
                inconsistent_files.append(file_name)
            elif matches[0] != version:
                print(f"{Fore.RED}Error: Version mismatch in {file_name}. Found {matches[0]}, expected {version}")
                inconsistent_files.append(file_name)
            else:
                print(f"{Fore.GREEN}Version check passed for {file_name}: {version}")
        except Exception as e:
            print(f"{Fore.RED}Error reading {file_name}: {str(e)}")
            inconsistent_files.append(file_name)
    
    if inconsistent_files:
        print(f"{Fore.RED}Version inconsistency found in: {', '.join(inconsistent_files)}")
        return False
    
    print(f"{Fore.GREEN}Version is consistent in all available files: {version}")
    return True

def run_syntax_check():
    """Run syntax check on all Python files."""
    print(f"{Fore.CYAN}Running syntax check...")
    syntax_checker = project_root / "scripts" / "utilities" / "check_syntax_errors.py"
    
    if not syntax_checker.exists():
        print(f"{Fore.YELLOW}Warning: Syntax checker script not found")
        return False
    
    # Use proper quoting for paths with spaces
    syntax_checker_str = str(syntax_checker).replace('\\', '\\\\')
    success, _ = run_command(f'python "{syntax_checker_str}"', exit_on_error=False)
    return success

def run_tests():
    """Run tests."""
    print(f"{Fore.CYAN}Running tests...")
    
    # Get the absolute path to the project root
    root_dir = str(project_root)
    print(f"Project root: {root_dir}")
    
    # Create a pythonpath environment that includes the project root
    env = os.environ.copy()
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{root_dir}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = root_dir
    
    # Try to run tests with the properly set environment
    try:
        # Use subprocess.Popen to run tests
        process = subprocess.Popen(
            ["python", "-m", "pytest", "Tests", "-v"],
            cwd=root_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=(sys.platform == 'win32')  # Use shell on Windows
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"{Fore.RED}Tests failed with return code {process.returncode}")
            if stdout:
                print(stdout)
            if stderr:
                print(stderr)
            return False
        
        print(f"{Fore.GREEN}Tests passed successfully")
        print(stdout)
        return True
    except Exception as e:
        print(f"{Fore.RED}Error running tests: {str(e)}")
        return False

def main():
    """Main function."""
    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}{' ' * 25}CBS_PYTHON GitHub Preparation{' ' * 25}")
    print(f"{Fore.CYAN}{'=' * 80}")
    
    # Check version consistency
    version_consistent = check_version_consistency()
    
    # Run syntax check
    syntax_valid = run_syntax_check()
    
    # Run tests
    tests_pass = run_tests()
      # Print summary
    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}{' ' * 30}Summary{' ' * 30}")
    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"{'[OK]' if version_consistent else '[FAIL]'} Version Consistency: {Fore.GREEN if version_consistent else Fore.RED}{version_consistent}")
    print(f"{'[OK]' if syntax_valid else '[FAIL]'} Syntax Check: {Fore.GREEN if syntax_valid else Fore.RED}{syntax_valid}")
    print(f"{'[OK]' if tests_pass else '[FAIL]'} Tests: {Fore.GREEN if tests_pass else Fore.RED}{tests_pass}")
    
    if version_consistent and syntax_valid and tests_pass:
        print(f"\n{Fore.GREEN}All checks passed! Ready to push to GitHub.")
        print(f"{Fore.GREEN}Suggested commands:")
        print(f"{Fore.GREEN}  git add .")
        print(f"{Fore.GREEN}  git commit -m \"Release v1.1.1: Code cleanup, syntax fixes, and documentation updates\"")
        print(f"{Fore.GREEN}  git tag -a v1.1.1 -m \"Version 1.1.1\"")
        print(f"{Fore.GREEN}  git push origin main")
        print(f"{Fore.GREEN}  git push origin v1.1.1")
    else:
        print(f"\n{Fore.RED}Some checks failed. Please fix the issues before pushing to GitHub.")
        sys.exit(1)

if __name__ == "__main__":
    main()
