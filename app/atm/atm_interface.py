# Import necessary components
from app.atm.card_validation import CardValidation
from app.atm.cash_withdrawal import CashWithdrawal
from app.atm.balance_inquiry import BalanceInquiry
from app.atm.pin_change import PinChange

class AtmInterface:
    def __init__(self):
        self.card_validator = CardValidation()
        self.cash_withdrawal = CashWithdrawal()
        self.balance_inquiry = BalanceInquiry()
        self.pin_change = PinChange()

    def start(self):
        print("Welcome to the ATM Interface (GUI mode coming soon)")
        # TODO: Replace this CLI with a PyQt5-based GUI for ATM operations
        while True:
            print("\nPlease select an option:")
            print("1. Cash Withdrawal")
            print("2. Balance Inquiry")
            print("3. Change PIN")
            print("4. Exit")

            choice = input("Enter your choice: ")

            if choice == '1':
                self.cash_withdrawal.process_withdrawal()
            elif choice == '2':
                self.balance_inquiry.check_balance()
            elif choice == '3':
                self.pin_change.change_pin()
            elif choice == '4':
                print("Thank you for using the ATM. Goodbye!")
                break
            else:
                print("Invalid choice. Please try again.")