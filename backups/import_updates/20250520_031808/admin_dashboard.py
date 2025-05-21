"""
Admin Dashboard for Core Banking System

This module provides the admin dashboard interface for system administration.
It includes functionalities like user management, system monitoring, and configuration.
"""

import os
import sys
import logging
import datetime
from typing import Dict, List, Any, Optional

# Import necessary modules
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# Configure logger
logger = logging.getLogger(__name__)

class AdminDashboard:
    """
    Admin Dashboard for the Core Banking System.
    Provides administrative functionality for system management.
    """
    
    def __init__(self):
        """Initialize the admin dashboard."""
        self.start_time = datetime.datetime.now()
        self.modules_status = self._check_modules_status()
        self.system_info = self._get_system_info() if PSUTIL_AVAILABLE else {"status": "Limited system info (psutil not available)"}
        
    def _check_modules_status(self) -> Dict[str, bool]:
        """Check the status of required modules."""
        return {
            "psutil": PSUTIL_AVAILABLE,
            "cryptography": CRYPTO_AVAILABLE,
            "schedule": SCHEDULE_AVAILABLE
        }
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information using psutil."""
        if not PSUTIL_AVAILABLE:
            return {"error": "psutil module not available"}
            
        try:
            return {
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent,
                "uptime": str(datetime.datetime.now() - self.start_time)
            }
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {"error": str(e)}
    
    def _get_db_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        # This would normally connect to the database and get stats
        # Using mock data for now
        return {
            "total_accounts": 1250,
            "active_accounts": 1100,
            "inactive_accounts": 150,
            "total_transactions_today": 320,
            "transaction_volume_today": 1450000.00
        }
    
    def show(self):
        """Display the admin dashboard."""
        print("\n===== Core Banking System - Admin Dashboard =====")
        
        while True:
            print("\nPlease select an option:")
            print("1. User Management")
            print("2. Transaction Logs")
            print("3. System Settings")
            print("4. View System Statistics")
            print("5. Database Management")
            print("6. Module Status")
            print("7. Back to Main Menu")
            
            choice = input("\nEnter your choice: ")
            
            if choice == '1':
                self._show_user_management()
            elif choice == '2':
                self._show_transaction_logs()
            elif choice == '3':
                self._show_system_settings()
            elif choice == '4':
                self._show_system_statistics()
            elif choice == '5':
                self._show_database_management()
            elif choice == '6':
                self._show_module_status()
            elif choice == '7':
                print("Returning to main menu...")
                break
            else:
                print("Invalid choice. Please try again.")
            
            input("\nPress Enter to continue...")
    
    def _show_user_management(self):
        """Show user management interface."""
        print("\n----- User Management -----")
        print("1. View All Users")
        print("2. Add New User")
        print("3. Modify User")
        print("4. Delete User")
        print("5. Back")
        
        subchoice = input("\nEnter your choice: ")
        
        if subchoice == '5':
            return
            
        print("Feature implementation in progress.")
    
    def _show_transaction_logs(self):
        """Show transaction logs interface."""
        print("\n----- Transaction Logs -----")
        print("1. View Today's Transactions")
        print("2. View Transaction by ID")
        print("3. View Transactions by Date Range")
        print("4. View Failed Transactions")
        print("5. Back")
        
        subchoice = input("\nEnter your choice: ")
        
        if subchoice == '5':
            return
            
        print("Feature implementation in progress.")
    
    def _show_system_settings(self):
        """Show system settings interface."""
        print("\n----- System Settings -----")
        print("1. General Settings")
        print("2. Security Settings")
        print("3. Notification Settings")
        print("4. Backup Settings")
        print("5. Back")
        
        subchoice = input("\nEnter your choice: ")
        
        if subchoice == '5':
            return
            
        print("Feature implementation in progress.")
    
    def _show_system_statistics(self):
        """Show system statistics."""
        print("\n----- System Statistics -----")
        
        # Update system info
        if PSUTIL_AVAILABLE:
            self.system_info = self._get_system_info()
            print("System Information:")
            for key, value in self.system_info.items():
                print(f"  {key}: {value}")
        else:
            print("System monitoring limited - psutil not available")
            print("Install psutil for complete system monitoring")
        
        print("\nDatabase Statistics:")
        db_stats = self._get_db_stats()
        for key, value in db_stats.items():
            print(f"  {key}: {value}")
    def _show_database_management(self):
        """Show database management interface."""
        print("\n----- Database Management -----")
        print("1. Backup Database")
        print("2. Restore Database")
        print("3. View Database Status")
        print("4. Database Maintenance")
        print("5. Toggle Database Type")
        print("6. Back")
        
        subchoice = input("\nEnter your choice: ")
        
        if subchoice == '1':
            self._backup_database()
        elif subchoice == '2':
            self._restore_database()
        elif subchoice == '3':
            self._view_database_status()
        elif subchoice == '4':
            self._database_maintenance()
        elif subchoice == '5':
            self._toggle_database_type()
        elif subchoice == '6':
            return
        else:
            print("Invalid choice. Please try again.")

    def _backup_database(self):
        """Backup the database."""
        print("\nInitiating database backup...")
        print("Feature implementation in progress.")
        
    def _restore_database(self):
        """Restore the database from backup."""
        print("\nWarning: Restoring database will overwrite current data!")
        confirm = input("Are you sure you want to proceed? (y/n): ")
        if confirm.lower() == 'y':
            print("Initiating database restore...")
            print("Feature implementation in progress.")
        else:
            print("Database restore cancelled.")
            
    def _view_database_status(self):
        """View database status."""
        print("\n----- Database Status -----")
        
        # Try to import database type manager
        try:
            from utils.database_type_manager import get_database_type
            
            # Get current database type
            db_type = get_database_type()
            print(f"Current Database Type: {db_type.upper()}")
        except ImportError:
            db_type = "mysql"  # Default
            print("Database Type Manager not available.")
            print(f"Using default database type: {db_type.upper()}")
        
        # Get connection and display statistics
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
            
        try:
            cursor = conn.cursor()
            
            # Get table count
            try:
                if db_type == 'mysql':
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE()")
                elif db_type == 'sqlite':
                    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                elif db_type == 'postgresql':
                    cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
                
                table_count = cursor.fetchone()[0]
                print(f"Total Tables: {table_count}")
            except Exception as e:
                print(f"Error getting table count: {str(e)}")
            
            # Display connection information
            print("\nConnection Information:")
            if db_type == 'mysql':
                cursor.execute("SELECT VERSION()")
                db_version = cursor.fetchone()[0]
                print(f"MySQL Version: {db_version}")
                
                cursor.execute("SHOW VARIABLES LIKE 'max_connections'")
                max_connections = cursor.fetchone()[1]
                print(f"Max Connections: {max_connections}")
                
                cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
                threads_connected = cursor.fetchone()[1]
                print(f"Current Connections: {threads_connected}")
            elif db_type == 'sqlite':
                cursor.execute("SELECT sqlite_version()")
                db_version = cursor.fetchone()[0]
                print(f"SQLite Version: {db_version}")
            elif db_type == 'postgresql':
                cursor.execute("SELECT version()")
                db_version = cursor.fetchone()[0]
                print(f"PostgreSQL Version: {db_version}")
            
            cursor.close()
            self.db.close_connection(conn)
            
        except Exception as e:
            print(f"Error getting database status: {str(e)}")
            if conn:
                self.db.close_connection(conn)
        
        input("\nPress Enter to continue...")
        
    def _database_maintenance(self):
        """Perform database maintenance operations."""
        print("\n----- Database Maintenance -----")
        print("1. Check Database Integrity")
        print("2. Optimize Database")
        print("3. Repair Database")
        print("4. Back")
        
        choice = input("\nEnter your choice: ")
        
        if choice == '1':
            print("\nChecking database integrity...")
            print("Feature implementation in progress.")
        elif choice == '2':
            print("\nOptimizing database...")
            print("Feature implementation in progress.")
        elif choice == '3':
            print("\nRepairing database...")
            print("Feature implementation in progress.")
        elif choice == '4':
            return
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")
    
    def _toggle_database_type(self):
        """Toggle between different database types."""
        print("\n----- Toggle Database Type -----")
        
        # Try to import database type manager
        try:
            from utils.database_type_manager import get_database_type, set_database_type, VALID_DB_TYPES
            
            # Get current database type
            current_db_type = get_database_type()
            print(f"Current Database Type: {current_db_type.upper()}")
            
            # Show available database types
            print("\nAvailable Database Types:")
            for i, db_type in enumerate(VALID_DB_TYPES, 1):
                print(f"{i}. {db_type.upper()}")
            
            # Get user choice
            choice = input("\nSelect database type (or enter 'cancel' to go back): ")
            
            if choice.lower() == 'cancel':
                return
                
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(VALID_DB_TYPES):
                    new_db_type = VALID_DB_TYPES[choice_idx]
                    
                    # Confirm change
                    if new_db_type == current_db_type:
                        print(f"\nAlready using {new_db_type.upper()} database.")
                        input("\nPress Enter to continue...")
                        return
                        
                    print(f"\nChanging database type from {current_db_type.upper()} to {new_db_type.upper()}.")
                    print("Warning: This change will require a system restart to take effect.")
                    print("Warning: Ensure that the target database exists and is properly configured.")
                    
                    # Additional warnings based on target database
                    if new_db_type == 'postgresql':
                        print("\nNote: PostgreSQL requires the psycopg2 package to be installed.")
                        print("Run: pip install psycopg2 before changing to PostgreSQL.")
                    
                    confirm = input("\nAre you sure you want to proceed? (yes/no): ")
                    
                    if confirm.lower() == 'yes':
                        # Update database type
                        success = set_database_type(new_db_type)
                        
                        if success:
                            print(f"\nDatabase type successfully changed to {new_db_type.upper()}.")
                            print("Please restart the system for the change to take effect.")
                        else:
                            print("\nFailed to change database type. Please check the logs for details.")
                    else:
                        print("\nDatabase type change cancelled.")
                else:
                    print("\nInvalid choice. Please select a valid database type.")
            except ValueError:
                print("\nInvalid input. Please enter a number.")
        except ImportError:
            print("\nDatabase Type Manager not available.")
            print("Please check that utils/database_type_manager.py exists.")
        
        input("\nPress Enter to continue...")
    
    def _show_module_status(self):
        """Show status of all system modules."""
        print("\n----- Module Status -----")
        
        print("Required Module Status:")
        for module, status in self.modules_status.items():
            status_text = "Installed" if status else "Not Installed"
            print(f"  {module}: {status_text}")
        
        if not all(self.modules_status.values()):
            print("\nWarning: Some required modules are not installed.")
            print("Install all dependencies for full functionality:")
            print("  pip install psutil cryptography schedule")
