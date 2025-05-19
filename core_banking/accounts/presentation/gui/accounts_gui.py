"""
Accounts GUI Interface

This module provides a PyQt5-based graphical user interface for the Accounts module.
"""

import sys
import logging
from decimal import Decimal
from uuid import UUID
from typing import Dict, Any, Optional
import json

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QGroupBox,
    QTabWidget, QFormLayout, QMessageBox, QDialog, QDialogButtonBox,
    QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QObject

from ..di_container import container

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class AccountsMainWindow(QMainWindow):
    """Main window for the accounts GUI application"""
    
    def __init__(self):
        super().__init__()
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Get account service from container
        self.account_service = container.account_service()
        
        # Set up UI
        self.setWindowTitle("CBS Accounts Manager")
        self.setMinimumSize(800, 600)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create main layout
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_account_tab = self._create_account_tab()
        self.account_details_tab = self._account_details_tab()
        self.deposit_tab = self._deposit_tab()
        self.withdraw_tab = self._withdraw_tab()
        self.transfer_tab = self._transfer_tab()
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.create_account_tab, "Create Account")
        self.tab_widget.addTab(self.account_details_tab, "Account Details")
        self.tab_widget.addTab(self.deposit_tab, "Deposit")
        self.tab_widget.addTab(self.withdraw_tab, "Withdraw")
        self.tab_widget.addTab(self.transfer_tab, "Transfer")
    
    def _create_account_tab(self) -> QWidget:
        """Create the account creation tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Customer ID field
        self.customer_id_input = QLineEdit()
        form_layout.addRow("Customer ID (UUID):", self.customer_id_input)
        
        # Account type dropdown
        self.account_type_dropdown = QComboBox()
        self.account_type_dropdown.addItems(["SAVINGS", "CURRENT", "FIXED_DEPOSIT", "LOAN"])
        form_layout.addRow("Account Type:", self.account_type_dropdown)
        
        # Initial deposit field
        self.initial_deposit_input = QLineEdit()
        self.initial_deposit_input.setPlaceholderText("Optional")
        form_layout.addRow("Initial Deposit:", self.initial_deposit_input)
        
        # Currency field
        self.currency_input = QLineEdit("INR")
        form_layout.addRow("Currency:", self.currency_input)
        
        layout.addLayout(form_layout)
        
        # Add some space
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Create account button
        self.create_account_button = QPushButton("Create Account")
        self.create_account_button.clicked.connect(self._handle_create_account)
        layout.addWidget(self.create_account_button)
        
        # Response area
        self.create_account_response = QTextEdit()
        self.create_account_response.setReadOnly(True)
        layout.addWidget(QLabel("Response:"))
        layout.addWidget(self.create_account_response)
        
        return tab
    
    def _account_details_tab(self) -> QWidget:
        """Create the account details tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Account ID field
        self.account_id_input = QLineEdit()
        form_layout.addRow("Account ID (UUID):", self.account_id_input)
        
        layout.addLayout(form_layout)
        
        # Get details button
        self.get_details_button = QPushButton("Get Account Details")
        self.get_details_button.clicked.connect(self._handle_get_account_details)
        layout.addWidget(self.get_details_button)
        
        # Response area
        self.account_details_response = QTextEdit()
        self.account_details_response.setReadOnly(True)
        layout.addWidget(QLabel("Account Details:"))
        layout.addWidget(self.account_details_response)
        
        return tab
    
    def _deposit_tab(self) -> QWidget:
        """Create the deposit tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Account ID field
        self.deposit_account_id_input = QLineEdit()
        form_layout.addRow("Account ID (UUID):", self.deposit_account_id_input)
        
        # Amount field
        self.deposit_amount_input = QLineEdit()
        form_layout.addRow("Amount:", self.deposit_amount_input)
        
        # Description field
        self.deposit_description_input = QLineEdit()
        self.deposit_description_input.setPlaceholderText("Optional")
        form_layout.addRow("Description:", self.deposit_description_input)
        
        # Reference ID field
        self.deposit_reference_id_input = QLineEdit()
        self.deposit_reference_id_input.setPlaceholderText("Optional")
        form_layout.addRow("Reference ID:", self.deposit_reference_id_input)
        
        layout.addLayout(form_layout)
        
        # Add some space
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Deposit button
        self.deposit_button = QPushButton("Deposit")
        self.deposit_button.clicked.connect(self._handle_deposit)
        layout.addWidget(self.deposit_button)
        
        # Response area
        self.deposit_response = QTextEdit()
        self.deposit_response.setReadOnly(True)
        layout.addWidget(QLabel("Response:"))
        layout.addWidget(self.deposit_response)
        
        return tab
    
    def _withdraw_tab(self) -> QWidget:
        """Create the withdraw tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Account ID field
        self.withdraw_account_id_input = QLineEdit()
        form_layout.addRow("Account ID (UUID):", self.withdraw_account_id_input)
        
        # Amount field
        self.withdraw_amount_input = QLineEdit()
        form_layout.addRow("Amount:", self.withdraw_amount_input)
        
        # Description field
        self.withdraw_description_input = QLineEdit()
        self.withdraw_description_input.setPlaceholderText("Optional")
        form_layout.addRow("Description:", self.withdraw_description_input)
        
        # Reference ID field
        self.withdraw_reference_id_input = QLineEdit()
        self.withdraw_reference_id_input.setPlaceholderText("Optional")
        form_layout.addRow("Reference ID:", self.withdraw_reference_id_input)
        
        layout.addLayout(form_layout)
        
        # Add some space
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Withdraw button
        self.withdraw_button = QPushButton("Withdraw")
        self.withdraw_button.clicked.connect(self._handle_withdraw)
        layout.addWidget(self.withdraw_button)
        
        # Response area
        self.withdraw_response = QTextEdit()
        self.withdraw_response.setReadOnly(True)
        layout.addWidget(QLabel("Response:"))
        layout.addWidget(self.withdraw_response)
        
        return tab

    def _transfer_tab(self) -> QWidget:
        """Create the fund transfer tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Source Account ID field
        self.source_account_id_input = QLineEdit()
        form_layout.addRow("Source Account ID (UUID):", self.source_account_id_input)
        
        # Target Account ID field
        self.target_account_id_input = QLineEdit()
        form_layout.addRow("Target Account ID (UUID):", self.target_account_id_input)
        
        # Amount field
        self.transfer_amount_input = QLineEdit()
        form_layout.addRow("Amount:", self.transfer_amount_input)
        
        # Description field
        self.transfer_description_input = QLineEdit()
        self.transfer_description_input.setPlaceholderText("Optional")
        form_layout.addRow("Description:", self.transfer_description_input)
        
        # Reference ID field
        self.transfer_reference_id_input = QLineEdit()
        self.transfer_reference_id_input.setPlaceholderText("Optional")
        form_layout.addRow("Reference ID:", self.transfer_reference_id_input)
        
        layout.addLayout(form_layout)
        
        # Add some space
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        
        # Transfer button
        self.transfer_button = QPushButton("Transfer")
        self.transfer_button.clicked.connect(self._handle_transfer)
        layout.addWidget(self.transfer_button)
        
        # Response area
        self.transfer_response = QTextEdit()
        self.transfer_response.setReadOnly(True)
        layout.addWidget(QLabel("Response:"))
        layout.addWidget(self.transfer_response)
        
        return tab
        
    @pyqtSlot()
    def _handle_create_account(self):
        """Handle the create account button click"""
        try:
            # Get input values
            customer_id = self.customer_id_input.text().strip()
            account_type = self.account_type_dropdown.currentText()
            initial_deposit = self.initial_deposit_input.text().strip()
            currency = self.currency_input.text().strip()
            
            # Validate required fields
            if not customer_id:
                QMessageBox.warning(self, "Input Error", "Customer ID is required")
                return
            
            # Create account
            result = self.account_service.create_account(
                customer_id=UUID(customer_id),
                account_type=account_type,
                initial_deposit=Decimal(initial_deposit) if initial_deposit else None,
                currency=currency if currency else "INR"
            )
            
            # Format and display the result
            self.create_account_response.setPlainText(
                json.dumps(result, indent=2, default=str)
            )
            
            # Show success message
            QMessageBox.information(self, "Success", "Account created successfully")
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            self.logger.error(f"Error creating account: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error creating account: {str(e)}")
    
    @pyqtSlot()
    def _handle_get_account_details(self):
        """Handle the get account details button click"""
        try:
            # Get input values
            account_id = self.account_id_input.text().strip()
            
            # Validate required fields
            if not account_id:
                QMessageBox.warning(self, "Input Error", "Account ID is required")
                return
            
            # Get account details
            result = self.account_service.get_account_details(
                account_id=UUID(account_id)
            )
            
            # Format and display the result
            self.account_details_response.setPlainText(
                json.dumps(result, indent=2, default=str)
            )
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            self.logger.error(f"Error getting account details: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error getting account details: {str(e)}")
    
    @pyqtSlot()
    def _handle_deposit(self):
        """Handle the deposit button click"""
        try:
            # Get input values
            account_id = self.deposit_account_id_input.text().strip()
            amount = self.deposit_amount_input.text().strip()
            description = self.deposit_description_input.text().strip()
            reference_id = self.deposit_reference_id_input.text().strip()
            
            # Validate required fields
            if not account_id:
                QMessageBox.warning(self, "Input Error", "Account ID is required")
                return
            if not amount:
                QMessageBox.warning(self, "Input Error", "Amount is required")
                return
            
            # Deposit funds
            result = self.account_service.deposit(
                account_id=UUID(account_id),
                amount=Decimal(amount),
                description=description if description else None,
                reference_id=reference_id if reference_id else None
            )
            
            # Format and display the result
            self.deposit_response.setPlainText(
                json.dumps(result, indent=2, default=str)
            )
            
            # Show success message
            QMessageBox.information(self, "Success", "Deposit successful")
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            self.logger.error(f"Error depositing funds: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error depositing funds: {str(e)}")
    
    @pyqtSlot()
    def _handle_withdraw(self):
        """Handle the withdraw button click"""
        try:
            # Get input values
            account_id = self.withdraw_account_id_input.text().strip()
            amount = self.withdraw_amount_input.text().strip()
            description = self.withdraw_description_input.text().strip()
            reference_id = self.withdraw_reference_id_input.text().strip()
            
            # Validate required fields
            if not account_id:
                QMessageBox.warning(self, "Input Error", "Account ID is required")
                return
            if not amount:
                QMessageBox.warning(self, "Input Error", "Amount is required")
                return
            
            # Withdraw funds
            result = self.account_service.withdraw(
                account_id=UUID(account_id),
                amount=Decimal(amount),
                description=description if description else None,
                reference_id=reference_id if reference_id else None
            )
            
            # Format and display the result
            self.withdraw_response.setPlainText(
                json.dumps(result, indent=2, default=str)
            )
            
            # Show success message
            QMessageBox.information(self, "Success", "Withdrawal successful")
            
        except ValueError as e:
            QMessageBox.warning(self, "Input Error", str(e))
        except Exception as e:
            self.logger.error(f"Error withdrawing funds: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error withdrawing funds: {str(e)}")

    @pyqtSlot()
    def _handle_transfer(self):
        """Handle the transfer button click"""
        try:
            # Get input values
            source_account_id = self.source_account_id_input.text().strip()
            target_account_id = self.target_account_id_input.text().strip()
            amount = self.transfer_amount_input.text().strip()
            description = self.transfer_description_input.text().strip() or None
            reference_id = self.transfer_reference_id_input.text().strip() or None
            
            # Validate inputs
            if not source_account_id:
                QMessageBox.critical(self, "Input Error", "Source account ID is required")
                return
            
            if not target_account_id:
                QMessageBox.critical(self, "Input Error", "Target account ID is required")
                return
            
            if not amount:
                QMessageBox.critical(self, "Input Error", "Amount is required")
                return
            
            # Call service
            result = self.account_service.transfer(
                source_account_id=UUID(source_account_id),
                target_account_id=UUID(target_account_id),
                amount=Decimal(amount),
                description=description,
                reference_id=reference_id
            )
            
            # Display result
            self.transfer_response.setText(json.dumps(result, indent=2, default=str))
            
            if result.get('success'):
                QMessageBox.information(self, "Success", "Funds transferred successfully!")
            else:
                QMessageBox.warning(self, "Transfer Failed", result.get('error', 'Unknown error'))
                
        except ValueError as ve:
            QMessageBox.critical(self, "Input Error", str(ve))
            self.logger.error(f"Validation error in transfer: {str(ve)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            self.logger.error(f"Error in transfer: {str(e)}", exc_info=True)


def run_gui():
    """Run the accounts GUI application"""
    app = QApplication(sys.argv)
    window = AccountsMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    
    # Run the GUI
    run_gui()
