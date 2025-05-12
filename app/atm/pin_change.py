import re
import datetime
from database.connection import DatabaseConnection
from app.lib.encryption import hash_password, verify_password

class PinChange:
    def __init__(self):
        self.db = DatabaseConnection()
        self.card_number = None

    def change_pin(self):
        if not self.card_number:
            self.card_number = input("Enter your card number: ")
        
        # Ask for current PIN
        current_pin = input("Enter your current PIN: ")
        
        # Validate current PIN
        if not self.validate_current_pin(current_pin):
            print("Incorrect PIN. PIN change failed.")
            return False
        
        # Ask for and validate new PIN
        new_pin = input("Enter new PIN (4 digits): ")
        confirm_pin = input("Confirm new PIN: ")
        
        if new_pin != confirm_pin:
            print("PINs do not match. PIN change failed.")
            return False
        
        if not self.is_valid_pin(new_pin):
            print("Invalid PIN format. PIN must be 4 digits and not sequential or repetitive.")
            return False
            
        if new_pin == current_pin:
            print("New PIN cannot be the same as the current PIN.")
            return False
        
        # Update PIN in the database
        result = self.update_pin(new_pin)
        
        if result:
            print("PIN changed successfully!")
            self.print_receipt()
            return True
        else:
            print("PIN change failed. Please try again later.")
            return False

    def validate_current_pin(self, current_pin):
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return False
        
        try:
            cursor = conn.cursor()
            # In a real system, we would retrieve the hashed PIN and salt
            cursor.execute(
                "SELECT pin_hash, pin_salt FROM cbs_cards WHERE card_number = %s",
                (self.card_number,)
            )
            result = cursor.fetchone()
            
            if not result:
                print("Card not found.")
                return False
                
            stored_hash, salt = result
            
            # Verify the PIN
            return verify_password(stored_hash, salt, current_pin)
            
        except Exception as e:
            print(f"Error validating PIN: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def update_pin(self, new_pin):
        conn = self.db.get_connection()
        if not conn:
            return False
        
        try:
            # Hash the new PIN
            pin_hash, salt = hash_password(new_pin)
            
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE cbs_cards SET pin_hash = %s, pin_salt = %s, updated_at = %s WHERE card_number = %s",
                (pin_hash, salt, datetime.datetime.now(), self.card_number)
            )
            conn.commit()
            
            # Record the PIN change event for security
            cursor.execute(
                "INSERT INTO cbs_security_events (event_type, user_id, event_date, details) "
                "VALUES (%s, %s, %s, %s)",
                ("PIN_CHANGE", self.card_number, datetime.datetime.now(), "PIN changed via ATM")
            )
            conn.commit()
            
            return True
        except Exception as e:
            conn.rollback()
            print(f"Error updating PIN: {e}")
            return False
        finally:
            cursor.close()
            conn.close()

    def is_valid_pin(self, pin):
        # Check if PIN is 4 digits
        if not re.match(r'^\d{4}$', pin):
            return False
        
        # Check if PIN is sequential (e.g., 1234, 9876)
        sequential_patterns = ['0123', '1234', '2345', '3456', '4567', '5678', '6789',
                              '9876', '8765', '7654', '6543', '5432', '4321', '3210']
        if any(pattern in pin for pattern in sequential_patterns):
            return False
        
        # Check if PIN has repeating digits (e.g., 1111, 2222)
        if pin[0] * 4 == pin:
            return False
        
        return True
        
    def print_receipt(self):
        print_receipt = input("Would you like a receipt for this PIN change? (y/n): ")
        
        if print_receipt.lower() == 'y':
            print("\n---------- PIN CHANGE RECEIPT ----------")
            print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Card: XXXX-XXXX-XXXX-{self.card_number[-4:]}")
            print("PIN successfully changed")
            print("--------------------------------------\n")