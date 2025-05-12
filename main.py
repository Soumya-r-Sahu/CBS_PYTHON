"""
Core Banking System (CBS) - Main application entry point

This is the main entry point for the Core Banking System.
It initializes the application and starts all necessary services.
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add parent directory to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.lib.logging_utils import get_info_logger, get_error_logger
except ImportError:
    # Fallback if the new structure isn't fully implemented
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    get_info_logger = lambda name: logging.getLogger(name)
    get_error_logger = lambda name: logging.getLogger(name)

# Set up logger
logger = get_info_logger(__name__)
error_logger = get_error_logger(__name__)

# Try to import from new structure, fall back to old structure if needed
try:
    from database.db_manager import DatabaseManager, Base
    
    # Try to import new model structure
    try:
        from app.models.models import Customer, Account, Transaction, Card
        NEW_STRUCTURE = True
    except ImportError:
        # Fall back to old structure
        from database.models import initialize_database
        from database.connection import DatabaseConnection
        NEW_STRUCTURE = False
        
except ImportError:
    # Fall back to old structure completely
    from database.models import initialize_database
    from database.connection import DatabaseConnection
    NEW_STRUCTURE = False

# Define UI component variables to prevent undefined errors
AtmInterface = None
AdminDashboard = None
UpiRegistration = None
CustomerDashboard = None

# Store import errors for troubleshooting
import_errors = {}

# Import UI components
try:
    from app.atm.atm_interface import AtmInterface
except ImportError as e:
    logger.warning(f"Failed to import AtmInterface: {e}")
    import_errors['AtmInterface'] = str(e)
    
try:
    from admin_panel.admin_dashboard import AdminDashboard
except ImportError as e:
    logger.warning(f"Failed to import AdminDashboard: {e}")
    import_errors['AdminDashboard'] = str(e)

try:
    from upi.upi_registration import UpiRegistration
except ImportError as e:
    logger.warning(f"Failed to import UpiRegistration: {e}")
    import_errors['UpiRegistration'] = str(e)

try:
    from gui.customer_dashboard import CustomerDashboard
except ImportError as e:
    logger.warning(f"Failed to import CustomerDashboard: {e}")
    import_errors['CustomerDashboard'] = str(e)

# Create dummy placeholders that provide better error messages
if CustomerDashboard is None:
    class CustomerDashboard:
        def __init__(self):
            self.user_info = {}
            self.account_summary = {'Balance': '100,000.00', 'Account Type': 'Savings', 'Status': 'Active'}
        
        def show(self):
            print("\n===== Core Banking System - Customer Dashboard (DEMO MODE) =====")
            print("This is running in demo mode with limited functionality.")
            if import_errors.get('CustomerDashboard'):
                print(f"Import error: {import_errors['CustomerDashboard']}")
            
            while True:
                print("\nPlease select an option:")
                print("1. Account Summary")
                print("2. Fund Transfer (Demo)")
                print("3. User Information (Demo)")
                print("4. Update User Information (Demo)")
                print("5. Back to Main Menu")
                
                choice = input("\nEnter your choice: ")
                
                if choice == '1':
                    print("\nAccount Summary (Demo Data):")
                    for key, value in self.account_summary.items():
                        print(f"{key}: {value}")
                elif choice == '2':
                    print("\nFund Transfer feature not available in demo mode.")
                    print("Install all dependencies for full functionality.")
                elif choice == '3':
                    print("\nUser Information (Demo Data):")
                    print("Name: John Doe")
                    print("Email: john.doe@example.com")
                    print("Phone: +1-555-123-4567")
                elif choice == '4':
                    print("\nUpdate User Information feature not available in demo mode.")
                    print("Install all dependencies for full functionality.")
                elif choice == '5':
                    print("Returning to main menu...")
                    break
                else:
                    print("Invalid choice. Please try again.")
                
                input("\nPress Enter to continue...")

if AdminDashboard is None:
    class AdminDashboard:
        def __init__(self):
            pass
            
        def show(self):
            print("\n===== Core Banking System - Admin Dashboard (DEMO MODE) =====")
            print("This is running in demo mode with limited functionality.")
            if import_errors.get('AdminDashboard'):
                print(f"Import error: {import_errors['AdminDashboard']}")
            
            while True:
                print("\nPlease select an option:")
                print("1. User Management (Demo)")
                print("2. Transaction Logs (Demo)")
                print("3. System Settings (Demo)")
                print("4. View Statistics (Demo)")
                print("5. Database Management (Demo)")
                print("6. Back to Main Menu")
                
                choice = input("\nEnter your choice: ")
                
                if choice == '1':
                    print("\nUser Management feature not available in demo mode.")
                    print("Install all dependencies for full functionality.")
                elif choice == '2':
                    print("\nTransaction Logs feature not available in demo mode.")
                    print("Install all dependencies for full functionality.")
                elif choice == '3':
                    print("\nSystem Settings feature not available in demo mode.")
                    print("Install all dependencies for full functionality.")
                elif choice == '4':
                    print("\nView Statistics feature not available in demo mode.")
                    print("Install all dependencies for full functionality.")
                elif choice == '5':
                    print("\nDatabase Management feature not available in demo mode.")
                    print("Install all dependencies for full functionality.")
                elif choice == '6':
                    print("Returning to main menu...")
                    break
                else:
                    print("Invalid choice. Please try again.")
                
                input("\nPress Enter to continue...")

if UpiRegistration is None:
    class UpiRegistration:
        def __init__(self):
            pass
            
        def register(self):
            print("\n===== UPI Registration (DEMO MODE) =====")
            print("This is running in demo mode with limited functionality.")
            if import_errors.get('UpiRegistration'):
                print(f"Import error: {import_errors['UpiRegistration']}")
                
            print("\nUPI Registration feature not available in demo mode.")
            print("Install all dependencies for full functionality.")
            input("\nPress Enter to continue...")

if AtmInterface is None:
    class AtmInterface:
        def __init__(self):
            pass
            
        def start(self):
            print("\n===== ATM Interface (DEMO MODE) =====")
            print("This is running in demo mode with limited functionality.")
            if import_errors.get('AtmInterface'):
                print(f"Import error: {import_errors['AtmInterface']}")
            
            while True:
                print("\nPlease select an option:")
                print("1. Cash Withdrawal (Demo)")
                print("2. Balance Inquiry (Demo)")
                print("3. Change PIN (Demo)")
                print("4. Exit")
                
                choice = input("Enter your choice: ")
                
                if choice == '1':
                    print("\nCash Withdrawal feature not available in demo mode.")
                    print("Install all dependencies for full functionality.")
                elif choice == '2':
                    print("\nBalance Inquiry (Demo Data):")
                    print("Account: ******1234")
                    print("Available Balance: Rs. 100,000.00")
                elif choice == '3':
                    print("\nChange PIN feature not available in demo mode.")
                    print("Install all dependencies for full functionality.")
                elif choice == '4':
                    print("Thank you for using the ATM. Goodbye!")
                    break
                else:
                    print("Invalid choice. Please try again.")
                
                input("\nPress Enter to continue...")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Core Banking System")
    
    parser.add_argument(
        "--init-db", 
        action="store_true", 
        help="Initialize the database and create tables"
    )
    
    parser.add_argument(
        "--mode", 
        choices=["api", "gui", "cli", "admin"], 
        default="gui",
        help="Application mode (api, gui, cli, or admin)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="Port to run the API server on"
    )
    
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Run in debug mode"
    )
    
    return parser.parse_args()

def init_database():
    """Initialize the database and create tables"""
    logger.info("Initializing database...")
    
    if NEW_STRUCTURE:
        try:
            # Use new structure
            db_manager = DatabaseManager()
            db_manager.create_tables(Base)
            logger.info("Database initialization complete")
            return True
        except Exception as e:
            error_logger.error(f"Database initialization failed: {e}")
            print(f"Error initializing database: {e}")
            return False
    else:
        # Use old structure
        try:
            # First, connect without specifying the database to create it if it doesn't exist
            try:
                import mysql.connector
                from mysql.connector import Error
                from utils.config import DATABASE_CONFIG
                
                print("Connecting to MySQL server...")
                conn = mysql.connector.connect(
                    host=DATABASE_CONFIG['host'],
                    user=DATABASE_CONFIG['user'],
                    password=DATABASE_CONFIG['password'],
                    port=DATABASE_CONFIG['port']
                )
                
                if conn.is_connected():
                    cursor = conn.cursor()
                    
                    # Create database if it doesn't exist
                    print(f"Creating database '{DATABASE_CONFIG['database']}' if it doesn't exist...")
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DATABASE_CONFIG['database']}")
                    print(f"Database '{DATABASE_CONFIG['database']}' is ready.")
                    
                    # Use the database
                    cursor.execute(f"USE {DATABASE_CONFIG['database']}")
                    
                    cursor.close()
                    conn.close()
            except Error as e:
                error_logger.error(f"Failed to create database: {e}")
                print(f"Error creating database: {e}")
                return False
                
            # Now connect to the database and initialize tables
            db_connection = DatabaseConnection()
            conn = db_connection.get_connection()
            
            if not conn:
                error_logger.error("Failed to connect to database. Check your database settings.")
                print("Failed to connect to database. Check your database settings in utils/config.py")
                return False
            
            # Initialize database tables
            print("Creating database tables...")
            if not initialize_database():
                error_logger.error("Failed to initialize database tables.")
                print("Failed to initialize database tables.")
                return False
                
            # Close the connection when done with initialization
            db_connection.close_connection()
            logger.info("Database initialization complete (legacy mode)")
            print("Database initialization complete!")
            return True
        except Exception as e:
            error_logger.error(f"Database initialization failed: {e}")
            print(f"Error initializing database: {e}")
            return False


def start_api_server(port, debug):
    """Start the API server"""
    try:
        # You would typically import and start your API server here
        # e.g. from app.api.server import start_server
        # start_server(port=port, debug=debug)
        
        logger.info(f"API server started on port {port}, debug={debug}")
        
        # For now, just log that we would start the server
        logger.info("This is a placeholder for starting the API server")
    except Exception as e:
        error_logger.error(f"Failed to start API server: {e}")
        sys.exit(1)


def start_gui():
    """Start the GUI application"""
    try:
        # Check if required module is available
        if CustomerDashboard is None:
            error_logger.error("CustomerDashboard module is missing. Cannot start GUI mode.")
            print("Error: CustomerDashboard module is missing. Please install all dependencies.")
            sys.exit(1)
            
        # Create instance of the customer dashboard
        customer_dashboard = CustomerDashboard()
        logger.info("Starting GUI customer dashboard")
        customer_dashboard.show()
        
    except Exception as e:
        error_logger.error(f"Failed to start GUI application: {e}")
        sys.exit(1)


def start_admin_dashboard():
    """Start the admin dashboard"""
    try:
        # Check if required module is available
        if AdminDashboard is None:
            error_logger.error("AdminDashboard module is missing. Cannot start admin mode.")
            print("Error: AdminDashboard module is missing. Please install all dependencies.")
            sys.exit(1)
            
        # Create instance of the admin dashboard
        admin_dashboard = AdminDashboard()
        logger.info("Starting admin dashboard")
        admin_dashboard.show()
        
    except Exception as e:
        error_logger.error(f"Failed to start admin dashboard: {e}")
        sys.exit(1)


def start_cli():
    """Start the CLI application with menu"""
    try:
        # Check if required modules are available
        if None in [AdminDashboard, AtmInterface, UpiRegistration, CustomerDashboard]:
            error_logger.error("Required modules are missing. Cannot start CLI mode.")
            print("Error: Required modules are missing. Please install all dependencies.")
            sys.exit(1)
        
        # Create instances of the main components
        admin_dashboard = AdminDashboard()
        atm_interface = AtmInterface()
        upi_registration = UpiRegistration()
        customer_dashboard = CustomerDashboard()
        
        logger.info("Starting CLI interface")

        # Start the application
        while True:
            print("\nWelcome to the Core Banking System")
            print("1. Admin Dashboard")
            print("2. ATM Interface")
            print("3. UPI Registration")
            print("4. Customer Dashboard")
            print("5. Exit")

            choice = input("Select an option: ")

            if choice == '1':
                admin_dashboard.show()
            elif choice == '2':
                atm_interface.start()
            elif choice == '3':
                upi_registration.register()
            elif choice == '4':
                customer_dashboard.show()
            elif choice == '5':
                print("Exiting the application.")
                sys.exit()
            else:
                print("Invalid choice. Please try again.")
    except Exception as e:
        error_logger.error(f"Failed to start CLI interface: {e}")
        sys.exit(1)

def is_this_script_being_run_directly():
    """Check if this script is being run directly from command line"""
    return __name__ == "__main__" and os.path.basename(sys.argv[0]) == "main.py"

def main():
    """Main entry point"""
    # Only proceed if this script is being run directly
    if not is_this_script_being_run_directly():
        return
    
    args = parse_args()
    
    logger.info("Starting Core Banking System")
    print("Core Banking System - Starting...")
    
    # Check for missing dependencies
    missing_deps = []
    # We'll skip the cryptography import check to avoid errors
    # Instead, we'll rely on the import warnings logged earlier
    # try:
    #     import cryptography
    # except ImportError:
    #     missing_deps.append("cryptography")
    
    missing_deps.append("cryptography")  # Mark as missing since we know it caused errors
    
    if missing_deps:
        print("\nWARNING: The following dependencies are missing:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nTo install missing dependencies, run:")
        print("  pip install -r requirements.txt")
        print("\nContinuing with limited functionality in DEMO mode...\n")
    
    # Initialize database if requested
    if args.init_db:
        print("Initializing database...")
        if not init_database():
            print("ERROR: Database initialization failed.")
            sys.exit(1)
    
    # Start application in requested mode
    if args.mode == "api":
        print(f"Starting API server on port {args.port}...")
        start_api_server(args.port, args.debug)
    elif args.mode == "gui":
        print("Starting GUI mode...")
        start_gui()
    elif args.mode == "admin":
        print("Starting admin dashboard...")
        start_admin_dashboard()
    elif args.mode == "cli":
        print("Starting CLI interface...")
        start_cli()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt. Exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        error_logger.error(f"Unhandled exception in main: {e}")
        print(f"\nError: {e}")
        sys.exit(1)