import os
import json
from database.python.connection import DatabaseConnection

class SystemSettings:
    def __init__(self):
        self.db = DatabaseConnection()
        self.settings_path = os.path.join(os.path.dirname(__file__), '..', 'app', 'config', 'settings.yaml')
        self.configurations = {
            "max_login_attempts": 5,
            "session_timeout": 30,  # in minutes
            "enable_logging": True,
            "log_level": "INFO",
            "admin_email": "admin@example.com",
            "notification_enabled": True,
            "backup_schedule": "DAILY",
            "maintenance_mode": False,
            "interest_rate_savings": 3.5,
            "interest_rate_current": 0.0,
            "interest_rate_fixed": 5.5,
            "min_balance_savings": 1000,
            "min_balance_current": 5000,
            "transaction_fee": 0.0,
        }
        
        # Load settings from database if available
        self._load_settings_from_db()

    def show_menu(self):
        """Show settings menu"""
        print("\n===== System Settings =====")
        
        while True:
            print("\n1. View All Settings")
            print("2. Edit Setting")
            print("3. Import Settings")
            print("4. Export Settings")
            print("5. Reset to Default")
            print("6. Back to Admin Dashboard")
            
            choice = input("\nEnter your choice: ")
            
            if choice == '1':
                self.display_settings()
            elif choice == '2':
                self.edit_setting()
            elif choice == '3':
                self.import_settings()
            elif choice == '4':
                self.export_settings()
            elif choice == '5':
                self.reset_to_default()
            elif choice == '6':
                return
            else:
                print("Invalid choice. Please try again.")
    
    def _load_settings_from_db(self):
        """Load settings from database"""
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed. Using default settings.")
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT setting_key, setting_value, value_type FROM cbs_system_settings")
            
            rows = cursor.fetchall()
            
            for row in rows:
                key, value, value_type = row
                
                # Convert value to appropriate type based on value_type
                if value_type == 'int':
                    value = int(value)
                elif value_type == 'float':
                    value = float(value)
                elif value_type == 'bool':
                    value = (value.lower() == 'true')
                
                # Update configuration
                self.configurations[key] = value
            
        except Exception as e:
            print(f"Error loading settings from database: {e}")
        finally:
            cursor.close()
            conn.close()
    
    def get_setting(self, key):
        """Get value of a specific setting"""
        return self.configurations.get(key, None)

    def set_setting(self, key, value):
        """Set value of a specific setting"""
        if key in self.configurations:
            old_value = self.configurations[key]
            self.configurations[key] = value
            
            # Save to database
            conn = self.db.get_connection()
            if not conn:
                print("Database connection failed. Setting not saved.")
                return False
            
            try:
                cursor = conn.cursor()
                
                # Determine value type
                value_type = type(value).__name__
                if value_type == 'str':
                    db_type = 'str'
                elif value_type == 'int':
                    db_type = 'int'
                elif value_type == 'float':
                    db_type = 'float'
                elif value_type == 'bool':
                    db_type = 'bool'
                    value = str(value).lower()  # Convert True/False to 'true'/'false'
                else:
                    db_type = 'str'
                    value = str(value)
                
                # Check if setting exists
                cursor.execute("SELECT COUNT(*) FROM cbs_system_settings WHERE setting_key = %s", (key,))
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    # Update existing setting
                    cursor.execute(
                        "UPDATE cbs_system_settings SET setting_value = %s, value_type = %s, updated_at = NOW() "
                        "WHERE setting_key = %s",
                        (str(value), db_type, key)
                    )
                else:
                    # Insert new setting
                    cursor.execute(
                        "INSERT INTO cbs_system_settings (setting_key, setting_value, value_type, created_at) "
                        "VALUES (%s, %s, %s, NOW())",
                        (key, str(value), db_type)
                    )
                
                conn.commit()
                print(f"Setting '{key}' changed from '{old_value}' to '{value}'")
                return True
                
            except Exception as e:
                conn.rollback()
                print(f"Error saving setting to database: {e}")
                return False
            finally:
                cursor.close()
                conn.close()
        
        else:
            print(f"Setting '{key}' does not exist.")
            return False

    def display_settings(self):
        """Display all settings"""
        print("\n===== Current System Settings =====")
        print(f"{'Setting':<30} {'Value':<30}")
        print("-" * 60)
        
        for key, value in sorted(self.configurations.items()):
            print(f"{key:<30} {str(value):<30}")
        
        input("\nPress Enter to continue...")
    
    def edit_setting(self):
        """Edit a system setting"""
        print("\n===== Edit Setting =====")
        
        # Display available settings
        print("Available settings:")
        for i, (key, value) in enumerate(sorted(self.configurations.items())):
            print(f"{i+1}. {key} = {value}")
        
        try:
            choice = int(input("\nEnter setting number to edit (0 to cancel): "))
            
            if choice == 0:
                return
                
            if choice < 1 or choice > len(self.configurations):
                print("Invalid choice.")
                return
                
            # Get the key based on choice
            key = list(sorted(self.configurations.keys()))[choice - 1]
            current_value = self.configurations[key]
            
            print(f"\nEditing setting: {key}")
            print(f"Current value: {current_value}")
            print(f"Value type: {type(current_value).__name__}")
            
            # Get new value
            new_value = input("Enter new value: ")
            
            # Convert value to appropriate type
            if isinstance(current_value, bool):
                new_value = new_value.lower() in ('true', 'yes', 'y', '1')
            elif isinstance(current_value, int):
                new_value = int(new_value)
            elif isinstance(current_value, float):
                new_value = float(new_value)
            
            # Save the setting
            self.set_setting(key, new_value)
            
        except ValueError:
            print("Invalid input. Please enter a number.")
        except Exception as e:
            print(f"Error: {e}")
    
    def import_settings(self):
        """Import settings from a JSON file"""
        file_path = input("Enter path to settings JSON file: ")
        
        if not os.path.isfile(file_path):
            print(f"File not found: {file_path}")
            return
            
        try:
            with open(file_path, 'r') as file:
                settings = json.load(file)
                
            # Validate settings
            invalid_keys = [k for k in settings if k not in self.configurations]
            if invalid_keys:
                print(f"Warning: The following settings will be ignored: {', '.join(invalid_keys)}")
                
            # Update valid settings
            for key, value in settings.items():
                if key in self.configurations:
                    self.set_setting(key, value)
                
            print(f"Settings imported successfully from {file_path}")
                
        except json.JSONDecodeError:
            print("Invalid JSON file format.")
        except Exception as e:
            print(f"Error importing settings: {e}")
    
    def export_settings(self):
        """Export settings to a JSON file"""
        file_path = input("Enter path for settings JSON file (or press Enter for default): ")
        
        if not file_path:
            file_path = "system_settings.json"
            
        try:
            with open(file_path, 'w') as file:
                json.dump(self.configurations, file, indent=4)
                
            print(f"Settings exported successfully to {file_path}")
                
        except Exception as e:
            print(f"Error exporting settings: {e}")
    
    def reset_to_default(self):
        """Reset settings to default values"""
        confirm = input("Are you sure you want to reset all settings to default? (y/n): ")
        
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return
            
        conn = self.db.get_connection()
        if not conn:
            print("Database connection failed.")
            return
            
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cbs_system_settings")
            conn.commit()
            
            # Reset configurations to default
            self.configurations = {
                "max_login_attempts": 5,
                "session_timeout": 30,
                "enable_logging": True,
                "log_level": "INFO",
                "admin_email": "admin@example.com",
                "notification_enabled": True,
                "backup_schedule": "DAILY",
                "maintenance_mode": False,
                "interest_rate_savings": 3.5,
                "interest_rate_current": 0.0,
                "interest_rate_fixed": 5.5,
                "min_balance_savings": 1000,
                "min_balance_current": 5000,
                "transaction_fee": 0.0,
            }
            
            print("All settings have been reset to default values.")
            
        except Exception as e:
            conn.rollback()
            print(f"Error resetting settings: {e}")
        finally:
            cursor.close()
            conn.close()