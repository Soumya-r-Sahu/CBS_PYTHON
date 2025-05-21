"""
Create Employee Use Case

This module defines the use case for creating new employees
in the HR-ERP system.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from ...domain.entities.employee import Employee
from ...domain.value_objects.employee_id import EmployeeId
from ...domain.value_objects.address import Address
from ...domain.value_objects.contact_info import ContactInfo
from ...domain.repositories.employee_repository import EmployeeRepository


@dataclass
class CreateEmployeeInputDto:
    """Data Transfer Object for employee creation input"""
    first_name: str
    last_name: str
    date_of_birth: date
    hire_date: date
    department: str
    position: str
    status: str = "Active"
    manager_employee_id: Optional[str] = None
    
    # Address fields
    street: str
    city: str
    state: str
    postal_code: str
    country: str
    street2: Optional[str] = None
    
    # Contact fields
    email: str
    phone: str
    alternate_email: Optional[str] = None
    mobile: Optional[str] = None


@dataclass
class CreateEmployeeOutputDto:
    """Data Transfer Object for employee creation output"""
    id: str
    employee_id: str
    first_name: str
    last_name: str
    full_name: str
    date_of_birth: date
    hire_date: date
    department: str
    position: str
    status: str


class CreateEmployeeUseCase:
    """
    Use case for creating new employees
    
    This class implements the application logic for creating
    new employees following Clean Architecture principles.
    """
    
    def __init__(self, employee_repository: EmployeeRepository):
        """
        Initialize the use case
        
        Args:
            employee_repository: Repository for employee data access
        """
        self._employee_repository = employee_repository
    
    def execute(self, input_dto: CreateEmployeeInputDto) -> CreateEmployeeOutputDto:
        """
        Execute the use case to create a new employee
        
        Args:
            input_dto: Input data for employee creation
            
        Returns:
            Output DTO with created employee details
            
        Raises:
            ValueError: If input data is invalid
        """
        # Get the next employee number for the ID
        year = input_dto.hire_date.year
        employee_number = self._employee_repository.get_next_employee_number(year)
        
        # Create an EmployeeId value object
        employee_id = EmployeeId.create(year, employee_number)
        
        # Create Address value object
        address = Address(
            street=input_dto.street,
            street2=input_dto.street2,
            city=input_dto.city,
            state=input_dto.state,
            postal_code=input_dto.postal_code,
            country=input_dto.country
        )
        
        # Create ContactInfo value object
        contact_info = ContactInfo(
            email=input_dto.email,
            phone=input_dto.phone,
            alternate_email=input_dto.alternate_email,
            mobile=input_dto.mobile
        )
        
        # Create Manager EmployeeId if provided
        manager_id = None
        if input_dto.manager_employee_id:
            manager_id = EmployeeId(input_dto.manager_employee_id)
        
        # Create Employee entity
        employee = Employee(
            first_name=input_dto.first_name,
            last_name=input_dto.last_name,
            date_of_birth=input_dto.date_of_birth,
            hire_date=input_dto.hire_date,
            employee_id=employee_id,
            address=address,
            contact_info=contact_info,
            department=input_dto.department,
            position=input_dto.position,
            status=input_dto.status,
            manager_id=manager_id
        )
        
        # Save the employee
        saved_employee = self._employee_repository.save(employee)
        
        # Return output DTO
        return CreateEmployeeOutputDto(
            id=str(saved_employee.id),
            employee_id=str(saved_employee.employee_id),
            first_name=saved_employee.first_name,
            last_name=saved_employee.last_name,
            full_name=saved_employee.full_name(),
            date_of_birth=saved_employee.date_of_birth,
            hire_date=saved_employee.hire_date,
            department=saved_employee.department,
            position=saved_employee.position,
            status=saved_employee.status
        )
