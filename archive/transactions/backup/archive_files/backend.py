"""
CBS_PYTHON Backend Entry Point

This script initializes and runs all backend services required by the CBS_PYTHON system.
"""

import os
import sys
import argparse
from pathlib import Path
import importlib
import threading
import time
import signal
import subprocess

# Add project root to path
current_dir = Path(__file__).resolve().parent
project_root = current_dir
sys.path.insert(0, str(project_root))

# Import configuration with fallback
try:
    from Backend.utils.config.environment import (
        get_environment,
        get_environment_name,
        is_production,
        is_development,
        is_debug_enabled
    )
except ImportError:
    # Define fallbacks
    def get_environment(): return "development"
    def get_environment_name(): return "Development"
    def is_production(): return False
    def is_development(): return True
    def is_debug_enabled(): return True

# Define services that can be started
AVAILABLE_SERVICES = {
    "api": {
        "module": "Backend.integration_interfaces.api.app",
        "function": "create_app",
        "description": "API Server for mobile and web applications",
        "enabled_by_default": True
    },
    "core": {
        "module": "Backend.core_banking.app",
        "function": "start_core_services",
        "description": "Core Banking Services",
        "enabled_by_default": True
    },
    "transaction-processor": {
        "module": "Backend.transactions.processor",
        "function": "start_processor",
        "description": "Transaction Processing Service",
        "enabled_by_default": True
    },
    "scheduler": {
        "module": "Backend.utils.scheduler",
        "function": "start_scheduler",
        "description": "Scheduled Jobs Service",
        "enabled_by_default": True
    },
    "monitoring": {
        "module": "Backend.monitoring.app",
        "function": "start_monitoring",
        "description": "System Monitoring Service",
        "enabled_by_default": False
    }
}

def start_service(service_name, service_config, args):
    """
    Start a specific backend service
    
    Args:
        service_name: Name of the service to start
        service_config: Service configuration dictionary
        args: Command-line arguments
        
    Returns:
        True if service started successfully, False otherwise
    """
    print(f"Starting {service_name} service...")
    
    try:
        # Try to import the module
        module_name = service_config["module"]
        function_name = service_config["function"]
        
        try:
            # Import module
            module = importlib.import_module(module_name)
            
            # Get the function to start the service
            start_function = getattr(module, function_name)
            
            # Start the service
            if args.subprocess:
                # Start as a separate process
                cmd = [sys.executable, "-m", module_name]
                if args.debug:
                    cmd.append("--debug")
                
                subprocess.Popen(cmd)
                print(f"{service_name} started as subprocess")
                return True
            else:
                # Start in a thread
                if args.debug:
                    # In debug mode, start directly for easier debugging
                    start_function()
                    return True
                else:
                    # Start in a thread
                    thread = threading.Thread(
                        target=start_function,
                        name=f"{service_name}-thread",
                        daemon=True
                    )
                    thread.start()
                    print(f"{service_name} started in thread")
                    return True
                
        except (ImportError, AttributeError) as e:
            print(f"Error starting {service_name}: {e}")
            
            if args.debug:
                print(f"Module: {module_name}")
                print(f"Function: {function_name}")
                import traceback
                traceback.print_exc()
                
            return False
            
    except Exception as e:
        print(f"Unexpected error starting {service_name}: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return False

def start_api_server():
    """
    Start the API server directly using Flask
    """
    try:
        from Backend.integration_interfaces.api.app import create_app
        
        app = create_app()
        
        # Get API configuration
        try:
            from Backend.utils.config.api import get_api_config
            api_config = get_api_config()
        except ImportError:
            api_config = {
                "host": "0.0.0.0",
                "port": 5000,
                "debug": is_debug_enabled()
            }
            
        host = api_config.get("host", "0.0.0.0")
        port = api_config.get("port", 5000)
        debug = api_config.get("debug", is_debug_enabled())
        
        print(f"Starting API server on http://{host}:{port}")
        app.run(host=host, port=port, debug=debug)
        
    except Exception as e:
        print(f"Error starting API server: {e}")
        if is_debug_enabled():
            import traceback
            traceback.print_exc()

def main():
    """
    Main entry point for the backend
    """
    parser = argparse.ArgumentParser(description="CBS_PYTHON Backend Services")
    
    parser.add_argument("--services", nargs="+", default=["all"],
                        help="Services to start (default: all)")
    parser.add_argument("--subprocess", action="store_true",
                        help="Start services as separate processes")
    parser.add_argument("--debug", action="store_true",
                        help="Run in debug mode")
    parser.add_argument("--api-only", action="store_true",
                        help="Start only the API server")
    
    args = parser.parse_args()
    
    # Print banner
    env_name = get_environment_name().upper()
    print(f"============================================")
    print(f"  CBS_PYTHON Backend - {env_name} Environment")
    print(f"============================================")
    
    # Start only API server if requested
    if args.api_only:
        start_api_server()
        return
    
    # Determine which services to start
    services_to_start = []
    
    if "all" in args.services:
        # Start all enabled-by-default services
        services_to_start = [
            name for name, config in AVAILABLE_SERVICES.items()
            if config.get("enabled_by_default", False)
        ]
    elif "none" in args.services:
        # Don't start any services (useful with --interactive)
        services_to_start = []
    else:
        # Start specific services
        services_to_start = args.services
    
    # Validate services
    for service in services_to_start[:]:
        if service not in AVAILABLE_SERVICES:
            print(f"Warning: Unknown service '{service}' - skipping")
            services_to_start.remove(service)
    
    if not services_to_start:
        print("No services specified to start")
        parser.print_help()
        return
    
    # Start services
    print(f"Starting {len(services_to_start)} services: {', '.join(services_to_start)}")
    
    started_services = []
    for service_name in services_to_start:
        service_config = AVAILABLE_SERVICES[service_name]
        if start_service(service_name, service_config, args):
            started_services.append(service_name)
    
    # Keep main thread running to allow services to run
    if started_services and not args.subprocess:
        print(f"\nServices started: {', '.join(started_services)}")
        print("Press Ctrl+C to stop all services")
        
        try:
            # Keep main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")

if __name__ == "__main__":
    main()
