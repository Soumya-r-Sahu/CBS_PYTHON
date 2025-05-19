"""
Django Client Library Path Helper

This module helps ensure the Django client library is correctly accessible
in the test environment and other scripts.
"""

import os
import sys
from pathlib import Path

# Get the absolute path to the project root directory
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))

# Add project root to the Python path if not already there
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add Backend directory to the path
backend_dir = os.path.join(project_root, 'Backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Add integration_interfaces directory to the path
integration_dir = os.path.join(backend_dir, 'integration_interfaces')
if integration_dir not in sys.path:
    sys.path.insert(0, integration_dir)

def fix_paths():
    """
    Add necessary paths to sys.path to ensure client libraries can be imported.
    """
    # Print path information for debugging
    print(f"Project root: {project_root}")
    print(f"Backend directory: {backend_dir}")
    print(f"Integration interfaces directory: {integration_dir}")
    
    # Verify Django client exists
    django_client_dir = os.path.join(integration_dir, 'django_client')
    if os.path.exists(django_client_dir):
        print(f"Django client directory found at: {django_client_dir}")
    else:
        print(f"Warning: Django client directory not found at: {django_client_dir}")

if __name__ == "__main__":
    fix_paths()
    
    # Test importing the client
    try:
        from Backend.integration_interfaces.django_client import BankingAPIClient
        print("Successfully imported BankingAPIClient from Django client library")
    except ImportError as e:
        print(f"Error importing Django client: {e}")
