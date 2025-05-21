"""
Employee Management Presentation Package

This package contains presentation layer components for the
employee management module in the HR-ERP system, including
API controllers, CLI interfaces, and DTOs.
"""

from .api.employee_controller import EmployeeApiController
from .cli.employee_processor import EmployeeCliProcessor
from .dto.employee_dto import EmployeeDto, EmployeeListDto

__all__ = [
    'EmployeeApiController',
    'EmployeeCliProcessor',
    'EmployeeDto',
    'EmployeeListDto'
]