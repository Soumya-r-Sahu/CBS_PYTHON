"""
Employee Repository Interface

This module defines the interface for employee repository operations
in the HR-ERP system.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..entities.employee import Employee
from ..value_objects.employee_id import EmployeeId


class EmployeeRepository(ABC):
    """
    Interface for employee data access operations
    
    This abstract class defines the contract that any employee
    repository implementation must follow.
    """
    
    @abstractmethod
    def get_by_id(self, employee_id: UUID) -> Optional[Employee]:
        """
        Retrieve an employee by their internal UUID
        
        Args:
            employee_id: The UUID of the employee
            
        Returns:
            The employee if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_employee_id(self, employee_id: EmployeeId) -> Optional[Employee]:
        """
        Retrieve an employee by their employee ID (EMP-YYYY-NNNN)
        
        Args:
            employee_id: The employee ID value object
            
        Returns:
            The employee if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_all(self) -> List[Employee]:
        """
        Retrieve all employees
        
        Returns:
            List of all employees
        """
        pass
    
    @abstractmethod
    def save(self, employee: Employee) -> Employee:
        """
        Save an employee (create or update)
        
        Args:
            employee: The employee to save
            
        Returns:
            The saved employee with any updates (e.g., ID)
        """
        pass
    
    @abstractmethod
    def delete(self, employee_id: UUID) -> bool:
        """
        Delete an employee by UUID
        
        Args:
            employee_id: The UUID of the employee to delete
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Employee]:
        """
        Find employees matching specific criteria
        
        Args:
            criteria: Dict of field names and values to filter by
            
        Returns:
            List of matching employees
        """
        pass
    
    @abstractmethod
    def get_by_department(self, department: str) -> List[Employee]:
        """
        Retrieve employees by department
        
        Args:
            department: Department name
            
        Returns:
            List of employees in the department
        """
        pass
    
    @abstractmethod
    def get_by_manager(self, manager_id: EmployeeId) -> List[Employee]:
        """
        Retrieve employees reporting to a specific manager
        
        Args:
            manager_id: The employee ID of the manager
            
        Returns:
            List of employees under the manager
        """
        pass
    
    @abstractmethod
    def get_next_employee_number(self, year: int) -> int:
        """
        Get the next available sequential number for an employee ID
        
        Args:
            year: The year part of the employee ID
            
        Returns:
            The next available number (1-9999)
        """
        pass
