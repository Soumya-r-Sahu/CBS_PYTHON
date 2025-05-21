"""
Employee REST API Controller

This module provides REST API endpoints for employee management
in the HR-ERP system.
"""

import logging
import json
from datetime import datetime, date
from typing import Dict, Any, List, Optional

from ...infrastructure.di_container import get_container
from ...application.use_cases.create_employee_use_case import (
    CreateEmployeeUseCase, 
    CreateEmployeeInputDto,
    CreateEmployeeOutputDto
)
from ..dto.employee_dto import EmployeeDto


class EmployeeApiController:
    """
    Controller for employee management REST API endpoints
    
    This class handles HTTP requests related to employee management,
    transforming requests into use case inputs and responses from use case outputs.
    """
    
    def __init__(self):
        """Initialize the controller"""
        self._logger = logging.getLogger('hr-employee-api')
        self._container = get_container()
    
    def create_employee(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new employee
        
        Args:
            request_data: HTTP request data
            
        Returns:
            Response data
            
        Raises:
            ValueError: If the request data is invalid
        """
        try:
            # Transform request data to input DTO
            input_dto = self._map_create_request_to_dto(request_data)
            
            # Get use case from DI container
            use_case: CreateEmployeeUseCase = self._container.resolve(CreateEmployeeUseCase)
            
            # Execute use case
            output_dto = use_case.execute(input_dto)
            
            # Transform output DTO to response
            response = self._map_create_output_to_response(output_dto)
            
            self._logger.info(f"Created employee: {output_dto.employee_id}")
            return {
                "status": "success",
                "message": "Employee created successfully",
                "data": response
            }
            
        except ValueError as e:
            self._logger.error(f"Validation error creating employee: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": None
            }
            
        except Exception as e:
            self._logger.error(f"Error creating employee: {e}")
            return {
                "status": "error",
                "message": "Internal server error",
                "data": None
            }
    
    def get_employee(self, employee_id: str) -> Dict[str, Any]:
        """
        Get employee details
        
        Args:
            employee_id: Employee ID
            
        Returns:
            Response data
        """
        try:
            # Get repository from DI container
            repository = self._container.resolve('EmployeeRepository')
            
            # Get employee from repository
            employee = repository.get_by_employee_id(employee_id)
            
            if not employee:
                return {
                    "status": "error",
                    "message": f"Employee not found: {employee_id}",
                    "data": None
                }
            
            # Transform entity to DTO
            employee_dto = EmployeeDto.from_entity(employee)
            
            return {
                "status": "success",
                "message": "Employee retrieved successfully",
                "data": employee_dto.to_dict()
            }
            
        except Exception as e:
            self._logger.error(f"Error retrieving employee: {e}")
            return {
                "status": "error",
                "message": "Internal server error",
                "data": None
            }
    
    def update_employee(self, employee_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update employee details
        
        Args:
            employee_id: Employee ID
            request_data: HTTP request data
            
        Returns:
            Response data
        """
        try:
            # Get repository from DI container
            repository = self._container.resolve('EmployeeRepository')
            
            # Get employee from repository
            employee = repository.get_by_employee_id(employee_id)
            
            if not employee:
                return {
                    "status": "error",
                    "message": f"Employee not found: {employee_id}",
                    "data": None
                }
            
            # Update employee properties from request data
            if 'first_name' in request_data:
                employee.first_name = request_data['first_name']
                
            if 'last_name' in request_data:
                employee.last_name = request_data['last_name']
                
            if 'department' in request_data:
                employee.department = request_data['department']
                
            if 'position' in request_data:
                employee.position = request_data['position']
                
            if 'status' in request_data:
                employee.change_status(request_data['status'])
            
            # Save updated employee
            updated_employee = repository.save(employee)
            
            # Transform entity to DTO
            employee_dto = EmployeeDto.from_entity(updated_employee)
            
            return {
                "status": "success",
                "message": "Employee updated successfully",
                "data": employee_dto.to_dict()
            }
            
        except ValueError as e:
            self._logger.error(f"Validation error updating employee: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": None
            }
            
        except Exception as e:
            self._logger.error(f"Error updating employee: {e}")
            return {
                "status": "error",
                "message": "Internal server error",
                "data": None
            }
    
    def delete_employee(self, employee_id: str) -> Dict[str, Any]:
        """
        Delete/terminate an employee
        
        Args:
            employee_id: Employee ID
            
        Returns:
            Response data
        """
        try:
            # Get repository from DI container
            repository = self._container.resolve('EmployeeRepository')
            
            # Get employee from repository
            employee = repository.get_by_employee_id(employee_id)
            
            if not employee:
                return {
                    "status": "error",
                    "message": f"Employee not found: {employee_id}",
                    "data": None
                }
            
            # Terminate the employee (change status)
            employee.change_status("Terminated")
            repository.save(employee)
            
            return {
                "status": "success",
                "message": "Employee terminated successfully",
                "data": None
            }
            
        except Exception as e:
            self._logger.error(f"Error terminating employee: {e}")
            return {
                "status": "error",
                "message": "Internal server error",
                "data": None
            }
    
    def get_all_employees(self) -> Dict[str, Any]:
        """
        Get all employees
        
        Returns:
            Response data with list of employees
        """
        try:
            # Get repository from DI container
            repository = self._container.resolve('EmployeeRepository')
            
            # Get all employees
            employees = repository.get_all()
            
            # Transform entities to DTOs
            employee_dtos = [EmployeeDto.from_entity(emp).to_dict() for emp in employees]
            
            return {
                "status": "success",
                "message": "Employees retrieved successfully",
                "data": employee_dtos
            }
            
        except Exception as e:
            self._logger.error(f"Error retrieving employees: {e}")
            return {
                "status": "error",
                "message": "Internal server error",
                "data": None
            }
    
    def _map_create_request_to_dto(self, request_data: Dict[str, Any]) -> CreateEmployeeInputDto:
        """
        Map HTTP request data to use case input DTO
        
        Args:
            request_data: HTTP request data
            
        Returns:
            Input DTO for create employee use case
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = [
            'first_name', 'last_name', 'date_of_birth', 'hire_date', 
            'department', 'position', 'street', 'city', 'state', 
            'postal_code', 'country', 'email', 'phone'
        ]
        
        for field in required_fields:
            if field not in request_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Parse dates
        try:
            date_of_birth = datetime.strptime(request_data['date_of_birth'], '%Y-%m-%d').date()
            hire_date = datetime.strptime(request_data['hire_date'], '%Y-%m-%d').date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
        
        return CreateEmployeeInputDto(
            first_name=request_data['first_name'],
            last_name=request_data['last_name'],
            date_of_birth=date_of_birth,
            hire_date=hire_date,
            department=request_data['department'],
            position=request_data['position'],
            status=request_data.get('status', 'Active'),
            manager_employee_id=request_data.get('manager_id'),
            street=request_data['street'],
            street2=request_data.get('street2'),
            city=request_data['city'],
            state=request_data['state'],
            postal_code=request_data['postal_code'],
            country=request_data['country'],
            email=request_data['email'],
            phone=request_data['phone'],
            alternate_email=request_data.get('alternate_email'),
            mobile=request_data.get('mobile')
        )
    
    def _map_create_output_to_response(self, output_dto: CreateEmployeeOutputDto) -> Dict[str, Any]:
        """
        Map use case output DTO to HTTP response
        
        Args:
            output_dto: Use case output DTO
            
        Returns:
            Response data
        """
        return {
            "id": output_dto.id,
            "employee_id": output_dto.employee_id,
            "first_name": output_dto.first_name,
            "last_name": output_dto.last_name,
            "full_name": output_dto.full_name,
            "date_of_birth": output_dto.date_of_birth.isoformat(),
            "hire_date": output_dto.hire_date.isoformat(),
            "department": output_dto.department,
            "position": output_dto.position,
            "status": output_dto.status
        }
"""
