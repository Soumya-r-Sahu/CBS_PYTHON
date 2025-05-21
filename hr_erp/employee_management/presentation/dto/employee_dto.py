"""
Employee Data Transfer Objects

This module defines DTOs for the employee management presentation layer
in the HR-ERP system.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, Dict, Any, List

from ...domain.entities.employee import Employee


@dataclass
class EmployeeDto:
    """Data Transfer Object for employee entities"""
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
    email: str
    phone: str
    address: Dict[str, str]
    manager_id: Optional[str] = None
    
    @classmethod
    def from_entity(cls, employee: Employee) -> 'EmployeeDto':
        """
        Create a DTO from an employee entity
        
        Args:
            employee: The employee entity
            
        Returns:
            EmployeeDto instance
        """
        address_dict = {
            "street": employee.address.street,
            "city": employee.address.city,
            "state": employee.address.state,
            "postal_code": employee.address.postal_code,
            "country": employee.address.country
        }
        
        if employee.address.street2:
            address_dict["street2"] = employee.address.street2
        
        return cls(
            id=str(employee.id),
            employee_id=str(employee.employee_id),
            first_name=employee.first_name,
            last_name=employee.last_name,
            full_name=employee.full_name(),
            date_of_birth=employee.date_of_birth,
            hire_date=employee.hire_date,
            department=employee.department,
            position=employee.position,
            status=employee.status,
            email=employee.contact_info.email,
            phone=employee.contact_info.phone,
            address=address_dict,
            manager_id=str(employee.manager_id) if employee.manager_id else None
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert DTO to dictionary for JSON serialization
        
        Returns:
            Dictionary representation of the DTO
        """
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "date_of_birth": self.date_of_birth.isoformat(),
            "hire_date": self.hire_date.isoformat(),
            "department": self.department,
            "position": self.position,
            "status": self.status,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "manager_id": self.manager_id
        }


@dataclass
class EmployeeListDto:
    """Data Transfer Object for a list of employees"""
    employees: List[EmployeeDto]
    total: int
    page: int
    page_size: int
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert DTO to dictionary for JSON serialization
        
        Returns:
            Dictionary representation of the DTO
        """
        return {
            "employees": [emp.to_dict() for emp in self.employees],
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size
        }
"""
