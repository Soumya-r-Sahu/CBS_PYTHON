"""
Employee Management REST API Controller

This module implements the REST API for employee management.
"""

import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

from ...application.use_cases.onboard_employee_use_case import OnboardEmployeeUseCase, OnboardEmployeeInputDto
from ..di_container import get_employee_onboarding_use_case

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
employee_api = Blueprint('employee_api', __name__)


@employee_api.route('/api/employees', methods=['POST'])
def create_employee():
    """
    API endpoint for creating a new employee
    
    This demonstrates a presentation layer that uses the application layer
    use cases without knowing about domain or infrastructure details.
    """
    try:
        # Extract data from request
        data = request.json
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'dateOfBirth', 'hireDate', 
                          'department', 'position', 'street', 'city', 'state', 
                          'zipCode', 'country', 'email', 'phone']
        
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Convert date strings to date objects
        try:
            date_of_birth = datetime.strptime(data['dateOfBirth'], '%Y-%m-%d').date()
            hire_date = datetime.strptime(data['hireDate'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400
        
        # Create use case input DTO
        input_dto = OnboardEmployeeInputDto(
            first_name=data['firstName'],
            last_name=data['lastName'],
            date_of_birth=date_of_birth,
            hire_date=hire_date,
            department=data['department'],
            position=data['position'],
            status=data.get('status', 'Active'),
            manager_employee_id=data.get('managerId'),
            street=data['street'],
            city=data['city'],
            state=data['state'],
            zip_code=data['zipCode'],
            country=data['country'],
            email=data['email'],
            phone=data['phone'],
            emergency_contact_name=data.get('emergencyContactName', ''),
            emergency_contact_phone=data.get('emergencyContactPhone', ''),
            skills=data.get('skills', []),
            certifications=data.get('certifications', [])
        )
        
        # Get use case from dependency injection container
        use_case: OnboardEmployeeUseCase = get_employee_onboarding_use_case()
        
        # Execute use case
        output_dto = use_case.execute(input_dto)
        
        # Return response
        return jsonify({
            "employeeId": output_dto.employee_id,
            "systemId": output_dto.system_id, 
            "fullName": output_dto.full_name,
            "email": output_dto.email,
            "department": output_dto.department,
            "position": output_dto.position,
            "onboardingTasksCreated": output_dto.onboarding_tasks_created,
            "documentsPending": output_dto.documents_pending,
            "notificationSent": output_dto.notification_sent
        }), 201
        
    except ValueError as e:
        # Domain validation errors
        logger.error(f"Validation error: {str(e)}")
        return jsonify({"error": str(e)}), 400
        
    except Exception as e:
        # Unexpected errors
        logger.exception(f"Error creating employee: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@employee_api.route('/api/employees/<employee_id>', methods=['GET'])
def get_employee(employee_id):
    """API endpoint for retrieving an employee"""
    # This would be implemented with a query use case
    return jsonify({"error": "Not implemented yet"}), 501


@employee_api.route('/api/employees/<employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """API endpoint for updating an employee"""
    # This would be implemented with an update use case
    return jsonify({"error": "Not implemented yet"}), 501
