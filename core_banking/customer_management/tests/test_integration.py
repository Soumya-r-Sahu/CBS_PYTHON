"""
Integration Tests for Customer Management Module

Tests that verify the integration between layers of the Customer Management module.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta

# Add parent directories to path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
core_banking_dir = os.path.dirname(os.path.dirname(current_dir))
project_root = os.path.dirname(core_banking_dir)
sys.path.append(project_root)

from core_banking.customer_management.di_container import get_create_customer_use_case, get_verify_customer_kyc_use_case
from core_banking.customer_management.application.use_cases.create_customer import CreateCustomerRequest
from core_banking.customer_management.application.use_cases.verify_customer_kyc import VerifyCustomerKycRequest
from core_banking.customer_management.domain.entities.customer import CustomerType


class TestCustomerManagementIntegration(unittest.TestCase):
    """Integration tests for the Customer Management module"""
    
    def setUp(self):
        """Set up for tests"""
        self.create_customer_use_case = get_create_customer_use_case()
        self.verify_customer_kyc_use_case = get_verify_customer_kyc_use_case()
        
        # Default individual customer data
        self.individual_customer_data = {
            'customer_type': CustomerType.INDIVIDUAL.value,
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': '1990-01-01',
            'email': 'john.doe@example.com',
            'primary_phone': '+1234567890',
            'addresses': [
                {
                    'type': 'HOME',
                    'line1': '123 Main St',
                    'city': 'Anytown',
                    'state': 'ST',
                    'postal_code': '12345',
                    'country': 'US'
                }
            ],
            'documents': [
                {
                    'type': 'PASSPORT',
                    'number': 'AB123456',
                    'issuing_country': 'US',
                    'issue_date': '2020-01-01',
                    'expiry_date': (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
                }
            ]
        }
        
        # Default corporate customer data
        self.corporate_customer_data = {
            'customer_type': CustomerType.CORPORATE.value,
            'company_name': 'ACME Corp',
            'registration_number': 'REG12345',
            'tax_id': 'TAX12345',
            'email': 'contact@acme.example.com',
            'primary_phone': '+1987654321',
            'addresses': [
                {
                    'type': 'BUSINESS',
                    'line1': '456 Corporate Ave',
                    'city': 'Business City',
                    'state': 'ST',
                    'postal_code': '54321',
                    'country': 'US'
                }
            ],
            'documents': [
                {
                    'type': 'REGISTRATION_CERTIFICATE',
                    'number': 'CERT12345',
                    'issuing_country': 'US',
                    'issue_date': '2015-01-01',
                    'expiry_date': (datetime.now() + timedelta(days=730)).strftime('%Y-%m-%d')
                }
            ]
        }
    
    def test_create_individual_customer(self):
        """Test creating an individual customer"""
        request = CreateCustomerRequest(**self.individual_customer_data)
        response = self.create_customer_use_case.execute(request)
        
        self.assertTrue(response.success)
        self.assertIsNotNone(response.customer_id)
        self.assertEqual(response.message, "Customer created successfully")
        self.assertIsNone(response.error_code)
        self.assertEqual(response.validation_errors, {})
        
        return response.customer_id
    
    def test_create_corporate_customer(self):
        """Test creating a corporate customer"""
        request = CreateCustomerRequest(**self.corporate_customer_data)
        response = self.create_customer_use_case.execute(request)
        
        self.assertTrue(response.success)
        self.assertIsNotNone(response.customer_id)
        self.assertEqual(response.message, "Customer created successfully")
        self.assertIsNone(response.error_code)
        self.assertEqual(response.validation_errors, {})
        
        return response.customer_id
    
    def test_create_customer_with_invalid_data(self):
        """Test creating a customer with invalid data"""
        # Missing required fields
        invalid_data = {
            'customer_type': CustomerType.INDIVIDUAL.value,
            # Missing first_name and last_name
            'date_of_birth': '1990-01-01'
        }
        
        request = CreateCustomerRequest(**invalid_data)
        response = self.create_customer_use_case.execute(request)
        
        self.assertFalse(response.success)
        self.assertIsNone(response.customer_id)
        self.assertIsNotNone(response.error_code)
        self.assertGreater(len(response.validation_errors), 0)
    
    def test_verify_customer_kyc(self):
        """Test verifying customer KYC"""
        # First create a customer
        customer_id = self.test_create_individual_customer()
        
        # Now verify KYC
        request = VerifyCustomerKycRequest(
            customer_id=customer_id,
            verify_kyc=True,
            verify_aml=True,
            documents_verified=[
                {
                    'type': 'PASSPORT',
                    'number': 'AB123456',
                    'verified': True
                }
            ],
            notes="Verified all documents in person"
        )
        
        response = self.verify_customer_kyc_use_case.execute(request)
        
        self.assertTrue(response.success)
        self.assertTrue(response.is_fully_compliant)
        self.assertEqual(len(response.missing_documents), 0)
        self.assertEqual(len(response.expired_documents), 0)
    
    def test_verification_requirements(self):
        """Test getting verification requirements"""
        # First create a customer
        customer_id = self.test_create_corporate_customer()
        
        # Get verification requirements
        requirements = self.verify_customer_kyc_use_case.get_verification_requirements(customer_id)
        
        self.assertTrue(isinstance(requirements, dict))
        self.assertIn('required_documents', requirements)
        self.assertIn('current_documents', requirements)
        self.assertIn('missing_documents', requirements)
        self.assertIn('expired_documents', requirements)


if __name__ == '__main__':
    unittest.main()
