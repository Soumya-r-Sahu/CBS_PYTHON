"""
Database Migration Reference File

This file serves as a reference to the `manage_database.py` script that handles database migrations.
The actual script is located in the maintenance/database directory.

To run database migrations, use:
    python ../../maintenance/database/manage_database.py

Or navigate to the maintenance directory:
    cd ../../maintenance/database
    python manage_database.py
"""

# This is a reference file - the actual implementation is in:
# ../../maintenance/database/manage_database.py

print("Database migration script is located at: ../../maintenance/database/manage_database.py")
print("Please run that script directly for database migrations.")

if __name__ == "__main__":
    import os
    import sys
      # Try to import and run the actual script
    script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "maintenance", "database", "manage_database.py")
    
    if os.path.exists(script_path):
        print(f"Redirecting to {script_path}...")
        # Change directory to the maintenance directory
        os.chdir(os.path.dirname(script_path))
        # Load the module without importing it
        import importlib.util
        spec = importlib.util.spec_from_file_location("manage_database", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.exit(0)
    else:
        print(f"Error: Could not find {script_path}")
        print("Please check if the file exists and try again.")
        sys.exit(1)
