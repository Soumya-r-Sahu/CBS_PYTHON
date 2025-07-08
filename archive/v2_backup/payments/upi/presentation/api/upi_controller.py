"""
UPI API controller for handling UPI payment requests.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from flask import Blueprint, request, jsonify

from ...application.use_cases.send_money_use_case import SendMoneyUseCase, SendMoneyRequest
from ...application.use_cases.complete_transaction_use_case import CompleteTransactionUseCase, CompleteTransactionRequest


class UpiController:
    """API controller for UPI transactions."""
    
    def __init__(
        self,
        send_money_use_case: SendMoneyUseCase,
        complete_transaction_use_case: CompleteTransactionUseCase
    ):
        """
        Initialize with required use cases.
        
        Args:
            send_money_use_case: Use case for sending money
            complete_transaction_use_case: Use case for completing transactions
        """
        self.send_money_use_case = send_money_use_case
        self.complete_transaction_use_case = complete_transaction_use_case
        
        # Create Flask Blueprint
        self.blueprint = Blueprint('upi', __name__)
        
        # Register routes
        self.blueprint.route('/send-money', methods=['POST'])(self.send_money)
        self.blueprint.route('/complete-transaction', methods=['POST'])(self.complete_transaction)
        self.blueprint.route('/transaction/<transaction_id>', methods=['GET'])(self.get_transaction)
        self.blueprint.route('/reconcile', methods=['POST'])(self.reconcile_transactions)
        self.blueprint.route('/fraud-analysis/<transaction_id>', methods=['GET'])(self.analyze_transaction_fraud)
    
    def send_money(self):
        """Handle send money API request."""
        try:
            data = request.json
            
            # Validate request data
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Invalid request data'
                }), 400
            
            # Extract request data
            sender_vpa = data.get('sender_vpa')
            receiver_vpa = data.get('receiver_vpa')
            amount = data.get('amount')
            remarks = data.get('remarks')
            
            # Validate required fields
            if not sender_vpa or not receiver_vpa or not amount:
                return jsonify({
                    'success': False,
                    'error': 'Missing required fields'
                }), 400
            
            # Convert amount to float if needed
            try:
                amount = float(amount)
            except (ValueError, TypeError):
                return jsonify({
                    'success': False,
                    'error': 'Invalid amount format'
                }), 400
            
            # Create use case request
            send_money_request = SendMoneyRequest(
                sender_vpa=sender_vpa,
                receiver_vpa=receiver_vpa,
                amount=amount,
                remarks=remarks
            )
            
            # Execute use case
            response = self.send_money_use_case.execute(send_money_request)
            
            # Return response
            if response.success:
                return jsonify({
                    'success': True,
                    'message': response.message,
                    'transaction_id': str(response.transaction_id)
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': response.message,
                    'error_code': response.error_code
                }), 400
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }), 500
    
    def complete_transaction(self):
        """Handle complete transaction API request."""
        try:
            data = request.json
            
            # Validate request data
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Invalid request data'
                }), 400
            
            # Extract request data
            transaction_id = data.get('transaction_id')
            reference_id = data.get('reference_id')
            
            # Validate required fields
            if not transaction_id or not reference_id:
                return jsonify({
                    'success': False,
                    'error': 'Missing required fields'
                }), 400
            
            # Convert transaction_id to UUID
            try:
                transaction_id = UUID(transaction_id)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Invalid transaction ID format'
                }), 400
            
            # Create use case request
            complete_request = CompleteTransactionRequest(
                transaction_id=transaction_id,
                reference_id=reference_id
            )
            
            # Execute use case
            response = self.complete_transaction_use_case.execute(complete_request)
            
            # Return response
            if response.success:
                return jsonify({
                    'success': True,
                    'message': response.message
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': response.message,
                    'error_code': response.error_code
                }), 400
        
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }), 500
    
    def get_transaction(self, transaction_id):
        """Handle get transaction API request."""
        try:
            # This is a placeholder - in a real implementation, we would get the transaction from the repository
            return jsonify({
                'success': False,
                'error': 'Not implemented yet'
            }), 501
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def reconcile_transactions(self):
        """Handle reconciliation of pending transactions."""
        try:
            # Get the reconciliation service from the dependency injection container
            # This assumes we have access to the container, which we might need to inject
            # In a real implementation, we would use proper dependency injection
            from ...di_container import UpiDiContainer
            from ... import main_clean_architecture
            
            container = UpiDiContainer(main_clean_architecture.get_config())
            reconciliation_service = container.get_reconciliation_service()
            
            # Run reconciliation
            reconciliation_stats = reconciliation_service.reconcile_pending_transactions()
            
            # Also generate a daily summary if requested
            generate_summary = request.args.get('generate_summary', 'false').lower() == 'true'
            
            response_data = {
                'success': True,
                'reconciliation_stats': reconciliation_stats
            }
            
            if generate_summary:
                daily_summary = reconciliation_service.reconcile_daily_summary()
                response_data['daily_summary'] = daily_summary
            
            return jsonify(response_data), 200
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    def analyze_transaction_fraud(self, transaction_id):
        """Handle fraud analysis for a specific transaction."""
        try:
            # Convert transaction ID string to UUID
            from uuid import UUID
            transaction_uuid = UUID(transaction_id)
            
            # Get the fraud detection service and transaction repository from the DI container
            from ...di_container import UpiDiContainer
            from ... import main_clean_architecture
            
            container = UpiDiContainer(main_clean_architecture.get_config())
            fraud_detection_service = container.get_fraud_detection_service()
            transaction_repository = container.get_transaction_repository()
            
            # Get the transaction
            transaction = transaction_repository.get_by_id(transaction_uuid)
            
            if not transaction:
                return jsonify({
                    'success': False,
                    'error': f'Transaction with ID {transaction_id} not found'
                }), 404
            
            # Analyze the transaction for fraud
            fraud_analysis = fraud_detection_service.analyze_transaction(transaction)
            
            return jsonify({
                'success': True,
                'transaction_id': transaction_id,
                'fraud_analysis': fraud_analysis
            }), 200
            
        except ValueError:
            return jsonify({
                'success': False,
                'error': f'Invalid transaction ID format: {transaction_id}'
            }), 400
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
