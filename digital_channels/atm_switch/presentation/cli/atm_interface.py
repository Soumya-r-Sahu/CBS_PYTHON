"""
ATM Command-Line Interface

This module provides a command-line interface for the ATM-Switch module.
"""

import argparse
import json
import os
import sys
import time
import datetime
from decimal import Decimal
from typing import Dict, Any, List

from ...application.services.atm_service import AtmService
from ...di_container import get_atm_service


class AtmCli:
    """Command-line interface for ATM operations"""
    
    def __init__(self):
        """Initialize CLI with ATM service"""
        self.atm_service = get_atm_service()
        self.session_token = None
        self.account_number = None
        self.last_activity_time = None
        # Session timeout in seconds (3 minutes)
        self.session_timeout = 180
    
    def display_menu(self):
        """Display main menu"""
        print("\n===== ATM SYSTEM =====")
        print("1. Insert Card & Enter PIN")
        print("2. Withdraw Cash")
        print("3. Check Balance")
        print("4. Mini Statement")
        print("5. Change PIN")
        print("6. Exit")
        print("=====================")
    
    def is_session_valid(self) -> bool:
        """Check if the current session is valid or has timed out"""
        if not self.session_token or not self.last_activity_time:
            return False
            
        # Check if session has timed out
        elapsed_time = time.time() - self.last_activity_time
        if elapsed_time > self.session_timeout:
            print("\nSession expired due to inactivity. Please log in again.")
            self.logout()
            return False
            
        # Update last activity time
        self.last_activity_time = time.time()
        return True
    
    def update_activity_time(self):
        """Update the last activity timestamp"""
        self.last_activity_time = time.time()
    
    def validate_card(self):
        """Handle card validation"""
        print("\n--- CARD VALIDATION ---")
        card_number = input("Enter Card Number: ")
        
        # Validate card number format
        if not self.validate_input(card_number, "card_number"):
            return False
            
        pin = input("Enter PIN: ")
        
        # Validate PIN format
        if not self.validate_input(pin, "pin"):
            return False
            
        response = self.atm_service.login(card_number, pin)
        
        if response.get('success', False):
            self.session_token = response['data']['session_token']
            self.account_number = response['data'].get('account_number')
            self.update_activity_time()
            print(f"\nWelcome! You are now logged in to account ending with ...{self.account_number[-4:]}")
            return True
        else:
            print(f"\nError: {response['message']}")
            return False
    def withdraw_cash(self):
        """Handle cash withdrawal"""
        if not self.session_token:
            print("\nPlease insert card and enter PIN first.")
            return
        
        print("\n--- CASH WITHDRAWAL ---")
        amount = input("Enter amount to withdraw: ")
        
        try:
            amount = Decimal(amount)
        except (ValueError, TypeError):
            print("\nInvalid amount format. Please enter a valid number.")
            return
        
        response = self.atm_service.withdraw(self.session_token, amount)
        if response.get('success', False):
            print("\nWithdrawal successful!")
            data = response.get('data', {})
            print(f"Amount: ${data.get('amount')}")
            if Decimal(data.get('fee', '0')) > 0:
                print(f"Fee: ${data.get('fee')}")
            print(f"Total: ${data.get('total')}")
            print(f"Remaining Balance: ${data.get('balance')}")
            print(f"Transaction ID: {data.get('transaction_id')}")
        else:
            print(f"\nError: {response.get('message', 'Unknown error')}")
    def check_balance(self):
        """Handle balance inquiry"""
        if not self.session_token:
            print("\nPlease insert card and enter PIN first.")
            return
        
        print("\n--- BALANCE INQUIRY ---")
        response = self.atm_service.get_balance(self.session_token)
        
        if response.get('success', False):
            print("\nAccount Information:")
            print(f"Account Number: ...{self.account_number[-4:]}")
            print(f"Available Balance: ${response['data']['balance']}")
            if response['data'].get('ledger_balance'):
                print(f"Ledger Balance: ${response['data']['ledger_balance']}")
        else:
            print(f"\nError: {response.get('message', 'Unknown error')}")
    def get_mini_statement(self):
        """Handle mini statement request"""
        if not self.session_token:
            print("\nPlease insert card and enter PIN first.")
            return
        
        print("\n--- MINI STATEMENT ---")
        limit = input("Enter number of transactions to show (default 10): ")
        
        try:
            limit = int(limit) if limit else 10
        except (ValueError, TypeError):
            limit = 10
            
        response = self.atm_service.get_statement(self.session_token, limit)
        
        if response.get('success', False):
            print(f"\nMini Statement for Account ...{self.account_number[-4:]}")
            print(f"Current Balance: ${response['data']['current_balance']}")
            print("\nRecent Transactions:")
            
            transactions = response['data']['transactions']
            if not transactions:
                print("No transactions found.")
            else:
                print(f"{'Date':<12} {'Type':<20} {'Amount':<12} {'Balance':<12}")
                print("-" * 60)
                
                for txn in transactions:
                    date = txn['date'][:10]
                    txn_type = txn['type'][:18] + ".." if len(txn['type']) > 20 else txn['type']
                    amount = f"${txn['amount']}"
                    balance = f"${txn['balance']}"
                    
                    print(f"{date:<12} {txn_type:<20} {amount:<12} {balance:<12}")
        else:
            print(f"\nError: {response['message']}")
    def change_pin(self):
        """Handle PIN change"""
        if not self.session_token:
            print("\nPlease insert card and enter PIN first.")
            return
        
        print("\n--- CHANGE PIN ---")
        current_pin = input("Enter Current PIN: ")
        new_pin = input("Enter New PIN: ")
        confirm_pin = input("Confirm New PIN: ")
        
        if new_pin != confirm_pin:
            print("\nPIN confirmation does not match. Please try again.")
            return
            
        response = self.atm_service.update_pin(self.session_token, current_pin, new_pin)
        
        if response.get('success', False):
            print("\nPIN changed successfully!")
        else:
            print(f"\nError: {response.get('message', 'Unknown error')}")
    
    def exit_application(self):
        """Exit the application"""
        print("\nThank you for using our ATM service. Goodbye!")
        sys.exit(0)
    
    def validate_input(self, input_value: str, input_type: str) -> bool:
        """
        Validate user input based on type
        
        Args:
            input_value: The value to validate
            input_type: Type of input ('card_number', 'pin', 'amount', etc.)
            
        Returns:
            bool: True if input is valid, False otherwise
        """
        if not input_value:
            print(f"Error: Input cannot be empty.")
            return False
            
        if input_type == "card_number":
            # Basic validation: 16-19 digits, no spaces or special chars
            if not input_value.isdigit() or not (16 <= len(input_value) <= 19):
                print("Error: Card number must be 16-19 digits with no spaces or special characters.")
                return False
                
        elif input_type == "pin":
            # Basic validation: 4-6 digits
            if not input_value.isdigit() or not (4 <= len(input_value) <= 6):
                print("Error: PIN must be 4-6 digits.")
                return False
                
        elif input_type == "amount":
            # Validate amount as decimal number greater than zero
            try:
                amount = Decimal(input_value)
                if amount <= Decimal('0'):
                    print("Error: Amount must be greater than zero.")
                    return False
                if amount % Decimal('10') != Decimal('0'):
                    print("Error: Amount must be in multiples of 10.")
                    return False
            except:
                print("Error: Please enter a valid amount.")
                return False
                
        elif input_type == "account_number":
            # Basic validation: typically 10-12 digits
            if not input_value.isdigit() or not (10 <= len(input_value) <= 12):
                print("Error: Account number must be 10-12 digits.")
                return False
                
        return True
        
    def format_currency(self, amount: Decimal) -> str:
        """Format amount as currency string"""
        return f"${amount:,.2f}"
        
    def format_datetime(self, timestamp: float) -> str:
        """Format timestamp as human-readable date and time"""
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
        
    def withdraw(self):
        """Handle cash withdrawal"""
        if not self.is_session_valid():
            print("\nPlease log in first.")
            return
            
        print("\n--- CASH WITHDRAWAL ---")
        amount_str = input("Enter amount to withdraw: ")
        
        # Validate amount input
        if not self.validate_input(amount_str, "amount"):
            return
            
        try:
            amount = Decimal(amount_str)
            response = self.atm_service.withdraw(self.session_token, amount)
            
            if response.get('success', False):
                print(f"\nWithdrawal successful!")
                print(f"Amount: {self.format_currency(amount)}")
                print(f"Available balance: {self.format_currency(response['data']['available_balance'])}")
                print(f"Transaction ID: {response['data']['transaction_id']}")
                print(f"Please collect your cash and receipt.")
            else:
                print(f"\nError: {response['message']}")
                if 'error_code' in response and response['error_code'] == 'insufficient_funds':
                    print(f"Available balance: {self.format_currency(response['data']['available_balance'])}")
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            
        self.update_activity_time()
        
    def check_balance(self):
        """Handle balance inquiry"""
        if not self.is_session_valid():
            print("\nPlease log in first.")
            return
            
        print("\n--- BALANCE INQUIRY ---")
        response = self.atm_service.check_balance(self.session_token)
        
        if response.get('success', False):
            print(f"\nAccount Number: ...{self.account_number[-4:]}")
            print(f"Available Balance: {self.format_currency(response['data']['available_balance'])}")
            print(f"Ledger Balance: {self.format_currency(response['data']['ledger_balance'])}")
            print(f"As of: {self.format_datetime(response['data']['timestamp'])}")
        else:
            print(f"\nError: {response['message']}")
            
        self.update_activity_time()
        
    def get_mini_statement(self):
        """Handle mini statement request"""
        if not self.is_session_valid():
            print("\nPlease log in first.")
            return
            
        print("\n--- MINI STATEMENT ---")
        response = self.atm_service.get_mini_statement(self.session_token)
        
        if response.get('success', False):
            print(f"\nAccount Number: ...{self.account_number[-4:]}")
            print("Recent Transactions:")
            print("=" * 60)
            print(f"{'Date':<12} | {'Description':<25} | {'Amount':<12} | {'Balance':<12}")
            print("-" * 60)
            
            for txn in response['data']['transactions']:
                date = self.format_datetime(txn['timestamp'])[:10]  # Just the date part
                description = txn['description'][:25]
                amount_str = self.format_currency(txn['amount'])
                balance_str = self.format_currency(txn['balance'])
                print(f"{date:<12} | {description:<25} | {amount_str:<12} | {balance_str:<12}")
                
            print("=" * 60)
            print(f"Available Balance: {self.format_currency(response['data']['available_balance'])}")
        else:
            print(f"\nError: {response['message']}")
            
        self.update_activity_time()
        
    def change_pin(self):
        """Handle PIN change"""
        if not self.is_session_valid():
            print("\nPlease log in first.")
            return
            
        print("\n--- CHANGE PIN ---")
        current_pin = input("Enter current PIN: ")
        
        # Validate current PIN
        if not self.validate_input(current_pin, "pin"):
            return
            
        new_pin = input("Enter new PIN: ")
        
        # Validate new PIN
        if not self.validate_input(new_pin, "pin"):
            return
            
        confirm_pin = input("Confirm new PIN: ")
        
        # Check if PINs match
        if new_pin != confirm_pin:
            print("\nError: New PIN and confirmation PIN do not match.")
            return
            
        # Confirm change
        print("\nAre you sure you want to change your PIN?")
        confirm = input("Type 'YES' to confirm: ")
        
        if confirm.upper() != "YES":
            print("PIN change cancelled.")
            return
            
        response = self.atm_service.change_pin(self.session_token, current_pin, new_pin)
        
        if response.get('success', False):
            print("\nPIN changed successfully!")
            print("Please remember your new PIN.")
            # For security, end the session after PIN change
            self.logout()
        else:
            print(f"\nError: {response['message']}")
            
    def logout(self):
        """Log out by clearing session data"""
        if self.session_token:
            try:
                self.atm_service.logout(self.session_token)
            except:
                pass  # Ignore errors during logout
                
        self.session_token = None
        self.account_number = None
        self.last_activity_time = None
        print("\nYou have been logged out.")
        
    def run(self):
        """Run the ATM CLI"""
        print("\nWelcome to the ATM System")
        print("========================")
        
        while True:
            self.display_menu()
            
            try:
                choice = input("\nSelect option (1-6): ")
                
                if choice == '1':
                    self.validate_card()
                elif choice == '2':
                    self.withdraw()
                elif choice == '3':
                    self.check_balance()
                elif choice == '4':
                    self.get_mini_statement()
                elif choice == '5':
                    self.change_pin()
                elif choice == '6':
                    print("\nThank you for using the ATM. Goodbye!")
                    self.logout()
                    break
                else:
                    print("\nInvalid option. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\nOperation cancelled. Logging out...")
                self.logout()
                break
                
            except Exception as e:
                print(f"\nAn unexpected error occurred: {str(e)}")
                print("Please try again or contact customer support.")
                
            input("\nPress Enter to continue...")
        
if __name__ == "__main__":
    try:
        cli = AtmCli()
        cli.run()
    except Exception as e:
        print(f"Critical error: {str(e)}")
        print("The ATM system has encountered a problem.")
        print("Please contact customer support.")
        sys.exit(1)
