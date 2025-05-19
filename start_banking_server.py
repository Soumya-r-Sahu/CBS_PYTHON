#!/usr/bin/env python
"""
Banking System - Startup Script

This user-friendly script starts the Core Banking System with appropriate
configuration options. It provides an easy way to:
  1. Start the entire banking system
  2. Start only the API service
  3. Configure environment settings
  4. Enable debug mode
  5. Start admin portal

Examples:
  python start_banking_server.py                      # Standard startup
  python start_banking_server.py --environment=test   # Start in test mode
  python start_banking_server.py --api-only           # Start only API
  python start_banking_server.py --debug              # Start with debug logging
  python start_banking_server.py --admin-portal       # Start only admin portal
"""

import os
import sys
import argparse
import logging
import importlib
import subprocess
from pathlib import Path

# Add project root to path for easier imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def start_admin_portal(config, portal_config, debug=False):
    """Start the Django-based Admin Portal"""
    try:
        use_django_admin = config.get("USE_DJANGO_ADMIN_PORTAL", True)
        
        if use_django_admin:
            # Get configuration
            port = portal_config.get("port", 8001)
            host = portal_config.get("host", "0.0.0.0")
            
            # Get the path to the manage.py file
            admin_dir = os.path.join(project_root, "app", "Portals", "Admin")
            
            if not os.path.exists(os.path.join(admin_dir, "manage.py")):
                print(f"Error: manage.py not found in {admin_dir}")
                print("Falling back to standalone admin dashboard")
                start_standalone_admin(debug)
                return
            
            print(f"Starting Django Admin Portal at http://{host}:{port}/")
            print("Press Ctrl+C to stop the server")
            
            # Run Django server
            cmd = [sys.executable, "manage.py", "runserver", f"{host}:{port}"]
            if debug:
                cmd.append("--verbosity=2")
            
            subprocess.run(cmd, cwd=admin_dir)
        else:
            # Use standalone admin dashboard
            start_standalone_admin(debug)
    except Exception as e:
        print(f"Error starting Admin Portal: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        
        print("Falling back to standalone admin dashboard")
        start_standalone_admin(debug)

def start_standalone_admin(debug=False):
    """Start the standalone admin dashboard"""
    try:
        print("Starting standalone Admin Dashboard...")
        from main import start_admin_dashboard
        start_admin_dashboard()
    except Exception as e:
        print(f"Error starting standalone Admin Dashboard: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def start_api_server(api_config, debug=False):
    """Start the API server"""
    try:
        # Get configuration
        port = api_config.get("port", 8000)
        host = api_config.get("host", "0.0.0.0")
        
        print(f"Starting API Server at http://{host}:{port}/")
        print("Press Ctrl+C to stop the server")
        
        # Try to import and start the API server
        try:
            from main import start_api_server as start_api
            start_api(port=port, debug=debug)
        except (ImportError, AttributeError):
            # Fall back to alternative implementation
            print("Warning: Could not use main.py API server implementation")
            print("Trying alternate implementation...")
            
            try:
                # Look for API server modules
                api_module_paths = [
                    "api.server",
                    "integration_interfaces.api.server",
                    "app.api.server"
                ]
                
                for module_path in api_module_paths:
                    try:
                        api_module = importlib.import_module(module_path)
                        if hasattr(api_module, "start_server"):
                            print(f"Found API server in {module_path}")
                            api_module.start_server(host=host, port=port, debug=debug)
                            return
                    except ImportError:
                        continue
                
                print("Error: Could not find API server implementation")
                sys.exit(1)
            except Exception as e:
                print(f"Error starting API server: {e}")
                if debug:
                    import traceback
                    traceback.print_exc()
                sys.exit(1)
    except Exception as e:
        print(f"Error starting API server: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

def main():
    """Process command line options and start the banking system"""
    parser = argparse.ArgumentParser(description="Banking System Startup")
    
    parser.add_argument("--environment", default=None,
                      help="Environment to run (development, testing, production)")
    parser.add_argument("--api-only", action="store_true",
                      help="Start only the API server")
    parser.add_argument("--admin-portal", action="store_true",
                      help="Start only the admin portal")
    parser.add_argument("--debug", action="store_true",
                      help="Run in debug mode")
    
    args = parser.parse_args()
    
    # Set environment variable if specified
    if args.environment:
        os.environ["CBS_ENVIRONMENT"] = args.environment
    
    # Set debug flag if requested
    if args.debug:
        os.environ["CBS_DEBUG"] = "1"
        print("Debug mode enabled - detailed logging will be shown")
    
    # Try to import system configuration
    try:
        from system_config import IMPLEMENTATION_CONFIG, API_SERVER_CONFIG, DJANGO_ADMIN_PORTAL_CONFIG
        print("Using configuration from system_config.py")
    except ImportError:
        print("Warning: Could not import system_config.py. Using default configuration.")
        # Create default configurations
        IMPLEMENTATION_CONFIG = {
            "USE_DJANGO_ADMIN_PORTAL": True,
            "USE_CLEAN_ARCHITECTURE": True,
            "DATABASE_IMPLEMENTATION": "sqlite",
            "ENABLE_API_SERVER": True
        }
        API_SERVER_CONFIG = {
            "port": 8000,
            "host": "0.0.0.0",
            "debug": args.debug
        }
        DJANGO_ADMIN_PORTAL_CONFIG = {
            "port": 8001,
            "host": "0.0.0.0"
        }
    
    # Start admin portal if requested
    if args.admin_portal:
        start_admin_portal(IMPLEMENTATION_CONFIG, DJANGO_ADMIN_PORTAL_CONFIG, args.debug)
        return
    
    # Start API server if requested
    if args.api_only:
        start_api_server(API_SERVER_CONFIG, args.debug)
        return
      # Otherwise, start the full banking system
    try:
        print("Starting Full Banking System...")
        from main import main as main_entry
        
        # Prepare arguments
        sys.argv = [sys.argv[0]]
        
        if args.debug:
            sys.argv.append("--debug")
        
        # Start the system
        main_entry()
    except Exception as e:
        print(f"Error starting banking system: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
