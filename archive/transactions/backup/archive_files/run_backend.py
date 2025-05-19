#!/usr/bin/env python
"""
Start the CBS_PYTHON backend services.
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="CBS_PYTHON Backend Runner")
    
    parser.add_argument("--environment", default=None,
                      help="Environment to run (development, testing, production)")
    parser.add_argument("--api-only", action="store_true",
                      help="Start only the API server")
    parser.add_argument("--debug", action="store_true",
                      help="Run in debug mode")
    
    args = parser.parse_args()
    
    # Set environment variable if specified
    if args.environment:
        os.environ["CBS_ENVIRONMENT"] = args.environment
    
    # Import and run the backend script
    try:
        # Set debug flag if requested
        if args.debug:
            os.environ["CBS_DEBUG"] = "1"
        
        # Import the backend module
        from backend import main as backend_main
        
        # Run backend with appropriate arguments
        sys.argv = [sys.argv[0]]
        
        if args.api_only:
            sys.argv.append("--api-only")
            
        if args.debug:
            sys.argv.append("--debug")
            
        # Start the backend
        backend_main()
        
    except ImportError as e:
        print(f"Error importing backend module: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting backend: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
