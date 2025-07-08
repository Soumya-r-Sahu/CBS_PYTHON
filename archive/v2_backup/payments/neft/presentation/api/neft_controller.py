"""
NEFT API Controller.
This module provides REST API endpoints for NEFT payment operations.
"""
import logging
from typing import Dict, Any, Optional
from uuid import UUID
from flask import Blueprint, request, jsonify

from ...application.use_cases.transaction_creation_use_case import NEFTTransactionCreationUseCase
from ...application.use_cases.transaction_processing_use_case import NEFTTransactionProcessingUseCase
from ...application.use_cases.batch_processing_use_case import NEFTBatchProcessingUseCase
from ...application.use_cases.transaction_query_use_case import NEFTTransactionQueryUseCase
from ...application.use_cases.batch_query_use_case import NEFTBatchQueryUseCase


class NEFTController:
    """Controller for NEFT payment API endpoints."""
    
    def __init__(
        self,
        transaction_creation_use_case: NEFTTransactionCreationUseCase,
        transaction_processing_use_case: NEFTTransactionProcessingUseCase,
        batch_processing_use_case: NEFTBatchProcessingUseCase,
        transaction_query_use_case: NEFTTransactionQueryUseCase,
        batch_query_use_case: NEFTBatchQueryUseCase
    ):
        """
        Initialize the controller.
        
        Args:
            transaction_creation_use_case: Use case for creating transactions
            transaction_processing_use_case: Use case for processing transactions
            batch_processing_use_case: Use case for processing batches
            transaction_query_use_case: Use case for querying transactions
            batch_query_use_case: Use case for querying batches
        """
        self.transaction_creation_use_case = transaction_creation_use_case
        self.transaction_processing_use_case = transaction_processing_use_case
        self.batch_processing_use_case = batch_processing_use_case
        self.transaction_query_use_case = transaction_query_use_case
        self.batch_query_use_case = batch_query_use_case
        
        self.logger = logging.getLogger(__name__)
        self.blueprint = self._create_blueprint()
    
    def _create_blueprint(self) -> Blueprint:
        """
        Create Flask blueprint with routes.
        
        Returns:
            Blueprint: Flask blueprint
        """
        bp = Blueprint('neft', __name__)
        
        # Transaction routes
        bp.route('/transactions', methods=['POST'])(self.initiate_neft_transfer)
        bp.route('/transactions/<transaction_id>', methods=['GET'])(self.get_transaction_status)
        bp.route('/transactions/<transaction_id>/process', methods=['POST'])(self.process_transaction)
        
        # Batch routes
        bp.route('/batches/<batch_id>', methods=['GET'])(self.get_batch_status)
        bp.route('/batches/<batch_id>/process', methods=['POST'])(self.process_batch)
        bp.route('/batches/pending', methods=['GET'])(self.get_pending_batches)
        bp.route('/batches/date/<date_str>', methods=['GET'])(self.get_batches_by_date)
        
        # Customer routes
        bp.route('/customers/<customer_id>/transactions', methods=['GET'])(self.get_customer_transactions)
        
        return bp
    
    def initiate_neft_transfer(self) -> Dict[str, Any]:
        """
        API endpoint to initiate a new NEFT transfer.
        """
        try:
            # Get request data
            payment_data = request.json
            
            # Extract customer_id and user_id if provided
            customer_id = payment_data.pop('customer_id', None)
            user_id = payment_data.pop('user_id', None)
            
            # Use the use case
            result = self.transaction_creation_use_case.execute(
                payment_data=payment_data,
                customer_id=customer_id,
                user_id=user_id
            )
            
            # Return response
            status_code = 400 if result.get('status') == 'error' else 201
            return jsonify(result), status_code
            
        except Exception as e:
            self.logger.error(f"Error in initiate_neft_transfer: {str(e)}")
            return jsonify({
                "status": "error",
                "error_type": "system",
                "message": "An unexpected error occurred"
            }), 500
    
    def get_transaction_status(self, transaction_id: str) -> Dict[str, Any]:
        """
        API endpoint to get status of a NEFT transaction.
        """
        try:
            # Get user_id if provided
            user_id = request.args.get('user_id')
            
            # Use the use case
            result = self.transaction_query_use_case.get_transaction(
                transaction_id=UUID(transaction_id),
                user_id=user_id
            )
            
            # Return response
            status_code = 404 if result.get('status') == 'error' and result.get('error_type') == 'not_found' else 200
            return jsonify(result), status_code
            
        except ValueError:
            return jsonify({
                "status": "error",
                "error_type": "validation",
                "message": "Invalid transaction ID format"
            }), 400
            
        except Exception as e:
            self.logger.error(f"Error in get_transaction_status: {str(e)}")
            return jsonify({
                "status": "error",
                "error_type": "system",
                "message": "An unexpected error occurred"
            }), 500
    
    def process_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        API endpoint to process a NEFT transaction.
        """
        try:
            # Get user_id if provided
            user_id = request.json.get('user_id') if request.is_json else None
            
            # Use the use case
            result = self.transaction_processing_use_case.process_transaction(
                transaction_id=UUID(transaction_id),
                user_id=user_id
            )
            
            # Return response
            status_code = 400 if result.get('status') == 'error' else 200
            return jsonify(result), status_code
            
        except ValueError:
            return jsonify({
                "status": "error",
                "error_type": "validation",
                "message": "Invalid transaction ID format"
            }), 400
            
        except Exception as e:
            self.logger.error(f"Error in process_transaction: {str(e)}")
            return jsonify({
                "status": "error",
                "error_type": "system",
                "message": "An unexpected error occurred"
            }), 500
    
    def get_batch_status(self, batch_id: str) -> Dict[str, Any]:
        """
        API endpoint to get status of a NEFT batch.
        """
        try:
            # Get user_id if provided
            user_id = request.args.get('user_id')
            
            # Use the use case
            result = self.batch_query_use_case.get_batch(
                batch_id=UUID(batch_id),
                user_id=user_id
            )
            
            # Return response
            status_code = 404 if result.get('status') == 'error' and result.get('error_type') == 'not_found' else 200
            return jsonify(result), status_code
            
        except ValueError:
            return jsonify({
                "status": "error",
                "error_type": "validation",
                "message": "Invalid batch ID format"
            }), 400
            
        except Exception as e:
            self.logger.error(f"Error in get_batch_status: {str(e)}")
            return jsonify({
                "status": "error",
                "error_type": "system",
                "message": "An unexpected error occurred"
            }), 500
    
    def process_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        API endpoint to process a NEFT batch.
        """
        try:
            # Get user_id if provided
            user_id = request.json.get('user_id') if request.is_json else None
            
            # Use the use case
            result = self.batch_processing_use_case.process_batch(
                batch_id=UUID(batch_id),
                user_id=user_id
            )
            
            # Return response
            status_code = 400 if result.get('status') == 'error' else 200
            return jsonify(result), status_code
            
        except ValueError:
            return jsonify({
                "status": "error",
                "error_type": "validation",
                "message": "Invalid batch ID format"
            }), 400
            
        except Exception as e:
            self.logger.error(f"Error in process_batch: {str(e)}")
            return jsonify({
                "status": "error",
                "error_type": "system",
                "message": "An unexpected error occurred"
            }), 500
    
    def get_pending_batches(self) -> Dict[str, Any]:
        """
        API endpoint to get all pending NEFT batches.
        """
        try:
            # Get user_id if provided
            user_id = request.args.get('user_id')
            
            # Use the use case
            result = self.batch_query_use_case.get_pending_batches(user_id)
            
            # Return response
            return jsonify(result), 200
            
        except Exception as e:
            self.logger.error(f"Error in get_pending_batches: {str(e)}")
            return jsonify({
                "status": "error",
                "error_type": "system",
                "message": "An unexpected error occurred"
            }), 500
    
    def get_batches_by_date(self, date_str: str) -> Dict[str, Any]:
        """
        API endpoint to get NEFT batches by date.
        """
        try:
            # Get user_id if provided
            user_id = request.args.get('user_id')
            
            # Use the use case
            result = self.batch_query_use_case.get_batches_by_date(
                date_str=date_str,
                user_id=user_id
            )
            
            # Return response
            return jsonify(result), 200
            
        except Exception as e:
            self.logger.error(f"Error in get_batches_by_date: {str(e)}")
            return jsonify({
                "status": "error",
                "error_type": "system",
                "message": "An unexpected error occurred"
            }), 500
    
    def get_customer_transactions(self, customer_id: str) -> Dict[str, Any]:
        """
        API endpoint to get NEFT transactions for a customer.
        """
        try:
            # Get parameters
            limit = request.args.get('limit', default=10, type=int)
            user_id = request.args.get('user_id')
            
            # Use the use case
            result = self.transaction_query_use_case.get_customer_transactions(
                customer_id=customer_id,
                limit=limit,
                user_id=user_id
            )
            
            # Return response
            return jsonify(result), 200
            
        except Exception as e:
            self.logger.error(f"Error in get_customer_transactions: {str(e)}")
            return jsonify({
                "status": "error",
                "error_type": "system",
                "message": "An unexpected error occurred"
            }), 500
