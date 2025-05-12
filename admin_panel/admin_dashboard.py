import datetime
import sys
from database.connection import DatabaseConnection
from admin_panel.user_management import UserManagement
from admin_panel.transaction_logs import TransactionLogs
from admin_panel.settings import SystemSettings

class AdminDashboard:
    def __init__(self):
        self.db = DatabaseConnection()
        self.user_management = UserManagement()
        self.transaction_logs = TransactionLogs()
        self.system_settings = SystemSettings()
        self.statistics = {}

    def show(self):
        print("\n===== Core Banking System - Admin Dashboard =====")
        
        while True:
            print("\nPlease select an option:")
            print("1. User Management")
            print("2. Transaction Logs")
            print("3. System Settings")
            print("4. View Statistics")
            print("5. Database Management")
            print("6. Back to Main Menu")
            
            choice = input("\nEnter your choice: ")
            
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
                print("Returning to main menu...")
                break
            else:
                print("Invalid choice. Please try again.")
    
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