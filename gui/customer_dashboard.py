import datetime
from database.connection import DatabaseConnection
from gui.fund_transfer import FundTransfer

class CustomerDashboard:
    def __init__(self, customer_id=None):
        self.user_info = {}
        self.account_summary = {}
        self.customer_id = customer_id
        self.db = DatabaseConnection()
        self.fund_transfer = FundTransfer()

    def fetch_account_summary(self):
        """Fetch account summary from the database"""
        conn = self.db.get_connection()
        if not conn or not self.customer_id:
            print("Unable to fetch account summary.")
            return
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT account_number, account_type, balance, account_status FROM cbs_accounts WHERE customer_id = %s",
                (self.customer_id,)
            )
            accounts = cursor.fetchall()
            self.account_summary = {
                acc[0]: {
                    'type': acc[1],
                    'balance': acc[2],
                    'status': acc[3]
                } for acc in accounts
            }
        except Exception as e:
            print(f"Error fetching account summary: {e}")
        finally:
            cursor.close()
            conn.close()

    def show_account_summary(self):
        self.fetch_account_summary()
        print("\nAccount Summary:")
        if not self.account_summary:
            print("No accounts found.")
            return
        for acc_num, details in self.account_summary.items():
            print(f"Account: {acc_num} | Type: {details['type']} | Balance: {details['balance']} | Status: {details['status']}")
        self.show_recent_transactions()

    def show_recent_transactions(self, limit=5):
        """Display recent transactions for all accounts"""
        conn = self.db.get_connection()
        if not conn or not self.account_summary:
            return
        try:
            cursor = conn.cursor()
            acc_nums = tuple(self.account_summary.keys())
            if not acc_nums:
                return
            query = (
                "SELECT transaction_id, account_number, amount, transaction_type, transaction_date, transaction_status, description "
                "FROM cbs_transactions WHERE account_number IN %s "
                "ORDER BY transaction_date DESC LIMIT %s"
            )
            cursor.execute(query, (acc_nums, limit))
            transactions = cursor.fetchall()
            print("\nRecent Transactions:")
            if not transactions:
                print("No recent transactions found.")
                return
            print(f"{'ID':<15} {'Account':<15} {'Amount':<12} {'Type':<15} {'Date':<20} {'Status':<10} {'Description':<30}")
            print("-" * 120)
            for txn in transactions:
                txn_id, acc, amount, txn_type, txn_date, status, desc = txn
                print(f"{txn_id:<15} {acc:<15} {amount:<12.2f} {txn_type:<15} {txn_date.strftime('%Y-%m-%d %H:%M:%S'):<20} {status:<10} {desc[:30]:<30}")
        except Exception as e:
            print(f"Error fetching transactions: {e}")
        finally:
            cursor.close()
            conn.close()

    def update_user_info(self):
        """Update user information in the database"""
        if not self.customer_id:
            print("No customer ID set.")
            return
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
        try:
            cursor = conn.cursor()
            # Fetch current info
            cursor.execute("SELECT first_name, last_name, email, phone, address FROM cbs_customers WHERE customer_id = %s", (self.customer_id,))
            user = cursor.fetchone()
            if not user:
                print("User not found.")
                return
            first_name, last_name, email, phone, address = user
            print("Leave blank to keep current value.")
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
            print("User information updated successfully.")
        except Exception as e:
            conn.rollback()
            print(f"Error updating user info: {e}")
        finally:
            cursor.close()
            conn.close()

    def display_user_info(self):
        if not self.customer_id:
            print("No customer ID set.")
            return
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT first_name, last_name, email, phone, address FROM cbs_customers WHERE customer_id = %s", (self.customer_id,))
            user = cursor.fetchone()
            if not user:
                print("User not found.")
                return
            print("\nUser Information:")
            print(f"Name: {user[0]} {user[1]}")
            print(f"Email: {user[2]}")
            print(f"Phone: {user[3]}")
            print(f"Address: {user[4]}")
        except Exception as e:
            print(f"Error fetching user info: {e}")
        finally:
            cursor.close()
            conn.close()

    def initiate_fund_transfer(self):
        print("\nInitiating fund transfer...")
        self.fund_transfer.show(self.customer_id)

    def show(self):
        print("\n===== Core Banking System - Customer Dashboard =====")
        while True:
            print("\nPlease select an option:")
            print("1. Account Summary")
            print("2. Fund Transfer")
            print("3. User Information")
            print("4. Update User Information")
            print("5. Back to Main Menu")
            choice = input("\nEnter your choice: ")
            if choice == '1':
                self.show_account_summary()
            elif choice == '2':
                self.initiate_fund_transfer()
            elif choice == '3':
                self.display_user_info()
            elif choice == '4':
                self.update_user_info()
            elif choice == '5':
                print("Returning to main menu...")
                break
            else:
                print("Invalid choice. Please try again.")