"""
ATM Receipt Printing Service

This module handles the generation of various types of ATM transaction receipts
with proper formatting and layout based on standard ATM receipt formats.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path

from ..entities.transaction import Transaction
from ..entities.account import Account


class ReceiptPrinter:
    """
    Service for generating formatted ATM receipts
    
    This class provides methods to generate different types of ATM receipts
    with consistent formatting and proper placeholders.
    """
    
    # Class constants for receipt formatting
    RECEIPT_WIDTH = 50
    BANK_NAME = "CBS BANKING SYSTEM"
    DIVIDER = "-" * RECEIPT_WIDTH
    
    @classmethod
    def generate_withdrawal_receipt(cls, 
                                   transaction: Transaction, 
                                   account: Account, 
                                   atm_location: str,
                                   atm_id: str,
                                   card_number: str) -> str:
        """
        Generate a formatted receipt for ATM withdrawal transactions
        
        Args:
            transaction: The withdrawal transaction
            account: The account used for withdrawal
            atm_location: Physical location of the ATM
            atm_id: Identifier for the ATM terminal
            card_number: Customer's card number
            
        Returns:
            Formatted receipt as a string
        """
        receipt = []
        
        # Header
        receipt.append(cls.DIVIDER)
        receipt.append(cls._center_text(cls.BANK_NAME + " ATM RECEIPT"))
        receipt.append(cls.DIVIDER)
        
        # Transaction details
        current_time = transaction.timestamp
        receipt.append(f"Date         : {current_time.strftime('%d/%m/%Y')}          Time: {current_time.strftime('%H:%M:%S')}")
        receipt.append(f"ATM ID       : {atm_id}")
        receipt.append(f"Branch       : {atm_location}")
        receipt.append(cls.DIVIDER)
        
        # Card and account information
        receipt.append(f"Card Number  : {cls._mask_card_number(card_number)}")
        receipt.append(f"Transaction  : CASH WITHDRAWAL")
        receipt.append(f"Account Type : {account.account_type}")
        receipt.append(cls.DIVIDER)
        
        # Amount information
        receipt.append(f"Txn Ref No.  : {transaction.transaction_id}")
        receipt.append(f"Amount       : {cls._format_amount(transaction.amount)}")
        if transaction.fee > Decimal('0'):
            receipt.append(f"Charges      : {cls._format_amount(transaction.fee)}")
        receipt.append(f"Available Bal: {cls._format_amount(transaction.balance_after)}")
        receipt.append(cls.DIVIDER)
        
        # Response information
        receipt.append(f"Response     : TRANSACTION SUCCESSFUL")
        receipt.append(f"Response Code: 00")
        receipt.append(cls.DIVIDER)
        
        # Footer
        receipt.append(f"Helpline No. : 1800-XXX-XXXX")
        receipt.append(f"Website      : www.cbsbank.com")
        receipt.append(cls.DIVIDER)
        receipt.append(cls._center_text("Thank you for banking with CBS Banking System!"))
        receipt.append(cls.DIVIDER)
        
        return "\n".join(receipt)
    
    @classmethod
    def generate_deposit_receipt(cls,
                                transaction: Transaction,
                                account: Account,
                                atm_location: str,
                                atm_id: str,
                                card_number: str,
                                deposit_envelope_id: Optional[str] = None) -> str:
        """
        Generate a formatted receipt for ATM deposit transactions
        
        Args:
            transaction: The deposit transaction
            account: The account used for deposit
            atm_location: Physical location of the ATM
            atm_id: Identifier for the ATM terminal
            card_number: Customer's card number
            deposit_envelope_id: Optional identifier for deposit envelope
            
        Returns:
            Formatted receipt as a string
        """
        receipt = []
        
        # Header
        receipt.append(cls.DIVIDER)
        receipt.append(cls._center_text(cls.BANK_NAME + " ATM RECEIPT"))
        receipt.append(cls.DIVIDER)
        
        # Transaction details
        current_time = transaction.timestamp
        receipt.append(f"Date         : {current_time.strftime('%d/%m/%Y')}          Time: {current_time.strftime('%H:%M:%S')}")
        receipt.append(f"ATM ID       : {atm_id}")
        receipt.append(f"Branch       : {atm_location}")
        receipt.append(cls.DIVIDER)
        
        # Card and account information
        receipt.append(f"Card Number  : {cls._mask_card_number(card_number)}")
        receipt.append(f"Transaction  : CASH DEPOSIT")
        receipt.append(f"Account Type : {account.account_type}")
        receipt.append(cls.DIVIDER)
        
        # Amount information
        receipt.append(f"Txn Ref No.  : {transaction.transaction_id}")
        if deposit_envelope_id:
            receipt.append(f"Envelope ID  : {deposit_envelope_id}")
        receipt.append(f"Amount Deposited: {cls._format_amount(transaction.amount)}")
        
        # Balance information (may be pending verification)
        if transaction.status == "COMPLETED":
            receipt.append(f"Available Bal   : {cls._format_amount(transaction.balance_after)}")
        else:
            receipt.append("NOTE: Deposit subject to verification")
        receipt.append(cls.DIVIDER)
        
        # Response information
        receipt.append(f"Response     : TRANSACTION SUCCESSFUL")
        receipt.append(f"Response Code: 00")
        receipt.append(cls.DIVIDER)
        
        # Footer
        receipt.append(f"Helpline No. : 1800-XXX-XXXX")
        receipt.append(f"Website      : www.cbsbank.com")
        receipt.append(cls.DIVIDER)
        receipt.append(cls._center_text("Thank you for banking with CBS Banking System!"))
        receipt.append(cls.DIVIDER)
        
        return "\n".join(receipt)
    
    @classmethod
    def generate_balance_inquiry_receipt(cls,
                                        account: Account,
                                        atm_location: str,
                                        atm_id: str,
                                        transaction_id: str,
                                        card_number: str) -> str:
        """
        Generate a formatted receipt for balance inquiry
        
        Args:
            account: The account being queried
            atm_location: Physical location of the ATM
            atm_id: Identifier for the ATM terminal
            transaction_id: Unique transaction identifier
            card_number: Customer's card number
            
        Returns:
            Formatted receipt as a string
        """
        receipt = []
        
        # Header
        receipt.append(cls.DIVIDER)
        receipt.append(cls._center_text(cls.BANK_NAME + " ATM RECEIPT"))
        receipt.append(cls.DIVIDER)
        
        # Transaction details
        current_time = datetime.now()
        receipt.append(f"Date         : {current_time.strftime('%d/%m/%Y')}          Time: {current_time.strftime('%H:%M:%S')}")
        receipt.append(f"ATM ID       : {atm_id}")
        receipt.append(f"Branch       : {atm_location}")
        receipt.append(cls.DIVIDER)
        
        # Card and account information
        receipt.append(f"Card Number  : {cls._mask_card_number(card_number)}")
        receipt.append(f"Transaction  : BALANCE ENQUIRY")
        receipt.append(f"Account Type : {account.account_type}")
        receipt.append(cls.DIVIDER)
        
        # Balance information
        receipt.append(f"Available Bal: {cls._format_amount(account.balance)}")
        receipt.append(f"Ledger Balance: {cls._format_amount(account.balance)}")
        receipt.append(cls.DIVIDER)
        
        # Response information
        receipt.append(f"Response     : ENQUIRY SUCCESSFUL")
        receipt.append(f"Response Code: 00")
        receipt.append(cls.DIVIDER)
        
        # Footer
        receipt.append(f"Helpline No. : 1800-XXX-XXXX")
        receipt.append(f"Website      : www.cbsbank.com")
        receipt.append(cls.DIVIDER)
        receipt.append(cls._center_text("Thank you for banking with CBS Banking System!"))
        receipt.append(cls.DIVIDER)
        
        return "\n".join(receipt)
    
    @classmethod
    def generate_mini_statement_receipt(cls,
                                       account: Account,
                                       transactions: List[Transaction],
                                       atm_location: str,
                                       atm_id: str,
                                       card_number: str) -> str:
        """
        Generate a formatted mini statement receipt
        
        Args:
            account: The account for the mini statement
            transactions: List of recent transactions
            atm_location: Physical location of the ATM
            atm_id: Identifier for the ATM terminal
            card_number: Customer's card number
            
        Returns:
            Formatted receipt as a string
        """
        receipt = []
        
        # Header
        receipt.append(cls.DIVIDER)
        receipt.append(cls._center_text(cls.BANK_NAME + " ATM RECEIPT"))
        receipt.append(cls.DIVIDER)
        
        # Transaction details
        current_time = datetime.now()
        receipt.append(f"Date         : {current_time.strftime('%d/%m/%Y')}          Time: {current_time.strftime('%H:%M:%S')}")
        receipt.append(f"ATM ID       : {atm_id}")
        receipt.append(f"Branch       : {atm_location}")
        receipt.append(cls.DIVIDER)
        
        # Card and account information
        receipt.append(f"Card Number  : {cls._mask_card_number(card_number)}")
        receipt.append(f"Transaction  : MINI STATEMENT")
        receipt.append(f"Account Type : {account.account_type}")
        receipt.append(cls.DIVIDER)
        
        # Recent transactions
        receipt.append("Last 5 Transactions:")
        
        # Display up to 5 most recent transactions
        recent_txns = transactions[:5] if len(transactions) > 5 else transactions
        for txn in recent_txns:
            date_str = txn.timestamp.strftime('%d/%m')
            
            # Determine if debit or credit
            txn_type = "DR" if txn.is_debit() else "CR"
            
            # Get short description based on transaction type
            desc = cls._get_short_transaction_type(txn.transaction_type)
                
            receipt.append(f"{date_str}  {txn_type}  {cls._format_amount(txn.amount)}  {desc}")
            
        receipt.append(cls.DIVIDER)
        
        # Current balance
        receipt.append(f"Available Bal: {cls._format_amount(account.balance)}")
        receipt.append(f"Response     : SUCCESSFUL")
        receipt.append(cls.DIVIDER)
        
        # Footer
        receipt.append(f"Helpline No. : 1800-XXX-XXXX")
        receipt.append(f"Website      : www.cbsbank.com")
        receipt.append(cls.DIVIDER)
        receipt.append(cls._center_text("Thank you for banking with CBS Banking System!"))
        receipt.append(cls.DIVIDER)
        
        return "\n".join(receipt)
    
    @classmethod
    def generate_transfer_receipt(cls,
                                 transaction: Transaction,
                                 source_account: Account,
                                 destination_account_number: str,
                                 atm_location: str,
                                 atm_id: str,
                                 card_number: str) -> str:
        """
        Generate a formatted receipt for fund transfer transactions
        
        Args:
            transaction: The transfer transaction
            source_account: The account funds are transferred from
            destination_account_number: The receiving account number
            atm_location: Physical location of the ATM
            atm_id: Identifier for the ATM terminal
            card_number: Customer's card number
            
        Returns:
            Formatted receipt as a string
        """
        receipt = []
        
        # Header
        receipt.append(cls.DIVIDER)
        receipt.append(cls._center_text(cls.BANK_NAME + " ATM RECEIPT"))
        receipt.append(cls.DIVIDER)
        
        # Transaction details
        current_time = transaction.timestamp
        receipt.append(f"Date         : {current_time.strftime('%d/%m/%Y')}          Time: {current_time.strftime('%H:%M:%S')}")
        receipt.append(f"ATM ID       : {atm_id}")
        receipt.append(f"Branch       : {atm_location}")
        receipt.append(cls.DIVIDER)
        
        # Card and account information
        receipt.append(f"Card Number  : {cls._mask_card_number(card_number)}")
        receipt.append(f"Transaction  : FUND TRANSFER")
        receipt.append(f"From Account : {cls._mask_account_number(source_account.account_number)}")
        receipt.append(f"To Account   : {cls._mask_account_number(destination_account_number)}")
        receipt.append(f"Account Type : {source_account.account_type}")
        receipt.append(cls.DIVIDER)
        
        # Amount information
        receipt.append(f"Txn Ref No.  : {transaction.transaction_id}")
        receipt.append(f"Amount       : {cls._format_amount(transaction.amount)}")
        if transaction.fee > Decimal('0'):
            receipt.append(f"Charges      : {cls._format_amount(transaction.fee)}")
        receipt.append(f"Available Bal: {cls._format_amount(transaction.balance_after)}")
        receipt.append(cls.DIVIDER)
        
        # Response information
        receipt.append(f"Response     : TRANSFER SUCCESSFUL")
        receipt.append(f"Response Code: 00")
        receipt.append(cls.DIVIDER)
        
        # Footer
        receipt.append(f"Helpline No. : 1800-XXX-XXXX")
        receipt.append(f"Website      : www.cbsbank.com")
        receipt.append(cls.DIVIDER)
        receipt.append(cls._center_text("Thank you for banking with CBS Banking System!"))
        receipt.append(cls.DIVIDER)
        
        return "\n".join(receipt)
    
    @classmethod
    def generate_transaction_failed_receipt(cls,
                                          transaction_type: str,
                                          error_code: str,
                                          error_message: str,
                                          atm_location: str,
                                          atm_id: str,
                                          card_number: str,
                                          account_type: str = None,
                                          transaction_amount: Decimal = None,
                                          transaction_id: str = None) -> str:
        """
        Generate a formatted receipt for failed transactions
        
        Args:
            transaction_type: Type of transaction that failed
            error_code: Error code for troubleshooting
            error_message: Human-readable error message
            atm_location: Physical location of the ATM
            atm_id: Identifier for the ATM terminal
            card_number: Customer's card number
            account_type: Optional account type
            transaction_amount: Optional attempted transaction amount
            transaction_id: Optional transaction reference number
            
        Returns:
            Formatted receipt as a string
        """
        receipt = []
        
        # Header
        receipt.append(cls.DIVIDER)
        receipt.append(cls._center_text(cls.BANK_NAME + " ATM RECEIPT"))
        receipt.append(cls.DIVIDER)
        
        # Transaction details
        current_time = datetime.now()
        receipt.append(f"Date         : {current_time.strftime('%d/%m/%Y')}          Time: {current_time.strftime('%H:%M:%S')}")
        receipt.append(f"ATM ID       : {atm_id}")
        receipt.append(f"Branch       : {atm_location}")
        receipt.append(cls.DIVIDER)
        
        # Card and account information
        receipt.append(f"Card Number  : {cls._mask_card_number(card_number)}")
        receipt.append(f"Transaction  : {transaction_type}")
        if account_type:
            receipt.append(f"Account Type : {account_type}")
        receipt.append(cls.DIVIDER)
        
        # Transaction details if available
        if transaction_id:
            receipt.append(f"Txn Ref No.  : {transaction_id}")
        if transaction_amount:
            receipt.append(f"Amount       : {cls._format_amount(transaction_amount)}")
        receipt.append(cls.DIVIDER)
        
        # Response information
        receipt.append(f"Response     : TRANSACTION FAILED")
        receipt.append(f"Reason       : {error_message}")
        receipt.append(f"Response Code: {error_code}")
        receipt.append(cls.DIVIDER)
        
        # Footer
        receipt.append(f"Helpline No. : 1800-XXX-XXXX")
        receipt.append(f"Website      : www.cbsbank.com")
        receipt.append(cls.DIVIDER)
        receipt.append(cls._center_text("Sorry for the inconvenience. Please try again."))
        receipt.append(cls.DIVIDER)
        
        return "\n".join(receipt)
    
    @classmethod
    def generate_pin_change_receipt(cls,
                                   atm_location: str,
                                   atm_id: str,
                                   card_number: str,
                                   transaction_id: str) -> str:
        """
        Generate a formatted receipt for PIN change operation
        
        Args:
            atm_location: Physical location of the ATM
            atm_id: Identifier for the ATM terminal
            card_number: Customer's card number
            transaction_id: Unique transaction identifier
            
        Returns:
            Formatted receipt as a string
        """
        receipt = []
        
        # Header
        receipt.append(cls.DIVIDER)
        receipt.append(cls._center_text(cls.BANK_NAME + " ATM RECEIPT"))
        receipt.append(cls.DIVIDER)
        
        # Transaction details
        current_time = datetime.now()
        receipt.append(f"Date         : {current_time.strftime('%d/%m/%Y')}          Time: {current_time.strftime('%H:%M:%S')}")
        receipt.append(f"ATM ID       : {atm_id}")
        receipt.append(f"Branch       : {atm_location}")
        receipt.append(cls.DIVIDER)
        
        # Card information
        receipt.append(f"Card Number  : {cls._mask_card_number(card_number)}")
        receipt.append(f"Transaction  : PIN CHANGE")
        receipt.append(cls.DIVIDER)
        
        # Transaction details
        receipt.append(f"Txn Ref No.  : {transaction_id}")
        receipt.append(cls.DIVIDER)
        
        # Response information
        receipt.append(f"Response     : PIN CHANGE SUCCESSFUL")
        receipt.append(f"Response Code: 00")
        receipt.append(cls.DIVIDER)
        
        # Security message
        receipt.append(f"NOTE: For security reasons, your PIN")
        receipt.append(f"      is not printed on this receipt.")
        receipt.append(cls.DIVIDER)
        
        # Footer
        receipt.append(f"Helpline No. : 1800-XXX-XXXX")
        receipt.append(f"Website      : www.cbsbank.com")
        receipt.append(cls.DIVIDER)
        receipt.append(cls._center_text("Thank you for banking with CBS Banking System!"))
        receipt.append(cls.DIVIDER)
        
        return "\n".join(receipt)
    
    #
    # Helper methods for formatting
    #
    
    @classmethod
    def _center_text(cls, text: str) -> str:
        """Center text within receipt width"""
        return text.center(cls.RECEIPT_WIDTH)
    
    @classmethod
    def _format_amount(cls, amount: Decimal) -> str:
        """Format currency amount with proper symbol and formatting"""
        return f"₹{amount:,.2f}"
    
    @classmethod
    def _mask_account_number(cls, account_number: str) -> str:
        """Mask account number for privacy, showing only last 4 digits"""
        if len(account_number) <= 4:
            return account_number
        
        return f"XXXX{account_number[-4:]}"
    
    @classmethod
    def _mask_card_number(cls, card_number: str) -> str:
        """Mask card number showing only last 4 digits"""
        if len(card_number) <= 4:
            return "X" * len(card_number)
            
        return f"XXXX-XXXX-XXXX-{card_number[-4:]}"
    
    @classmethod
    def _get_short_transaction_type(cls, transaction_type: str) -> str:
        """Convert transaction type to short form for mini statement"""
        type_map = {
            "ATM_WITHDRAWAL": "ATM Withdrawal",
            "ATM_DEPOSIT": "Cash Deposit",
            "ATM_TRANSFER": "Fund Transfer",
            "ATM_FEE": "ATM Fee",
            "ATM_MINI_STATEMENT": "Mini Statement",
            "ATM_INQUIRY": "Balance Inquiry",
            "SALARY_CREDIT": "Salary Credit",
            "POS_PURCHASE": "POS Purchase",
            "ONLINE_PAYMENT": "Online Payment",
            "CHEQUE_DEPOSIT": "Cheque Deposit", 
            "DIRECT_DEBIT": "Direct Debit",
            "LOAN_DISBURSAL": "Loan Disbursal",
            "INTEREST_CREDIT": "Interest Credit"
        }
        return type_map.get(transaction_type, transaction_type)
