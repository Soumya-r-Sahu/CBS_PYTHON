class AccountSummary:
    def __init__(self, user_id, database_connection):
        self.user_id = user_id
        self.database_connection = database_connection

    def get_account_summary(self):
        query = "SELECT account_number, account_type, balance FROM Users WHERE user_id = ?"
        cursor = self.database_connection.cursor()
        cursor.execute(query, (self.user_id,))
        account_info = cursor.fetchone()
        cursor.close()
        
        if account_info:
            return {
                "account_number": account_info[0],
                "account_type": account_info[1],
                "balance": account_info[2]
            }
        else:
            return None

    def display_summary(self):
        summary = self.get_account_summary()
        if summary:
            print("Account Summary:")
            print(f"Account Number: {summary['account_number']}")
            print(f"Account Type: {summary['account_type']}")
            print(f"Balance: {summary['balance']}")
        else:
            print("No account found for the given user ID.")