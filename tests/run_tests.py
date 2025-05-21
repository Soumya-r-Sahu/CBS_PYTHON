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
    
    cmd = ["pytest", "Tests/unit", "-v"]
    if args.coverage:
        cmd.extend(["--cov=app", "--cov=database", "--cov=utils", 
                   "--cov=digital_channels", "--cov=risk_compliance", "--cov=core_banking", 
                   "--cov=payments", "--cov-report=html"])
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
    result = subprocess.run(cmd)
    return result.returncode == 0

def run_integration_tests(args):
    """Run integration tests"""
    print_header("Running Integration Tests")
    
    cmd = ["pytest", "Tests/integration", "-v"]
    if args.coverage:
        cmd.extend(["--cov=integration", "--cov=app", "--cov=database", "--cov=utils", 
                   "--cov=digital_channels", "--cov=risk_compliance", "--cov=core_banking", 
                   "--cov=payments", "--cov-report=html"])
    
    if args.markers:
        cmd.extend(["-m", args.markers])
    
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
    
    cmd = ["pytest", "Tests/e2e", "-v"]
    if args.coverage:
        cmd.extend(["--cov=app", "--cov=database", "--cov=utils",
                   "--cov=digital_channels", "--cov=risk_compliance", "--cov=core_banking", 
                   "--cov=payments", "--cov-report=html"])
        
    if args.markers:
        cmd.extend(["-m", args.markers])
        
    result = subprocess.run(cmd)
    return result.returncode == 0

def run_all_tests(args):
    """Run all tests"""
    print_header("Running All Tests")
    
    # Run tests in order of complexity
    results = []
    results.append(run_unit_tests(args))
    results.append(run_integration_tests(args))
    results.append(run_e2e_tests(args))
    
    # Print results summary
    print_header("Test Results Summary")
    categories = ["Unit", "Integration", "E2E"]
    
    for i, category in enumerate(categories):
        status = "PASSED" if results[i] else "FAILED"
        print(f"{category} Tests: {status}")
    
    # Generate coverage report if requested
    if args.coverage:
        print("\nCoverage report generated in htmlcov/ directory")
        print("Open htmlcov/index.html in a browser to view the report")
    
    return all(results)

def generate_test_report(args, results, execution_time):
    """Generate a detailed test report"""
    import datetime
    import json
    import os
    
    report_file = args.report
    report_dir = os.path.dirname(report_file)
    
    if report_dir and not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    # Create report content
    report = {
        "timestamp": datetime.datetime.now().isoformat(),
        "execution_time": execution_time,
        "results": results,
        "overall_success": all(results.values()),
        "coverage_report": args.coverage,
        "test_categories": list(results.keys())
    }
    
    # Create HTML report
    if report_file.endswith('.html'):
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CBS_PYTHON Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .success {{ color: green; }}
                .failure {{ color: red; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
        </head>
        <body>
            <h1>CBS_PYTHON Test Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Timestamp: {report['timestamp']}</p>
                <p>Execution Time: {report['execution_time']:.2f} seconds</p>
                <p>Overall Result: <span class="{'success' if report['overall_success'] else 'failure'}">{
                    'PASSED' if report['overall_success'] else 'FAILED'}</span></p>
                <p>Coverage Report: {'Generated' if report['coverage_report'] else 'Not Generated'}</p>
            </div>
            
            <h2>Test Results</h2>
            <table>
                <tr>
                    <th>Category</th>
                    <th>Result</th>
                </tr>
        """
        
        for category, result in results.items():
            html_content += f"""
                <tr>
                    <td>{category.capitalize()} Tests</td>
                    <td class="{'success' if result else 'failure'}">{
                        'PASSED' if result else 'FAILED'}</td>
                </tr>
            """
        
        html_content += """
            </table>
            
            <h2>Test Categories</h2>
            <ul>
                <li><strong>Unit Tests</strong>: Test individual components in isolation.</li>
                <li><strong>Integration Tests</strong>: Test interactions between components.</li>
                <li><strong>End-to-End Tests</strong>: Simulate real-world workflows to test the system as a whole.</li>
            </ul>
        </body>
        </html>
        """
        
        with open(report_file, 'w') as f:
            f.write(html_content)
    
    # Create JSON report
    elif report_file.endswith('.json'):
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=4)
    
    # Create markdown report
    else:
        md_content = f"""# CBS_PYTHON Test Report

## Summary
- **Timestamp**: {report['timestamp']}
- **Execution Time**: {report['execution_time']:.2f} seconds
- **Overall Result**: {'PASSED' if report['overall_success'] else 'FAILED'}
- **Coverage Report**: {'Generated' if report['coverage_report'] else 'Not Generated'}

## Test Results

| Category | Result |
|----------|--------|
"""
        
        for category, result in results.items():
            md_content += f"| {category.capitalize()} Tests | {'PASSED' if result else 'FAILED'} |\n"
        
        md_content += """
## Test Categories
- **Unit Tests**: Test individual components in isolation.
- **Integration Tests**: Test interactions between components.
- **End-to-End Tests**: Simulate real-world workflows to test the system as a whole.
"""
        
        with open(report_file, 'w') as f:
            f.write(md_content)
    
    print(f"\nTest report generated: {report_file}")

def main():
    """Run tests based on command-line arguments"""
    parser = argparse.ArgumentParser(description="Run Core Banking System tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--skip-api-check", action="store_true", help="Skip API server availability check")
    parser.add_argument("--markers", help="Only run tests with specific pytest markers")
    parser.add_argument("--report", help="Save test results to specified report file")
    args = parser.parse_args()
    
    # If no specific test category is selected, run all tests
    if not (args.unit or args.integration or args.e2e):
        args.all = True
    
    start_time = time.time()
    success = True
    results = {}
    
    try:
        if args.unit:
            unit_success = run_unit_tests(args)
            success = unit_success and success
            results["unit"] = unit_success
        
        if args.integration:
            integration_success = run_integration_tests(args)
            success = integration_success and success
            results["integration"] = integration_success
        
        if args.e2e:
            e2e_success = run_e2e_tests(args)
            success = e2e_success and success
            results["e2e"] = e2e_success
        
        if args.all:
            all_success = run_all_tests(args)
            success = all_success
            results = {
                "unit": True if all_success else False,
                "integration": True if all_success else False,
                "e2e": True if all_success else False
            }
        
        # Generate final report if requested
        if args.report:
            generate_test_report(args, results, time.time() - start_time)
        
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        return 130
    
    # Print execution time
    execution_time = time.time() - start_time
    print(f"\nTotal execution time: {execution_time:.2f} seconds")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())