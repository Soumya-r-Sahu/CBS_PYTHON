# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

class FundTransfer:
    def __init__(self, user):
        self.user = user

    def transfer_funds(self, recipient_account, amount):
        if self.validate_transfer(recipient_account, amount):
            # Logic to perform the fund transfer
            print(f"Transferring {amount} from {self.user['account_number']} to {recipient_account}.")
            # Update balances and log the transaction
            self.update_balances(recipient_account, amount)
            self.log_transaction(recipient_account, amount)
            print("Transfer successful.")
        else:
            print("Transfer failed. Please check the details.")

    def validate_transfer(self, recipient_account, amount):
        # Validate the recipient account and amount
        if amount <= 0:
            print("Amount must be greater than zero.")
            return False
        # Additional validation logic can be added here
        return True

    def update_balances(self, recipient_account, amount):
        # Logic to update the balances of both accounts
        pass

    def log_transaction(self, recipient_account, amount):
        # Logic to log the transaction details
        pass