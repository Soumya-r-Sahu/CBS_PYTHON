#!/usr/bin/env python
# filepath: d:\vs code\github\CBS-python\scripts\troubleshoot.py
"""
Troubleshooting Helper for Core Banking System

This script helps diagnose common issues with the Core Banking System setup.
It checks for required dependencies, database connectivity, and configuration issues.
"""

import os
import sys
import platform
import subprocess
import importlib.util
from pathlib import Path
import importlib
import platform

# Add parent directory to path

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment, get_database_connection
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
    print("=" * width)

def print_section(text):
    """Print a section header"""
    print(f"\n=== {text} ===")

def check_dependency(module_name, import_name=None, min_version=None):
    """Check if a Python module is installed and meets the minimum version"""
    if import_name is None:
        import_name = module_name
    
    try:
        module = importlib.import_module(import_name)
        if hasattr(module, '__version__'):
            version = module.__version__
        elif hasattr(module, 'version'):
            version = module.version
        else:
            version = "Unknown"
            
        result = "✓"
        
        if min_version and version != "Unknown":
            if version < min_version:
                result = f"! (v{version}, needs v{min_version}+)"
            else:
                result = f"✓ (v{version})"
    except ImportError:
        result = "✗"
        version = "Not installed"
        
    return (module_name, result, version)

def check_database_connection():
    """Check database connection using project settings"""
    print_section("Database Connection Check")
    
    # Try to import database configuration
    try:
        from utils.config import DATABASE_CONFIG
        
        # Display database configuration (but hide password)
        db_config = DATABASE_CONFIG.copy()
        if 'password' in db_config:
            db_config['password'] = '****' if db_config['password'] else '(empty)'
            
        print("Database configuration:")
        for key, value in db_config.items():
            print(f"  {key}: {value}")
            
        # Try to connect to the database
        try:
            import mysql.connector
            
            print("\nAttempting to connect to MySQL database...")
            conn = mysql.connector.connect(
                host=DATABASE_CONFIG.get('host', 'localhost'),
                user=DATABASE_CONFIG.get('user', 'root'),
                password=DATABASE_CONFIG.get('password', ''),
                port=DATABASE_CONFIG.get('port', 3306)
            )
            
            if conn.is_connected():
                print("✓ Successfully connected to MySQL server")
                
                # Check if database exists
                db_name = DATABASE_CONFIG.get('database', 'core_banking_system')
                cursor = conn.cursor()
                cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
                result = cursor.fetchone()
                
                if result:
                    print(f"✓ Database '{db_name}' exists")
                    
                    # Try to use the database and check for tables
                    conn.database = db_name
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()
                    
                    if tables:
                        print(f"✓ Found {len(tables)} tables in the database")
                        print("  Tables found: " + ", ".join([t[0] for t in tables][:5]) + 
                              (f" and {len(tables) - 5} more..." if len(tables) > 5 else ""))
                    else:
                        print(f"! No tables found in database '{db_name}'")
                        print("  Run: python main.py --init-db to initialize the database")
                else:
                    print(f"! Database '{db_name}' does not exist")
                    print("  Run: python main.py --init-db to create and initialize the database")
                
                cursor.close()
                conn.close()
            else:
                print("! Failed to connect to MySQL server")
                
        except ImportError:
            print("✗ MySQL connector package is not installed")
            print("  Run: pip install mysql-connector-python")
            
        except Exception as e:
            print(f"✗ Database connection error: {e}")
            print("  Check that MySQL server is running and your credentials are correct")
            print("  Update connection details in utils/config.py if needed")
            
    except ImportError:
        print("✗ Failed to import database configuration")
        print("  Check that utils/config.py exists and contains DATABASE_CONFIG dictionary")

def check_system_info():
    """Check system information"""
    print_section("System Information")
    
    print(f"Python version: {sys.version}")
    print(f"Operating system: {platform.platform()}")
    print(f"System architecture: {platform.architecture()[0]}")
    
    # Check if running in a virtual environment
    in_venv = (hasattr(sys, 'real_prefix') or 
              (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
    print(f"Virtual environment: {'✓ Active' if in_venv else '✗ Not active (recommended)'}")

def check_dependencies():
    """Check for project dependencies"""
    print_section("Dependency Check")
    
    dependencies = [
        # Core dependencies
        ("cryptography", None, "41.0.0"),
        ("sqlalchemy", None, "2.0.0"),
        ("mysql-connector-python", None, "8.0.0"),
        ("pydantic", None, "2.0.0"),
        
        # Web frameworks
        ("fastapi", None, "0.100.0"),
        ("flask", None, "2.3.0"),
        
        # Utilities
        ("PyYAML", "yaml", "6.0"),
        ("python-dotenv", "dotenv", "1.0.0"),
        ("requests", None, "2.30.0"),
    ]
    
    results = []
    for dep_name, import_name, min_version in dependencies:
        results.append(check_dependency(dep_name, import_name, min_version))
    
    # Calculate column widths
    name_width = max(len(r[0]) for r in results) + 2
    result_width = 10
    version_width = 15
    
    # Print header
    print(f"{'Module'.ljust(name_width)} {'Status'.ljust(result_width)} {'Version'.ljust(version_width)}")
    print(f"{'-' * name_width} {'-' * result_width} {'-' * version_width}")
    
    # Print results
    missing_deps = []
    for name, result, version in results:
        print(f"{name.ljust(name_width)} {result.ljust(result_width)} {version}")
        if result == "✗":
            missing_deps.append(name)
    
    # Print summary and recommendations
    if missing_deps:
        print("\nMissing dependencies:")
        print("pip install " + " ".join(missing_deps))

def check_project_structure():
    """Check for required project files and directories"""
    print_section("Project Structure Check")
    
    required_files = [
        "main.py",
        "requirements.txt",
        "utils/config.py",
        "database/connection.py",
        "database/setup_database.sql",
    ]
    
    required_dirs = [
        "app",
        "database",
        "admin_panel",
        "gui",
        "upi",
        "utils",
        "tests",
    ]
    
    missing_files = []
    missing_dirs = []
    
    # Get base directory
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    
    # Check required files
    for file_path in required_files:
        full_path = os.path.join(base_dir, file_path)
        if not os.path.isfile(full_path):
            missing_files.append(file_path)
    
    # Check required directories
    for dir_path in required_dirs:
        full_path = os.path.join(base_dir, dir_path)
        if not os.path.isdir(full_path):
            missing_dirs.append(dir_path)
    
    if not missing_files and not missing_dirs:
        print("✓ All required files and directories are present")
    else:
        if missing_files:
            print("Missing files:")
            for file_path in missing_files:
                print(f"  ✗ {file_path}")
        if missing_dirs:
            print("Missing directories:")
            for dir_path in missing_dirs:
                print(f"  ✗ {dir_path}")

def main():
    """Main function"""
    print_header("Core Banking System Troubleshooting Helper")
    
    check_system_info()
    check_dependencies()
    check_project_structure()
    check_database_connection()
    
    print_header("Troubleshooting Complete")
    print("For more help, please refer to the following resources:")
    print("1. README.md - General project documentation")
    print("2. database/TROUBLESHOOTING.md - Database-specific troubleshooting")
    print("3. GitHub Issues - https://github.com/your-username/CBS-python/issues")

if __name__ == "__main__":
    main()