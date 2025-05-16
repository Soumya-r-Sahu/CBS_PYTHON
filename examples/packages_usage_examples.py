#!/usr/bin/env python
"""
Centralized Import Manager Usage Examples

This script demonstrates the various features of the centralized import manager.
"""

# Import the import manager functions
from utils.lib.packages import (
    # Core functions
    import_module, fix_path, get_root, import_from,
    
    # Environment functions
    is_production, is_development, is_test, is_debug_enabled,
    get_environment_name, Environment,
    
    # Database helpers
    get_database_connection
)

def demonstrate_basic_imports():
    """Demonstrate basic module imports."""
    print("\n===== Basic Module Imports =====")
    
    # Import a standard library module
    os_module = import_module("os")
    print(f"Successfully imported os module: {os_module.__name__}")
    
    # Import a project module
    try:
        config_module = import_module("app.config.settings")
        print(f"Successfully imported config module: {config_module.__name__}")
    except Exception as e:
        print(f"Could not import config module, but no error raised: {e}")

def demonstrate_fallbacks():
    """Demonstrate fallback mechanisms."""
    print("\n===== Fallback Mechanisms =====")
    
    # Define a fallback module
    class FallbackSettings:
        DEBUG = False
        LOG_LEVEL = "WARNING"
        DATABASE_URL = "sqlite://:memory:"
        
        def get_config(self):
            return {"debug": self.DEBUG, "log_level": self.LOG_LEVEL}
    
    # Import with fallback
    settings_module = import_module("app.config.settings", fallback=FallbackSettings())
    
    # Use the module (real or fallback)
    print(f"Debug mode: {settings_module.DEBUG}")
    print(f"Log level: {settings_module.LOG_LEVEL}")

def demonstrate_environment_functions():
    """Demonstrate environment functions."""
    print("\n===== Environment Functions =====")
    
    # Get the current environment name
    env_name = get_environment_name()
    print(f"Current environment: {env_name}")
    
    # Check specific environments
    print(f"Is production? {is_production()}")
    print(f"Is development? {is_development()}")
    print(f"Is test? {is_test()}")
    
    # Check debug mode
    print(f"Is debug enabled? {is_debug_enabled()}")
    
    # Use Environment class constants
    if env_name == Environment.DEVELOPMENT:
        print("Running in development mode")
    elif env_name == Environment.PRODUCTION:
        print("Running in production mode")
    elif env_name == Environment.TEST:
        print("Running in test mode")

def demonstrate_database_connection():
    """Demonstrate database connection usage."""
    print("\n===== Database Connection =====")
    
    # Get the database connection class
    DBConnection = get_database_connection()
    
    # Print the class name
    print(f"Database connection class: {DBConnection.__name__ if hasattr(DBConnection, '__name__') else 'FallbackDatabaseConnection'}")
    
    # Try to use it
    db = DBConnection()
    print("Successfully created database connection instance")
    
    # Try to get a connection
    try:
        connection = db.get_connection()
        print(f"Got connection: {connection}")
    except Exception as e:
        print(f"Could not get actual connection (expected in fallback): {e}")

def demonstrate_import_from():
    """Demonstrate importing specific items from a module."""
    print("\n===== Import Specific Items =====")
    
    # Import specific items from the os module
    items = import_from("os", "path", "environ", "name")
    
    # Display what was imported
    print(f"Imported items: {list(items.keys())}")
    
    # Use the imported items
    if "path" in items:
        print(f"os.path exists: {items['path'].__name__}")
    
    if "environ" in items:
        print(f"os.environ exists: {type(items['environ'])}")

def demonstrate_project_root():
    """Demonstrate project root discovery."""
    print("\n===== Project Root Discovery =====")
    
    # Get the project root
    root = get_root()
    print(f"Project root: {root}")
    
    # Check if key files/directories exist
    utils_dir = root / "utils"
    if utils_dir.exists():
        print(f"Found utils directory: {utils_dir}")
    
    lib_dir = utils_dir / "lib"
    if lib_dir.exists():
        print(f"Found lib directory: {lib_dir}")
    
    packages_file = lib_dir / "packages.py"
    if packages_file.exists():
        print(f"Found packages.py: {packages_file}")

def demonstrate_advanced_features():
    """Demonstrate advanced features by accessing the import manager directly."""
    print("\n===== Advanced Features =====")
    
    # Access the import manager directly
    from utils.lib.packages import import_manager
    
    # Show module cache
    cached_modules = list(import_manager._module_cache.keys())
    print(f"Currently cached modules: {cached_modules[:5]}...")
    
    # Show module aliases
    aliases = import_manager._module_aliases
    print(f"Module aliases: {aliases}")
    
    # Create a temporary alias for demonstration
    old_aliases = dict(aliases)
    try:
        import_manager._module_aliases['my_os'] = 'os'
        
        # Import using the alias
        my_os = import_module('my_os')
        print(f"Successfully imported os via alias 'my_os': {my_os.__name__}")
    finally:
        # Restore original aliases
        import_manager._module_aliases = old_aliases

if __name__ == "__main__":
    print("\nCENTRALIZED IMPORT MANAGER - USAGE EXAMPLES")
    print("=" * 50)
    
    demonstrate_basic_imports()
    demonstrate_fallbacks()
    demonstrate_environment_functions()
    demonstrate_database_connection()
    demonstrate_import_from()
    demonstrate_project_root()
    demonstrate_advanced_features()
    
    print("\n" + "=" * 50)
    print("All examples completed successfully!")
    print("=" * 50 + "\n")
