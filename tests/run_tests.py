#!/usr/bin/env python
"""
Core Banking System - Master Test Runner

This script runs all tests for the Core Banking System.
Tests can be run by category or all at once.
"""

import sys
import os
import subprocess
import argparse
import time
import pytest

# Add parent directory to path

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


def print_header(text):
    """Print a formatted header"""
    width = 80
    print("\n" + "=" * width)
    print(f"{text.center(width)}")
    print("=" * width + "\n")

def run_unit_tests(args):
    """Run unit tests"""
    print_header("Running Unit Tests")
    
    cmd = ["pytest", "tests/unit", "-v"]
    if args.coverage:
        cmd.extend(["--cov=app", "--cov=database", "--cov=upi", "--cov=utils", 
                   "--cov=digital_channels", "--cov=risk_compliance", "--cov=loan_management", 
                   "--cov=payment_processors", "--cov-report=html"])
    
    result = subprocess.run(cmd)
    return result.returncode == 0

def run_integration_tests(args):
    """Run integration tests"""
    print_header("Running Integration Tests")
    
    cmd = ["pytest", "tests/integration", "-v"]
    if args.coverage:
        cmd.extend(["--cov=integration", "--cov=app", "--cov=database", "--cov=upi", 
                   "--cov=digital_channels", "--cov=risk_compliance", "--cov=loan_management", 
                   "--cov=payment_processors", "--cov-report=html"])
    
    result = subprocess.run(cmd)
    return result.returncode == 0

def run_api_tests(args):
    """Run API tests"""
    print_header("Running API Tests")

    cmd = ["pytest", "tests/api_tests", "-v"]
    if args.coverage:
        cmd.extend(["--cov=app/api", "--cov-report=html"])

    result = subprocess.run(cmd)
    return result.returncode == 0

def run_e2e_tests(args):
    """Run end-to-end tests"""
    print_header("Running E2E Tests")
    
    # Check if API server is running
    api_running = False
    try:
        import requests
        response = requests.get("http://localhost:5000/api/v1/health")
        api_running = response.status_code == 200
    except:
        api_running = False
    
    if not api_running and not args.skip_api_check:
        print("API server is not running. Start it with 'python run_api.py' in a separate terminal.")
        print("Or run with --skip-api-check to ignore this warning.")
        return False
    
    cmd = ["pytest", "tests/e2e", "-v"]
    if args.coverage:
        cmd.extend(["--cov=app", "--cov=database", "--cov=upi", "--cov=utils",
                   "--cov=digital_channels", "--cov=risk_compliance", "--cov=loan_management", 
                   "--cov=payment_processors", "--cov-report=html"])
        
    result = subprocess.run(cmd)
    return result.returncode == 0

def run_all_tests(args):
    """Run all tests"""
    print_header("Running All Tests")
    
    # Run tests in order of complexity
    results = []
    results.append(run_unit_tests(args))
    results.append(run_integration_tests(args))
    results.append(run_api_tests(args))
    results.append(run_e2e_tests(args))
    
    # Print results summary
    print_header("Test Results Summary")
    categories = ["Unit", "Integration", "API", "E2E"]
    
    for i, category in enumerate(categories):
        status = "PASSED" if results[i] else "FAILED"
        print(f"{category} Tests: {status}")
    
    return all(results)

def main():
    """Run tests based on command-line arguments"""
    parser = argparse.ArgumentParser(description="Run Core Banking System tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--api", action="store_true", help="Run API tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--skip-api-check", action="store_true", help="Skip API server availability check")
    args = parser.parse_args()
    
    # If no specific test category is selected, run all tests
    if not (args.unit or args.integration or args.api or args.e2e):
        args.all = True
    
    success = True
    
    try:
        if args.unit:
            success = run_unit_tests(args) and success
        
        if args.integration:
            success = run_integration_tests(args) and success

        if args.api:
            success = run_api_tests(args) and success
        
        if args.e2e:
            success = run_e2e_tests(args) and success
        
        if args.all:
            success = run_all_tests(args)
        
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        return 130
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())