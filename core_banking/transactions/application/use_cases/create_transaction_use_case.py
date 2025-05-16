"""
Create Transaction Use Case

This module defines the use case for creating a new transaction.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import UUID

from ...domain.entities.transaction import Transaction, TransactionStatus, TransactionType
from ...domain.services.transaction_rules_service import TransactionRulesService
from ...domain.services.validation_service import ValidationService
from ..interfaces.transaction_repository_interface import TransactionRepositoryInterface
from ..interfaces.account_service_interface import AccountServiceInterface
from ..interfaces.notification_service_interface import NotificationServiceInterface

class CreateTransactionUseCase:
    """Use case for creating a transaction"""
    
    def __init__(self, 
                 transaction_repository: TransactionRepositoryInterface,
                 account_service: AccountServiceInterface,
                 notification_service: NotificationServiceInterface,
                 transaction_rules_service: TransactionRulesService,
                 validation_service: ValidationService):
        """
        Initialize the use case
        
        Args:
            transaction_repository: Repository for transaction persistence
            account_service: Service for account operations
            notification_service: Service for sending notifications
            transaction_rules_service: Service for transaction business rules
            validation_service: Service for data validation
        """
        self._transaction_repository = transaction_repository
        self._account_service = account_service
        self._notification_service = notification_service
        self._transaction_rules_service = transaction_rules_service
        self._validation_service = validation_service
    
    def execute(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the use case
        
        Args:
            transaction_data: Transaction data dictionary
            
        Returns:
            Result dictionary
        """
        # Validate input data
        validation_errors = self._validation_service.validate_transaction_data(transaction_data)
        if validation_errors:
            return {
                "success": False,
                "errors": validation_errors
            }
        
        try:
            # Parse transaction type
            transaction_type_str = transaction_data["transaction_type"].upper()
            try:
                transaction_type = TransactionType[transaction_type_str]
            except KeyError:
                return {
                    "success": False,
                    "errors": [f"Invalid transaction type: {transaction_type_str}"]
                }
            
            # Convert account_id to UUID if necessary
            account_id = transaction_data["account_id"]
            if not isinstance(account_id, UUID):
                account_id = UUID(account_id)
            
            # Convert to_account_id to UUID if present and necessary
            to_account_id = transaction_data.get("to_account_id")
            if to_account_id and not isinstance(to_account_id, UUID):
                to_account_id = UUID(to_account_id)
            
            # Check account status
            account_status = self._account_service.validate_account_status(account_id)
            if not account_status["is_valid"]:
                return {
                    "success": False,
                    "errors": account_status["errors"]
                }
            
            # For debits, check sufficient funds
            if transaction_type in [TransactionType.WITHDRAWAL, TransactionType.TRANSFER]:
                if not account_status["can_debit"]:
                    return {
                        "success": False,
                        "errors": ["Account cannot be debited"]
                    }
                
                # Check balance
                amount = Decimal(str(transaction_data["amount"]))
                balance_check = self._account_service.check_balance(account_id, amount)
                if not balance_check["has_funds"]:
                    return {
                        "success": False,
                        "errors": ["Insufficient funds"],
                        "details": {
                            "required_amount": str(amount),
                            "available_balance": str(balance_check["available_balance"])
                        }
                    }
            
            # For credits, check if account can be credited
            if transaction_type in [TransactionType.DEPOSIT]:
                if not account_status["can_credit"]:
                    return {
                        "success": False,
                        "errors": ["Account cannot be credited"]
                    }
            
            # For transfers, check target account
            if transaction_type == TransactionType.TRANSFER:
                if not to_account_id:
                    return {
                        "success": False,
                        "errors": ["Target account ID is required for transfers"]
                    }
                
                target_account_status = self._account_service.validate_account_status(to_account_id)
                if not target_account_status["is_valid"]:
                    return {
                        "success": False,
                        "errors": ["Invalid target account", *target_account_status["errors"]]
                    }
                
                if not target_account_status["can_credit"]:
                    return {
                        "success": False,
                        "errors": ["Target account cannot be credited"]
                    }
            
            # Create transaction entity
            transaction = Transaction(
                account_id=account_id,
                amount=Decimal(str(transaction_data["amount"])),
                transaction_type=transaction_type,
                status=TransactionStatus.PENDING,
                description=transaction_data.get("description", ""),
                to_account_id=to_account_id,
                reference_transaction_id=transaction_data.get("reference_transaction_id")
            )
            
            # Apply business rules
            rule_violations = self._transaction_rules_service.validate_transaction(transaction)
            if rule_violations:
                return {
                    "success": False,
                    "errors": rule_violations
                }
            
            # Check if additional verification is needed
            needs_verification = self._transaction_rules_service.requires_additional_verification(transaction)
            
            # Save transaction
            saved_transaction = self._transaction_repository.save(transaction)
            
            # Process transaction based on verification need
            if needs_verification:
                # Return for further verification
                return {
                    "success": True,
                    "transaction_id": str(saved_transaction.transaction_id),
                    "status": saved_transaction.status.value,
                    "requires_verification": True
                }
            else:
                # Complete transaction immediately
                result = self._process_transaction(saved_transaction)
                
                return {
                    "success": result["success"],
                    "transaction_id": str(saved_transaction.transaction_id),
                    "status": result.get("status", saved_transaction.status.value),
                    "errors": result.get("errors", []),
                    "requires_verification": False
                }
                
        except Exception as e:
            # Log the error
            import logging
            logging.exception(f"Error creating transaction: {str(e)}")
            
            # Send error notification
            self._notification_service.send_error_notification(
                transaction_id=None,
                error=f"Transaction creation failed: {str(e)}",
                metadata=transaction_data
            )
            
            return {
                "success": False,
                "errors": [f"Transaction processing error: {str(e)}"]
            }
    
    def _process_transaction(self, transaction: Transaction) -> Dict[str, Any]:
        """
        Process a verified transaction
        
        Args:
            transaction: Transaction to process
            
        Returns:
            Processing result
        """
        try:
            # Get account data
            account_data = self._account_service.get_account(transaction.account_id)
            if not account_data:
                transaction.fail("Account not found")
                self._transaction_repository.update_status(transaction.transaction_id, TransactionStatus.FAILED)
                return {
                    "success": False,
                    "status": TransactionStatus.FAILED.value,
                    "errors": ["Account not found"]
                }
            
            # Process based on transaction type
            if transaction.transaction_type == TransactionType.DEPOSIT:
                # Credit account
                updated_account = self._account_service.update_balance(
                    transaction.account_id, 
                    transaction.amount, 
                    is_credit=True
                )
                
                if not updated_account:
                    transaction.fail("Failed to update account balance")
                    self._transaction_repository.update_status(transaction.transaction_id, TransactionStatus.FAILED)
                    return {
                        "success": False,
                        "status": TransactionStatus.FAILED.value,
                        "errors": ["Failed to update account balance"]
                    }
            
            elif transaction.transaction_type == TransactionType.WITHDRAWAL:
                # Debit account
                updated_account = self._account_service.update_balance(
                    transaction.account_id, 
                    transaction.amount, 
                    is_credit=False
                )
                
                if not updated_account:
                    transaction.fail("Failed to update account balance")
                    self._transaction_repository.update_status(transaction.transaction_id, TransactionStatus.FAILED)
                    return {
                        "success": False,
                        "status": TransactionStatus.FAILED.value,
                        "errors": ["Failed to update account balance"]
                    }
            
            elif transaction.transaction_type == TransactionType.TRANSFER:
                # Debit source account
                updated_source_account = self._account_service.update_balance(
                    transaction.account_id, 
                    transaction.amount, 
                    is_credit=False
                )
                
                if not updated_source_account:
                    transaction.fail("Failed to update source account balance")
                    self._transaction_repository.update_status(transaction.transaction_id, TransactionStatus.FAILED)
                    return {
                        "success": False,
                        "status": TransactionStatus.FAILED.value,
                        "errors": ["Failed to update source account balance"]
                    }
                
                # Credit target account
                updated_target_account = self._account_service.update_balance(
                    transaction.to_account_id, 
                    transaction.amount, 
                    is_credit=True
                )
                
                if not updated_target_account:
                    # Attempt to reverse source account debit
                    self._account_service.update_balance(
                        transaction.account_id, 
                        transaction.amount, 
                        is_credit=True
                    )
                    
                    transaction.fail("Failed to update target account balance")
                    self._transaction_repository.update_status(transaction.transaction_id, TransactionStatus.FAILED)
                    return {
                        "success": False,
                        "status": TransactionStatus.FAILED.value,
                        "errors": ["Failed to update target account balance"]
                    }
            
            # Complete transaction
            transaction.complete()
            self._transaction_repository.update_status(transaction.transaction_id, TransactionStatus.COMPLETED)
            
            # Send notification
            self._notification_service.send_transaction_notification(transaction, account_data)
            
            return {
                "success": True,
                "status": TransactionStatus.COMPLETED.value
            }
            
        except Exception as e:
            # Log the error
            import logging
            logging.exception(f"Error processing transaction {transaction.transaction_id}: {str(e)}")
            
            # Mark transaction as failed
            transaction.fail(str(e))
            self._transaction_repository.update_status(transaction.transaction_id, TransactionStatus.FAILED)
            
            # Send error notification
            self._notification_service.send_error_notification(
                transaction_id=transaction.transaction_id,
                error=f"Transaction processing failed: {str(e)}"
            )
            
            return {
                "success": False,
                "status": TransactionStatus.FAILED.value,
                "errors": [f"Transaction processing error: {str(e)}"]
            }
