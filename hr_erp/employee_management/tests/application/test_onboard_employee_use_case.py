"""
Test for Onboard Employee Use Case

This module demonstrates how to test use cases in isolation
by mocking the dependencies. This follows clean architecture
principles by testing business logic independently from
infrastructure concerns.
"""

import unittest
from unittest.mock import Mock, MagicMock
from datetime import date
from uuid import UUID

from ...application.use_cases.onboard_employee_use_case import (
    OnboardEmployeeUseCase,
    OnboardEmployeeInputDto,
    OnboardEmployeeOutputDto
)
from ...domain.entities.employee import Employee
from ...domain.value_objects.employee_id import EmployeeId


class TestOnboardEmployeeUseCase(unittest.TestCase):
    """
    Test cases for the OnboardEmployee use case
    
    This demonstrates testing application business rules without
    dependencies on actual infrastructure implementations.
    """
    
    def setUp(self):
        """Set up test dependencies with mocks"""
        # Create mock repository and services
        self.employee_repository = Mock()
        self.notification_service = Mock()
        self.document_service = Mock()
        
        # Create use case with mocked dependencies
        self.use_case = OnboardEmployeeUseCase(
            employee_repository=self.employee_repository,
            notification_service=self.notification_service,
            document_service=self.document_service
        )
        
        # Test data
        self.test_employee_id = "EMP-2025-HR001"
        self.test_uuid = UUID("12345678-1234-5678-1234-567812345678")
        
        # Set up mock behavior
        self.employee_repository.exists_by_employee_id.return_value = False
        self.employee_repository.get_next_employee_sequence.return_value = 1
        
        # Mock the add method to return the employee
        def mock_add(employee):
            # Return the employee as is, simulating persistence
            return employee
        self.employee_repository.add.side_effect = mock_add
        
        # Mock notification sending
        self.notification_service.send_onboarding_notification.return_value = True
        
        # Mock document requirements
        self.document_service.create_employee_document_requirements.return_value = [
            {"type": "ID_PROOF", "name": "Identity Proof", "required": True},
            {"type": "ADDRESS_PROOF", "name": "Address Proof", "required": True},
        ]
        
    def test_onboard_employee_successfully(self):
        """Test successful employee onboarding"""
        # Create input DTO
        input_dto = OnboardEmployeeInputDto(
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 15),
            hire_date=date(2025, 5, 1),
            department="HR",
            position="HR Specialist",
            street="123 Main St",
            city="Anytown",
            state="State",
            zip_code="12345",
            country="Country",
            email="john.doe@example.com",
            phone="123-456-7890",
            emergency_contact_name="Jane Doe",
            emergency_contact_phone="098-765-4321"
        )
        
        # Execute use case
        output_dto = self.use_case.execute(input_dto)
        
        # Verify output
        self.assertEqual(output_dto.employee_id, self.test_employee_id)
        self.assertEqual(output_dto.full_name, "John Doe")
        self.assertEqual(output_dto.email, "john.doe@example.com")
        self.assertEqual(output_dto.department, "HR")
        self.assertEqual(output_dto.position, "HR Specialist")
        self.assertEqual(output_dto.documents_pending, 2)
        self.assertTrue(output_dto.notification_sent)
        
        # Verify repository calls
        self.employee_repository.get_next_employee_sequence.assert_called_once()
        self.employee_repository.add.assert_called_once()
        
        # Verify service calls
        self.notification_service.send_onboarding_notification.assert_called_once()
        self.document_service.create_employee_document_requirements.assert_called_once()
        
    def test_onboard_employee_with_manager(self):
        """Test employee onboarding with a manager"""
        # Set up mock for manager validation
        self.employee_repository.exists_by_employee_id.return_value = True
        
        # Create input DTO with manager
        input_dto = OnboardEmployeeInputDto(
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1992, 5, 20),
            hire_date=date(2025, 5, 15),
            department="HR",
            position="HR Assistant",
            manager_employee_id="EMP-2020-HR001",  # Existing manager
            street="456 Oak St",
            city="Othertown",
            state="State",
            zip_code="67890",
            country="Country",
            email="jane.smith@example.com",
            phone="555-123-4567",
            emergency_contact_name="John Smith",
            emergency_contact_phone="555-987-6543"
        )
        
        # Execute use case
        output_dto = self.use_case.execute(input_dto)
        
        # Verify output
        self.assertEqual(output_dto.full_name, "Jane Smith")
        
        # Verify repository calls
        self.employee_repository.exists_by_employee_id.assert_called_once()
        self.employee_repository.add.assert_called_once()
        
    def test_onboard_employee_with_invalid_manager(self):
        """Test employee onboarding with an invalid manager ID"""
        # Set up mock for manager validation - manager doesn't exist
        self.employee_repository.exists_by_employee_id.return_value = False
        
        # Create input DTO with invalid manager
        input_dto = OnboardEmployeeInputDto(
            first_name="Alex",
            last_name="Johnson",
            date_of_birth=date(1988, 8, 10),
            hire_date=date(2025, 6, 1),
            department="HR",
            position="HR Coordinator",
            manager_employee_id="EMP-2020-HR999",  # Non-existent manager
            street="789 Pine St",
            city="Somewhere",
            state="State",
            zip_code="54321",
            country="Country",
            email="alex.johnson@example.com",
            phone="555-888-9999",
            emergency_contact_name="Sam Johnson",
            emergency_contact_phone="555-777-8888"
        )
        
        # Execute use case and expect error
        with self.assertRaises(ValueError):
            self.use_case.execute(input_dto)


if __name__ == "__main__":
    unittest.main()
