"""
UPI Transaction Tests

This module contains tests for UPI transaction-related functionality.
"""

import pytest
from datetime import datetime, date, timedelta
import mysql.connector
import uuid

class TestUPITransactions:
    """Tests for UPI transactions."""
    
    def test_upi_registration(self, clean_test_db, sample_customer_data, sample_account_data):
        """Test UPI registration process."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Create UPI registration
        upi_id = f"{sample_customer_data['name'].lower().replace(' ', '')}@cbs"
        device_id = "TEST_DEVICE_ID_123"
        mobile_number = sample_customer_data.get("phone", "9876543210")
        
        cursor.execute(
            """
            INSERT INTO cbs_upi_registrations
            (upi_id, customer_id, account_number, device_id, mobile_number, 
             status, created_at, modified_at)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """,
            (
                upi_id,
                sample_customer_data["customer_id"],
                sample_account_data["account_number"],
                device_id,
                mobile_number,
                "ACTIVE"
            )
        )
        conn.commit()
        
        # Check that UPI registration was successful
        cursor.execute(
            "SELECT * FROM cbs_upi_registrations WHERE upi_id = %s",
            (upi_id,)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == upi_id
        assert result[1] == sample_customer_data["customer_id"]
        assert result[2] == sample_account_data["account_number"]
        assert result[3] == device_id
        assert result[4] == mobile_number
        assert result[5] == "ACTIVE"
        
        cursor.close()
        
    def test_upi_transaction(self, clean_test_db, sample_account_data):
        """Test UPI transaction functionality."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Create sender UPI registration
        sender_upi_id = "sender@cbs"
        cursor.execute(
            """
            INSERT INTO cbs_upi_registrations
            (upi_id, customer_id, account_number, device_id, mobile_number, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                sender_upi_id,
                sample_account_data["customer_id"],
                sample_account_data["account_number"],
                "SENDER_DEVICE",
                "9876543210",
                "ACTIVE"
            )
        )
        
        # Create another account and UPI registration as recipient
        recipient_account = "ACC1003TEST"
        recipient_customer = "CUS1002TEST"
        
        # First create the recipient customer
        cursor.execute(
            """
            INSERT INTO cbs_customers 
            (customer_id, name, dob, gender, address, email, phone, customer_segment)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                recipient_customer,
                "Recipient User",
                "1991-05-15",
                "FEMALE",
                "456 Test Address",
                "recipient@example.com",
                "8765432109",
                "RETAIL"
            )
        )
        
        # Then create recipient account
        cursor.execute(
            """
            INSERT INTO cbs_accounts 
            (account_number, customer_id, account_type, balance, status, branch_code, ifsc_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                recipient_account,
                recipient_customer,
                "SAVINGS",
                5000.00,
                "ACTIVE",
                "BR001",
                "CBSTEST001"
            )
        )
        
        # Create recipient UPI registration
        recipient_upi_id = "recipient@cbs"
        cursor.execute(
            """
            INSERT INTO cbs_upi_registrations
            (upi_id, customer_id, account_number, device_id, mobile_number, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                recipient_upi_id,
                recipient_customer,
                recipient_account,
                "RECIPIENT_DEVICE",
                "8765432109",
                "ACTIVE"
            )
        )
        conn.commit()
        
        # Get balances before transaction
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        sender_balance_before = float(cursor.fetchone()[0])
        
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (recipient_account,)
        )
        recipient_balance_before = float(cursor.fetchone()[0])
        
        # Create a UPI transaction
        transaction_amount = 500.00
        upi_reference = f"UPITX{uuid.uuid4().hex[:8]}"
        transaction_id = f"UPITXN-{uuid.uuid4().hex[:10]}"
        
        # Create transaction record
        cursor.execute(
            """
            INSERT INTO cbs_transactions 
            (transaction_id, account_number, transaction_type, channel, amount, 
             balance_before, balance_after, value_date, status, reference_number) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                transaction_id,
                sample_account_data["account_number"],
                "TRANSFER",
                "UPI",
                transaction_amount,
                sender_balance_before,
                sender_balance_before - transaction_amount,
                date.today(),
                "SUCCESS",
                upi_reference
            )
        )
        
        # Create UPI transaction record
        cursor.execute(
            """
            INSERT INTO cbs_upi_transactions
            (upi_transaction_id, transaction_id, sender_upi_id, receiver_upi_id, 
             sender_account, receiver_account, amount, status, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                upi_reference,
                transaction_id,
                sender_upi_id,
                recipient_upi_id,
                sample_account_data["account_number"],
                recipient_account,
                transaction_amount,
                "SUCCESS"
            )
        )
        
        # Create a transfer record too
        cursor.execute(
            """
            INSERT INTO cbs_transfers
            (transfer_id, transaction_id, source_account, destination_account, 
             transfer_type, amount, transfer_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
            """,
            (
                f"UPITR{uuid.uuid4().hex[:8]}",
                transaction_id,
                sample_account_data["account_number"],
                recipient_account,
                "UPI",
                transaction_amount,
                "SUCCESS"
            )
        )
        conn.commit()
        
        # Update account balances
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (sender_balance_before - transaction_amount, sample_account_data["account_number"])
        )
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (recipient_balance_before + transaction_amount, recipient_account)
        )
        conn.commit()
        
        # Check that UPI transaction is recorded properly
        cursor.execute(
            """
            SELECT ut.upi_transaction_id, ut.sender_upi_id, ut.receiver_upi_id, ut.amount,
                  t.transaction_id, t.channel
            FROM cbs_upi_transactions ut
            JOIN cbs_transactions t ON ut.transaction_id = t.transaction_id
            WHERE ut.upi_transaction_id = %s
            """,
            (upi_reference,)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == upi_reference
        assert result[1] == sender_upi_id
        assert result[2] == recipient_upi_id
        assert float(result[3]) == transaction_amount
        assert result[4] == transaction_id
        assert result[5] == "UPI"
        
        # Verify account balances
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        sender_balance_after = float(cursor.fetchone()[0])
        
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (recipient_account,)
        )
        recipient_balance_after = float(cursor.fetchone()[0])
        
        # Check balances are updated correctly
        assert sender_balance_after == sender_balance_before - transaction_amount
        assert recipient_balance_after == recipient_balance_before + transaction_amount
        
        cursor.close()
    
    def test_collect_request(self, clean_test_db, sample_account_data):
        """Test UPI collect request functionality."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Set up similar UPI infrastructure as in test_upi_transaction
        # First create the payer/payee accounts and UPI registrations
        payer_upi_id = "payer@cbs"
        cursor.execute(
            """
            INSERT INTO cbs_upi_registrations
            (upi_id, customer_id, account_number, device_id, mobile_number, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                payer_upi_id,
                sample_account_data["customer_id"],
                sample_account_data["account_number"],
                "PAYER_DEVICE",
                "9876543210",
                "ACTIVE"
            )
        )
        
        # Create payee account and UPI registration (the one requesting payment)
        payee_account = "ACC1004TEST"
        payee_customer = "CUS1003TEST"
        
        # Create the payee customer
        cursor.execute(
            """
            INSERT INTO cbs_customers 
            (customer_id, name, dob, gender, address, email, phone, customer_segment)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                payee_customer,
                "Collection User",
                "1992-06-20",
                "MALE",
                "789 Test Address",
                "collector@example.com",
                "7654321098",
                "RETAIL"
            )
        )
        
        # Create payee account
        cursor.execute(
            """
            INSERT INTO cbs_accounts 
            (account_number, customer_id, account_type, balance, status, branch_code, ifsc_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                payee_account,
                payee_customer,
                "SAVINGS",
                2000.00,
                "ACTIVE",
                "BR001",
                "CBSTEST001"
            )
        )
        
        # Create payee UPI registration
        payee_upi_id = "collector@cbs"
        cursor.execute(
            """
            INSERT INTO cbs_upi_registrations
            (upi_id, customer_id, account_number, device_id, mobile_number, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                payee_upi_id,
                payee_customer,
                payee_account,
                "PAYEE_DEVICE",
                "7654321098",
                "ACTIVE"
            )
        )
        conn.commit()
        
        # Create a collect request
        collect_amount = 300.00
        collect_reference = f"COLLREQ{uuid.uuid4().hex[:8]}"
        collect_description = "Test Collection Request"
        
        cursor.execute(
            """
            INSERT INTO cbs_upi_collect_requests
            (request_id, requester_upi_id, payer_upi_id, amount, description, 
             expiry_time, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                collect_reference,
                payee_upi_id,
                payer_upi_id,
                collect_amount,
                collect_description,
                datetime.now() + timedelta(hours=24),  # 24 hour expiry
                "PENDING"
            )
        )
        conn.commit()
        
        # Check the collect request was created correctly
        cursor.execute(
            """
            SELECT request_id, requester_upi_id, payer_upi_id, amount, status
            FROM cbs_upi_collect_requests
            WHERE request_id = %s
            """,
            (collect_reference,)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == collect_reference
        assert result[1] == payee_upi_id
        assert result[2] == payer_upi_id
        assert float(result[3]) == collect_amount
        assert result[4] == "PENDING"
        
        # Now simulate the payer accepting the request
        # Get balances before transaction
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        payer_balance_before = float(cursor.fetchone()[0])
        
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (payee_account,)
        )
        payee_balance_before = float(cursor.fetchone()[0])
        
        # Create transaction for accepted collect request
        transaction_id = f"COLLTRX-{uuid.uuid4().hex[:10]}"
        
        # Update collect request status
        cursor.execute(
            """
            UPDATE cbs_upi_collect_requests
            SET status = %s, response_time = NOW(), transaction_id = %s
            WHERE request_id = %s
            """,
            ("ACCEPTED", transaction_id, collect_reference)
        )
        
        # Create the transaction record
        cursor.execute(
            """
            INSERT INTO cbs_transactions 
            (transaction_id, account_number, transaction_type, channel, amount, 
             balance_before, balance_after, value_date, status, reference_number) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                transaction_id,
                sample_account_data["account_number"],
                "TRANSFER",
                "UPI",
                collect_amount,
                payer_balance_before,
                payer_balance_before - collect_amount,
                date.today(),
                "SUCCESS",
                collect_reference
            )
        )
        
        # Create UPI transaction record
        cursor.execute(
            """
            INSERT INTO cbs_upi_transactions
            (upi_transaction_id, transaction_id, sender_upi_id, receiver_upi_id, 
             sender_account, receiver_account, amount, status, timestamp,
             collect_request_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            """,
            (
                f"COLLUPITX{uuid.uuid4().hex[:8]}",
                transaction_id,
                payer_upi_id,
                payee_upi_id,
                sample_account_data["account_number"],
                payee_account,
                collect_amount,
                "SUCCESS",
                collect_reference
            )
        )
        
        # Create transfer record
        cursor.execute(
            """
            INSERT INTO cbs_transfers
            (transfer_id, transaction_id, source_account, destination_account, 
             transfer_type, amount, transfer_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
            """,
            (
                f"COLLTR{uuid.uuid4().hex[:8]}",
                transaction_id,
                sample_account_data["account_number"],
                payee_account,
                "UPI",
                collect_amount,
                "SUCCESS"
            )
        )
        conn.commit()
        
        # Update account balances
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (payer_balance_before - collect_amount, sample_account_data["account_number"])
        )
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (payee_balance_before + collect_amount, payee_account)
        )
        conn.commit()
        
        # Verify the collect request flow worked correctly
        cursor.execute(
            """
            SELECT cr.request_id, cr.status, cr.transaction_id, t.amount
            FROM cbs_upi_collect_requests cr
            JOIN cbs_transactions t ON cr.transaction_id = t.transaction_id
            WHERE cr.request_id = %s
            """,
            (collect_reference,)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == collect_reference
        assert result[1] == "ACCEPTED"
        assert result[2] == transaction_id
        assert float(result[3]) == collect_amount
        
        # Verify account balances
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        payer_balance_after = float(cursor.fetchone()[0])
        
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (payee_account,)
        )
        payee_balance_after = float(cursor.fetchone()[0])
        
        # Check balances are updated correctly
        assert payer_balance_after == payer_balance_before - collect_amount
        assert payee_balance_after == payee_balance_before + collect_amount
        
        cursor.close()
    
    def test_upi_declined_collect_request(self, clean_test_db, sample_account_data):
        """Test declining a UPI collect request."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Set up UPI registration for sample customer
        payer_upi_id = "payer@cbs"
        cursor.execute(
            """
            INSERT INTO cbs_upi_registrations
            (upi_id, customer_id, account_number, device_id, mobile_number, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                payer_upi_id,
                sample_account_data["customer_id"],
                sample_account_data["account_number"],
                "PAYER_DEVICE",
                "9876543210",
                "ACTIVE"
            )
        )
        
        # Create a requester/payee
        payee_upi_id = "requester@cbs"
        
        # Create a collect request
        collect_amount = 1000.00
        collect_reference = f"DECLINE-REQ-{uuid.uuid4().hex[:8]}"
        collect_description = "Request to be Declined"
        
        cursor.execute(
            """
            INSERT INTO cbs_upi_collect_requests
            (request_id, requester_upi_id, payer_upi_id, amount, description, 
             expiry_time, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (
                collect_reference,
                payee_upi_id,
                payer_upi_id,
                collect_amount,
                collect_description,
                datetime.now() + timedelta(hours=24),
                "PENDING"
            )
        )
        conn.commit()
        
        # Decline the collect request
        cursor.execute(
            """
            UPDATE cbs_upi_collect_requests
            SET status = 'DECLINED', response_time = NOW(), remarks = %s
            WHERE request_id = %s
            """,
            ("Payment request declined by user", collect_reference)
        )
        conn.commit()
        
        # Verify the request was declined
        cursor.execute(
            """
            SELECT request_id, status, remarks, transaction_id
            FROM cbs_upi_collect_requests
            WHERE request_id = %s
            """,
            (collect_reference,)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == collect_reference
        assert result[1] == "DECLINED"
        assert "declined by user" in result[2]
        assert result[3] is None  # No transaction ID since it was declined
        
        # Ensure no transaction or transfer was created
        cursor.execute(
            """
            SELECT COUNT(*) 
            FROM cbs_transactions
            WHERE reference_number = %s
            """,
            (collect_reference,)
        )
        count = cursor.fetchone()[0]
        assert count == 0
        
        cursor.close()
    
    def test_qr_code_transaction(self, clean_test_db, sample_account_data):
        """Test UPI transaction via QR code."""
        conn = clean_test_db
        cursor = conn.cursor()
        
        # Set up payer UPI registration (the one scanning the QR code)
        payer_upi_id = "qrscan@cbs"
        cursor.execute(
            """
            INSERT INTO cbs_upi_registrations
            (upi_id, customer_id, account_number, device_id, mobile_number, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                payer_upi_id,
                sample_account_data["customer_id"],
                sample_account_data["account_number"],
                "SCANNER_DEVICE",
                "9876543210",
                "ACTIVE"
            )
        )
        
        # Create merchant registration (the one displaying the QR code)
        merchant_upi_id = "merchant@cbs"
        merchant_id = "MERCH001"
        merchant_name = "Test Merchant"
        qr_code_value = f"upi://pay?pa={merchant_upi_id}&pn={merchant_name}&am=250.00&cu=INR&tn=Payment%20for%20purchase"
        
        cursor.execute(
            """
            INSERT INTO cbs_upi_merchants
            (merchant_id, merchant_name, merchant_upi_id, merchant_category, qr_value, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                merchant_id,
                merchant_name,
                merchant_upi_id,
                "RETAIL",
                qr_code_value,
                "ACTIVE"
            )
        )
        conn.commit()
        
        # Get payer balance before transaction
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        payer_balance_before = float(cursor.fetchone()[0])
        
        # Simulate QR code scan and payment
        qr_payment_amount = 250.00  # Amount in QR code
        transaction_id = f"QRTRX-{uuid.uuid4().hex[:10]}"
        upi_reference = f"QRPAY{uuid.uuid4().hex[:8]}"
        
        # Record the QR scan
        cursor.execute(
            """
            INSERT INTO cbs_qr_scans
            (scan_id, qr_code, scanned_by_upi_id, merchant_id, amount, timestamp)
            VALUES (%s, %s, %s, %s, %s, NOW())
            """,
            (
                f"SCAN{uuid.uuid4().hex[:8]}",
                qr_code_value,
                payer_upi_id,
                merchant_id,
                qr_payment_amount
            )
        )
        
        # Create the transaction
        cursor.execute(
            """
            INSERT INTO cbs_transactions 
            (transaction_id, account_number, transaction_type, channel, amount, 
             balance_before, balance_after, value_date, status, reference_number,
             merchant_name, merchant_category_code) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                transaction_id,
                sample_account_data["account_number"],
                "PAYMENT",
                "UPI",
                qr_payment_amount,
                payer_balance_before,
                payer_balance_before - qr_payment_amount,
                date.today(),
                "SUCCESS",
                upi_reference,
                merchant_name,
                "5411"  # Sample MCC for groceries
            )
        )
        
        # Create UPI transaction record
        cursor.execute(
            """
            INSERT INTO cbs_upi_transactions
            (upi_transaction_id, transaction_id, sender_upi_id, receiver_upi_id, 
             sender_account, amount, status, timestamp, qr_code_payment)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            """,
            (
                upi_reference,
                transaction_id,
                payer_upi_id,
                merchant_upi_id,
                sample_account_data["account_number"],
                qr_payment_amount,
                "SUCCESS",
                True
            )
        )
        conn.commit()
        
        # Update payer balance
        cursor.execute(
            "UPDATE cbs_accounts SET balance = %s WHERE account_number = %s",
            (payer_balance_before - qr_payment_amount, sample_account_data["account_number"])
        )
        conn.commit()
        
        # Verify QR payment was processed correctly
        cursor.execute(
            """
            SELECT ut.upi_transaction_id, ut.qr_code_payment, t.merchant_name, t.amount,
                  t.transaction_type, t.channel
            FROM cbs_upi_transactions ut
            JOIN cbs_transactions t ON ut.transaction_id = t.transaction_id
            WHERE ut.upi_transaction_id = %s
            """,
            (upi_reference,)
        )
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == upi_reference
        assert result[1] == 1  # True for qr_code_payment
        assert result[2] == merchant_name
        assert float(result[3]) == qr_payment_amount
        assert result[4] == "PAYMENT"
        assert result[5] == "UPI"
        
        # Verify account balance
        cursor.execute(
            "SELECT balance FROM cbs_accounts WHERE account_number = %s",
            (sample_account_data["account_number"],)
        )
        payer_balance_after = float(cursor.fetchone()[0])
        
        assert payer_balance_after == payer_balance_before - qr_payment_amount
        
        cursor.close()
