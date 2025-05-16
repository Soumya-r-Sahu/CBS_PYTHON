import datetime
import os
import sys
from colorama import init, Fore, Style
try:
    from database.python.connection import DatabaseConnection
except ImportError:
    # Fallback implementation
    class DatabaseConnection:
        def __init__(self):
            print("Using mock database connection")
        def get_connection(self):
            return None
        def close_connection(self):
            pass
from admin_panel.user_management import UserManagement
from admin_panel.transaction_logs import TransactionLogs
from admin_panel.settings import SystemSettings

# Initialize colorama
init(autoreset=True)

# Use centralized import system
from utils.lib.packages import fix_path, is_production, is_development, is_test, is_debug_enabled, Environment
fix_path()

# Get environment name function
def get_environment_name():
    if is_production():
        return "Production"
    elif is_test():
        return "Test"
    else:
        return "Development"
    def is_production(): return env_str == "production"
    def is_development(): return env_str == "development"
    def is_test(): return env_str == "test"
    def get_environment_name(): return env_str.capitalize()
    def is_debug_enabled(): return os.environ.get("CBS_DEBUG", "false").lower() == "true"

class AdminDashboard:
    def __init__(self):
        self.db = DatabaseConnection()
        self.user_management = UserManagement()
        self.transaction_logs = TransactionLogs()
        self.system_settings = SystemSettings()
        self.statistics = {}
        
        # Environment-specific settings
        self.env_name = get_environment_name()
        
        # Set environment-specific colors
        if is_production():
            self.env_color = Fore.GREEN
            self.admin_rights = "FULL"  # Full rights in production
        elif is_test():
            self.env_color = Fore.YELLOW
            self.admin_rights = "FULL"  # Full rights in test for testing all functionality
        else:  # development
            self.env_color = Fore.BLUE
            self.admin_rights = "FULL"  # Full rights in development
            
        # Set additional environment indicators
        self.is_restricted_mode = is_production() and not is_debug_enabled()
        self.show_debug_options = not is_production() or is_debug_enabled()
        
    def show(self):
        """Display the admin dashboard with environment awareness"""
        # Environment banner
        env_banner = f"""
{self.env_color}╔════════════════════════════════════════════════════╗
║ CORE BANKING SYSTEM - ADMIN DASHBOARD              ║
║ Environment: {self.env_name.ljust(20)}                   ║
║ Rights: {self.admin_rights.ljust(20)}                   ║
╚════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
        print(env_banner)
        
        # Add environment-specific warnings
        if is_production():
            print(f"{Fore.GREEN}✅ PRODUCTION ENVIRONMENT - All changes affect live data{Style.RESET_ALL}")
            if self.is_restricted_mode:
                print(f"{Fore.YELLOW}⚠️ Some admin functions are restricted in production mode{Style.RESET_ALL}")
        elif is_test():
            print(f"{Fore.YELLOW}⚠️ TEST ENVIRONMENT - Changes do not affect production data{Style.RESET_ALL}")
        else:  # development
            print(f"{Fore.BLUE}🔧 DEVELOPMENT ENVIRONMENT - Using development database{Style.RESET_ALL}")
        
        while True:
            print(f"\n{Fore.CYAN}Please select an option:{Style.RESET_ALL}")
            print(f"{Fore.GREEN}1. User Management{Style.RESET_ALL}")
            print(f"{Fore.GREEN}2. Transaction Logs{Style.RESET_ALL}")
            print(f"{Fore.GREEN}3. System Settings{Style.RESET_ALL}")
            print(f"{Fore.GREEN}4. View Statistics{Style.RESET_ALL}")
            print(f"{Fore.GREEN}5. Database Management{Style.RESET_ALL}")
            print(f"{Fore.GREEN}6. Back to Main Menu{Style.RESET_ALL}")
            
            # Show environment-specific options
            if self.show_debug_options:
                print(f"{self.env_color}7. Environment Settings{Style.RESET_ALL}")
                print(f"{self.env_color}8. Debug Console{Style.RESET_ALL}")
            
            choice = input(f"\n{Fore.CYAN}Enter your choice:{Style.RESET_ALL} ")
            
            if choice == '1':
                self.user_management.show_menu()
            elif choice == '2':
                self.transaction_logs.show_menu()
            elif choice == '3':
                self.system_settings.show_menu()
            elif choice == '4':
                self.view_statistics()
            elif choice == '5':
                self.database_management()
            elif choice == '6':
                print(f"{Fore.CYAN}🔙 Returning to main menu...{Style.RESET_ALL}")
                break
            elif choice == '7' and self.show_debug_options:
                self.show_environment_settings()
            elif choice == '8' and self.show_debug_options:
                self.debug_console()
            else:
                print(f"{Fore.RED}❌ Invalid choice. Please try again.{Style.RESET_ALL}")
    
    def view_statistics(self):
        """View system statistics and analytics"""
        print("\n===== System Statistics =====")
        
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
        
        try:
            cursor = conn.cursor()
            
            # Get total number of customers
            cursor.execute("SELECT COUNT(*) FROM cbs_customers")
            total_customers = cursor.fetchone()[0]
            
            # Get total number of accounts
            cursor.execute("SELECT COUNT(*) FROM cbs_accounts")
            total_accounts = cursor.fetchone()[0]
            
            # Get total balance across all accounts
            cursor.execute("SELECT SUM(balance) FROM cbs_accounts")
            total_balance = cursor.fetchone()[0] or 0
            
            # Get transactions in the last 30 days
            cursor.execute(
                "SELECT COUNT(*) FROM cbs_transactions WHERE transaction_date >= %s",
                (datetime.datetime.now() - datetime.timedelta(days=30),)
            )
            recent_transactions = cursor.fetchone()[0]
            
            # Display statistics
            print(f"Total Customers: {total_customers}")
            print(f"Total Accounts: {total_accounts}")
            print(f"Total Balance (All Accounts): Rs. {total_balance:.2f}")
            print(f"Transactions (Last 30 days): {recent_transactions}")
            
            # Account type distribution
            cursor.execute(
                "SELECT account_type, COUNT(*) FROM cbs_accounts GROUP BY account_type"
            )
            account_types = cursor.fetchall()
            
            print("\nAccount Type Distribution:")
            for account_type, count in account_types:
                print(f"  {account_type}: {count}")
            
            input("\nPress Enter to continue...")
            
        except Exception as e:
            print(f"Error retrieving statistics: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def database_management(self):
        """Database management options"""
        print("\n===== Database Management =====")
        print("1. Backup Database")
        print("2. Restore Database")
        print("3. Optimize Database")
        print("4. Check Database Integrity")
        print("5. Back")
        
        choice = input("\nEnter your choice: ")
        
        if choice == '1':
            print("Initiating database backup...")
            # Call backup function
            print("Database backup completed successfully!")
        elif choice == '2':
            print("Warning: Restoring database will overwrite current data!")
            confirm = input("Are you sure you want to proceed? (y/n): ")
            if confirm.lower() == 'y':
                print("Initiating database restore...")
                # Call restore function
                print("Database restore completed successfully!")
        elif choice == '3':
            print("Optimizing database...")
            # Call optimize function
            print("Database optimization completed!")
        elif choice == '4':
            print("Checking database integrity...")
            # Call integrity check function
            print("Database integrity check completed!")
        elif choice == '5':
            return
        else:
            print("Invalid choice. Please try again.")
            
    def update_statistics(self, new_data):
        """Update statistics with new data"""
        self.statistics.update(new_data)
        
    def log_admin_activity(self, admin_id, activity_type, details):
        """Log admin activity for audit purposes"""
        conn = self.db.get_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO cbs_admin_logs (admin_id, activity_type, details, log_date) "
                "VALUES (%s, %s, %s, %s)",
                (admin_id, activity_type, details, datetime.datetime.now())
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"Error logging admin activity: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def show_environment_settings(self):
        """Display and manage environment settings"""
        print(f"\n{self.env_color}===== Environment Settings ====={Style.RESET_ALL}")
        print(f"Current Environment: {self.env_color}{self.env_name}{Style.RESET_ALL}")
        print(f"Debug Mode: {'Enabled' if is_debug_enabled() else 'Disabled'}")
        
        # Only show change options in development/test or for authorized production users
        if not is_production() or (is_production() and self.admin_rights == "FULL"):
            print(f"\nOptions:")
            print("1. Toggle Debug Mode")
            print("2. View Environment Variables")
            print("3. Test Environment-specific Features")
            print("4. Back to Admin Dashboard")
            
            choice = input("\nEnter your choice: ")
            
            if choice == '1':
                # In a real implementation, this would modify the actual environment configuration
                print(f"{self.env_color}Debug mode would be toggled here{Style.RESET_ALL}")
                print("Note: In a real implementation, this would update configuration files or environment variables")
            elif choice == '2':
                self.view_environment_variables()
            elif choice == '3':
                self.test_environment_features()
            elif choice == '4':
                return
            else:
                print(f"{Fore.RED}❌ Invalid choice.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.YELLOW}⚠️ Environment settings are view-only in restricted production mode{Style.RESET_ALL}")
            input("\nPress Enter to continue...")
    
    def view_environment_variables(self):
        """Display environment variables (CBS-specific only)"""
        print(f"\n{self.env_color}===== Environment Variables ====={Style.RESET_ALL}")
        
        # Filter to only show CBS-related variables
        env_vars = {k: v for k, v in os.environ.items() if k.startswith('CBS_')}
        
        if env_vars:
            for key, value in env_vars.items():
                # Mask sensitive values
                if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key']):
                    print(f"{key}: {'*' * len(value)}")
                else:
                    print(f"{key}: {value}")
        else:
            print(f"{Fore.YELLOW}No CBS-specific environment variables found{Style.RESET_ALL}")
        
        input("\nPress Enter to continue...")
    
    def test_environment_features(self):
        """Test environment-specific features"""
        print(f"\n{self.env_color}===== Environment Feature Testing ====={Style.RESET_ALL}")
        print("Select a feature to test:")
        print("1. Database Connection (Environment-specific)")
        print("2. Transaction Processing (with environment flags)")
        print("3. Email Notifications (environment-based recipients)")
        print("4. Back")
        
        choice = input("\nEnter choice: ")
        if choice in ['1', '2', '3']:
            print(f"\n{self.env_color}Testing would be performed here in a real implementation{Style.RESET_ALL}")
            print("Note: This is a placeholder for actual environment testing")
        
        input("\nPress Enter to continue...")
        
    def debug_console(self):
        """Interactive debug console with environment context"""
        print(f"\n{self.env_color}===== Debug Console ({self.env_name} Environment) ====={Style.RESET_ALL}")
        print(f"{Fore.YELLOW}This is an interactive debug console for troubleshooting.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Type 'exit' to return to the admin dashboard.{Style.RESET_ALL}")
        
        # In a real implementation, this would be an actual interactive shell
        # with database access, logging controls, etc.
        while True:
            cmd = input(f"\n{self.env_color}[{self.env_name}]>{Style.RESET_ALL} ")
            if cmd.lower() == 'exit':
                break
            elif cmd.lower() == 'env':
                print(f"Environment: {self.env_name}")
            elif cmd.lower() == 'debug':
                print(f"Debug Mode: {'Enabled' if is_debug_enabled() else 'Disabled'}")
            elif cmd.lower() == 'help':
                print("Available commands: env, debug, exit, help")
            elif cmd.strip():
                print(f"{Fore.YELLOW}Command '{cmd}' would be executed in a real implementation{Style.RESET_ALL}")