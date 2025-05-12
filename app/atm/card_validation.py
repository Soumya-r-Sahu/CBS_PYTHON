class CardValidation:
    def __init__(self):
        self.card_number = None
        self.pin = None

    def validate_card(self, card_number=None, pin=None):
        if card_number:
            self.card_number = card_number
        if pin:
            self.pin = pin
            
        if not self.card_number or not self.pin:
            print("Please enter both card number and PIN")
            self.prompt_for_credentials()
            
        if self.is_card_number_valid() and self.is_pin_valid():
            print("Card validation successful")
            return True
        else:
            print("Card validation failed. Please check your card number and PIN.")
            return False
            
    def prompt_for_credentials(self):
        self.card_number = input("Enter your card number: ")
        self.pin = input("Enter your PIN: ")

    def is_card_number_valid(self):
        # Implement card number validation logic (e.g., Luhn algorithm)
        return len(self.card_number) == 16 and self.card_number.isdigit()

    def is_pin_valid(self):
        # Implement PIN validation logic (e.g., check length and digits)
        return len(self.pin) == 4 and self.pin.isdigit()