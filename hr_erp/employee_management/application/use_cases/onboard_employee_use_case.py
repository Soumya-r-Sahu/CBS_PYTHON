"""
Onboard Employee Use Case

This module defines the use case for onboarding new employees in the HR-ERP system.
It demonstrates Clean Architecture principles by separating business rules from
external dependencies and framework concerns.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, List
import uuid

from ...domain.entities.employee import Employee
from ...domain.value_objects.employee_id import EmployeeId
from ...domain.value_objects.address import Address
from ...domain.value_objects.contact_info import ContactInfo
from ...domain.repositories.employee_repository import EmployeeRepository
from ..interfaces.notification_service import NotificationService
from ..interfaces.document_service import DocumentService


@dataclass
class OnboardEmployeeInputDto:
    """Data Transfer Object for employee onboarding input"""
    first_name: str
    last_name: str
    date_of_birth: date
    hire_date: date
    department: str
    position: str
    manager_employee_id: Optional[str] = None
    status: str = "Active"
    
    # Address fields
    street: str
    city: str
    state: str
    zip_code: str
    country: str
    
    # Contact fields
    email: str
    phone: str
    emergency_contact_name: str
    emergency_contact_phone: str
    
    # Skills and qualifications
    skills: List[str] = None
    certifications: List[str] = None


@dataclass
class OnboardEmployeeOutputDto:
    """Data Transfer Object for employee onboarding output"""
    employee_id: str
    system_id: str
    full_name: str
    email: str
    department: str
    position: str
    onboarding_tasks_created: int
    documents_pending: int
    notification_sent: bool


class OnboardEmployeeUseCase:
    """
    Use case for onboarding a new employee into the organization.
    
    This class implements the application business rules for employee onboarding,
    coordinating between multiple domain entities and services.
    """
    
    def __init__(
        self, 
        employee_repository: EmployeeRepository,
        notification_service: NotificationService,
        document_service: DocumentService
    ):
        """Initialize the use case with required repositories and services"""
        self._employee_repository = employee_repository
        self._notification_service = notification_service
        self._document_service = document_service
    
    def execute(self, input_dto: OnboardEmployeeInputDto) -> OnboardEmployeeOutputDto:
        """
        Execute the onboarding process for a new employee
        
        Args:
            input_dto: The data required to onboard an employee
            
        Returns:
            Output DTO containing the result of the onboarding process
            
        Raises:
            ValidationError: If input data doesn't meet business requirements
        """
        # 1. Create employee value objects
        employee_id = self._generate_employee_id(input_dto.hire_date, input_dto.department)
        
        address = Address(
            street=input_dto.street,
            city=input_dto.city,
            state=input_dto.state,
            zip_code=input_dto.zip_code,
            country=input_dto.country
        )
        
        contact_info = ContactInfo(
            email=input_dto.email,
            phone=input_dto.phone,
            emergency_contact_name=input_dto.emergency_contact_name,
            emergency_contact_phone=input_dto.emergency_contact_phone
        )
        
        # 2. Create manager reference if provided
        manager_id = None
        if input_dto.manager_employee_id:
            manager_id = EmployeeId(input_dto.manager_employee_id)
            # Validate manager exists
            if not self._employee_repository.exists_by_employee_id(manager_id):
                raise ValueError(f"Manager with ID {manager_id.value} does not exist")
        
        # 3. Create the employee entity
        skills = input_dto.skills or []
        certifications = input_dto.certifications or []
        
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
            manager_id=manager_id,
            skills=skills,
            certifications=certifications
        )
        
        # 4. Persist the employee
        saved_employee = self._employee_repository.add(employee)
        
        # 5. Create onboarding tasks and documents
        onboarding_tasks = self._create_onboarding_tasks(saved_employee)
        required_documents = self._document_service.create_employee_document_requirements(saved_employee.id)
        
        # 6. Send notifications
        notification_sent = self._notification_service.send_onboarding_notification(
            saved_employee.id, 
            saved_employee.first_name,
            saved_employee.contact_info.email
        )
        
        # 7. Return output DTO
        return OnboardEmployeeOutputDto(
            employee_id=saved_employee.employee_id.value,
            system_id=str(saved_employee.id),
            full_name=f"{saved_employee.first_name} {saved_employee.last_name}",
            email=saved_employee.contact_info.email,
            department=saved_employee.department,
            position=saved_employee.position,
            onboarding_tasks_created=len(onboarding_tasks),
            documents_pending=len(required_documents),
            notification_sent=notification_sent
        )
    
    def _generate_employee_id(self, hire_date: date, department: str) -> EmployeeId:
        """
        Generate a new employee ID based on business rules
        
        Format: EMP-YYYY-DDDD where YYYY is hire year and DDDD is department prefix + sequence
        """
        year = hire_date.year
        dept_prefix = department[:2].upper()
        
        # Get next sequence for this department and year
        sequence = self._employee_repository.get_next_employee_sequence(year, dept_prefix)
        
        # Format: EMP-2025-HR001 (for first HR hire in 2025)
        employee_id_value = f"EMP-{year}-{dept_prefix}{sequence:03d}"
        return EmployeeId(employee_id_value)
    
    def _create_onboarding_tasks(self, employee: Employee) -> List[dict]:
        """Create standard onboarding tasks for a new employee"""
        # This would be implemented based on company onboarding process
        # Just returning placeholder data for now
        tasks = [
            {"name": "IT Equipment Setup", "deadline": employee.hire_date},
            {"name": "HR Orientation", "deadline": employee.hire_date},
            {"name": "Department Introduction", "deadline": employee.hire_date},
            {"name": "Benefits Enrollment", "deadline": employee.hire_date},
            {"name": "Security Access", "deadline": employee.hire_date},
        ]
        return tasks
