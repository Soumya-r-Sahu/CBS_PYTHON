"""
UPI Registration Controller Module.

API endpoints for UPI user registration.
"""
import logging
from typing import Dict, Any
from flask import Blueprint, request, jsonify

from ..services.upi_service import upi_service
from ..validators.upi_validators import validate_upi_id
from ..exceptions.upi_exceptions import (
    UpiBaseException, UpiValidationError, UpiNotFoundError, 
    UpiRegistrationError, UpiAlreadyRegisteredError
)

# Set up logging
logger = logging.getLogger(__name__)

# Create Blueprint for registration APIs
upi_registration_api = Blueprint('upi_registration_api', __name__)


@upi_registration_api.route('/', methods=['POST'])
def register_user():
    """
    Register a new user for UPI services.
    
    Request body:
    {
        "upi_id": "user@upi",
        "account_number": "1234567890",
        "mobile_number": "9876543210",
        "name": "John Doe"
    }
    
    Returns:
        JSON with registration details
    """
    try:
        # Get registration data from request
        data = request.get_json()
        if not data:
            return jsonify({
                "status": "error",
                "message": "Missing request body"
            }), 400
        
        # Register user
        result = upi_service.register_user(data)
        
        # Return success response
        return jsonify({
            "status": "success",
            "message": "User registered successfully",
            "registration": result
        }), 201
        
    except UpiValidationError as e:
        logger.warning(f"Validation error in registration: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "details": getattr(e, 'details', {})
        }), 400
        
    except UpiAlreadyRegisteredError as e:
        logger.warning(f"UPI ID already registered: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "details": getattr(e, 'details', {})
        }), 409
        
    except UpiRegistrationError as e:
        logger.warning(f"Registration error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "details": getattr(e, 'details', {})
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error in registration: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred during registration"
        }), 500


@upi_registration_api.route('/<upi_id>', methods=['GET'])
def get_registration(upi_id):
    """
    Get user registration by UPI ID.
    
    Args:
        upi_id: UPI ID to retrieve
    
    Returns:
        JSON with registration details
    """
    try:
        # Validate UPI ID
        validate_upi_id(upi_id)
        
        # Get registration
        registration = upi_service.get_user_registration(upi_id)
        
        # Return success response
        return jsonify({
            "status": "success",
            "registration": registration
        }), 200
        
    except UpiValidationError as e:
        logger.warning(f"Invalid UPI ID: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
        
    except UpiNotFoundError as e:
        logger.warning(f"Registration not found: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"Unexpected error retrieving registration: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred while retrieving registration"
        }), 500


@upi_registration_api.route('/<upi_id>/status', methods=['PUT'])
def update_registration_status(upi_id):
    """
    Update UPI registration status.
    
    Args:
        upi_id: UPI ID to update
    
    Request body:
    {
        "status": "active/inactive/suspended"
    }
    
    Returns:
        JSON with updated registration details
    """
    try:
        # Validate UPI ID
        validate_upi_id(upi_id)
        
        # Get status from request
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing status in request body"
            }), 400
        
        new_status = data['status']
        valid_statuses = ['active', 'inactive', 'suspended']
        if new_status not in valid_statuses:
            return jsonify({
                "status": "error",
                "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            }), 400
        
        # Get existing registration
        registration = upi_service.get_user_registration(upi_id)
        
        # Update status
        registration['status'] = new_status
        updated_registration = upi_service.upi_repository.save_registration(registration)
        
        # Return success response
        return jsonify({
            "status": "success",
            "message": f"Registration status updated to {new_status}",
            "registration": updated_registration
        }), 200
        
    except UpiValidationError as e:
        logger.warning(f"Invalid UPI ID: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
        
    except UpiNotFoundError as e:
        logger.warning(f"Registration not found: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 404
        
    except Exception as e:
        logger.error(f"Unexpected error updating registration: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred while updating registration"
        }), 500
