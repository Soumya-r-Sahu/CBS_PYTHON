"""
Account and Transaction Integration Tests

This module contains integration tests for account and transaction operations.
"""

import pytest
from datetime import datetime, date, timedelta
import mysql.connector
from decimal import Decimal
import uuid

class TestAccountTransactions:
    """Integration tests for accounts and transactions."""
    
    def test_account_balance_after_multiple_transactions(self, clean_test_db, sample_account_data):
        """Test that account balance is correct after multiple transactions."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Get starting balance
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        initial_balance = float(cursor.fetchone()[0])
        
        # Create a series of transactions
        transactions = [
            # (type, amount)
            ("DEPOSIT", 500.00),      # +500
            ("WITHDRAWAL", 200.00),   # -200
            ("DEPOSIT", 1000.00),     # +1000
            ("PAYMENT", 150.00),      # -150
            ("WITHDRAWAL", 300.00)    # -300
        ]
        
        # Calculate expected final balance
        expected_balance = initial_balance
        for t_type, amount in transactions:
            if t_type in ["WITHDRAWAL", "PAYMENT", "TRANSFER"]:
                expected_balance -= amount
            else:
                expected_balance += amount
        
        # Execute transactions
        current_balance = initial_balance
        for i, (t_type, amount) in enumerate(transactions):
            transaction_id = f"INTTX{i+1}"
            
            if t_type in ["WITHDRAWAL", "PAYMENT", "TRANSFER"]:
                balance_after = current_balance - amount
            else:
                balance_after = current_balance + amount
                
            cursor.execute(
                """
                INSERT INTO cbs_transactions 
                (transaction_id, account_number, transaction_type, channel, amount, 
                 balance_before, balance_after, value_date, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    transaction_id,
                    sample_account_data["account_number"],
                    t_type,
                    "BRANCH",
                    amount,
                    current_balance,
                    balance_after,
                    date.today(),
                    "SUCCESS"
                )
            )
            conn.commit()
            
            # Update current balance
            current_balance = balance_after
        
        # Update account balance after all transactions
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (current_balance, sample_account_data["account_number"])
        )
        conn.commit()
        
        # Verify final account balance
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        final_balance = float(cursor.fetchone()[0])
        
        assert final_balance == expected_balance
        
        # Verify balance through transaction history
        cursor.execute(
            """
            SELECT transaction_type, amount, balance_before, balance_after
            FROM cbs_transactions 
            WHERE account_number = %s
            ORDER BY transaction_date
            """,
            (sample_account_data["account_number"],)
        )
        transactions_history = cursor.fetchall()
        
        # Check last transaction's balance_after matches account balance
        last_transaction = transactions_history[-1]
        assert float(last_transaction[3]) == final_balance
        
        cursor.close()
    
    def test_transfer_between_accounts(self, clean_test_db, sample_account_data, sample_customer_data):
        """Test transferring money between accounts."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Create a second account for the same customer
        second_account_number = "ACC2002TEST"
        cursor.execute(
            """
            INSERT INTO cbs_accounts 
            (account_number, customer_id, account_type, balance, status, branch_code, ifsc_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                second_account_number,
                sample_customer_data["customer_id"],
                "SAVINGS",
                2000.00,
                "ACTIVE",
                "BR001",
                "CBSTEST001"
            )
        )
        conn.commit()
        
        # Get starting balances
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        source_balance = float(cursor.fetchone()[0])
        
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (second_account_number,)
        )
        destination_balance = float(cursor.fetchone()[0])
        
        # Create transfer
        transfer_amount = 500.00
        transaction_id = "TRANSFER001"
        transfer_id = "TRF001"
        
        # First create the transaction
        cursor.execute(
            """
            INSERT INTO cbs_transactions 
            (transaction_id, account_number, transaction_type, channel, amount, 
             balance_before, balance_after, value_date, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                transaction_id,
                sample_account_data["account_number"],
                "TRANSFER",
                "INTERNET",
                transfer_amount,
                source_balance,
                source_balance - transfer_amount,
                date.today(),
                "SUCCESS"
            )
        )
        
        # Create the transfer record
        cursor.execute(
            """
            INSERT INTO cbs_transfers
            (transfer_id, transaction_id, source_account, destination_account, 
             transfer_type, amount, transfer_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
            """,
            (
                transfer_id,
                transaction_id,
                sample_account_data["account_number"],
                second_account_number,
                "INTERNAL",
                transfer_amount,
                "SUCCESS"
            )
        )
        conn.commit()
        
        # Update both account balances
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (source_balance - transfer_amount, sample_account_data["account_number"])
        )
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (destination_balance + transfer_amount, second_account_number)
        )
        conn.commit()
        
        # Create the credit transaction for the destination account
        cursor.execute(
            """
            INSERT INTO cbs_transactions 
            (transaction_id, account_number, transaction_type, channel, amount, 
             balance_before, balance_after, value_date, status, reference_number) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                f"{transaction_id}-CR",  # Credit transaction
                second_account_number,
                "DEPOSIT",
                "INTERNET",
                transfer_amount,
                destination_balance,
                destination_balance + transfer_amount,
                date.today(),
                "SUCCESS",
                transaction_id  # Reference the original transaction
            )
        )
        conn.commit()
        
        # Verify balances after transfer
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        source_balance_after = float(cursor.fetchone()[0])
        
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (second_account_number,)
        )
        destination_balance_after = float(cursor.fetchone()[0])
        
        # Check balances
        assert source_balance_after == source_balance - transfer_amount
        assert destination_balance_after == destination_balance + transfer_amount
        
        # Verify transfer records
        cursor.execute(
            """
            SELECT tr.transfer_id, tr.source_account, tr.destination_account, tr.amount,
                  tx.transaction_id, tx.transaction_type
            FROM cbs_transfers tr
            JOIN cbs_transactions tx ON tr.transaction_id = tx.transaction_id
            WHERE tr.transfer_id = %s
            """,
            (transfer_id,)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == transfer_id
        assert result[1] == sample_account_data["account_number"]
        assert result[2] == second_account_number
        assert float(result[3]) == transfer_amount
        assert result[4] == transaction_id
        assert result[5] == "TRANSFER"
        
        # Verify both transactions are linked
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM cbs_transactions 
            WHERE transaction_id IN (%s, %s)
            """,
            (transaction_id, f"{transaction_id}-CR")
        )
        count = cursor.fetchone()[0]
        assert count == 2
        
        cursor.close()
    
    def test_insufficient_balance_handling(self, clean_test_db, sample_account_data):
        """Test handling of transactions with insufficient balance."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Get current balance
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        current_balance = float(cursor.fetchone()[0])
        
        # Try a withdrawal larger than the balance
        large_amount = current_balance + 1000.00  # Exceeds balance by 1000
        transaction_id = "INSUFFICIENT001"
        
        # Create a transaction but mark it as FAILED
        cursor.execute(
            """
            INSERT INTO cbs_transactions 
            (transaction_id, account_number, transaction_type, channel, amount, 
             balance_before, balance_after, value_date, status, remarks) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                transaction_id,
                sample_account_data["account_number"],
                "WITHDRAWAL",
                "ATM",
                large_amount,
                current_balance,
                current_balance,  # No change in balance
                date.today(),
                "FAILED",
                "Insufficient funds"
            )
        )
        conn.commit()
        
        # Verify the account balance didn't change
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        balance_after = float(cursor.fetchone()[0])
        
        assert balance_after == current_balance
        
        # Verify the transaction status
        cursor.execute(
            "SELECT status, remarks FROM cbs_transactions WHERE transaction_id = %s",
            (transaction_id,)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == "FAILED"
        assert "Insufficient" in result[1]
        
        cursor.close()
    
    def test_transaction_reversal(self, clean_test_db, sample_account_data):
        """Test reversing a transaction."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Get starting balance
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        initial_balance = float(cursor.fetchone()[0])
        
        # Create a withdrawal transaction
        withdrawal_amount = 300.00
        transaction_id = "REVERSAL001"
        
        cursor.execute(
            """
            INSERT INTO cbs_transactions 
            (transaction_id, account_number, transaction_type, channel, amount, 
             balance_before, balance_after, value_date, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                transaction_id,
                sample_account_data["account_number"],
                "WITHDRAWAL",
                "ATM",
                withdrawal_amount,
                initial_balance,
                initial_balance - withdrawal_amount,
                date.today(),
                "SUCCESS"
            )
        )
        conn.commit()
        
        # Update account balance
        new_balance = initial_balance - withdrawal_amount
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (new_balance, sample_account_data["account_number"])
        )
        conn.commit()
        
        # Now reverse the transaction
        reversal_transaction_id = "REVERSAL001-REV"
        
        cursor.execute(
            """
            INSERT INTO cbs_transactions 
            (transaction_id, account_number, transaction_type, channel, amount, 
             balance_before, balance_after, value_date, status, reference_number, remarks) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                reversal_transaction_id,
                sample_account_data["account_number"],
                "REVERSAL",
                "SYSTEM",
                withdrawal_amount,
                new_balance,
                initial_balance,  # Back to initial balance
                date.today(),
                "SUCCESS",
                transaction_id,
                f"Reversal of transaction {transaction_id}"
            )
        )
        conn.commit()
        
        # Update the status of the original transaction
        cursor.execute(
            """
            UPDATE cbs_transactions 
            SET status = %s, remarks = %s
            WHERE transaction_id = %s
            """,
            ("REVERSED", "Transaction reversed", transaction_id)
        )
        conn.commit()
        
        # Update account balance back to initial
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (initial_balance, sample_account_data["account_number"])
        )
        conn.commit()
        
        # Verify account balance is back to initial
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        final_balance = float(cursor.fetchone()[0])
        
        assert final_balance == initial_balance
        
        # Verify the original transaction is marked as reversed
        cursor.execute(
            "SELECT status FROM cbs_transactions WHERE transaction_id = %s",
            (transaction_id,)
        )
        status = cursor.fetchone()[0]
        
        assert status == "REVERSED"
        
        # Verify the reversal transaction exists and links to the original
        cursor.execute(
            "SELECT reference_number FROM cbs_transactions WHERE transaction_id = %s",
            (reversal_transaction_id,)
        )
        reference = cursor.fetchone()[0]
        
        assert reference == transaction_id
        
        cursor.close()
    
    def test_scheduled_recurring_transfer(self, clean_test_db, sample_account_data):
        """Test scheduled recurring transfer functionality."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Create a second account as destination
        dest_account = "ACC3001TEST"
        cursor.execute(
            """
            INSERT INTO cbs_accounts 
            (account_number, customer_id, account_type, balance, status, branch_code, ifsc_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                dest_account,
                sample_account_data["customer_id"],
                "SAVINGS",
                1000.00,
                "ACTIVE",
                "BR001",
                "CBSTEST001"
            )
        )
        conn.commit()
        
        # Create a scheduled recurring transfer
        transfer_amount = 100.00
        
        # Create a transfer record without a transaction yet (it's scheduled)
        transfer_id = "SCHED001"
        cursor.execute(
            """
            INSERT INTO cbs_transfers
            (transfer_id, source_account, destination_account, 
             transfer_type, amount, scheduled_transfer, recurring_transfer, 
             frequency, next_execution_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                transfer_id,
                sample_account_data["account_number"],
                dest_account,
                "INTERNAL",
                transfer_amount,
                True,  # scheduled
                True,  # recurring
                "MONTHLY",
                date.today() + timedelta(days=30),  # Next month
                "SCHEDULED"
            )
        )
        conn.commit()
        
        # Verify the scheduled transfer exists
        cursor.execute(
            """
            SELECT transfer_id, source_account, destination_account, amount, 
                   frequency, next_execution_date, status
            FROM cbs_transfers
            WHERE transfer_id = %s
            """,
            (transfer_id,)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == transfer_id
        assert result[1] == sample_account_data["account_number"]
        assert result[2] == dest_account
        assert float(result[3]) == transfer_amount
        assert result[4] == "MONTHLY"
        assert result[6] == "SCHEDULED"
        
        # Now simulate executing the scheduled transfer
        get_source_balance_sql = """
            SELECT balance FROM cbs_accounts WHERE account_number = %s
        """
        cursor.execute(get_source_balance_sql, (sample_account_data["account_number"],))
        source_balance = float(cursor.fetchone()[0])
        
        cursor.execute(get_source_balance_sql, (dest_account,))
        dest_balance = float(cursor.fetchone()[0])
        
        # Create a transaction for the executed scheduled transfer
        transaction_id = f"{transfer_id}-EXEC1"
        cursor.execute(
            """
            INSERT INTO cbs_transactions 
            (transaction_id, account_number, transaction_type, channel, amount, 
             balance_before, balance_after, value_date, status, remarks) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                transaction_id,
                sample_account_data["account_number"],
                "TRANSFER",
                "STANDING_INSTRUCTION",
                transfer_amount,
                source_balance,
                source_balance - transfer_amount,
                date.today(),
                "SUCCESS",
                "Monthly recurring transfer"
            )
        )
        
        # Update the transfer record with transaction ID
        cursor.execute(
            """
            UPDATE cbs_transfers
            SET transaction_id = %s, status = %s, transfer_date = NOW(),
                next_execution_date = %s
            WHERE transfer_id = %s
            """,
            (
                transaction_id,
                "SUCCESS",
                date.today() + timedelta(days=60),  # Next execution in 2 months
                transfer_id
            )
        )
        
        # Update account balances
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (source_balance - transfer_amount, sample_account_data["account_number"])
        )
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (dest_balance + transfer_amount, dest_account)
        )
        conn.commit()
        
        # Create the destination credit transaction
        cursor.execute(
            """
            INSERT INTO cbs_transactions 
            (transaction_id, account_number, transaction_type, channel, amount, 
             balance_before, balance_after, value_date, status, reference_number) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                f"{transaction_id}-CR",
                dest_account,
                "DEPOSIT",
                "STANDING_INSTRUCTION",
                transfer_amount,
                dest_balance,
                dest_balance + transfer_amount,
                date.today(),
                "SUCCESS",
                transaction_id
            )
        )
        conn.commit()
        
        # Verify the transfer is marked as executed but still active for future
        cursor.execute(
            """
            SELECT status, transaction_id, next_execution_date 
            FROM cbs_transfers
            WHERE transfer_id = %s
            """,
            (transfer_id,)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == "SUCCESS"
        assert result[1] == transaction_id
        
        # Verify account balances
        cursor.execute(get_source_balance_sql, (sample_account_data["account_number"],))
        final_source_balance = float(cursor.fetchone()[0])
        
        cursor.execute(get_source_balance_sql, (dest_account,))
        final_dest_balance = float(cursor.fetchone()[0])
        
        assert final_source_balance == source_balance - transfer_amount
        assert final_dest_balance == dest_balance + transfer_amount
        
        cursor.close()
    
    def test_overdraft_account(self, clean_test_db, sample_customer_data):
        """Test account with overdraft facility."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Create an overdraft-enabled account
        od_account = "OD001TEST"
        initial_balance = 1000.00
        overdraft_limit = 2000.00
        
        cursor.execute(
            """
            INSERT INTO cbs_accounts 
            (account_number, customer_id, account_type, balance, status, branch_code, 
             ifsc_code, overdraft_limit)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                od_account,
                sample_customer_data["customer_id"],
                "CURRENT",  # Usually current accounts have overdraft
                initial_balance,
                "ACTIVE",
                "BR001",
                "CBSTEST001",
                overdraft_limit
            )
        )
        conn.commit()
        
        # Try a withdrawal exceeding balance but within overdraft
        withdrawal_amount = 2500.00  # Exceeds balance but within overdraft+balance
        transaction_id = "ODTEST001"
        
        cursor.execute(
            """
            INSERT INTO cbs_transactions 
            (transaction_id, account_number, transaction_type, channel, amount, 
             balance_before, balance_after, value_date, status, remarks) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                transaction_id,
                od_account,
                "WITHDRAWAL",
                "BRANCH",
                withdrawal_amount,
                initial_balance,
                initial_balance - withdrawal_amount,  # Negative balance
                date.today(),
                "SUCCESS",
                "Withdrawal using overdraft"
            )
        )
        conn.commit()
        
        # Update account balance
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (initial_balance - withdrawal_amount, od_account)
        )
        conn.commit()
        
        # Verify the new negative balance
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (od_account,)
        )
        new_balance = float(cursor.fetchone()[0])
        
        assert new_balance < 0
        assert new_balance == initial_balance - withdrawal_amount
        assert abs(new_balance) <= overdraft_limit  # Within overdraft limit
        
        # Try another withdrawal that would exceed overdraft limit
        excessive_amount = 1000.00  # Would exceed overdraft limit if allowed
        excessive_txn_id = "ODTEST002"
        
        cursor.execute(
            """
            INSERT INTO cbs_transactions 
            (transaction_id, account_number, transaction_type, channel, amount, 
             balance_before, balance_after, value_date, status, remarks) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                excessive_txn_id,
                od_account,
                "WITHDRAWAL",
                "ATM",
                excessive_amount,
                new_balance,
                new_balance,  # No change
                date.today(),
                "FAILED",
                "Exceeds overdraft limit"
            )
        )
        conn.commit()
        
        # Verify that the failed transaction didn't change the balance
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (od_account,)
        )
        final_balance = float(cursor.fetchone()[0])
        
        assert final_balance == new_balance  # Balance unchanged
        
        # Verify second transaction was properly rejected
        cursor.execute(
            "SELECT status, remarks FROM cbs_transactions WHERE transaction_id = %s",
            (excessive_txn_id,)
        )
        result = cursor.fetchone()
        
        assert result[0] == "FAILED"
        assert "overdraft limit" in result[1].lower()
        
        cursor.close()
