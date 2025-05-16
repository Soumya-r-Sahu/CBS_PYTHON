"""
Accounts Module Test Script

This script demonstrates the accounts module functionality with Clean Architecture.
It performs basic operations like creating an account, depositing, and withdrawing funds.
"""

import os
import sys
import logging
from decimal import Decimal
from uuid import uuid4
from pprint import pprint
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the accounts container and services
from core_banking.accounts.di_container import container

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_clean_architecture():
    """
    Test the clean architecture implementation of the accounts module
    
    This test demonstrates the usage of all the core use cases:
    - Creating accounts
    - Depositing funds
    - Withdrawing funds
    - Transferring funds
    - Getting account details
    - Getting account statement
    - Closing an account
    """
    try:
        # Get the account service from the container
        account_service = container.account_service()
        
        logger.info("Starting Clean Architecture test for Accounts module...")
        
        # Create customer IDs for testing
        customer_id_1 = uuid4()
        customer_id_2 = uuid4()
        
        logger.info(f"Using test customer IDs: {customer_id_1}, {customer_id_2}")
        
        # Test 1: Create accounts
        logger.info("Test 1: Creating accounts...")
        
        savings_result = account_service.create_account(
            customer_id=customer_id_1,
            account_type="SAVINGS",
            initial_deposit=Decimal("5000.00"),
            currency="USD"
        )
        
        current_result = account_service.create_account(
            customer_id=customer_id_1,
            account_type="CURRENT",
            initial_deposit=Decimal("10000.00"),
            currency="USD"
        )
        
        savings_account_id = savings_result["account_id"]
        current_account_id = current_result["account_id"]
        
        logger.info(f"Created SAVINGS account: {savings_account_id}")
        logger.info(f"Created CURRENT account: {current_account_id}")
        
        # Test 2: Deposit funds
        logger.info("Test 2: Depositing funds...")
        
        deposit_result = account_service.deposit(
            account_id=savings_account_id,
            amount=Decimal("1500.00"),
            description="Salary deposit",
            reference_id="SALARY-MAY-2025"
        )
        
        logger.info(f"Deposit result: {deposit_result['success']}")
        logger.info(f"New balance: {deposit_result['balance']}")
        
        # Test 3: Withdraw funds
        logger.info("Test 3: Withdrawing funds...")
        
        withdraw_result = account_service.withdraw(
            account_id=current_account_id,
            amount=Decimal("2000.00"),
            description="ATM Withdrawal",
            reference_id="ATM-001-20250516"
        )
        
        logger.info(f"Withdrawal result: {withdraw_result['success']}")
        logger.info(f"New balance: {withdraw_result['balance']}")
        
        # Test 4: Transfer funds
        logger.info("Test 4: Transferring funds between accounts...")
        
        transfer_result = account_service.transfer(
            source_account_id=current_account_id,
            target_account_id=savings_account_id,
            amount=Decimal("1500.00"),
            description="Monthly savings transfer",
            reference_id="TRANSFER-MS-20250516"
        )
        
        logger.info(f"Transfer result: {transfer_result['success']}")
        logger.info(f"Source account balance: {transfer_result['source_balance']}")
        logger.info(f"Target account balance: {transfer_result['target_balance']}")
        
        # Test 5: Get account details
        logger.info("Test 5: Getting account details...")
        
        details_result = account_service.get_account_details(
            account_id=savings_account_id
        )
        
        logger.info(f"Account number: {details_result['account_number']}")
        logger.info(f"Account type: {details_result['account_type']}")
        logger.info(f"Balance: {details_result['balance']}")
        logger.info(f"Status: {details_result['status']}")
        
        # Test 6: Get account statement
        logger.info("Test 6: Getting account statement...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        statement_result = account_service.get_account_statement(
            account_id=savings_account_id,
            start_date=start_date,
            end_date=end_date
        )
        
        logger.info(f"Statement period: {statement_result['statement_period']['start_date']} to {statement_result['statement_period']['end_date']}")
        logger.info(f"Opening balance: {statement_result['opening_balance']}")
        logger.info(f"Closing balance: {statement_result['closing_balance']}")
        logger.info(f"Total transactions: {statement_result['total_records']}")
        
        # Test 7: Close account (testing both success and error cases)
        logger.info("Test 7: Closing account...")
        
        # Create a temporary account to close
        temp_account_result = account_service.create_account(
            customer_id=customer_id_2,
            account_type="SAVINGS",
            initial_deposit=Decimal("100.00"),
            currency="USD"
        )
        
        temp_account_id = temp_account_result["account_id"]
        
        # Withdraw all funds
        account_service.withdraw(
            account_id=temp_account_id,
            amount=Decimal("100.00"),
            description="Withdraw all funds before closing"
        )
        
        # Now close the account
        close_result = account_service.close_account(
            account_id=temp_account_id,
            reason="Testing account closure"
        )
        
        logger.info(f"Account closure result: {close_result['success']}")
        logger.info(f"Account status: {close_result['status']}")
        
        # Try to close an account with balance (should fail)
        try:
            account_service.close_account(
                account_id=savings_account_id,
                reason="Should fail due to balance"
            )
        except ValueError as e:
            logger.info(f"Expected error when trying to close account with balance: {str(e)}")
        
        logger.info("Clean Architecture test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    test_clean_architecture()
