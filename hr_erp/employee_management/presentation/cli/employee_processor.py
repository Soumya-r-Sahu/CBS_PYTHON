"""
Employee CLI Processor

This module provides command-line interface for employee management
in the HR-ERP system.
"""

import argparse
import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional

from ...infrastructure.di_container import get_container
from ...application.use_cases.create_employee_use_case import (
    CreateEmployeeUseCase, 
    CreateEmployeeInputDto
)
from ..dto.employee_dto import EmployeeDto


class EmployeeCliProcessor:
    """
    Command Line Interface for employee management
    
    This class processes CLI commands related to employee management,
    transforming arguments into use case inputs and outputs to console.
    """
    
    def __init__(self):
        """Initialize the CLI processor"""
        self._logger = logging.getLogger('hr-employee-cli')
        self._container = get_container()
    
    def process_command(self, args: List[str]) -> int:
        """
        Process a CLI command
        
        Args:
            args: Command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for errors)
        """
        parser = argparse.ArgumentParser(description='Employee Management CLI')
        subparsers = parser.add_subparsers(dest='command', help='Command')
        
        # Create employee command
        create_parser = subparsers.add_parser('create', help='Create a new employee')
        create_parser.add_argument('--first-name', required=True, help='First name')
        create_parser.add_argument('--last-name', required=True, help='Last name')
        create_parser.add_argument('--date-of-birth', required=True, help='Date of birth (YYYY-MM-DD)')
        create_parser.add_argument('--hire-date', required=True, help='Hire date (YYYY-MM-DD)')
        create_parser.add_argument('--department', required=True, help='Department')
        create_parser.add_argument('--position', required=True, help='Position/job title')
        create_parser.add_argument('--street', required=True, help='Street address')
        create_parser.add_argument('--street2', help='Street address line 2')
        create_parser.add_argument('--city', required=True, help='City')
        create_parser.add_argument('--state', required=True, help='State/province')
        create_parser.add_argument('--postal-code', required=True, help='Postal code')
        create_parser.add_argument('--country', required=True, help='Country')
        create_parser.add_argument('--email', required=True, help='Email address')
        create_parser.add_argument('--phone', required=True, help='Phone number')
        create_parser.add_argument('--manager-id', help='Manager employee ID')
        
        # Get employee command
        get_parser = subparsers.add_parser('get', help='Get employee details')
        get_parser.add_argument('employee_id', help='Employee ID')
        
        # List employees command
        list_parser = subparsers.add_parser('list', help='List all employees')
        list_parser.add_argument('--department', help='Filter by department')
        list_parser.add_argument('--json', action='store_true', help='Output in JSON format')
        
        # Update employee command
        update_parser = subparsers.add_parser('update', help='Update employee details')
        update_parser.add_argument('employee_id', help='Employee ID')
        update_parser.add_argument('--first-name', help='First name')
        update_parser.add_argument('--last-name', help='Last name')
        update_parser.add_argument('--department', help='Department')
        update_parser.add_argument('--position', help='Position/job title')
        update_parser.add_argument('--status', help='Employee status')
        
        # Terminate employee command
        terminate_parser = subparsers.add_parser('terminate', help='Terminate an employee')
        terminate_parser.add_argument('employee_id', help='Employee ID')
        
        # Parse arguments
        parsed_args = parser.parse_args(args)
        
        # Process command
        try:
            if parsed_args.command == 'create':
                return self._process_create(parsed_args)
            elif parsed_args.command == 'get':
                return self._process_get(parsed_args)
            elif parsed_args.command == 'list':
                return self._process_list(parsed_args)
            elif parsed_args.command == 'update':
                return self._process_update(parsed_args)
            elif parsed_args.command == 'terminate':
                return self._process_terminate(parsed_args)
            else:
                parser.print_help()
                return 1
        except Exception as e:
            self._logger.error(f"Error processing command: {e}")
            print(f"Error: {e}")
            return 1
    
    def _process_create(self, args) -> int:
        """
        Process create employee command
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code
        """
        try:
            # Parse dates
            date_of_birth = datetime.strptime(args.date_of_birth, '%Y-%m-%d').date()
            hire_date = datetime.strptime(args.hire_date, '%Y-%m-%d').date()
            
            # Create input DTO
            input_dto = CreateEmployeeInputDto(
                first_name=args.first_name,
                last_name=args.last_name,
                date_of_birth=date_of_birth,
                hire_date=hire_date,
                department=args.department,
                position=args.position,
                status="Active",
                manager_employee_id=args.manager_id,
                street=args.street,
                street2=args.street2,
                city=args.city,
                state=args.state,
                postal_code=args.postal_code,
                country=args.country,
                email=args.email,
                phone=args.phone
            )
            
            # Get use case from DI container
            use_case: CreateEmployeeUseCase = self._container.resolve(CreateEmployeeUseCase)
            
            # Execute use case
            output_dto = use_case.execute(input_dto)
            
            # Print result
            print(f"Employee created successfully!")
            print(f"Employee ID: {output_dto.employee_id}")
            print(f"Name: {output_dto.full_name}")
            print(f"ID: {output_dto.id}")
            
            return 0
            
        except ValueError as e:
            print(f"Validation error: {e}")
            return 1
            
        except Exception as e:
            self._logger.error(f"Error creating employee: {e}")
            print(f"Error: Internal server error")
            return 1
    
    def _process_get(self, args) -> int:
        """
        Process get employee command
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code
        """
        try:
            # Get repository from DI container
            repository = self._container.resolve('EmployeeRepository')
            
            # Get employee from repository
            employee = repository.get_by_employee_id(args.employee_id)
            
            if not employee:
                print(f"Employee not found: {args.employee_id}")
                return 1
            
            # Transform entity to DTO
            employee_dto = EmployeeDto.from_entity(employee)
            
            # Print employee details
            print(f"Employee ID: {employee_dto.employee_id}")
            print(f"Name: {employee_dto.full_name}")
            print(f"Department: {employee_dto.department}")
            print(f"Position: {employee_dto.position}")
            print(f"Status: {employee_dto.status}")
            print(f"Hire Date: {employee_dto.hire_date}")
            print(f"Email: {employee_dto.email}")
            print(f"Phone: {employee_dto.phone}")
            
            return 0
            
        except Exception as e:
            self._logger.error(f"Error getting employee: {e}")
            print(f"Error: Internal server error")
            return 1
    
    def _process_list(self, args) -> int:
        """
        Process list employees command
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code
        """
        try:
            # Get repository from DI container
            repository = self._container.resolve('EmployeeRepository')
            
            # Get employees
            if args.department:
                employees = repository.get_by_department(args.department)
            else:
                employees = repository.get_all()
            
            if not employees:
                print("No employees found")
                return 0
            
            # Transform entities to DTOs
            employee_dtos = [EmployeeDto.from_entity(emp) for emp in employees]
            
            if args.json:
                # Output as JSON
                json_data = {
                    "employees": [dto.to_dict() for dto in employee_dtos],
                    "total": len(employee_dtos)
                }
                print(json.dumps(json_data, indent=2))
            else:
                # Print as table
                print(f"{'ID':<12} {'Name':<30} {'Department':<20} {'Position':<20} {'Status':<10}")
                print("-" * 92)
                
                for dto in employee_dtos:
                    print(f"{dto.employee_id:<12} {dto.full_name:<30} {dto.department:<20} {dto.position:<20} {dto.status:<10}")
            
            return 0
            
        except Exception as e:
            self._logger.error(f"Error listing employees: {e}")
            print(f"Error: Internal server error")
            return 1
    
    def _process_update(self, args) -> int:
        """
        Process update employee command
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code
        """
        try:
            # Get repository from DI container
            repository = self._container.resolve('EmployeeRepository')
            
            # Get employee from repository
            employee = repository.get_by_employee_id(args.employee_id)
            
            if not employee:
                print(f"Employee not found: {args.employee_id}")
                return 1
            
            # Update employee properties
            updated = False
            
            if args.first_name:
                employee.first_name = args.first_name
                updated = True
                
            if args.last_name:
                employee.last_name = args.last_name
                updated = True
                
            if args.department:
                employee.department = args.department
                updated = True
                
            if args.position:
                employee.position = args.position
                updated = True
                
            if args.status:
                employee.change_status(args.status)
                updated = True
            
            if not updated:
                print("No changes specified")
                return 0
            
            # Save updated employee
            repository.save(employee)
            
            print(f"Employee updated successfully!")
            print(f"Employee ID: {employee.employee_id}")
            print(f"Name: {employee.full_name()}")
            
            return 0
            
        except ValueError as e:
            print(f"Validation error: {e}")
            return 1
            
        except Exception as e:
            self._logger.error(f"Error updating employee: {e}")
            print(f"Error: Internal server error")
            return 1
    
    def _process_terminate(self, args) -> int:
        """
        Process terminate employee command
        
        Args:
            args: Parsed arguments
            
        Returns:
            Exit code
        """
        try:
            # Get repository from DI container
            repository = self._container.resolve('EmployeeRepository')
            
            # Get employee from repository
            employee = repository.get_by_employee_id(args.employee_id)
            
            if not employee:
                print(f"Employee not found: {args.employee_id}")
                return 1
            
            # Confirm termination
            confirm = input(f"Are you sure you want to terminate employee {employee.full_name()}? (y/n): ")
            if confirm.lower() != 'y':
                print("Termination cancelled")
                return 0
            
            # Terminate the employee
            employee.change_status("Terminated")
            repository.save(employee)
            
            print(f"Employee terminated successfully:")
            print(f"Employee ID: {employee.employee_id}")
            print(f"Name: {employee.full_name()}")
            
            return 0
            
        except Exception as e:
            self._logger.error(f"Error terminating employee: {e}")
            print(f"Error: Internal server error")
            return 1
"""
