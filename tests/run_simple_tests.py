"""
Test execution script for CBS_PYTHON tests.

This script bypasses the run_tests.py module and directly runs pytest.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def print_header(text):
    """Print a formatted header"""
    width = 80
    print("\n" + "=" * width)
    print(f"{text.center(width)}")
    print("=" * width + "\n")

def main():
    """Run tests based on command-line arguments"""
    parser = argparse.ArgumentParser(description="Run Core Banking System tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    args = parser.parse_args()
    
    # If no specific test category is selected, run all tests
    if not (args.unit or args.integration or args.e2e):
        args.all = True
    
    # Base directory
    base_dir = Path(__file__).resolve().parent.parent
    tests_dir = base_dir / "Tests"
    
    # Configure test commands
    if args.unit or args.all:
        print_header("Running Unit Tests")
        subprocess.run(["pytest", str(tests_dir / "unit" / "test_placeholder.py"), "-v"])
    
    if args.integration or args.all:
        print_header("Running Integration Tests")
        subprocess.run(["pytest", str(tests_dir / "integration" / "test_placeholder.py"), "-v"])
    
    if args.e2e or args.all:
        print_header("Running E2E Tests")
        subprocess.run(["pytest", str(tests_dir / "e2e" / "test_placeholder.py"), "-v"])
    
    print_header("Test Execution Complete")

if __name__ == "__main__":
    main()
