import datetime
from database.connection import DatabaseConnection

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
            print("Database connection failed. Please try again later.")
            return
        
        try:
            # Get current balance
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM cbs_accounts WHERE account_number = %s", (self.account_number,))
            result = cursor.fetchone()
            
            if not result:
                print("Account not found. Please check your account number.")
                return
            
            current_balance = result[0]
            print(f"Your current balance is: Rs. {current_balance:.2f}")
            
            # Get withdrawal amount
            amount = float(input("Enter withdrawal amount: "))
            
            # Validate withdrawal amount
            if self.validate_withdrawal(amount, current_balance):
                # Process withdrawal
                self.withdraw(amount, current_balance, cursor, conn)
        except ValueError:
            print("Invalid amount. Please enter a numeric value.")
        except Exception as e:
            print(f"Error processing withdrawal: {e}")
        finally:
            conn.close()
    
    def validate_withdrawal(self, amount, current_balance):
        if amount <= 0:
            print("Invalid amount. Please enter a positive value.")
            return False
        
        if amount > current_balance:
            print("Insufficient balance.")
            return False
        
        # Daily withdrawal limit check (e.g., Rs. 25,000)
        daily_limit = 25000
        if amount > daily_limit:
            print(f"Amount exceeds daily withdrawal limit of Rs. {daily_limit}.")
            return False
        
        # Denomination check (ATM usually dispenses in multiples of 100)
        if amount % 100 != 0:
            print("Please enter amount in multiples of 100.")
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
            
            print(f"\nWithdrawal successful!")
            print(f"Amount withdrawn: Rs. {amount:.2f}")
            print(f"New balance: Rs. {new_balance:.2f}")
            print(f"Transaction ID: {transaction_id}")
            
            # Ask for receipt
            self.print_receipt(amount, new_balance, transaction_id)
            
        except Exception as e:
            conn.rollback()
            print(f"Error processing withdrawal: {e}")
    
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
            print("\n---------- ATM WITHDRAWAL ----------")
            print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Transaction ID: {transaction_id}")
            print(f"Account: {self.account_number[:6]}XXXX")
            print(f"Amount withdrawn: Rs. {amount:.2f}")
            print(f"Available balance: Rs. {new_balance:.2f}")
            print("------------------------------------\n")