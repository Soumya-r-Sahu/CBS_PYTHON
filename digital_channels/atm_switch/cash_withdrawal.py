import datetime
# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

# Import database connection after path is fixed
from database.python.connection import DatabaseConnection
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

class CashWithdrawal:
    def __init__(self):
        self.db = DatabaseConnection()
        self.account_number = None
        self.card_number = None

    def process_withdrawal(self):
        # Get account information if not already provided
        if not self.account_number:
            self.account_number = input("Enter your account number: ")
        
        # Connect to database
        conn = self.db.get_connection()
        if not conn:
            print(f"{Fore.RED}❌ Database connection failed. Please try again later.{Style.RESET_ALL}")
            return
        
        try:
            # Get current balance
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM cbs_accounts WHERE account_number = %s", (self.account_number,))
            result = cursor.fetchone()
            
            if not result:
                print(f"{Fore.YELLOW}⚠️ Account not found. Please check your account number.{Style.RESET_ALL}")
                return
            
            current_balance = result[0]
            print(f"{Fore.CYAN}💰 Your current balance is: Rs. {current_balance:.2f}{Style.RESET_ALL}")
            
            # Get withdrawal amount
            amount = float(input("Enter withdrawal amount: "))
              # Validate withdrawal amount
            if self.validate_withdrawal(amount, current_balance):
                # Process withdrawal
                self.withdraw(amount, current_balance, cursor, conn)
        except ValueError:
            print(f"{Fore.YELLOW}⚠️ Invalid amount. Please enter a numeric value.{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Error processing withdrawal: {e}{Style.RESET_ALL}")
        finally:
            conn.close()
    
    def validate_withdrawal(self, amount, current_balance):
        if amount <= 0:
            print(f"{Fore.YELLOW}⚠️ Invalid amount. Please enter a positive value.{Style.RESET_ALL}")
            return False
        
        if amount > current_balance:
            print(f"{Fore.YELLOW}⚠️ Insufficient balance.{Style.RESET_ALL}")
            return False
        
        # Daily withdrawal limit check (e.g., Rs. 25,000)
        daily_limit = 25000
        if amount > daily_limit:
            print(f"{Fore.YELLOW}⚠️ Amount exceeds daily withdrawal limit of Rs. {daily_limit}.{Style.RESET_ALL}")
            return False
        
        # Denomination check (ATM usually dispenses in multiples of 100)
        if amount % 100 != 0:
            print(f"{Fore.YELLOW}⚠️ Please enter amount in multiples of 100.{Style.RESET_ALL}")
            return False
        
        return True
    
    def withdraw(self, amount, current_balance, cursor, conn):
        try:
            # Update account balance
            new_balance = current_balance - amount
            cursor.execute(
                "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
                (new_balance, self.account_number)
            )
            
            # Record the transaction
            transaction_id = self.record_transaction(amount, cursor)
            
            # Commit the transaction
            conn.commit()
            
            print(f"\n{Fore.GREEN}✅ Withdrawal successful!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}💸 Amount withdrawn: Rs. {amount:.2f}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}💰 New balance: Rs. {new_balance:.2f}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🆔 Transaction ID: {transaction_id}{Style.RESET_ALL}")
            
            # Ask for receipt
            self.print_receipt(amount, new_balance, transaction_id)
            
        except Exception as e:
            conn.rollback()
            print(f"{Fore.RED}❌ Error processing withdrawal: {e}{Style.RESET_ALL}")
    
    def record_transaction(self, amount, cursor):
        # Generate transaction ID (simple implementation)
        transaction_id = f"TXN{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Record transaction in database
        cursor.execute(
            "INSERT INTO cbs_transactions (transaction_id, account_number, amount, transaction_type, transaction_date) "
            "VALUES (%s, %s, %s, %s, %s)",
            (transaction_id, self.account_number, amount, "WITHDRAWAL", datetime.datetime.now())
        )
        
        return transaction_id
    
    def print_receipt(self, amount, new_balance, transaction_id):
        print_receipt = input("Would you like a receipt? (y/n): ")
        
        if print_receipt.lower() == 'y':
            print(f"\n{Fore.CYAN}---------- ATM WITHDRAWAL ----------{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📅 Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🆔 Transaction ID: {transaction_id}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}💳 Account: {self.account_number[:6]}XXXX{Style.RESET_ALL}")
            print(f"{Fore.CYAN}💸 Amount withdrawn: Rs. {amount:.2f}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}💰 Available balance: Rs. {new_balance:.2f}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}------------------------------------{Style.RESET_ALL}\n")