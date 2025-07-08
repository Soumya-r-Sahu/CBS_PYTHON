"""
SQL implementation of RTGS Transaction Repository.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from ...domain.entities.rtgs_transaction import RTGSTransaction, RTGSPaymentDetails, RTGSStatus, RTGSPriority
from ...application.interfaces.rtgs_transaction_repository_interface import RTGSTransactionRepositoryInterface


class SQLRTGSTransactionRepository(RTGSTransactionRepositoryInterface):
    """SQL implementation of RTGS transaction repository."""
    
    def __init__(self, db_connection):
        """
        Initialize the repository.
        
        Args:
            db_connection: Database connection
        """
        self.db_connection = db_connection
    
    def get_by_id(self, transaction_id: UUID) -> Optional[RTGSTransaction]:
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: The transaction ID
            
        Returns:
            Optional[RTGSTransaction]: The transaction if found, None otherwise
        """
        # In a real implementation, this would execute a SQL query
        # For demonstration purposes, we'll simulate fetching from a database
        
        query = f"""
        SELECT * FROM rtgs_transactions 
        LEFT JOIN rtgs_payment_details ON rtgs_transactions.id = rtgs_payment_details.transaction_id
        WHERE rtgs_transactions.id = '{transaction_id}'
        """
        
        try:
            # Execute query and fetch data
            cursor = self.db_connection.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            
            if not result:
                return None
            
            # Build the transaction object from the query result
            return self._build_transaction_from_db_record(result)
            
        except Exception as e:
            # Log the error
            print(f"Error retrieving RTGS transaction: {e}")
            return None
    
    def save(self, transaction: RTGSTransaction) -> RTGSTransaction:
        """
        Save a transaction.
        
        Args:
            transaction: The transaction to save
            
        Returns:
            RTGSTransaction: The saved transaction
        """
        # In a real implementation, this would execute SQL INSERT statements
        # For demonstration purposes, we'll simulate saving to a database
        
        try:
            # Start a transaction
            cursor = self.db_connection.cursor()
            
            # Insert into rtgs_transactions table
            transaction_query = """
            INSERT INTO rtgs_transactions (
                id, transaction_reference, utr_number, status, 
                created_at, updated_at, processed_at
            ) VALUES (
                %s, %s, %s, %s, 
                %s, %s, %s
            )
            """
            
            cursor.execute(transaction_query, (
                str(transaction.id),
                transaction.transaction_reference,
                transaction.utr_number,
                transaction.status.value,
                transaction.created_at,
                transaction.updated_at,
                transaction.processed_at
            ))
            
            # Insert into rtgs_payment_details table
            payment_details_query = """
            INSERT INTO rtgs_payment_details (
                transaction_id, sender_account_number, sender_ifsc_code, 
                sender_account_type, sender_name, beneficiary_account_number, 
                beneficiary_ifsc_code, beneficiary_account_type, beneficiary_name, 
                amount, payment_reference, remarks, priority
            ) VALUES (
                %s, %s, %s, 
                %s, %s, %s, 
                %s, %s, %s, 
                %s, %s, %s, %s
            )
            """
            
            cursor.execute(payment_details_query, (
                str(transaction.id),
                transaction.payment_details.sender_account_number,
                transaction.payment_details.sender_ifsc_code,
                transaction.payment_details.sender_account_type,
                transaction.payment_details.sender_name,
                transaction.payment_details.beneficiary_account_number,
                transaction.payment_details.beneficiary_ifsc_code,
                transaction.payment_details.beneficiary_account_type,
                transaction.payment_details.beneficiary_name,
                transaction.payment_details.amount,
                transaction.payment_details.payment_reference,
                transaction.payment_details.remarks,
                transaction.payment_details.priority.value
            ))
            
            # Commit the transaction
            self.db_connection.commit()
            
            return transaction
            
        except Exception as e:
            # Rollback in case of error
            self.db_connection.rollback()
            # Log the error
            print(f"Error saving RTGS transaction: {e}")
            raise
    
    def update(self, transaction: RTGSTransaction) -> RTGSTransaction:
        """
        Update a transaction.
        
        Args:
            transaction: The transaction to update
            
        Returns:
            RTGSTransaction: The updated transaction
        """
        # In a real implementation, this would execute SQL UPDATE statements
        # For demonstration purposes, we'll simulate updating in a database
        
        try:
            # Start a transaction
            cursor = self.db_connection.cursor()
            
            # Update rtgs_transactions table
            transaction_query = """
            UPDATE rtgs_transactions SET
                transaction_reference = %s,
                utr_number = %s,
                status = %s,
                updated_at = %s,
                processed_at = %s
            WHERE id = %s
            """
            
            cursor.execute(transaction_query, (
                transaction.transaction_reference,
                transaction.utr_number,
                transaction.status.value,
                transaction.updated_at,
                transaction.processed_at,
                str(transaction.id)
            ))
            
            # Commit the transaction
            self.db_connection.commit()
            
            return transaction
            
        except Exception as e:
            # Rollback in case of error
            self.db_connection.rollback()
            # Log the error
            print(f"Error updating RTGS transaction: {e}")
            raise
    
    def get_by_customer_id(self, customer_id: str, limit: int = 10) -> List[RTGSTransaction]:
        """
        Get transactions by customer ID.
        
        Args:
            customer_id: The customer ID
            limit: Maximum number of transactions to return
            
        Returns:
            List[RTGSTransaction]: List of transactions
        """
        # In a real implementation, this would execute a SQL query with customer_id
        # For demonstration purposes, we'll return an empty list
        
        query = f"""
        SELECT * FROM rtgs_transactions 
        LEFT JOIN rtgs_payment_details ON rtgs_transactions.id = rtgs_payment_details.transaction_id
        LEFT JOIN customer_accounts ON rtgs_payment_details.sender_account_number = customer_accounts.account_number
        WHERE customer_accounts.customer_id = '{customer_id}'
        ORDER BY rtgs_transactions.created_at DESC
        LIMIT {limit}
        """
        
        try:
            # Execute query and fetch data
            cursor = self.db_connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Build transaction objects from the query results
            transactions = []
            for result in results:
                transaction = self._build_transaction_from_db_record(result)
                if transaction:
                    transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            # Log the error
            print(f"Error retrieving RTGS transactions for customer: {e}")
            return []
    
    def get_by_status(self, status: str, limit: int = 100) -> List[RTGSTransaction]:
        """
        Get transactions by status.
        
        Args:
            status: The transaction status
            limit: Maximum number of transactions to return
            
        Returns:
            List[RTGSTransaction]: List of transactions
        """
        # In a real implementation, this would execute a SQL query with status
        # For demonstration purposes, we'll return an empty list
        
        query = f"""
        SELECT * FROM rtgs_transactions 
        LEFT JOIN rtgs_payment_details ON rtgs_transactions.id = rtgs_payment_details.transaction_id
        WHERE rtgs_transactions.status = '{status}'
        ORDER BY rtgs_transactions.created_at DESC
        LIMIT {limit}
        """
        
        try:
            # Execute query and fetch data
            cursor = self.db_connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Build transaction objects from the query results
            transactions = []
            for result in results:
                transaction = self._build_transaction_from_db_record(result)
                if transaction:
                    transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            # Log the error
            print(f"Error retrieving RTGS transactions by status: {e}")
            return []
    
    def get_by_date_range(self, start_date: str, end_date: str, limit: int = 100) -> List[RTGSTransaction]:
        """
        Get transactions by date range.
        
        Args:
            start_date: Start date in ISO format (YYYY-MM-DD)
            end_date: End date in ISO format (YYYY-MM-DD)
            limit: Maximum number of transactions to return
            
        Returns:
            List[RTGSTransaction]: List of transactions
        """
        # In a real implementation, this would execute a SQL query with date range
        # For demonstration purposes, we'll return an empty list
        
        query = f"""
        SELECT * FROM rtgs_transactions 
        LEFT JOIN rtgs_payment_details ON rtgs_transactions.id = rtgs_payment_details.transaction_id
        WHERE DATE(rtgs_transactions.created_at) BETWEEN '{start_date}' AND '{end_date}'
        ORDER BY rtgs_transactions.created_at DESC
        LIMIT {limit}
        """
        
        try:
            # Execute query and fetch data
            cursor = self.db_connection.cursor()
            cursor.execute(query)
            results = cursor.fetchall()
            
            # Build transaction objects from the query results
            transactions = []
            for result in results:
                transaction = self._build_transaction_from_db_record(result)
                if transaction:
                    transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            # Log the error
            print(f"Error retrieving RTGS transactions by date range: {e}")
            return []
    
    def get_by_utr_number(self, utr_number: str) -> Optional[RTGSTransaction]:
        """
        Get a transaction by UTR number.
        
        Args:
            utr_number: The Unique Transaction Reference number
            
        Returns:
            Optional[RTGSTransaction]: The transaction if found, None otherwise
        """
        # In a real implementation, this would execute a SQL query
        # For demonstration purposes, we'll simulate fetching from a database
        
        query = f"""
        SELECT * FROM rtgs_transactions 
        LEFT JOIN rtgs_payment_details ON rtgs_transactions.id = rtgs_payment_details.transaction_id
        WHERE rtgs_transactions.utr_number = '{utr_number}'
        """
        
        try:
            # Execute query and fetch data
            cursor = self.db_connection.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            
            if not result:
                return None
            
            # Build the transaction object from the query result
            return self._build_transaction_from_db_record(result)
            
        except Exception as e:
            # Log the error
            print(f"Error retrieving RTGS transaction by UTR: {e}")
            return None
    
    def _build_transaction_from_db_record(self, record: Dict[str, Any]) -> RTGSTransaction:
        """
        Build a transaction object from a database record.
        
        Args:
            record: Database record
            
        Returns:
            RTGSTransaction: The transaction object
        """
        # Create payment details
        payment_details = RTGSPaymentDetails(
            sender_account_number=record.get("sender_account_number", ""),
            sender_ifsc_code=record.get("sender_ifsc_code", ""),
            sender_account_type=record.get("sender_account_type", "SAVINGS"),
            sender_name=record.get("sender_name", ""),
            beneficiary_account_number=record.get("beneficiary_account_number", ""),
            beneficiary_ifsc_code=record.get("beneficiary_ifsc_code", ""),
            beneficiary_account_type=record.get("beneficiary_account_type", "SAVINGS"),
            beneficiary_name=record.get("beneficiary_name", ""),
            amount=float(record.get("amount", 0)),
            payment_reference=record.get("payment_reference", ""),
            remarks=record.get("remarks", ""),
            priority=RTGSPriority(record.get("priority", "NORMAL"))
        )
        
        # Create transaction
        transaction = RTGSTransaction(
            id=UUID(record.get("id")),
            payment_details=payment_details
        )
        
        # Set additional fields
        transaction.transaction_reference = record.get("transaction_reference", "")
        transaction.utr_number = record.get("utr_number")
        transaction.status = RTGSStatus(record.get("status", "INITIATED"))
        transaction.created_at = record.get("created_at")
        transaction.updated_at = record.get("updated_at")
        transaction.processed_at = record.get("processed_at")
        
        return transaction
