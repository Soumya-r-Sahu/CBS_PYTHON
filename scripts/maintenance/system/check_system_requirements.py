#!/usr/bin/env python
"""
System Requirements Checker for CBS_PYTHON

This script checks if your system meets the minimum requirements
specified in the README.md for development purposes.
"""

import os
import platform
import sys
import subprocess
import shutil
import psutil
import importlib
import urllib.request
from pathlib import Path

# Minimum requirements for development
MIN_PYTHON_VERSION = (3, 8)
MIN_RAM_GB = 4
MIN_DISK_SPACE_GB = 10

# Required packages (core ones that must be checked separately)
REQUIRED_PACKAGES = [
    "numpy", "pandas", "sqlalchemy", "pyyaml", "cryptography",
    "PyQt5", "tensorflow", "psycopg2"
]

def print_header(message):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80)

def print_status(component, status, details=None):
    """Print a status check result."""
    status_symbol = "✅" if status else "❌"
    print(f"{status_symbol} {component:<30} {'PASS' if status else 'FAIL'}")
    if details:
        print(f"   ↳ {details}")

def check_python_version():
    """Check if Python version meets minimum requirements."""
    current_version = sys.version_info
    meets_requirement = current_version >= MIN_PYTHON_VERSION
    version_str = f"{current_version.major}.{current_version.minor}.{current_version.micro}"
    
    print_status(
        "Python Version", 
        meets_requirement,
        f"Current: {version_str}, Required: {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+"
    )
    return meets_requirement

def check_ram():
    """Check if system RAM meets minimum requirements."""
    try:
        ram_bytes = psutil.virtual_memory().total
        ram_gb = ram_bytes / (1024**3)  # Convert to GB
        meets_requirement = ram_gb >= MIN_RAM_GB
        
        print_status(
            "RAM", 
            meets_requirement,
            f"Current: {ram_gb:.1f} GB, Required: {MIN_RAM_GB}+ GB"
        )
        return meets_requirement
    except Exception as e:
        print_status("RAM", False, f"Could not check RAM: {e}")
        return False

def check_disk_space():
    """Check if free disk space meets minimum requirements."""
    try:
        path = Path.cwd().anchor  # Root drive
        free_bytes = shutil.disk_usage(path).free
        free_gb = free_bytes / (1024**3)  # Convert to GB
        meets_requirement = free_gb >= MIN_DISK_SPACE_GB
        
        print_status(
            "Disk Space", 
            meets_requirement,
            f"Free space: {free_gb:.1f} GB, Required: {MIN_DISK_SPACE_GB}+ GB"
        )
        return meets_requirement
    except Exception as e:
        print_status("Disk Space", False, f"Could not check disk space: {e}")
        return False

def check_package(package_name):
    """Check if a Python package is installed."""
    try:
        importlib.import_module(package_name)
        print_status(f"Package: {package_name}", True, "Installed")
        return True
    except ImportError:
        print_status(f"Package: {package_name}", False, "Not installed")
        return False

def check_postgresql():
    """Check if PostgreSQL is available."""
    # First try to import the psycopg2 package
    psycopg2_installed = check_package("psycopg2")
    
    # Try to detect PostgreSQL executable
    pg_exe = None
    if platform.system() == "Windows":
        locations = [
            r"C:\Program Files\PostgreSQL\14\bin\psql.exe",
            r"C:\Program Files\PostgreSQL\13\bin\psql.exe",
            r"C:\Program Files\PostgreSQL\12\bin\psql.exe"
        ]
        for loc in locations:
            if os.path.exists(loc):
                pg_exe = loc
                break
    else:
        pg_exe = shutil.which("psql")

    if pg_exe:
        print_status("PostgreSQL", True, f"Found at: {pg_exe}")
        return True
    
    print_status("PostgreSQL", False, "Not found or not in PATH")
    return False

def install_packages():
    """Install required Python packages."""
    print_header("Installing required Python packages")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✅ Successfully installed Python packages")
    except subprocess.CalledProcessError:
        print("❌ Failed to install required packages")

def install_postgresql_instructions():
    """Provide instructions for installing PostgreSQL."""
    print_header("PostgreSQL Installation Instructions")
    
    if platform.system() == "Windows":
        print("""
To install PostgreSQL on Windows:
1. Download the installer from https://www.postgresql.org/download/windows/
2. Run the installer and follow the instructions
3. Add PostgreSQL bin directory to your PATH environment variable
4. Restart your terminal
""")
    elif platform.system() == "Darwin":  # macOS
        print("""
To install PostgreSQL on macOS:
1. Using Homebrew: brew install postgresql
2. Start PostgreSQL: brew services start postgresql
""")
    else:  # Linux
        print("""
To install PostgreSQL on Linux (Ubuntu/Debian):
1. sudo apt update
2. sudo apt install postgresql postgresql-contrib
3. sudo systemctl enable postgresql
4. sudo systemctl start postgresql

For other Linux distributions, please refer to the PostgreSQL documentation.
""")

def main():
    """Main function to check system requirements."""
    print_header("CBS_PYTHON System Requirements Check")
    
    # Check basic system requirements
    python_ok = check_python_version()
    ram_ok = check_ram()
    disk_ok = check_disk_space()
    
    # Check database requirements
    postgres_ok = check_postgresql()
    
    # Check required packages
    print_header("Checking Required Packages")
    package_failures = 0
    for pkg in REQUIRED_PACKAGES:
        if not check_package(pkg):
            package_failures += 1
    
    # Summary
    print_header("Summary")
    
    all_requirements_met = (python_ok and ram_ok and disk_ok and 
                           postgres_ok and package_failures == 0)
    
    if all_requirements_met:
        print("✅ Your system meets all the minimum requirements for development!")
    else:
        print("❌ Your system does not meet all the requirements.")
        
        # Offer to install missing components
        if not postgres_ok:
            print("\nPostgreSQL is required for optimal development experience.")
            install_postgresql_instructions()
        
        if package_failures > 0:
            try:
                answer = input("\nDo you want to install missing Python packages? (y/n): ").lower()
                if answer == 'y' or answer == 'yes':
                    install_packages()
            except KeyboardInterrupt:
                print("\nInstallation cancelled.")
    
    return 0 if all_requirements_met else 1

if __name__ == "__main__":
    sys.exit(main())
