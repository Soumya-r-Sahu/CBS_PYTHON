"""
Employee Entity

This module defines the Employee entity which represents the core domain concept
of an employee within the HR-ERP system.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Optional
from uuid import UUID, uuid4

from ..value_objects.employee_id import EmployeeId
from ..value_objects.address import Address
from ..value_objects.contact_info import ContactInfo


@dataclass
class Employee:
    """
    Employee entity representing a staff member in the organization
    
    This is a core domain entity that contains business logic related to employees.
    It enforces business rules and invariants for employee data.
    """
    first_name: str
    last_name: str
    date_of_birth: date
    hire_date: date
    employee_id: EmployeeId
    address: Address
    contact_info: ContactInfo
    department: str
    position: str
    status: str
    manager_id: Optional[EmployeeId] = None
    id: UUID = field(default_factory=uuid4)
    documents: Dict[str, str] = field(default_factory=dict)
    skills: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate the employee object after initialization"""
        self._validate()
    
    def _validate(self) -> None:
        """Validate business rules for employees"""
        if not self.first_name or not self.last_name:
            raise ValueError("Employee must have a first and last name")
        
        if self.date_of_birth >= date.today():
            raise ValueError("Date of birth must be in the past")
        
        if self.hire_date > date.today():
            raise ValueError("Hire date cannot be in the future")
        
        # Check age is at least 18
        today = date.today()
        age = today.year - self.date_of_birth.year
        if age < 18 or (age == 18 and (today.month, today.day) < 
                       (self.date_of_birth.month, self.date_of_birth.day)):
            raise ValueError("Employee must be at least 18 years old")
        
        if self.status not in ["Active", "On Leave", "Suspended", "Terminated", "Retired"]:
            raise ValueError(f"Invalid employee status: {self.status}")
    
    def full_name(self) -> str:
        """Get the employee's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def is_active(self) -> bool:
        """Check if the employee is currently active"""
        return self.status == "Active"
    
    def change_status(self, new_status: str) -> None:
        """
        Change employee status
        
        Args:
            new_status: The new status to set
            
        Raises:
            ValueError: If the status transition is not allowed
        """
        valid_statuses = ["Active", "On Leave", "Suspended", "Terminated", "Retired"]
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status: {new_status}")
        
        # Some status transitions may have business rules
        if self.status == "Terminated" and new_status != "Terminated":
            raise ValueError("Cannot change status once terminated")
        
        if self.status == "Retired" and new_status != "Retired":
            raise ValueError("Cannot change status once retired")
        
        self.status = new_status
    
    def add_certification(self, certification: str) -> None:
        """Add a certification to the employee's profile"""
        if certification not in self.certifications:
            self.certifications.append(certification)
    
    def remove_certification(self, certification: str) -> None:
        """Remove a certification from the employee's profile"""
        if certification in self.certifications:
            self.certifications.remove(certification)
    
    def add_skill(self, skill: str) -> None:
        """Add a skill to the employee's profile"""
        if skill not in self.skills:
            self.skills.append(skill)
    
    def remove_skill(self, skill: str) -> None:
        """Remove a skill from the employee's profile"""
        if skill in self.skills:
            self.skills.remove(skill)
    
    def add_document(self, doc_type: str, doc_path: str) -> None:
        """
        Add a document to the employee's profile
        
        Args:
            doc_type: Type of document (e.g., 'passport', 'resume')
            doc_path: Path to the stored document
        """
        self.documents[doc_type] = doc_path
    
    def assign_manager(self, manager_id: EmployeeId) -> None:
        """Assign a manager to this employee"""
        if manager_id == self.employee_id:
            raise ValueError("An employee cannot be their own manager")
        self.manager_id = manager_id
    
    def years_of_service(self) -> int:
        """Calculate the employee's years of service"""
        today = date.today()
        years = today.year - self.hire_date.year
        
        # Adjust for hire date that hasn't occurred this year yet
        if (today.month, today.day) < (self.hire_date.month, self.hire_date.day):
            years -= 1
            
        return max(0, years)
