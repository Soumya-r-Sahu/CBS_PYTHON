"""
CBS_PYTHON Integration Utility

This script helps integrate various components of the CBS_PYTHON system.
It can be used to:
1. Install missing dependencies
2. Set up the admin portal
3. Initialize the database
4. Generate test data
5. Configure system settings
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path

# Add project root to path for easier imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def install_dependencies():
    """Install required dependencies"""
    print("Installing required dependencies...")
    
    # Install base requirements
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Check for optional dependencies
    try:
        # Try to import optional dependencies
        import psutil
        print("✓ psutil already installed")
    except ImportError:
        print("Installing psutil...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil"])
    
    try:
        import cryptography
        print("✓ cryptography already installed")
    except ImportError:
        print("Installing cryptography...")
        subprocess.run([sys.executable, "-m", "pip", "install", "cryptography"])
    
    try:
        import schedule
        print("✓ schedule already installed")
    except ImportError:
        print("Installing schedule...")
        subprocess.run([sys.executable, "-m", "pip", "install", "schedule"])
    
    print("All dependencies installed successfully!")

def setup_admin_portal():
    """Set up the Django-based Admin Portal"""
    print("Setting up Admin Portal...")
    
    # Check if Django is installed
    try:
        import django
        print(f"✓ Django {django.get_version()} already installed")
    except ImportError:
        print("Installing Django...")
        subprocess.run([sys.executable, "-m", "pip", "install", "django"])
    
    # Check if admin portal requirements.txt exists
    admin_req_path = os.path.join(project_root, "app", "Portals", "Admin", "requirements.txt")
    if os.path.exists(admin_req_path):
        print("Installing Admin Portal dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", admin_req_path])
    
    # Check if we need to initialize the database
    admin_dir = os.path.join(project_root, "app", "Portals", "Admin")
    if os.path.exists(os.path.join(admin_dir, "manage.py")):
        print("Initializing Admin Portal database...")
        subprocess.run([sys.executable, "manage.py", "makemigrations"], cwd=admin_dir)
        subprocess.run([sys.executable, "manage.py", "migrate"], cwd=admin_dir)
        
        # Check if we need to create a superuser
        create_superuser = input("Do you want to create a superuser for the Admin Portal? (y/n): ")
        if create_superuser.lower() == 'y':
            subprocess.run([sys.executable, "manage.py", "createsuperuser"], cwd=admin_dir)
    
    print("Admin Portal setup complete!")

def initialize_database():
    """Initialize the system database"""
    print("Initializing system database...")
    
    # Check if main.py exists
    if os.path.exists(os.path.join(project_root, "main.py")):
        subprocess.run([sys.executable, "main.py", "--init-db"])
    else:
        print("Error: main.py not found. Cannot initialize database.")
    
    print("Database initialization complete!")

def configure_system():
    """Configure the system"""
    print("Configuring system...")
    
    # Check if system_config.py exists
    config_path = os.path.join(project_root, "system_config.py")
    if os.path.exists(config_path):
        # Import the configuration
        sys.path.insert(0, str(project_root))
        from system_config import IMPLEMENTATION_CONFIG, API_SERVER_CONFIG, DJANGO_ADMIN_PORTAL_CONFIG, FEATURE_FLAGS
        
        # Show current configuration
        print("\nCurrent Configuration:")
        print("Implementation Config:")
        for key, value in IMPLEMENTATION_CONFIG.items():
            print(f"  {key}: {value}")
        
        print("\nAPI Server Config:")
        for key, value in API_SERVER_CONFIG.items():
            print(f"  {key}: {value}")
        
        print("\nDjango Admin Portal Config:")
        for key, value in DJANGO_ADMIN_PORTAL_CONFIG.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")
        
        print("\nFeature Flags:")
        for key, value in FEATURE_FLAGS.items():
            print(f"  {key}: {value}")
        
        # Ask if user wants to modify
        modify = input("\nDo you want to modify any of these settings? (y/n): ")
        if modify.lower() == 'y':
            # TODO: Implement configuration editor
            print("Configuration editor not implemented yet.")
    else:
        print("system_config.py not found. Creating default configuration...")
        
        # Create default configuration
        config = {
            "IMPLEMENTATION_CONFIG": {
                "USE_DJANGO_ADMIN_PORTAL": True,
                "USE_CLEAN_ARCHITECTURE": True,
                "DATABASE_IMPLEMENTATION": "sqlite",
                "ENABLE_API_SERVER": True,
                "ENABLE_TRANSACTION_LOGGING": True,
                "ENABLE_PERFORMANCE_MONITORING": True
            },
            "API_SERVER_CONFIG": {
                "port": 8000,
                "host": "0.0.0.0",
                "debug": False,
                "use_ssl": False,
                "ssl_cert": "",
                "ssl_key": ""
            },
            "DJANGO_ADMIN_PORTAL_CONFIG": {
                "port": 8001,
                "host": "0.0.0.0",
                "static_root": "app/Portals/Admin/static",
                "media_root": "app/Portals/Admin/media",
                "database": {
                    "engine": "django.db.backends.sqlite3",
                    "name": "app/Portals/Admin/db.sqlite3"
                }
            },
            "FEATURE_FLAGS": {
                "ENABLE_MULTI_CURRENCY": True,
                "ENABLE_SCHEDULED_PAYMENTS": True,
                "ENABLE_MOBILE_NOTIFICATIONS": True,
                "ENABLE_TWO_FACTOR_AUTH": True,
                "ENABLE_BIOMETRIC_AUTH": False,
                "ENABLE_AI_FRAUD_DETECTION": False
            }
        }
        
        # Write to file
        with open(config_path, "w") as f:
            f.write('"""\nSystem Configuration for Core Banking System\n\nThis file defines which implementations to use for different components\nof the system.\n"""\n\n')
            
            for section, values in config.items():
                f.write(f"# {section}\n")
                f.write(f"{section} = {json.dumps(values, indent=4)}\n\n")
        
        print(f"Default configuration written to {config_path}")
    
    print("System configuration complete!")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="CBS_PYTHON Integration Utility")
    
    parser.add_argument("--install-deps", action="store_true",
                      help="Install required dependencies")
    parser.add_argument("--setup-admin", action="store_true",
                      help="Set up the Admin Portal")
    parser.add_argument("--init-db", action="store_true",
                      help="Initialize the database")
    parser.add_argument("--configure", action="store_true",
                      help="Configure the system")
    parser.add_argument("--all", action="store_true",
                      help="Perform all integration steps")
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not any(vars(args).values()):
        parser.print_help()
        return
    
    # Install dependencies
    if args.install_deps or args.all:
        install_dependencies()
    
    # Set up admin portal
    if args.setup_admin or args.all:
        setup_admin_portal()
    
    # Initialize database
    if args.init_db or args.all:
        initialize_database()
    
    # Configure system
    if args.configure or args.all:
        configure_system()
    
    print("\nIntegration completed successfully!")

if __name__ == "__main__":
    main()
