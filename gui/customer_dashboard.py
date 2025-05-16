import datetime
import os
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
from gui.fund_transfer import FundTransfer
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

# Try to import environment module
try:
    
# Import with fallback for backward compatibility
try:
    from utils.config.environment import get_environment_name, is_production, is_development, is_test
except ImportError:
    # Fallback to old import path
    from app.config.environment import get_environment_name, is_production, is_development, is_test

    
# Import with fallback for backward compatibility
try:
    from utils.config.environment import Environment
except ImportError:
    # Fallback to old import path
    from app.config.environment import Environment


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
except ImportError:
    # Fallback environment detection
    env_str = os.environ.get("CBS_ENVIRONMENT", "development").lower()
    def is_production(): return env_str == "production"
    def is_development(): return env_str == "development"
    def is_test(): return env_str == "test"
    def get_environment_name(): return env_str.capitalize()

class CustomerDashboard:
    def __init__(self, customer_id=None):
        self.user_info = {}
        self.account_summary = {}
        self.customer_id = customer_id
        self.db = DatabaseConnection()
        self.fund_transfer = FundTransfer()
        
        # Environment-specific settings
        self.env_name = get_environment_name()
        
        # Set environment-specific colors
        if is_production():
            self.env_color = Fore.GREEN
            self.show_env_info = False
        elif is_test():
            self.env_color = Fore.YELLOW
            self.show_env_info = True
        else:  # development
            self.env_color = Fore.BLUE
            self.show_env_info = True

    def fetch_account_summary(self):
        """Fetch account summary from the database with optimized query"""
        conn = self.db.get_connection()
        if not conn or not self.customer_id:
            print(f"{Fore.YELLOW}📊 Unable to fetch account summary.{Style.RESET_ALL}")
            return
        try:
            cursor = conn.cursor(dictionary=True)  # Use dictionary cursor to avoid manual mapping
            cursor.execute(
                "SELECT account_number, account_type, balance, account_status FROM cbs_accounts WHERE customer_id = %s",
                (self.customer_id,)
            )
            self.account_summary = cursor.fetchall()
        except Exception as e:
            print(f"{Fore.RED}❌ Error fetching account summary: {e}{Style.RESET_ALL}")
        finally:
            cursor.close()
            conn.close()

    def show_account_summary(self):
        self.fetch_account_summary()
        print(f"\n{Fore.CYAN}Account Summary:{Style.RESET_ALL}")
        if not self.account_summary:
            print(f"{Fore.YELLOW}📊 No accounts found.{Style.RESET_ALL}")
            return
        for acc in self.account_summary:
            print(f"{Fore.CYAN}📊 Account: {acc['account_number']} | Type: {acc['account_type']} | Balance: {Fore.GREEN}₹{acc['balance']}{Fore.CYAN} | Status: {acc['account_status']}{Style.RESET_ALL}")
        self.show_recent_transactions()

    def show_recent_transactions(self, limit=5):
        """Display recent transactions for all accounts"""
        conn = self.db.get_connection()
        if not conn or not self.account_summary:
            return
        try:
            cursor = conn.cursor()
            acc_nums = tuple(acc['account_number'] for acc in self.account_summary)
            if not acc_nums:
                return
            query = (
                "SELECT transaction_id, account_number, amount, transaction_type, transaction_date, transaction_status, description "
                "FROM cbs_transactions WHERE account_number IN %s "
                "ORDER BY transaction_date DESC LIMIT %s"
            )
            cursor.execute(query, (acc_nums, limit))
            transactions = cursor.fetchall()
            print(f"\n{Fore.CYAN}📊 Recent Transactions:{Style.RESET_ALL}")
            if not transactions:
                print(f"{Fore.YELLOW}📊 No recent transactions found.{Style.RESET_ALL}")
                return
            print(f"{Fore.CYAN}{'ID':<15} {'Account':<15} {'Amount':<12} {'Type':<15} {'Date':<20} {'Status':<10} {'Description':<30}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'-' * 120}{Style.RESET_ALL}")
            for txn in transactions:
                txn_id, acc, amount, txn_type, txn_date, status, desc = txn
                # Use different colors based on transaction type
                amount_color = Fore.GREEN if txn_type == "CREDIT" else Fore.RED
                print(f"{Fore.CYAN}{txn_id:<15} {acc:<15} {amount_color}{amount:<12.2f}{Fore.CYAN} {txn_type:<15} {txn_date.strftime('%Y-%m-%d %H:%M:%S'):<20} {status:<10} {desc[:30]:<30}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Error fetching transactions: {e}{Style.RESET_ALL}")
        finally:
            cursor.close()
            conn.close()

    def update_user_info(self):
        """Update user information in the database"""
        if not self.customer_id:
            print(f"{Fore.YELLOW}⚠️ No customer ID set.{Style.RESET_ALL}")
            return
        conn = self.db.get_connection()
        if not conn:
            print(f"{Fore.RED}❌ Database connection failed.{Style.RESET_ALL}")
            return
        try:
            cursor = conn.cursor()
            # Fetch current info
            cursor.execute("SELECT first_name, last_name, email, phone, address FROM cbs_customers WHERE customer_id = %s", (self.customer_id,))
            user = cursor.fetchone()
            if not user:
                print(f"{Fore.YELLOW}⚠️ User not found.{Style.RESET_ALL}")
                return
            first_name, last_name, email, phone, address = user
            print(f"{Fore.CYAN}ℹ️ Leave blank to keep current value.{Style.RESET_ALL}")
            new_first_name = input(f"First Name [{first_name}]: ") or first_name
            new_last_name = input(f"Last Name [{last_name}]: ") or last_name
            new_email = input(f"Email [{email}]: ") or email
            new_phone = input(f"Phone [{phone}]: ") or phone
            new_address = input(f"Address [{address}]: ") or address
            cursor.execute(
                "UPDATE cbs_customers SET first_name=%s, last_name=%s, email=%s, phone=%s, address=%s, updated_at=%s WHERE customer_id=%s",
                (new_first_name, new_last_name, new_email, new_phone, new_address, datetime.datetime.now(), self.customer_id)
            )
            conn.commit()
            print(f"{Fore.GREEN}✅ User information updated successfully.{Style.RESET_ALL}")
        except Exception as e:
            conn.rollback()
            print(f"{Fore.RED}❌ Error updating user info: {e}{Style.RESET_ALL}")
        finally:
            cursor.close()
            conn.close()

    def display_user_info(self):
        if not self.customer_id:
            print(f"{Fore.YELLOW}⚠️ No customer ID set.{Style.RESET_ALL}")
            return
        conn = self.db.get_connection()
        if not conn:
            print(f"{Fore.RED}❌ Database connection failed.{Style.RESET_ALL}")
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT first_name, last_name, email, phone, address FROM cbs_customers WHERE customer_id = %s", (self.customer_id,))
            user = cursor.fetchone()
            if not user:
                print(f"{Fore.YELLOW}⚠️ User not found.{Style.RESET_ALL}")
                return
            print(f"\n{Fore.CYAN}👤 User Information:{Style.RESET_ALL}")
            print(f"{Fore.CYAN}👤 Name: {user[0]} {user[1]}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📧 Email: {user[2]}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📞 Phone: {user[3]}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🏠 Address: {user[4]}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Error fetching user info: {e}{Style.RESET_ALL}")
        finally:
            cursor.close()
            conn.close()

    def initiate_fund_transfer(self):
        print(f"\n{Fore.YELLOW}💸 Initiating fund transfer...{Style.RESET_ALL}")
        self.fund_transfer.show(self.customer_id)

    def show(self):
        """Display the customer dashboard with environment awareness"""
        # Show environment banner if not in production or if explicitly enabled
        if not is_production() or self.show_env_info:
            env_banner = f"""
{self.env_color}╔════════════════════════════════════════════════════╗
║ CORE BANKING SYSTEM - CUSTOMER DASHBOARD           ║
║ Environment: {self.env_name.ljust(20)}                   ║
╚════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""
            print(env_banner)
        
        print(f"\n{Fore.CYAN}===== Core Banking System - Customer Dashboard ====={Style.RESET_ALL}")
        
        # Add environment-specific notifications
        if is_test():
            print(f"\n{Fore.YELLOW}⚠️ TEST ENVIRONMENT: Data shown is for testing purposes only{Style.RESET_ALL}")
        elif is_development():
            print(f"\n{Fore.BLUE}ℹ️ DEVELOPMENT ENVIRONMENT: Using development database{Style.RESET_ALL}")
        
        while True:
            print(f"\n{Fore.CYAN}Please select an option:{Style.RESET_ALL}")
            print(f"{Fore.GREEN}1. 📊 Account Summary{Style.RESET_ALL}")
            print(f"{Fore.GREEN}2. 💸 Fund Transfer{Style.RESET_ALL}")
            print(f"{Fore.GREEN}3. 👤 User Information{Style.RESET_ALL}")
            print(f"{Fore.GREEN}4. ✏️ Update User Information{Style.RESET_ALL}")
            print(f"{Fore.GREEN}5. 🔙 Back to Main Menu{Style.RESET_ALL}")
            
            # Only show environment info option in non-production environments
            if not is_production():
                print(f"{self.env_color}6. 🔍 Environment Information{Style.RESET_ALL}")
            
            choice = input(f"\nEnter your choice: ")
            if choice == '1':
                self.show_account_summary()
            elif choice == '2':
                self.initiate_fund_transfer()
            elif choice == '3':
                self.display_user_info()
            elif choice == '4':
                self.update_user_info()
            elif choice == '5':
                print(f"{Fore.CYAN}🔙 Returning to main menu...{Style.RESET_ALL}")
                break
            elif choice == '6' and not is_production():
                self.show_environment_info()
            else:
                print(f"{Fore.RED}❌ Invalid choice. Please try again.{Style.RESET_ALL}")
                
    def show_environment_info(self):
        """Display detailed environment information"""
        print(f"\n{self.env_color}===== Environment Information ====={Style.RESET_ALL}")
        print(f"Environment: {self.env_color}{self.env_name}{Style.RESET_ALL}")
        
        # Database connection info
        try:
            conn = self.db.get_connection()
            if conn:
                print(f"Database connected: {Fore.GREEN}✓{Style.RESET_ALL}")
                # Get database version - safely handling different database types
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()
                    print(f"Database version: {version[0] if version else 'Unknown'}")
                    cursor.close()
                except:
                    print("Database version: Unable to retrieve")
                conn.close()
            else:
                print(f"Database connected: {Fore.RED}✗{Style.RESET_ALL}")
        except Exception as e:
            print(f"Database error: {str(e)}")
        
        # Environment-specific behaviors
        print("\nEnvironment-specific behaviors:")
        if is_test():
            print(f"{Fore.YELLOW}• Test accounts are used{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}• Transactions are not processed against real accounts{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}• Emails and SMS notifications are disabled{Style.RESET_ALL}")
        elif is_development():
            print(f"{Fore.BLUE}• Development database is used{Style.RESET_ALL}")
            print(f"{Fore.BLUE}• Debug logging is enabled{Style.RESET_ALL}")
            print(f"{Fore.BLUE}• Emails and SMS are sent to test recipients only{Style.RESET_ALL}")
        
        input("\nPress Enter to continue...")