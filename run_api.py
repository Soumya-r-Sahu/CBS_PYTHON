"""
CLI utility to run the Mobile Banking API server
"""

import os
import sys
import argparse

# Add parent directory to path if needed

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed

# Note: Import handling for hyphenated directories has been removed
# as there are no hyphenated directories being imported in this file

from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Import from our API module
try:
    from integration_interfaces.api.app import create_app
except ImportError:
    # Create a fallback app if the real one isn't available
    print(f"{Fore.YELLOW}Warning: Could not import create_app from integration_interfaces.api.app{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Using a fallback Flask application instead.{Style.RESET_ALL}")
    
    from flask import Flask
    
    def create_app():
        """Create a fallback Flask application."""
        app = Flask("Core Banking API")
        
        @app.route('/')
        def index():
            return {"status": "API Server Running (Fallback Mode)", 
                    "message": "The real API module could not be loaded."}
        
        return app

# Import from our API module
from app.api.app import create_app

# Use environment functions from utils.lib.packages that we already imported
# Define additional functions for compatibility
def get_environment_name():
    """Get the current environment name as a string."""
    if is_production():
        return "production"
    elif is_test():
        return "test"
    else:
        return "development"

# Set environment color based on type
ENV_COLOR = Fore.RED if is_production() else Fore.YELLOW if is_test() else Fore.GREEN
ENV_NAME = get_environment_name().upper()

def parse_args():
    """
    Parse command line arguments
    
    Returns:
        Parsed arguments
    """
    # Default port based on environment
    if is_production():
        default_port = 5000
    elif is_test():
        default_port = 5001
    else:  # development
        default_port = 5002
    
    parser = argparse.ArgumentParser(description='Run the Mobile Banking API server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=default_port, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--env', choices=['development', 'test', 'production'], 
                        help='Override environment setting (default: from CBS_ENVIRONMENT)')
    
    return parser.parse_args()

def main():
    """
    Main entry point
    """
    args = parse_args()
    
    # Override environment if specified
    if args.env:
        os.environ["CBS_ENVIRONMENT"] = args.env
        
    # Display environment banner
    env_banner = f"""
    {ENV_COLOR}╔═══════════════════════════════════════════════════════════════╗
    ║ CORE BANKING SYSTEM API SERVER                              ║
    ║ Environment: {ENV_NAME.ljust(20)}                              ║
    ║ Debug Mode: {"ENABLED" if is_debug_enabled() else "DISABLED".ljust(20)}                             ║
    ╚═══════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(env_banner)
    
    # Create and configure Flask app
    app = create_app()
      # Set debug mode based on environment and arguments
    debug_mode = args.debug
    if not args.debug:
        debug_mode = is_debug_enabled() and not is_production()
    
    # Warn if trying to enable debug mode in production
    if debug_mode and is_production():
        print(f"{Fore.RED}WARNING: Debug mode is enabled in production environment!{Style.RESET_ALL}")
        print(f"{Fore.RED}This is a security risk and should not be used in real production deployments.{Style.RESET_ALL}")
        
    # Run the app
    print(f"Starting API server on {args.host}:{args.port} (Debug: {'ON' if debug_mode else 'OFF'})")
    app.run(
        host=args.host,
        port=args.port,
        debug=debug_mode
    )

if __name__ == '__main__':
    main()