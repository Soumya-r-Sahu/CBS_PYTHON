"""
RTGS Payment Controllers - Core Banking System

This module provides API controllers for RTGS payments.
"""
import logging
from typing import Dict, Any
from datetime import datetime
import json

from ..models.rtgs_model import RTGSPaymentDetails, RTGSStatus, RTGSTransaction
from ..services.rtgs_service import rtgs_service
from ..exceptions.rtgs_exceptions import (
    RTGSException,
    RTGSValidationError,
    RTGSTransactionNotFound
)
from ..utils.rtgs_utils import mask_account_number

# Configure logger
logger = logging.getLogger(__name__)


class RTGSController:
    """Controller for RTGS payment API endpoints."""
    
    def __init__(self):
        """Initialize controller."""
        self.service = rtgs_service
    
    def create_transaction(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new RTGS transaction from API request.
        
        Args:
            request_data: API request data
            
        Returns:
            Dict[str, Any]: API response
        """
        try:
            # Extract payment details from request
            payment_details = RTGSPaymentDetails(
                sender_account_number=request_data.get("sender_account_number", ""),
                sender_ifsc_code=request_data.get("sender_ifsc_code", ""),
                sender_account_type=request_data.get("sender_account_type", ""),
                sender_name=request_data.get("sender_name", ""),
                beneficiary_account_number=request_data.get("beneficiary_account_number", ""),
                beneficiary_ifsc_code=request_data.get("beneficiary_ifsc_code", ""),
                beneficiary_account_type=request_data.get("beneficiary_account_type", ""),
                beneficiary_name=request_data.get("beneficiary_name", ""),
                amount=float(request_data.get("amount", 0)),
                payment_reference=request_data.get("payment_reference", ""),
                remarks=request_data.get("remarks"),
                purpose_code=request_data.get("purpose_code")
            )
            
            # Get customer ID from request if available
            customer_id = request_data.get("customer_id")
            
            # Create transaction
            transaction = self.service.create_transaction(payment_details, customer_id)
            
            # Return API response
            return {
                "status": "success",
                "message": "RTGS transaction created successfully",
                "data": {
                    "transaction_id": transaction.transaction_id,
                    "status": transaction.status,
                    "created_at": transaction.created_at.isoformat(),
                    "reference": payment_details.payment_reference,
                    "amount": payment_details.amount
                }
            }
        except RTGSValidationError as e:
            logger.warning(f"RTGS validation error: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "error_code": "VALIDATION_ERROR"
            }
        except Exception as e:
            logger.error(f"Error creating RTGS transaction: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": "Internal server error",
                "error_code": "SERVER_ERROR"
            }
    
    def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get status of an RTGS transaction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Dict[str, Any]: API response with transaction status
        """
        try:
            # Get transaction
            transaction = self.service.get_transaction(transaction_id)
            
            # Mask sensitive data
            masked_account = mask_account_number(
                transaction.payment_details.beneficiary_account_number)
            
            # Return API response
            return {
                "status": "success",
                "data": {
                    "transaction_id": transaction.transaction_id,
                    "status": transaction.status,
                    "created_at": transaction.created_at.isoformat(),
                    "updated_at": transaction.updated_at.isoformat(),
                    "amount": transaction.payment_details.amount,
                    "beneficiary": transaction.payment_details.beneficiary_name,
                    "account_number": masked_account,
                    "remarks": transaction.payment_details.remarks
                }
            }
        except RTGSTransactionNotFound as e:
            logger.warning(f"RTGS transaction not found: {transaction_id}")
            return {
                "status": "error",
                "message": str(e),
                "error_code": "NOT_FOUND"
            }
        except Exception as e:
            logger.error(f"Error getting RTGS transaction: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": "Internal server error",
                "error_code": "SERVER_ERROR"
            }
    
    def process_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Process an RTGS transaction.
        
        Args:
            transaction_id: Transaction ID to process
            
        Returns:
            Dict[str, Any]: API response
        """
        try:
            # Process transaction
            updated_transaction = self.service.process_transaction(transaction_id)
            
            # Return API response
            return {
                "status": "success",
                "message": "RTGS transaction processing initiated",
                "data": {
                    "transaction_id": updated_transaction.transaction_id,
                    "status": updated_transaction.status,
                    "processed_at": updated_transaction.processed_at.isoformat() 
                        if updated_transaction.processed_at else None
                }
            }
        except RTGSTransactionNotFound as e:
            logger.warning(f"RTGS transaction not found: {transaction_id}")
            return {
                "status": "error",
                "message": str(e),
                "error_code": "NOT_FOUND"
            }
        except RTGSException as e:
            logger.warning(f"RTGS processing error: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "error_code": "PROCESSING_ERROR"
            }
        except Exception as e:
            logger.error(f"Error processing RTGS transaction: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": "Internal server error",
                "error_code": "SERVER_ERROR"
            }
    
    def get_customer_transactions(self, customer_id: str) -> Dict[str, Any]:
        """
        Get all RTGS transactions for a customer.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dict[str, Any]: API response with list of transactions
        """
        try:
            # Get transactions
            transactions = self.service.get_customer_transactions(customer_id)
            
            # Format transaction data for API response
            transaction_data = []
            for trx in transactions:
                transaction_data.append({
                    "transaction_id": trx.transaction_id,
                    "status": trx.status,
                    "created_at": trx.created_at.isoformat(),
                    "amount": trx.payment_details.amount,
                    "beneficiary": trx.payment_details.beneficiary_name
                })
            
            return {
                "status": "success",
                "data": {
                    "customer_id": customer_id,
                    "transaction_count": len(transactions),
                    "transactions": transaction_data
                }
            }
        except Exception as e:
            logger.error(f"Error getting customer transactions: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": "Internal server error",
                "error_code": "SERVER_ERROR"
            }
