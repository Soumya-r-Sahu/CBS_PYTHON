"""
Interactive Customer Management CLI

This module provides an interactive command-line interface for the Customer Management module,
allowing users to perform customer-related operations through a menu-driven interface.
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directories to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
core_banking_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
project_root = os.path.dirname(core_banking_dir)
sys.path.append(project_root)

from core_banking.customer_management.presentation.cli.customer_management_cli import CustomerManagementCli

# Session timeout in seconds (5 minutes)
SESSION_TIMEOUT = 300

class InteractiveCustomerCli:
    """Interactive command-line interface for Customer Management module"""
    
    def __init__(self):
        """Initialize the interactive CLI with the customer management CLI"""
        self.cli = CustomerManagementCli()
        self.last_activity_time = time.time()
        self.running = True
        self.current_customer_id = None
    
    def update_activity_time(self):
        """Update the last activity time"""
        self.last_activity_time = time.time()
    
    def check_session_timeout(self) -> bool:
        """
        Check if the session has timed out.
        
        Returns:
            bool: True if the session has timed out, False otherwise
        """
        current_time = time.time()
        elapsed_time = current_time - self.last_activity_time
        
        if elapsed_time > SESSION_TIMEOUT:
            print("\n⚠️ Session timed out due to inactivity")
            return True
        
        return False
    
    def get_input(self, prompt: str, required: bool = False) -> str:
        """
        Get input from the user with timeout check.
        
        Args:
            prompt: The prompt to display to the user
            required: Whether the input is required
            
        Returns:
            User input string or empty string if optional
        """
        while True:
            self.update_activity_time()
            value = input(prompt).strip()
            
            if value or not required:
                return value
            
            print("⚠️ This field is required. Please provide a value.")
    
    def get_json_input(self, prompt: str) -> Any:
        """
        Get JSON input from the user.
        
        Args:
            prompt: The prompt to display to the user
            
        Returns:
            Parsed JSON object or None if invalid
        """
        print(prompt)
        print("Enter JSON data (type 'END' on a new line when finished):")
        
        lines = []
        while True:
            line = self.get_input("").strip()
            if line == "END":
                break
            lines.append(line)
        
        json_text = "\n".join(lines)
        
        if not json_text.strip():
            return None
        
        try:
            return json.loads(json_text)
        except json.JSONDecodeError as e:
            print(f"⚠️ Invalid JSON format: {str(e)}")
            return None
    
    def get_date_input(self, prompt: str) -> Optional[str]:
        """
        Get a date input from the user in YYYY-MM-DD format.
        
        Args:
            prompt: The prompt to display to the user
            
        Returns:
            Date string in YYYY-MM-DD format or None if invalid
        """
        while True:
            value = self.get_input(prompt)
            
            if not value:
                return None
            
            try:
                datetime.strptime(value, "%Y-%m-%d")
                return value
            except ValueError:
                print("⚠️ Invalid date format. Please use YYYY-MM-DD format.")
    
    def get_boolean_input(self, prompt: str) -> bool:
        """
        Get a boolean input from the user.
        
        Args:
            prompt: The prompt to display to the user
            
        Returns:
            Boolean value based on user input
        """
        while True:
            value = self.get_input(f"{prompt} (y/n): ").lower()
            
            if value in ("y", "yes", "true", "1"):
                return True
            
            if value in ("n", "no", "false", "0") or not value:
                return False
            
            print("⚠️ Invalid input. Please enter 'y' or 'n'.")
    
    def print_result(self, result: Dict[str, Any]):
        """
        Print the result of an operation in a formatted way.
        
        Args:
            result: The result dictionary to print
        """
        print("\n" + "="*50)
        print("OPERATION RESULT:")
        print("="*50)
        
        # Extract and print success/failure first
        success = result.get("success", False)
        if success:
            print("✅ SUCCESS")
        else:
            print("❌ FAILED")
        
        # Print message if available
        if "message" in result:
            print(f"\nMessage: {result['message']}")
        
        # Extract error information if available
        if "error_code" in result and result["error_code"]:
            print(f"Error Code: {result['error_code']}")
        
        if "validation_errors" in result and result["validation_errors"]:
            print("\nValidation Errors:")
            for field, error in result["validation_errors"].items():
                print(f"  - {field}: {error}")
        
        # Print customer ID if available
        if "customer_id" in result and result["customer_id"]:
            self.current_customer_id = result["customer_id"]
            print(f"\nCustomer ID: {result['customer_id']}")
        
        # Print KYC/AML information if available
        if "is_fully_compliant" in result:
            print(f"\nFully Compliant: {'Yes' if result['is_fully_compliant'] else 'No'}")
        
        if "missing_documents" in result and result["missing_documents"]:
            print("\nMissing Documents:")
            for doc in result["missing_documents"]:
                print(f"  - {doc}")
        
        if "expired_documents" in result and result["expired_documents"]:
            print("\nExpired Documents:")
            for doc in result["expired_documents"]:
                print(f"  - {doc['type']}: Expired on {doc['expiry_date']}")
        
        print("="*50 + "\n")
    
    def create_customer_menu(self):
        """Display the create customer menu and process user input"""
        print("\n=== CREATE NEW CUSTOMER ===\n")
        
        # Get customer type
        print("Customer Types:")
        print("  individual - Individual person")
        print("  corporate - Corporate entity")
        print("  joint - Joint account holder")
        print("  minor - Minor (under 18)")
        
        customer_type = None
        while customer_type not in ["individual", "corporate", "joint", "minor"]:
            customer_type = self.get_input("Customer Type: ", required=True).lower()
            if customer_type not in ["individual", "corporate", "joint", "minor"]:
                print("⚠️ Invalid customer type. Please choose from the options above.")
        
        # Prepare arguments dictionary
        args = {
            "customer_type": customer_type
        }
        
        # Get fields based on customer type
        if customer_type in ["individual", "joint", "minor"]:
            args["first_name"] = self.get_input("First Name: ", required=True)
            args["last_name"] = self.get_input("Last Name: ", required=True)
            args["middle_name"] = self.get_input("Middle Name (optional): ")
            args["date_of_birth"] = self.get_date_input("Date of Birth (YYYY-MM-DD): ")
        
        if customer_type == "corporate":
            args["company_name"] = self.get_input("Company Name: ", required=True)
            args["registration_number"] = self.get_input("Registration Number: ", required=True)
        
        # Common fields for all customer types
        args["tax_id"] = self.get_input("Tax ID/SSN (optional): ")
        args["email"] = self.get_input("Email Address: ")
        args["primary_phone"] = self.get_input("Primary Phone: ")
        args["secondary_phone"] = self.get_input("Secondary Phone (optional): ")
        
        # Get addresses as JSON
        addresses = self.get_json_input("Customer Addresses (JSON array):")
        if addresses:
            args["addresses"] = json.dumps(addresses)
        
        # Get documents as JSON
        documents = self.get_json_input("Customer Documents (JSON array):")
        if documents:
            args["documents"] = json.dumps(documents)
        
        # Get custom fields as JSON
        custom_fields = self.get_json_input("Custom Fields (JSON object):")
        if custom_fields:
            args["custom_fields"] = json.dumps(custom_fields)
        
        # Confirm submission
        print("\nReview Customer Information:")
        for key, value in args.items():
            if key not in ["addresses", "documents", "custom_fields"]:
                print(f"  {key}: {value}")
        
        if self.get_boolean_input("\nSubmit customer information?"):
            result = self.cli.create_customer(args)
            self.print_result(result)
    
    def verify_customer_kyc_menu(self):
        """Display the verify customer KYC menu and process user input"""
        print("\n=== VERIFY CUSTOMER KYC ===\n")
        
        # Get customer ID
        customer_id = self.current_customer_id
        if not customer_id:
            customer_id = self.get_input("Customer ID: ", required=True)
        else:
            print(f"Using current customer ID: {customer_id}")
            if not self.get_boolean_input("Continue with this customer?"):
                customer_id = self.get_input("Customer ID: ", required=True)
        
        # Prepare arguments dictionary
        args = {
            "customer_id": customer_id
        }
        
        # Get verification flags
        args["verify_kyc"] = self.get_boolean_input("Verify KYC?")
        args["verify_aml"] = self.get_boolean_input("Verify AML?")
        
        # Get verified documents as JSON
        documents_verified = self.get_json_input("Verified Documents (JSON array):")
        if documents_verified:
            args["documents_verified"] = json.dumps(documents_verified)
        
        # Get verification notes
        args["notes"] = self.get_input("Verification Notes (optional): ")
        
        # Confirm submission
        if self.get_boolean_input("\nSubmit verification information?"):
            result = self.cli.verify_customer_kyc(args)
            self.print_result(result)
    
    def get_verification_requirements_menu(self):
        """Display the get verification requirements menu and process user input"""
        print("\n=== GET VERIFICATION REQUIREMENTS ===\n")
        
        # Get customer ID
        customer_id = self.current_customer_id
        if not customer_id:
            customer_id = self.get_input("Customer ID: ", required=True)
        else:
            print(f"Using current customer ID: {customer_id}")
            if not self.get_boolean_input("Continue with this customer?"):
                customer_id = self.get_input("Customer ID: ", required=True)
        
        # Prepare arguments dictionary
        args = {
            "customer_id": customer_id
        }
        
        # Get verification requirements
        result = self.cli.get_verification_requirements(args)
        self.print_result(result)
    
    def display_help(self):
        """Display help information"""
        print("\n=== CUSTOMER MANAGEMENT HELP ===\n")
        print("Available Commands:")
        print("  1. Create Customer - Create a new customer record")
        print("  2. Verify KYC - Verify customer KYC/AML information")
        print("  3. Requirements - Get verification requirements for a customer")
        print("  4. Help - Display this help information")
        print("  5. Exit - Exit the application")
        print("\nInput Formats:")
        print("  - Dates: YYYY-MM-DD (e.g., 1990-01-15)")
        print("  - JSON: Valid JSON arrays/objects")
        print("    Example Address JSON:")
        print('    [{"type": "HOME", "line1": "123 Main St", "city": "Anytown", "state": "ST", "postal_code": "12345", "country": "US"}]')
        print("    Example Document JSON:")
        print('    [{"type": "PASSPORT", "number": "AB123456", "issuing_country": "US", "issue_date": "2020-01-01", "expiry_date": "2030-01-01"}]')
        print("\nSession Information:")
        print(f"  - Timeout: {SESSION_TIMEOUT} seconds of inactivity")
        print("  - Customer Context: The system remembers the last customer ID used")
        print("\n")
    
    def display_menu(self):
        """Display the main menu"""
        print("\n===== CUSTOMER MANAGEMENT SYSTEM =====")
        print("1. Create New Customer")
        print("2. Verify Customer KYC")
        print("3. Get Verification Requirements")
        print("4. Help")
        print("5. Exit")
        
        if self.current_customer_id:
            print(f"\nCurrent Customer: {self.current_customer_id}")
        
        print("=====================================")
    
    def run(self):
        """Run the interactive CLI"""
        print("\n🏦 Welcome to the Customer Management System 🏦")
        print("Type 'help' or '4' for more information")
        
        while self.running:
            if self.check_session_timeout():
                print("Please restart the application to continue.")
                self.running = False
                break
            
            self.display_menu()
            choice = self.get_input("\nEnter your choice (1-5): ")
            
            if choice in ["1", "create"]:
                self.create_customer_menu()
            elif choice in ["2", "verify"]:
                self.verify_customer_kyc_menu()
            elif choice in ["3", "requirements"]:
                self.get_verification_requirements_menu()
            elif choice in ["4", "help"]:
                self.display_help()
            elif choice in ["5", "exit", "quit"]:
                print("Thank you for using the Customer Management System. Goodbye!")
                self.running = False
            else:
                print("⚠️ Invalid choice. Please enter a number between 1 and 5.")


def main():
    """Main entry point for the interactive CLI"""
    parser = argparse.ArgumentParser(description='Interactive Customer Management CLI')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()
    
    try:
        cli = InteractiveCustomerCli()
        cli.run()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        if args.debug:
            import traceback
            print(f"\n⚠️ An error occurred: {str(e)}")
            print("\nStacktrace:")
            traceback.print_exc()
        else:
            print(f"\n⚠️ An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
