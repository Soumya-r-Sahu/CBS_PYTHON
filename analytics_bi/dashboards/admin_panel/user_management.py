import datetime
import os
import sys
from pathlib import Path

# Use centralized import system
from utils.lib.packages import fix_path, import_module
fix_path()  # Ensures the project root is in sys.path

# Import database connection
try:
    from core_banking.database.connection import DatabaseConnection
except ImportError:
    try:
        from database.python.connection import DatabaseConnection
    except ImportError:
        # Fallback implementation if not available
        class DatabaseConnection:
            def __init__(self):
                print("Using mock database connection")
            def get_connection(self):
                return None
            def close_connection(self):
                pass

# Import ID generator
try:
    from core_banking.utils.id_generator import generate_customer_id
except ImportError:
    # Fallback implementation
    def generate_customer_id():
        import uuid
        return f"CUST{uuid.uuid4().hex[:8].upper()}"

class UserManagement:
    def __init__(self):
        self.db = DatabaseConnection()

    def show_menu(self):
        """Show user management menu"""
        print("\n===== User Management =====")
        
        while True:
            print("\n1. List Users")
            print("2. Search User")
            print("3. Create User")
            print("4. Edit User")
            print("5. Deactivate/Activate User")
            print("6. Back to Admin Dashboard")
            
            choice = input("\nEnter your choice: ")
            
            if choice == '1':
                self.list_users()
            elif choice == '2':
                self.search_user()
            elif choice == '3':
                self.create_user()
            elif choice == '4':
                self.edit_user()
            elif choice == '5':
                self.toggle_user_status()
            elif choice == '6':
                return
            else:
                print("Invalid choice. Please try again.")
    
    def list_users(self, page=1, limit=10):
        """List users with pagination"""
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
        
        try:
            cursor = conn.cursor()
            offset = (page - 1) * limit
            
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM cbs_customers")
            total = cursor.fetchone()[0] or 0
            
            if total == 0:
                print("No users found.")
                return
                
            total_pages = (total + limit - 1) // limit
            
            # Get users with pagination
            cursor.execute(
                "SELECT customer_id, first_name, last_name, email, phone, is_active "
                "FROM cbs_customers LIMIT %s OFFSET %s",
                (limit, offset)
            )
            
            users = cursor.fetchall()
            
            print(f"\n===== Users (Page {page}/{total_pages}) =====")
            print(f"{'Customer ID':<15} {'Name':<30} {'Email':<30} {'Phone':<15} {'Status':<10}")
            print("-" * 100)
            
            for user in users:
                customer_id, first_name, last_name, email, phone, is_active = user
                status = "Active" if is_active else "Inactive"
                name = f"{first_name} {last_name}" if first_name and last_name else "N/A"
                print(f"{customer_id:<15} {name:<30} {email:<30} {phone:<15} {status:<10}")
            
            print(f"\nShowing {len(users)} of {total} users")
            
            if page < total_pages:
                next_page = input("Press 'n' for next page, any other key to return: ")
                if next_page.lower() == 'n':
                    self.list_users(page + 1, limit)
            
        except Exception as e:
            print(f"Error listing users: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def search_user(self):
        """Search for a user"""
        print("\n===== Search User =====")
        search_term = input("Enter search term (customer ID, name, email, or phone): ")
        
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
        
        try:
            cursor = conn.cursor()
            
            # Search in multiple fields
            cursor.execute(
                "SELECT customer_id, first_name, last_name, email, phone, is_active "
                "FROM cbs_customers WHERE customer_id LIKE %s OR first_name LIKE %s OR "
                "last_name LIKE %s OR email LIKE %s OR phone LIKE %s",
                (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", 
                 f"%{search_term}%", f"%{search_term}%")
            )
            
            users = cursor.fetchall()
            
            if not users:
                print("No users found matching your search.")
                return
            
            print(f"\nFound {len(users)} matching users:")
            print(f"{'Customer ID':<15} {'Name':<30} {'Email':<30} {'Phone':<15} {'Status':<10}")
            print("-" * 100)
            
            for user in users:
                customer_id, first_name, last_name, email, phone, is_active = user
                status = "Active" if is_active else "Inactive"
                name = f"{first_name} {last_name}" if first_name and last_name else "N/A"
                print(f"{customer_id:<15} {name:<30} {email:<30} {phone:<15} {status:<10}")
            
            # View detailed info option
            user_id = input("\nEnter customer ID to view details (or press Enter to return): ")
            if user_id:
                self.view_user_details(user_id)
                
        except Exception as e:
            print(f"Error searching users: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def view_user_details(self, customer_id):
        """View detailed user information"""
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
        
        try:
            cursor = conn.cursor()
            
            # Get user details
            cursor.execute(
                "SELECT * FROM cbs_customers WHERE customer_id = %s",
                (customer_id,)
            )
            
            user = cursor.fetchone()
            
            if not user:
                print(f"User with ID {customer_id} not found.")
                return
            
            # Get column names
            column_names = [desc[0] for desc in cursor.description]
            
            print(f"\n===== User Details: {customer_id} =====")
            for i, value in enumerate(user):
                # Skip displaying sensitive information
                if column_names[i] in ['password_hash', 'password_salt']:
                    continue
                print(f"{column_names[i]}: {value}")
            
            # Get user accounts
            cursor.execute(
                "SELECT account_number, account_type, balance, opening_date, account_status "
                "FROM cbs_accounts WHERE customer_id = %s",
                (user[0],)  # Assuming user[0] is the internal ID
            )
            
            accounts = cursor.fetchall()
            
            if accounts:
                print("\n--- Associated Accounts ---")
                print(f"{'Account Number':<20} {'Type':<15} {'Balance':<15} {'Status':<15}")
                for account in accounts:
                    acc_num, acc_type, balance, opening_date, status = account
                    print(f"{acc_num:<20} {acc_type:<15} {balance:<15.2f} {status:<15}")
            
        except Exception as e:
            print(f"Error retrieving user details: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def create_user(self):
        """Create a new user"""
        print("\n===== Create New User =====")
        
        # Collect user information
        first_name = input("First Name: ")
        last_name = input("Last Name: ")
        email = input("Email Address: ")
        phone = input("Phone Number: ")
        address = input("Address: ")
        city = input("City: ")
        state = input("State: ")
        pin_code = input("PIN Code: ")
        
        # Generate customer ID
        customer_id = generate_customer_id() 
        
        # Connect to database
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
        
        try:
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT customer_id FROM cbs_customers WHERE email = %s", (email,))
            if cursor.fetchone():
                print("Error: A user with this email already exists.")
                return
            
            # Insert new user
            cursor.execute(
                "INSERT INTO cbs_customers (customer_id, first_name, last_name, email, phone, "
                "address, city, state, pin_code, is_active, created_at) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (customer_id, first_name, last_name, email, phone, address, city, state,
                 pin_code, True, datetime.datetime.now())
            )
            
            conn.commit()
            print(f"\nUser created successfully with Customer ID: {customer_id}")
            
        except Exception as e:
            conn.rollback()
            print(f"Error creating user: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def edit_user(self):
        """Edit an existing user"""
        print("\n===== Edit User =====")
        
        # Get user ID
        customer_id = input("Enter Customer ID to edit: ")
        
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
        
        try:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute(
                "SELECT first_name, last_name, email, phone, address, city, state, pin_code "
                "FROM cbs_customers WHERE customer_id = %s", 
                (customer_id,)
            )
            user = cursor.fetchone()
            
            if not user:
                print(f"User with ID {customer_id} not found.")
                return
            
            first_name, last_name, email, phone, address, city, state, pin_code = user
            
            print(f"\nEditing User: {customer_id}")
            print("Leave blank to keep current value")
            
            # Collect updated information
            new_first_name = input(f"First Name [{first_name}]: ") or first_name
            new_last_name = input(f"Last Name [{last_name}]: ") or last_name
            new_email = input(f"Email [{email}]: ") or email
            new_phone = input(f"Phone [{phone}]: ") or phone
            new_address = input(f"Address [{address}]: ") or address
            new_city = input(f"City [{city}]: ") or city
            new_state = input(f"State [{state}]: ") or state
            new_pin_code = input(f"PIN Code [{pin_code}]: ") or pin_code
            
            # Update user
            cursor.execute(
                "UPDATE cbs_customers SET first_name = %s, last_name = %s, email = %s, "
                "phone = %s, address = %s, city = %s, state = %s, pin_code = %s, "
                "updated_at = %s WHERE customer_id = %s",
                (new_first_name, new_last_name, new_email, new_phone, new_address,
                 new_city, new_state, new_pin_code, datetime.datetime.now(), customer_id)
            )
            
            conn.commit()
            print(f"\nUser {customer_id} updated successfully!")
            
        except Exception as e:
            conn.rollback()
            print(f"Error updating user: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def toggle_user_status(self):
        """Activate or deactivate a user"""
        print("\n===== Activate/Deactivate User =====")
        
        customer_id = input("Enter Customer ID: ")
        
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
        
        try:
            cursor = conn.cursor()
            
            # Check if user exists and get current status
            cursor.execute(
                "SELECT is_active, first_name, last_name FROM cbs_customers WHERE customer_id = %s", 
                (customer_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                print(f"User with ID {customer_id} not found.")
                return
                
            is_active, first_name, last_name = result
            
            # Ask for confirmation
            new_status = not is_active
            action = "activate" if new_status else "deactivate"
            
            print(f"User: {first_name} {last_name} ({customer_id})")
            print(f"Current status: {'Active' if is_active else 'Inactive'}")
            confirm = input(f"Are you sure you want to {action} this user? (y/n): ")
            
            if confirm.lower() != 'y':
                print("Operation cancelled.")
                return
            
            # Update status
            cursor.execute(
                "UPDATE cbs_customers SET is_active = %s, updated_at = %s WHERE customer_id = %s",
                (new_status, datetime.datetime.now(), customer_id)
            )
            conn.commit()
            
            print(f"User {customer_id} has been {'activated' if new_status else 'deactivated'} successfully.")
        
        except Exception as e:
            conn.rollback()
            print(f"Error updating user status: {e}")
        finally:
            cursor.close()
            conn.close()
            
    def generate_temp_password(self, length=10):
        """Generate a temporary password"""
        import random
        import string
        
        # Generate a random password with mixed case, digits, and special characters
        chars = string.ascii_letters + string.digits + "!@#$%^&*()"
        return ''.join(random.choice(chars) for _ in range(length))