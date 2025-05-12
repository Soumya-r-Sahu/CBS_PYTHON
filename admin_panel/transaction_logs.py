import datetime
from database.connection import DatabaseConnection

class TransactionLogs:
    def __init__(self):
        self.db = DatabaseConnection()

    def show_menu(self):
        """Show transaction logs menu"""
        print("\n===== Transaction Logs =====")
        
        while True:
            print("\n1. View Recent Transactions")
            print("2. Search Transactions by Account")
            print("3. Search Transactions by Date Range")
            print("4. Filter by Transaction Type")
            print("5. Export Transaction Logs")
            print("6. Back to Admin Dashboard")
            
            choice = input("\nEnter your choice: ")
            
            if choice == '1':
                self.view_recent_logs()
            elif choice == '2':
                account = input("Enter account number: ")
                self.filter_logs_by_account(account)
            elif choice == '3':
                from_date = input("Enter start date (YYYY-MM-DD): ")
                to_date = input("Enter end date (YYYY-MM-DD): ")
                self.filter_logs_by_date(from_date, to_date)
            elif choice == '4':
                self.filter_by_transaction_type()
            elif choice == '5':
                self.export_logs()
            elif choice == '6':
                return
            else:
                print("Invalid choice. Please try again.")
    
    def view_recent_logs(self, limit=20):
        """View the most recent transaction logs"""
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT t.transaction_id, t.account_number, t.amount, t.transaction_type, "
                "t.transaction_date, t.transaction_status, t.description "
                "FROM cbs_transactions t "
                "ORDER BY t.transaction_date DESC LIMIT %s",
                (limit,)
            )
            
            logs = cursor.fetchall()
            
            if not logs:
                print("No transaction logs found.")
                return
            
            print(f"\n===== Recent Transactions (Last {limit}) =====")
            print(f"{'ID':<15} {'Account':<15} {'Amount':<12} {'Type':<15} {'Date':<20} {'Status':<10} {'Description':<30}")
            print("-" * 120)
            
            for log in logs:
                txn_id, account, amount, txn_type, txn_date, status, desc = log
                print(f"{txn_id:<15} {account:<15} {amount:<12.2f} {txn_type:<15} {txn_date.strftime('%Y-%m-%d %H:%M:%S'):<20} {status:<10} {desc[:30]:<30}")
            
        except Exception as e:
            print(f"Error retrieving transaction logs: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def filter_logs_by_account(self, account_number):
        """Filter transaction logs by account number"""
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT t.transaction_id, t.account_number, t.amount, t.transaction_type, "
                "t.transaction_date, t.transaction_status, t.description "
                "FROM cbs_transactions t "
                "WHERE t.account_number = %s "
                "ORDER BY t.transaction_date DESC",
                (account_number,)
            )
            
            logs = cursor.fetchall()
            
            if not logs:
                print(f"No transaction logs found for account {account_number}.")
                return
            
            print(f"\n===== Transactions for Account {account_number} =====")
            print(f"{'ID':<15} {'Amount':<12} {'Type':<15} {'Date':<20} {'Status':<10} {'Description':<30}")
            print("-" * 120)
            
            for log in logs:
                txn_id, account, amount, txn_type, txn_date, status, desc = log
                print(f"{txn_id:<15} {amount:<12.2f} {txn_type:<15} {txn_date.strftime('%Y-%m-%d %H:%M:%S'):<20} {status:<10} {desc[:30]:<30}")
            
        except Exception as e:
            print(f"Error retrieving transaction logs: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def filter_logs_by_date(self, from_date, to_date):
        """Filter transaction logs by date range"""
        try:
            from_date_obj = datetime.datetime.strptime(from_date, "%Y-%m-%d")
            to_date_obj = datetime.datetime.strptime(to_date, "%Y-%m-%d")
            to_date_obj = to_date_obj.replace(hour=23, minute=59, second=59)  # End of day
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            return
        
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT t.transaction_id, t.account_number, t.amount, t.transaction_type, "
                "t.transaction_date, t.transaction_status, t.description "
                "FROM cbs_transactions t "
                "WHERE t.transaction_date BETWEEN %s AND %s "
                "ORDER BY t.transaction_date DESC",
                (from_date_obj, to_date_obj)
            )
            
            logs = cursor.fetchall()
            
            if not logs:
                print(f"No transaction logs found between {from_date} and {to_date}.")
                return
            
            print(f"\n===== Transactions from {from_date} to {to_date} =====")
            print(f"{'ID':<15} {'Account':<15} {'Amount':<12} {'Type':<15} {'Date':<20} {'Status':<10} {'Description':<30}")
            print("-" * 120)
            
            for log in logs:
                txn_id, account, amount, txn_type, txn_date, status, desc = log
                print(f"{txn_id:<15} {account:<15} {amount:<12.2f} {txn_type:<15} {txn_date.strftime('%Y-%m-%d %H:%M:%S'):<20} {status:<10} {desc[:30]:<30}")
            
        except Exception as e:
            print(f"Error retrieving transaction logs: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def filter_by_transaction_type(self):
        """Filter transactions by type"""
        print("\nAvailable Transaction Types:")
        print("1. WITHDRAWAL")
        print("2. DEPOSIT")
        print("3. TRANSFER")
        print("4. PAYMENT")
        print("5. INTEREST_CREDIT")
        
        choice = input("\nSelect transaction type (1-5): ")
        
        transaction_types = {
            "1": "WITHDRAWAL",
            "2": "DEPOSIT",
            "3": "TRANSFER",
            "4": "PAYMENT",
            "5": "INTEREST_CREDIT"
        }
        
        if choice not in transaction_types:
            print("Invalid choice.")
            return
        
        transaction_type = transaction_types[choice]
        
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT t.transaction_id, t.account_number, t.amount, "
                "t.transaction_date, t.transaction_status, t.description "
                "FROM cbs_transactions t "
                "WHERE t.transaction_type = %s "
                "ORDER BY t.transaction_date DESC LIMIT 50",
                (transaction_type,)
            )
            
            logs = cursor.fetchall()
            
            if not logs:
                print(f"No {transaction_type} transactions found.")
                return
            
            print(f"\n===== {transaction_type} Transactions =====")
            print(f"{'ID':<15} {'Account':<15} {'Amount':<12} {'Date':<20} {'Status':<10} {'Description':<30}")
            print("-" * 100)
            
            for log in logs:
                txn_id, account, amount, txn_date, status, desc = log
                print(f"{txn_id:<15} {account:<15} {amount:<12.2f} {txn_date.strftime('%Y-%m-%d %H:%M:%S'):<20} {status:<10} {desc[:30]:<30}")
            
        except Exception as e:
            print(f"Error retrieving transaction logs: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def export_logs(self):
        """Export transaction logs to CSV file"""
        from_date = input("Enter start date (YYYY-MM-DD): ")
        to_date = input("Enter end date (YYYY-MM-DD): ")
        
        try:
            from_date_obj = datetime.datetime.strptime(from_date, "%Y-%m-%d")
            to_date_obj = datetime.datetime.strptime(to_date, "%Y-%m-%d")
            to_date_obj = to_date_obj.replace(hour=23, minute=59, second=59)  # End of day
        except ValueError:
            print("Invalid date format. Please use YYYY-MM-DD.")
            return
        
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT t.transaction_id, t.account_number, t.amount, t.transaction_type, "
                "t.transaction_date, t.transaction_status, t.description "
                "FROM cbs_transactions t "
                "WHERE t.transaction_date BETWEEN %s AND %s "
                "ORDER BY t.transaction_date DESC",
                (from_date_obj, to_date_obj)
            )
            
            logs = cursor.fetchall()
            
            if not logs:
                print(f"No transaction logs found between {from_date} and {to_date}.")
                return
            
            # Generate CSV filename
            filename = f"transaction_logs_{from_date}_{to_date}.csv"
            
            # Write to CSV
            with open(filename, 'w') as f:
                # Write header
                f.write("Transaction ID,Account Number,Amount,Type,Date,Status,Description\n")
                
                # Write data
                for log in logs:
                    txn_id, account, amount, txn_type, txn_date, status, desc = log
                    f.write(f"{txn_id},{account},{amount},{txn_type},{txn_date.strftime('%Y-%m-%d %H:%M:%S')},{status},\"{desc}\"\n")
            
            print(f"\nExported {len(logs)} transactions to {filename}")
            
        except Exception as e:
            print(f"Error exporting transaction logs: {e}")
        finally:
            cursor.close()
            conn.close()