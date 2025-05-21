import re
import datetime
import random
import string
try:
    from database.python.common.database_operations import DatabaseConnection
except ImportError:
    # Fallback implementation
    class DatabaseConnection:
        def __init__(self):
            print("Using mock database connection")
        def get_connection(self):
            return None
        def close_connection(self):
            pass
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

class UpiRegistration:
    def __init__(self):
        self.db = DatabaseConnection()
        self.user_id = None
        self.account_number = None
        self.status = "PENDING"

    def register(self):
        """Main method to register UPI"""
        print(f"{Fore.CYAN}📋 ===== UPI Registration ====={Style.RESET_ALL}")
        
        # Get customer information
        account_number = input("Enter your account number: ")
        mobile_number = input("Enter your mobile number: ")
        
        # Validate account
        if not self.validate_account(account_number, mobile_number):
            return
            
        # Set the account number
        self.account_number = account_number
        
        # Generate UPI ID
        upi_id = self.generate_upi_id()
        
        # Set UPI PIN
        upi_pin = self.set_upi_pin()
        
        if not upi_pin:
            return
        
        # Complete registration
        if self.complete_registration(upi_id, upi_pin):
            print(f"{Fore.GREEN}🎉 UPI registration successful!{Style.RESET_ALL}")
            print(f"{Fore.CYAN}🆔 Your UPI ID: {upi_id}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}🔒 Please keep your UPI PIN confidential.{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}❌ UPI registration failed. Please try again later.{Style.RESET_ALL}")
    
    def validate_account(self, account_number, mobile_number):
        """Validate account details"""
        conn = self.db.get_connection()
        if not conn:
            print(f"{Fore.RED}❌ Database connection failed.{Style.RESET_ALL}")
            return False
        
        try:
            cursor = conn.cursor()
            
            # Check if account exists
            cursor.execute(
                "SELECT c.customer_id, c.phone FROM cbs_accounts a "
                "JOIN cbs_customers c ON a.customer_id = c.id "
                "WHERE a.account_number = %s",
                (account_number,)
            )
            
            result = cursor.fetchone()
            
            if not result:
                print(f"{Fore.RED}❌ Account not found. Please check your account number.{Style.RESET_ALL}")
                return False
            
            self.user_id, registered_mobile = result
            
            # Validate mobile number
            if not registered_mobile or not registered_mobile.endswith(mobile_number[-10:]):
                print(f"{Fore.RED}❌ Mobile number does not match the registered number for this account.{Style.RESET_ALL}")
                return False
            
            # Check if UPI already registered
            cursor.execute(
                "SELECT upi_id FROM cbs_upi_registrations WHERE account_number = %s AND is_active = TRUE",
                (account_number,)
            )
            
            existing_upi = cursor.fetchone()
            if existing_upi:
                print(f"{Fore.YELLOW}This account is already linked to UPI ID: {existing_upi[0]}{Style.RESET_ALL}")
                return False
            
            return True
            
        except Exception as e:
            print(f"{Fore.RED}Error validating account: {e}{Style.RESET_ALL}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def generate_upi_id(self):
        """Generate UPI ID"""
        # Get account holder name
        conn = self.db.get_connection()
        first_name = ""
        
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT first_name FROM cbs_customers WHERE id = %s",
                    (self.user_id,)
                )
                result = cursor.fetchone()
                if result:
                    first_name = result[0].lower()
            except Exception:
                pass
            finally:
                cursor.close()
                conn.close()
        
        # If no name found, use a random string
        if not first_name:
            first_name = ''.join(random.choices(string.ascii_lowercase, k=5))
        
        # Make sure the name is suitable for UPI ID (alphanumeric only)
        first_name = re.sub(r'[^a-z0-9]', '', first_name)
        
        # Generate a random number suffix if the name is too short
        if len(first_name) < 3:
            first_name += ''.join(random.choices(string.digits, k=3))
        
        # Add a random numeric suffix to ensure uniqueness
        random_suffix = ''.join(random.choices(string.digits, k=3))
        
        # Format: name@bank (e.g., john@sbi)
        upi_id = f"{first_name}{random_suffix}@sbi"
        
        return upi_id
    
    def set_upi_pin(self):
        """Set UPI PIN"""
        print(f"\n{Fore.CYAN}Set your 6-digit UPI PIN{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Your UPI PIN will be used to authenticate transactions.{Style.RESET_ALL}")
        
        while True:
            upi_pin = input("Enter 6-digit PIN: ")
            
            if not re.match(r'^\d{6}$', upi_pin):
                print(f"{Fore.RED}PIN must be 6 digits.{Style.RESET_ALL}")
                continue
                
            confirm_pin = input("Confirm PIN: ")
            
            if upi_pin != confirm_pin:
                print(f"{Fore.RED}PINs do not match. Please try again.{Style.RESET_ALL}")
                continue
                
            # PIN validation
            if self.is_weak_pin(upi_pin):
                print(f"{Fore.RED}PIN is too weak. Avoid sequential or repetitive numbers.{Style.RESET_ALL}")
                continue
                
            return upi_pin
    
    def is_weak_pin(self, pin):
        """Check if PIN is weak"""
        # Check for sequential numbers (e.g., 123456, 654321)
        if pin in ['123456', '234567', '345678', '456789', 
                   '987654', '876543', '765432', '654321']:
            return True
            
        # Check for repetitive digits (e.g., 111111, 222222)
        if len(set(pin)) == 1:
            return True
            
        # Check for common PINs
        common_pins = ['000000', '111111', '222222', '333333', '444444', 
                      '555555', '666666', '777777', '888888', '999999', 
                      '123123', '456456', '789789', '159159', '147147']
        if pin in common_pins:
            return True
            
        return False
    
    def complete_registration(self, upi_id, upi_pin):
        """Complete UPI registration"""
        conn = self.db.get_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
              # Hash PIN (in production, use proper encryption)
            try:
                from app.lib.encryption import hash_password
            except ImportError:
                # Fallback if module not available
                def hash_password(password):
                    # Not secure, just for development!
                    import hashlib
                    salt = "development_salt"
                    hash_value = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
                    return hash_value, salt
            
            pin_hash, pin_salt = hash_password(upi_pin)
            
            # Register UPI
            cursor.execute(
                "INSERT INTO cbs_upi_registrations "
                "(customer_id, account_number, upi_id, pin_hash, pin_salt, is_active, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (self.user_id, self.account_number, upi_id, pin_hash, pin_salt, 
                 True, datetime.datetime.now())
            )
            
            conn.commit()
            self.status = "REGISTERED"
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"{Fore.RED}Error completing registration: {e}{Style.RESET_ALL}")
            return False
        finally:
            cursor.close()
            conn.close()
    
    def get_status(self):
        """Get UPI registration status"""
        return self.status
    
    def unlink_upi(self, upi_id):
        """Unlink UPI ID from account"""
        conn = self.db.get_connection()
        if not conn:
            print(f"{Fore.RED}❌ Database connection failed.{Style.RESET_ALL}")
            return False
        
        try:
            cursor = conn.cursor()
            
            # Verify UPI ID exists
            cursor.execute(
                "SELECT customer_id, account_number FROM cbs_upi_registrations "
                "WHERE upi_id = %s AND is_active = TRUE",
                (upi_id,)
            )
            
            result = cursor.fetchone()
            if not result:
                print(f"{Fore.RED}UPI ID {upi_id} not found or already deactivated.{Style.RESET_ALL}")
                return False
                
            # Update status
            cursor.execute(
                "UPDATE cbs_upi_registrations SET is_active = FALSE, updated_at = %s "
                "WHERE upi_id = %s",
                (datetime.datetime.now(), upi_id)
            )
            
            conn.commit()
            self.status = "UNLINKED"
            
            print(f"{Fore.GREEN}UPI ID {upi_id} has been deactivated successfully.{Style.RESET_ALL}")
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"{Fore.RED}Error unlinking UPI: {e}{Style.RESET_ALL}")
            return False
        finally:
            cursor.close()
            conn.close()