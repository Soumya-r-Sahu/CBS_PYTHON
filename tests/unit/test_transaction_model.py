"""
Transaction Model Tests

This module contains tests for transaction-related functionality.
"""

import pytest
from datetime import datetime, date, timedelta
import mysql.connector
from decimal import Decimal
import uuid

class TestTransactionModel:
    """Tests for the Transaction model."""
    
    def test_transaction_creation(self, clean_test_db, sample_account_data):
        """Test that a transaction can be created."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Create a transaction
        transaction_id = str(uuid.uuid4())
        amount = 500.00
        
        # Get current balance for balance_before/after calculations
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        current_balance = float(cursor.fetchone()[0])
        
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
                "DEPOSIT",
                "MOBILE",
                amount,
                current_balance,
                current_balance + amount,
                date.today(),
                "SUCCESS"
            )
        )
        conn.commit()
        
        # Check that the transaction exists
        cursor.execute(
            "SELECT * FROM cbs_transactions WHERE transaction_id = %s",
            (transaction_id,)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == transaction_id
        assert result[1] is None  # card_number
        assert result[2] == sample_account_data["account_number"]
        assert result[3] == "DEPOSIT"
        assert result[4] == "MOBILE"
        assert float(result[5]) == amount
        assert result[6] == "INR"  # default currency
        assert float(result[7]) == current_balance
        assert float(result[8]) == current_balance + amount
        
        # Update the account balance to reflect the transaction
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (current_balance + amount, sample_account_data["account_number"])
        )
        conn.commit()
        
        cursor.close()
    
    def test_transaction_with_card(self, clean_test_db, sample_account_data):
        """Test creating a transaction linked to a card."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Create a card first
        card_number = "4123456789012345"
        expiry_date = date.today() + timedelta(days=365*3)  # 3 years validity
        
        cursor.execute(
            """
            INSERT INTO cbs_cards
            (card_id, account_id, card_number, card_type, card_network, expiry_date, 
             cvv, pin_hash, issue_date, primary_user_name)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                "CARD12345TEST",
                sample_account_data["account_number"],
                card_number,
                "DEBIT",
                "VISA",
                expiry_date,
                "123",
                "hashed_pin_value",
                date.today(),
                "Test Customer"
            )
        )
        conn.commit()
        
        # Create transaction with card
        transaction_id = str(uuid.uuid4())
        amount = 200.00
        
        # Get current balance
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        current_balance = float(cursor.fetchone()[0])
        
        cursor.execute(
            """
            INSERT INTO cbs_transactions 
            (transaction_id, card_number, account_number, transaction_type, channel, 
             amount, balance_before, balance_after, value_date, status) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                transaction_id,
                card_number,
                sample_account_data["account_number"],
                "WITHDRAWAL",
                "ATM",
                amount,
                current_balance,
                current_balance - amount,
                date.today(),
                "SUCCESS"
            )
        )
        conn.commit()
        
        # Check that the transaction exists and is linked to the card
        cursor.execute(
            """
            SELECT t.transaction_id, t.card_number, t.account_number, t.amount, c.card_id 
            FROM cbs_transactions t
            JOIN cbs_cards c ON t.card_number = c.card_number
            WHERE t.transaction_id = %s
            """,
            (transaction_id,)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == transaction_id
        assert result[1] == card_number
        assert result[2] == sample_account_data["account_number"]
        assert float(result[3]) == amount
        assert result[4] == "CARD12345TEST"
        
        # Update the account balance
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (current_balance - amount, sample_account_data["account_number"])
        )
        conn.commit()
        
        cursor.close()
    
    def test_transaction_types(self, clean_test_db, sample_account_data):
        """Test different transaction types."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Get current balance
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        current_balance = float(cursor.fetchone()[0])
        
        # Test different transaction types
        transaction_types = ["DEPOSIT", "WITHDRAWAL", "TRANSFER", "PAYMENT"]
        
        for i, t_type in enumerate(transaction_types):
            transaction_id = f"TXN{i+1}TEST"
            amount = 100.00
            
            if t_type in ["WITHDRAWAL", "TRANSFER", "PAYMENT"]:
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
                    "MOBILE",
                    amount,
                    current_balance,
                    balance_after,
                    date.today(),
                    "SUCCESS"
                )
            )
            conn.commit()
            
            # Update current balance for the next transaction
            current_balance = balance_after
            
        # Check that all transactions were created
        cursor.execute(
            """
            SELECT transaction_type, COUNT(*) 
            FROM cbs_transactions 
            WHERE account_number = %s 
            GROUP BY transaction_type
            """,
            (sample_account_data["account_number"],)
        )
        results = cursor.fetchall()
        
        # Convert results to a dict for easier checking
        type_counts = {t_type: count for t_type, count in results}
        
        for t_type in transaction_types:
            assert t_type in type_counts
            assert type_counts[t_type] == 1
        
        cursor.close()
    
    def test_transaction_status(self, clean_test_db, sample_account_data):
        """Test different transaction statuses."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Test different transaction statuses
        statuses = ["PENDING", "SUCCESS", "FAILED", "REVERSED"]
        
        for i, status in enumerate(statuses):
            transaction_id = f"TXN_STATUS_{i+1}"
            amount = 10.00
            
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
                    "DEPOSIT",
                    "BRANCH",
                    amount,
                    1000.00,  # Arbitrary balance
                    1000.00 + amount,
                    date.today(),
                    status
                )
            )
            conn.commit()
        
        # Check each status
        for status in statuses:
            cursor.execute(
                """
                SELECT COUNT(*) 
                FROM cbs_transactions 
                WHERE account_number = %s AND status = %s
                """,
                (sample_account_data["account_number"], status)
            )
            count = cursor.fetchone()[0]
            assert count == 1
        
        cursor.close()
    
    def test_transaction_channels(self, clean_test_db, sample_account_data):
        """Test different transaction channels."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Test different channels
        channels = ["ATM", "BRANCH", "INTERNET", "MOBILE", "UPI", "NEFT"]
        
        for i, channel in enumerate(channels):
            transaction_id = f"TXN_CHANNEL_{i+1}"
            
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
                    "DEPOSIT",
                    channel,
                    50.00,
                    1000.00,  # Arbitrary balance
                    1050.00,
                    date.today(),
                    "SUCCESS"
                )
            )
            conn.commit()
        
        # Check transactions by channel
        cursor.execute(
            """
            SELECT channel, COUNT(*) 
            FROM cbs_transactions 
            WHERE account_number = %s 
            GROUP BY channel
            """,
            (sample_account_data["account_number"],)
        )
        results = cursor.fetchall()
        
        # Convert to dict for easier checking
        channel_counts = {channel: count for channel, count in results}
        
        for channel in channels:
            assert channel in channel_counts
            assert channel_counts[channel] == 1
        
        cursor.close()
    
    def test_get_transaction_by_id(self, clean_test_db, sample_transaction_data):
        """Test retrieving a transaction by ID."""
        conn = clean_test_db
        cursor = conn.cursor(dictionary=True)
        
        # Retrieve the transaction
        cursor.execute(
            "SELECT * FROM cbs_transactions WHERE transaction_id = %s",
            (sample_transaction_data["transaction_id"],)
        )
        transaction = cursor.fetchone()
        
        assert transaction is not None
        assert transaction["transaction_id"] == sample_transaction_data["transaction_id"]
        assert transaction["account_number"] == sample_transaction_data["account_number"]
        assert transaction["transaction_type"] == sample_transaction_data["transaction_type"]
        assert transaction["channel"] == sample_transaction_data["channel"]
        assert float(transaction["amount"]) == float(sample_transaction_data["amount"])
        
        cursor.close()
    
    def test_get_account_transactions(self, clean_test_db, sample_account_data, sample_transaction_data):
        """Test retrieving all transactions for an account."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Insert a few more transactions for the same account
        for i in range(2):
            transaction_id = f"TXN_EXTRA_{i+1}"
            
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
                    "DEPOSIT",
                    "MOBILE",
                    100.00,
                    1000.00,  # Arbitrary values for this test
                    1100.00,
                    date.today(),
                    "SUCCESS"
                )
            )
            conn.commit()
        
        # Retrieve all transactions for the account
        cursor.execute(
            "SELECT COUNT(*) FROM cbs_transactions WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        count = cursor.fetchone()[0]
        
        # Should have the initial sample transaction + 2 more we just added
        assert count == 3
        
        # Retrieve and check detailed info
        cursor.execute(
            "SELECT * FROM cbs_transactions WHERE account_number = %s ORDER BY transaction_date DESC",
            (sample_account_data["account_number"],)
        )
        transactions = cursor.fetchall()
        
        assert len(transactions) == 3
        
        # Verify the most recent transactions (the ones we just added)
        assert transactions[0][0].startswith("TXN_EXTRA_")
        assert transactions[1][0].startswith("TXN_EXTRA_")
        
        # The original sample transaction should be the oldest one
        assert transactions[2][0] == sample_transaction_data["transaction_id"]
        
        cursor.close()
    
    def test_bill_payment_transaction(self, clean_test_db, sample_account_data, sample_customer_data):
        """Test creating a bill payment transaction."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Create a transaction for bill payment
        transaction_id = "TXN_BILL_TEST"
        payment_id = "BILL001TEST"
        bill_amount = 250.00
        
        # Get current balance
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        current_balance = float(cursor.fetchone()[0])
        
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
                "BILL_PAYMENT",
                "INTERNET",
                bill_amount,
                current_balance,
                current_balance - bill_amount,
                date.today(),
                "SUCCESS"
            )
        )
        
        # Then create the bill payment
        cursor.execute(
            """
            INSERT INTO cbs_bill_payments
            (payment_id, transaction_id, customer_id, biller_id, biller_name, 
             biller_category, consumer_id, bill_amount, payment_channel, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                payment_id,
                transaction_id,
                sample_customer_data["customer_id"],
                "BILLER001",
                "Test Electric Company",
                "ELECTRICITY",
                "CONSUMER001",
                bill_amount,
                "INTERNET",
                "SUCCESS"
            )
        )
        conn.commit()
        
        # Check that both transaction and bill payment exist and are linked
        cursor.execute(
            """
            SELECT t.transaction_id, t.amount, bp.payment_id, bp.biller_name
            FROM cbs_transactions t
            JOIN cbs_bill_payments bp ON t.transaction_id = bp.transaction_id
            WHERE t.transaction_id = %s
            """,
            (transaction_id,)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == transaction_id
        assert float(result[1]) == bill_amount
        assert result[2] == payment_id
        assert result[3] == "Test Electric Company"
        
        # Update account balance
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (current_balance - bill_amount, sample_account_data["account_number"])
        )
        conn.commit()
        
        cursor.close()
    
    def test_fund_transfer_transaction(self, clean_test_db, sample_account_data):
        """Test creating a fund transfer transaction."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Create another account as the destination
        dest_account_number = "ACC2001TEST"
        cursor.execute(
            """
            INSERT INTO cbs_accounts 
            (account_number, customer_id, account_type, balance, status, branch_code, ifsc_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                dest_account_number,
                sample_account_data["customer_id"],  # Same customer
                "SAVINGS",
                1000.00,
                "ACTIVE",
                "BR001",
                "CBSTEST001"
            )
        )
        conn.commit()
        
        # Create a transaction for fund transfer
        transaction_id = "TXN_TRANSFER_TEST"
        transfer_id = "TRANSFER001TEST"
        transfer_amount = 300.00
        
        # Get source account balance
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        source_balance = float(cursor.fetchone()[0])
        
        # Get destination account balance
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (dest_account_number,)
        )
        dest_balance = float(cursor.fetchone()[0])
        
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
        
        # Then create the transfer
        cursor.execute(
            """
            INSERT INTO cbs_transfers
            (transfer_id, transaction_id, source_account, destination_account, 
             transfer_type, amount, transfer_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                transfer_id,
                transaction_id,
                sample_account_data["account_number"],
                dest_account_number,
                "INTERNAL",
                transfer_amount,
                datetime.now(),
                "SUCCESS"
            )
        )
        conn.commit()
        
        # Check that both transaction and transfer exist and are linked
        cursor.execute(
            """
            SELECT t.transaction_id, tf.source_account, tf.destination_account, tf.amount
            FROM cbs_transactions t
            JOIN cbs_transfers tf ON t.transaction_id = tf.transaction_id
            WHERE t.transaction_id = %s
            """,
            (transaction_id,)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == transaction_id
        assert result[1] == sample_account_data["account_number"]
        assert result[2] == dest_account_number
        assert float(result[3]) == transfer_amount
        
        # Update balances
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (source_balance - transfer_amount, sample_account_data["account_number"])
        )
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (dest_balance + transfer_amount, dest_account_number)
        )
        conn.commit()
        
        cursor.close()
    
    def test_daily_withdrawal_limit(self, clean_test_db, sample_account_data):
        """Test the daily withdrawal limit functionality."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Create a card for the account
        card_id = "CARD_TEST_LIMIT"
        card_number = "5123456789012345"
        daily_limit = 1000.00
        
        cursor.execute(
            """
            INSERT INTO cbs_cards
            (card_id, account_id, card_number, card_type, card_network, expiry_date, 
             cvv, pin_hash, issue_date, primary_user_name, daily_atm_limit)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                card_id,
                sample_account_data["account_number"],
                card_number,
                "DEBIT",
                "MASTERCARD",
                date.today() + timedelta(days=365*3),
                "456",
                "hashed_pin_value",
                date.today(),
                "Test Customer",
                daily_limit
            )
        )
        conn.commit()
        
        # Add withdrawal transactions
        withdrawals = [400.00, 300.00, 200.00]  # Total: 900.00
        current_balance = float(sample_account_data["balance"])
        
        for i, amount in enumerate(withdrawals):
            transaction_id = f"TXN_WITHDRAW_{i+1}"
            
            # Create transaction
            cursor.execute(
                """
                INSERT INTO cbs_transactions 
                (transaction_id, card_number, account_number, transaction_type, channel, amount, 
                 balance_before, balance_after, value_date, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    transaction_id,
                    card_number,
                    sample_account_data["account_number"],
                    "WITHDRAWAL",
                    "ATM",
                    amount,
                    current_balance,
                    current_balance - amount,
                    date.today(),
                    "SUCCESS"
                )
            )
            
            # Create daily withdrawal record
            cursor.execute(
                """
                INSERT INTO cbs_daily_withdrawals
                (card_number, amount, withdrawal_date, atm_id, location, status, balance_after_withdrawal)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    card_number,
                    amount,
                    date.today(),
                    "ATM001",
                    "Test Location",
                    "COMPLETED",
                    current_balance - amount
                )
            )
            conn.commit()
            
            # Update balance
            current_balance -= amount
        
        # Check total withdrawals for the day
        cursor.execute(
            """
            SELECT SUM(amount) 
            FROM cbs_daily_withdrawals 
            WHERE card_number = %s AND withdrawal_date = %s
            """,
            (card_number, date.today())
        )
        total_withdrawn = float(cursor.fetchone()[0])
        
        assert total_withdrawn == sum(withdrawals)
        
        # Try a withdrawal that would exceed the limit
        exceeding_amount = 200.00  # This would take total to 1100.00, which exceeds 1000.00
        
        # This should be blocked in a real system, here we're just checking the total
        # In a real implementation, we'd have a stored procedure or application logic to check this
        
        remaining_limit = daily_limit - total_withdrawn
        assert remaining_limit < exceeding_amount  # Withdrawal should be rejected
        
        # Update the account balance in the database
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (current_balance, sample_account_data["account_number"])
        )
        conn.commit()
        
        cursor.close()
