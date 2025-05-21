import re
import datetime
from colorama import init, Fore, Style

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

# Import database connection after path is fixed
from database.python.common.database_operations import DatabaseConnection
from utils.lib.encryption import hash_password, verify_password

# Initialize colorama
init(autoreset=True)

class PinChange:
    def __init__(self):
        self.db = DatabaseConnection()
        self.card_number = None

    def change_pin(self):
        if not self.card_number:
            self.card_number = input("Enter your card number: ")

    def change_pin(self):
        if not self.card_number:
            self.card_number = input("Enter your card number: ")
        
        # Ask for current PIN
        current_pin = input("Enter your current PIN: ")
        
        # Validate current PIN
        if not self.validate_current_pin(current_pin):
            print(f"{Fore.RED}❌ Incorrect PIN. PIN change failed.{Style.RESET_ALL}")
            return False
        
        # Ask for and validate new PIN
        new_pin = input("Enter new PIN (4 digits): ")
        confirm_pin = input("Confirm new PIN: ")
        
        if new_pin != confirm_pin:
            print(f"{Fore.RED}❌ PINs do not match. PIN change failed.{Style.RESET_ALL}")
            return False
        
        if not self.is_valid_pin(new_pin):
            print(f"{Fore.YELLOW}⚠️ Invalid PIN format. PIN must be 4 digits and not sequential or repetitive.{Style.RESET_ALL}")
            return False
            
        if new_pin == current_pin:
            print(f"{Fore.YELLOW}⚠️ New PIN cannot be the same as the current PIN.{Style.RESET_ALL}")
            return False
        
        # Update PIN in the database
        result = self.update_pin(new_pin)
        
        if result:
            print(f"{Fore.GREEN}✅ PIN changed successfully!{Style.RESET_ALL}")
            self.print_receipt()
            return True
        else:
            print(f"{Fore.RED}❌ PIN change failed. Please try again later.{Style.RESET_ALL}")
            return False

    def validate_current_pin(self, current_pin):
        conn = self.db.get_connection()
        if not conn:
            print(f"{Fore.RED}❌ Database connection failed.{Style.RESET_ALL}")
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
                print(f"{Fore.YELLOW}⚠️ Card not found.{Style.RESET_ALL}")
                return False
                
            stored_hash, salt = result
            
            # Verify the PIN
            return verify_password(stored_hash, salt, current_pin)
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error validating PIN: {e}{Style.RESET_ALL}")
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
            print(f"{Fore.RED}❌ Error updating PIN: {e}{Style.RESET_ALL}")
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
            print(f"\n{Fore.CYAN}---------- PIN CHANGE RECEIPT ----------{Style.RESET_ALL}")
            print(f"{Fore.CYAN}📅 Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}💳 Card: XXXX-XXXX-XXXX-{self.card_number[-4:]}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}🔐 PIN successfully changed{Style.RESET_ALL}")
            print(f"{Fore.CYAN}--------------------------------------{Style.RESET_ALL}\n")