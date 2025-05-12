import datetime
from database.connection import DatabaseConnection

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
            print("Database connection failed. Please try again later.")
            return
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM cbs_accounts WHERE account_number = %s", (self.account_number,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            else:
                print("Account not found. Please check your account number.")
                return None
        except Exception as e:
            print(f"Error retrieving balance: {e}")
            return None
        finally:
            cursor.close()
            self.db.close_connection()

    def display_balance(self):
        balance = self.check_balance()
        
        if balance is not None:
            print(f"\nYour current balance is: Rs. {balance:.2f}")
            print("Thank you for using the ATM service.")
            
    def print_receipt(self, balance):
        print_receipt = input("Would you like a receipt? (y/n): ")
        
        if print_receipt.lower() == 'y':
            print("\n----- BALANCE INQUIRY RECEIPT -----")
            print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Account: {self.account_number[:6]}XXXX")
            print(f"Balance: Rs. {balance:.2f}")
            print("-----------------------------------\n")