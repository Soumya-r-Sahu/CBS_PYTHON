import datetime
from database.python.connection import DatabaseConnection
from colorama import init, Fore, Style


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
# Initialize colorama
init(autoreset=True)

class BalanceInquiry:
    def __init__(self):
        self.user_id = None
        self.account_number = None
        self.db = DatabaseConnection()

    def check_balance(self):
        if not self.account_number:
            self.account_number = input("Please enter your account number: ")
            
        conn = self.db.get_connection()
        if not conn:
            print(f"{Fore.RED}❌ Database connection failed. Please try again later.{Style.RESET_ALL}")
            return
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM cbs_accounts WHERE account_number = %s", (self.account_number,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            else:
                print(f"{Fore.YELLOW}⚠️ Account not found. Please check your account number.{Style.RESET_ALL}")
                return None
        except Exception as e:
            print(f"{Fore.RED}❌ Error retrieving balance: {e}{Style.RESET_ALL}")
            return None
        finally:
            cursor.close()
            self.db.close_connection()

    def display_balance(self):
        balance = self.check_balance()
        
        if balance is not None:
            print(f"\n{Fore.GREEN}💰 Your current balance is: Rs. {balance:.2f}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🙏 Thank you for using the ATM service.{Style.RESET_ALL}")
            
    def print_receipt(self, balance):
        print_receipt = input("Would you like a receipt? (y/n): ")
        
        if print_receipt.lower() == 'y':
            print(f"\n{Fore.CYAN}----- BALANCE INQUIRY RECEIPT -----{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📅 Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}💳 Account: {self.account_number[:6]}XXXX{Style.RESET_ALL}")
            print(f"{Fore.CYAN}💰 Balance: Rs. {balance:.2f}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}-----------------------------------{Style.RESET_ALL}\n")