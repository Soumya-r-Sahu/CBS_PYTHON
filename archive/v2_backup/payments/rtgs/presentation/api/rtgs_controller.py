"""
RTGS Controller for API endpoints.
"""
import logging
from flask import Blueprint, request, jsonify
from uuid import UUID
from datetime import datetime

logger = logging.getLogger(__name__)

rtgs_blueprint = Blueprint('rtgs', __name__, url_prefix='/api/payments/rtgs')


def register_blueprint(app, container):
    """
    Register the RTGS blueprint with the Flask app.
    
    Args:
        app: Flask application
        container: Dependency injection container
    """
    # Add container to the blueprint for dependency injection
    rtgs_blueprint.container = container
    
    # Register the blueprint with the Flask app
    app.register_blueprint(rtgs_blueprint)


@rtgs_blueprint.route('/transactions', methods=['POST'])
def create_transaction():
    """Create a new RTGS transaction."""
    try:
        # Get data from request
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        # Get the use case from container
        transaction_creation_use_case = rtgs_blueprint.container.get_transaction_creation_use_case()
        
        # Execute the use case
        result = transaction_creation_use_case.execute(
            payment_data=data,
            customer_id=data.get('customer_id'),
            user_id=data.get('user_id')
        )
        
        # Return the result
        if result.get('status') == 'error':
            return jsonify(result), 400
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Error creating RTGS transaction: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rtgs_blueprint.route('/transactions/<transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """Get a specific RTGS transaction."""
    try:
        # Validate UUID
        try:
            transaction_uuid = UUID(transaction_id)
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid transaction ID"}), 400
        
        # Get the use case from container
        transaction_query_use_case = rtgs_blueprint.container.get_transaction_query_use_case()
        
        # Execute the use case
        result = transaction_query_use_case.get_by_id(transaction_uuid)
        
        # Return the result
        if not result:
            return jsonify({"status": "error", "message": "Transaction not found"}), 404
        return jsonify({"status": "success", "data": result}), 200
        
    except Exception as e:
        logger.error(f"Error retrieving RTGS transaction: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rtgs_blueprint.route('/transactions/customer/<customer_id>', methods=['GET'])
def get_customer_transactions(customer_id):
    """Get transactions for a specific customer."""
    try:
        # Get query parameters
        limit = request.args.get('limit', default=10, type=int)
        
        # Get the use case from container
        transaction_query_use_case = rtgs_blueprint.container.get_transaction_query_use_case()
        
        # Execute the use case
        result = transaction_query_use_case.get_by_customer_id(customer_id, limit)
        
        # Return the result
        return jsonify({"status": "success", "data": result}), 200
        
    except Exception as e:
        logger.error(f"Error retrieving customer RTGS transactions: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rtgs_blueprint.route('/transactions/<transaction_id>/cancel', methods=['POST'])
def cancel_transaction(transaction_id):
    """Cancel a pending RTGS transaction."""
    try:
        # Validate UUID
        try:
            transaction_uuid = UUID(transaction_id)
        except ValueError:
            return jsonify({"status": "error", "message": "Invalid transaction ID"}), 400
        
        # Get data from request
        data = request.get_json() or {}
        
        # Get the use case from container
        transaction_processing_use_case = rtgs_blueprint.container.get_transaction_processing_use_case()
        
        # Execute the use case
        result = transaction_processing_use_case.cancel_transaction(
            transaction_id=transaction_uuid,
            cancellation_reason=data.get('reason', 'User requested cancellation'),
            user_id=data.get('user_id')
        )
        
        # Return the result
        if result.get('status') == 'error':
            return jsonify(result), 400
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error cancelling RTGS transaction: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rtgs_blueprint.route('/batches', methods=['GET'])
def get_batches():
    """Get RTGS batches."""
    try:
        # Get query parameters
        status = request.args.get('status', default=None)
        limit = request.args.get('limit', default=10, type=int)
        
        # Get date range parameters
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
        end_date = datetime.fromisoformat(end_date_str) if end_date_str else None
        
        # Get the use case from container
        batch_query_use_case = rtgs_blueprint.container.get_batch_query_use_case()
        
        # Execute the use case
        if start_date and end_date:
            result = batch_query_use_case.get_by_date_range(start_date, end_date)
        elif status:
            result = batch_query_use_case.get_by_status(status, limit)
        else:
            # Default to recent batches
            result = batch_query_use_case.get_recent_batches(limit)
        
        # Return the result
        return jsonify({"status": "success", "data": result}), 200
        
    except Exception as e:
        logger.error(f"Error retrieving RTGS batches: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rtgs_blueprint.route('/batches/<batch_number>', methods=['GET'])
def get_batch(batch_number):
    """Get a specific RTGS batch."""
    try:
        # Get the use case from container
        batch_query_use_case = rtgs_blueprint.container.get_batch_query_use_case()
        
        # Execute the use case
        result = batch_query_use_case.get_by_batch_number(batch_number)
        
        # Return the result
        if not result:
            return jsonify({"status": "error", "message": "Batch not found"}), 404
        return jsonify({"status": "success", "data": result}), 200
        
    except Exception as e:
        logger.error(f"Error retrieving RTGS batch: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@rtgs_blueprint.route('/batches/process', methods=['POST'])
def process_pending_batches():
    """Process pending RTGS batches."""
    try:
        # Get the use case from container
        batch_processing_use_case = rtgs_blueprint.container.get_batch_processing_use_case()
        
        # Execute the use case
        result = batch_processing_use_case.process_pending_batches()
        
        # Return the result
        return jsonify({"status": "success", "data": result}), 200
        
    except Exception as e:
        logger.error(f"Error processing RTGS batches: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
