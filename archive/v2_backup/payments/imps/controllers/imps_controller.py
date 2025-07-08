"""
IMPS Payment Controllers - Core Banking System

This module provides API controllers for IMPS payments.
"""
import logging
from typing import Dict, Any
from datetime import datetime
import json

from ..models.imps_model import IMPSPaymentDetails, IMPSStatus, IMPSTransaction, IMPSType, IMPSChannel
from ..services.imps_service import imps_service
from ..exceptions.imps_exceptions import (
    IMPSException, 
    IMPSValidationError,
    IMPSTransactionNotFound
)
from ..utils.imps_utils import mask_account_number, mask_mobile_number

# Configure logger
logger = logging.getLogger(__name__)


class IMPSController:
    """Controller for IMPS payment API endpoints."""
    
    def __init__(self):
        """Initialize controller."""
        self.service = imps_service
    
    def create_transaction(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new IMPS transaction from API request.
        
        Args:
            request_data: API request data
            
        Returns:
            Dict[str, Any]: API response
        """
        try:
            # Extract payment details from request
            payment_details = IMPSPaymentDetails(
                sender_account_number=request_data.get("sender_account_number", ""),
                sender_ifsc_code=request_data.get("sender_ifsc_code", ""),
                sender_mobile_number=request_data.get("sender_mobile_number"),
                sender_mmid=request_data.get("sender_mmid"),
                sender_name=request_data.get("sender_name", ""),
                beneficiary_account_number=request_data.get("beneficiary_account_number", ""),
                beneficiary_ifsc_code=request_data.get("beneficiary_ifsc_code", ""),
                beneficiary_mobile_number=request_data.get("beneficiary_mobile_number"),
                beneficiary_mmid=request_data.get("beneficiary_mmid"),
                beneficiary_name=request_data.get("beneficiary_name", ""),
                amount=float(request_data.get("amount", 0)),
                reference_number=request_data.get("reference_number", ""),
                remarks=request_data.get("remarks"),
                imps_type=IMPSType(request_data.get("imps_type", "P2A")),
                channel=IMPSChannel(request_data.get("channel", "API"))
            )
            
            # Get customer ID if available
            customer_id = request_data.get("customer_id")
            
            # Create transaction
            transaction = self.service.create_transaction(payment_details, customer_id)
            
            # Return API response
            return {
                "status": "success",
                "message": "IMPS transaction created successfully",
                "data": {
                    "transaction_id": transaction.transaction_id,
                    "status": transaction.status,
                    "created_at": transaction.created_at.isoformat(),
                    "reference_number": payment_details.reference_number,
                    "amount": payment_details.amount
                }
            }
        except IMPSValidationError as e:
            logger.warning(f"IMPS validation error: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "error_code": "VALIDATION_ERROR"
            }
        except Exception as e:
            logger.error(f"Error creating IMPS transaction: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": "Internal server error",
                "error_code": "SERVER_ERROR"
            }
    
    def process_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Process an IMPS transaction.
        
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
                "message": "IMPS transaction processing initiated",
                "data": {
                    "transaction_id": updated_transaction.transaction_id,
                    "status": updated_transaction.status,
                    "processed_at": updated_transaction.processed_at.isoformat() 
                        if updated_transaction.processed_at else None
                }
            }
        except IMPSTransactionNotFound as e:
            logger.warning(f"IMPS transaction not found: {transaction_id}")
            return {
                "status": "error",
                "message": str(e),
                "error_code": "NOT_FOUND"
            }
        except IMPSException as e:
            logger.warning(f"IMPS processing error: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "error_code": "PROCESSING_ERROR"
            }
        except Exception as e:
            logger.error(f"Error processing IMPS transaction: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": "Internal server error",
                "error_code": "SERVER_ERROR"
            }
    
    def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        Get status of an IMPS transaction.
        
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
            
            masked_mobile = None
            if transaction.payment_details.beneficiary_mobile_number:
                masked_mobile = mask_mobile_number(
                    transaction.payment_details.beneficiary_mobile_number)
            
            # Return API response
            return {
                "status": "success",
                "data": {
                    "transaction_id": transaction.transaction_id,
                    "rrn": transaction.rrn,
                    "status": transaction.status,
                    "created_at": transaction.created_at.isoformat(),
                    "updated_at": transaction.updated_at.isoformat(),
                    "amount": transaction.payment_details.amount,
                    "beneficiary": transaction.payment_details.beneficiary_name,
                    "account_number": masked_account,
                    "mobile_number": masked_mobile,
                    "remarks": transaction.payment_details.remarks,
                    "type": transaction.payment_details.imps_type,
                    "channel": transaction.payment_details.channel
                }
            }
        except IMPSTransactionNotFound as e:
            logger.warning(f"IMPS transaction not found: {transaction_id}")
            return {
                "status": "error",
                "message": str(e),
                "error_code": "NOT_FOUND"
            }
        except Exception as e:
            logger.error(f"Error getting IMPS transaction: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": "Internal server error",
                "error_code": "SERVER_ERROR"
            }
    
    def search_transactions(self, search_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Search for IMPS transactions.
        
        Args:
            search_params: Search parameters
            
        Returns:
            Dict[str, Any]: API response with search results
        """
        try:
            # Extract search parameters
            mobile_number = search_params.get("mobile_number")
            account_number = search_params.get("account_number")
            status = search_params.get("status")
            
            # Get transactions
            transactions = []
            
            if mobile_number:
                transactions = self.service.get_transactions_by_mobile(mobile_number)
            elif account_number:
                transactions = self.service.get_transactions_by_account(account_number)
            elif status:
                transactions = self.service.get_transactions_by_status(IMPSStatus(status))
            
            # Format transaction data for API response
            transaction_data = []
            for trx in transactions:
                transaction_data.append({
                    "transaction_id": trx.transaction_id,
                    "rrn": trx.rrn,
                    "status": trx.status,
                    "created_at": trx.created_at.isoformat(),
                    "amount": trx.payment_details.amount,
                    "beneficiary": trx.payment_details.beneficiary_name,
                    "type": trx.payment_details.imps_type
                })
            
            return {
                "status": "success",
                "data": {
                    "transaction_count": len(transactions),
                    "transactions": transaction_data
                }
            }
        except Exception as e:
            logger.error(f"Error searching IMPS transactions: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": "Internal server error",
                "error_code": "SERVER_ERROR"
            }
    
    def p2p_transfer(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle P2P transfer using mobile number and MMID.
        
        Args:
            request_data: API request data
            
        Returns:
            Dict[str, Any]: API response
        """
        try:
            # Extract payment details from request
            payment_details = IMPSPaymentDetails(
                sender_account_number=request_data.get("sender_account_number", ""),
                sender_ifsc_code=request_data.get("sender_ifsc_code", ""),
                sender_mobile_number=request_data.get("sender_mobile_number", ""),
                sender_mmid=request_data.get("sender_mmid", ""),
                sender_name=request_data.get("sender_name", ""),
                
                # In P2P, we may not have beneficiary account details
                beneficiary_account_number=request_data.get("beneficiary_account_number", ""),
                beneficiary_ifsc_code=request_data.get("beneficiary_ifsc_code", ""),
                beneficiary_mobile_number=request_data.get("beneficiary_mobile_number", ""),
                beneficiary_mmid=request_data.get("beneficiary_mmid", ""),
                beneficiary_name=request_data.get("beneficiary_name", ""),
                
                amount=float(request_data.get("amount", 0)),
                reference_number=request_data.get("reference_number", ""),
                remarks=request_data.get("remarks"),
                imps_type=IMPSType.P2P,
                channel=IMPSChannel(request_data.get("channel", "MOBILE"))
            )
            
            # Create and process P2P transaction
            transaction = self.service.create_p2p_transaction(payment_details)
            
            # Return API response
            return {
                "status": "success",
                "message": "IMPS P2P transfer initiated",
                "data": {
                    "transaction_id": transaction.transaction_id,
                    "status": transaction.status,
                    "created_at": transaction.created_at.isoformat(),
                    "reference_number": payment_details.reference_number,
                    "amount": payment_details.amount
                }
            }
        except IMPSValidationError as e:
            logger.warning(f"IMPS validation error: {str(e)}")
            return {
                "status": "error",
                "message": str(e),
                "error_code": "VALIDATION_ERROR"
            }
        except Exception as e:
            logger.error(f"Error creating IMPS P2P transfer: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": "Internal server error",
                "error_code": "SERVER_ERROR"
            }
