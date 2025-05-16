"""
Tests for Customer Management Module Domain Layer

This module contains unit tests for the customer management domain entities and services.
"""

import unittest
from datetime import date, timedelta
from ...domain.entities.customer import Customer, CustomerType, CustomerStatus, RiskCategory, Address, ContactInformation
from ...domain.services.kyc_rules_service import KycRulesService


class TestCustomerEntity(unittest.TestCase):
    """Test cases for the Customer entity"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a valid individual customer for testing
        self.valid_individual = Customer(
            customer_id="CUST123",
            customer_type=CustomerType.INDIVIDUAL,
            status=CustomerStatus.ACTIVE,
            registration_date=date.today(),
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            contact_information=ContactInformation(
                email="john.doe@example.com",
                primary_phone="1234567890"
            ),
            addresses=[
                Address(
                    street="123 Main St",
                    city="New York",
                    state="NY",
                    postal_code="10001",
                    country="US",
                    address_type="residential",
                    is_primary=True
                )
            ]
        )
        
        # Create a valid corporate customer for testing
        self.valid_corporate = Customer(
            customer_id="CORP456",
            customer_type=CustomerType.CORPORATE,
            status=CustomerStatus.ACTIVE,
            registration_date=date.today(),
            company_name="Acme Corp",
            registration_number="REG123456",
            contact_information=ContactInformation(
                email="contact@acmecorp.com",
                primary_phone="9876543210"
            ),
            addresses=[
                Address(
                    street="456 Business Ave",
                    city="Los Angeles",
                    state="CA",
                    postal_code="90001",
                    country="US",
                    address_type="business",
                    is_primary=True
                )
            ]
        )
    
    def test_individual_customer_creation(self):
        """Test creating a valid individual customer"""
        self.assertEqual(self.valid_individual.customer_id, "CUST123")
        self.assertEqual(self.valid_individual.customer_type, CustomerType.INDIVIDUAL)
        self.assertEqual(self.valid_individual.status, CustomerStatus.ACTIVE)
        self.assertEqual(self.valid_individual.first_name, "John")
        self.assertEqual(self.valid_individual.last_name, "Doe")
    
    def test_corporate_customer_creation(self):
        """Test creating a valid corporate customer"""
        self.assertEqual(self.valid_corporate.customer_id, "CORP456")
        self.assertEqual(self.valid_corporate.customer_type, CustomerType.CORPORATE)
        self.assertEqual(self.valid_corporate.company_name, "Acme Corp")
        self.assertEqual(self.valid_corporate.registration_number, "REG123456")
    
    def test_individual_missing_required_fields(self):
        """Test validation of required fields for individual customers"""
        with self.assertRaises(ValueError):
            Customer(
                customer_id="CUST123",
                customer_type=CustomerType.INDIVIDUAL,
                status=CustomerStatus.ACTIVE,
                registration_date=date.today(),
                # Missing first_name
                last_name="Doe",
                date_of_birth=date(1980, 1, 15)
            )
        
        with self.assertRaises(ValueError):
            Customer(
                customer_id="CUST123",
                customer_type=CustomerType.INDIVIDUAL,
                status=CustomerStatus.ACTIVE,
                registration_date=date.today(),
                first_name="John",
                # Missing last_name
                date_of_birth=date(1980, 1, 15)
            )
        
        with self.assertRaises(ValueError):
            Customer(
                customer_id="CUST123",
                customer_type=CustomerType.INDIVIDUAL,
                status=CustomerStatus.ACTIVE,
                registration_date=date.today(),
                first_name="John",
                last_name="Doe",
                # Missing date_of_birth
            )
    
    def test_corporate_missing_required_fields(self):
        """Test validation of required fields for corporate customers"""
        with self.assertRaises(ValueError):
            Customer(
                customer_id="CORP456",
                customer_type=CustomerType.CORPORATE,
                status=CustomerStatus.ACTIVE,
                registration_date=date.today(),
                # Missing company_name
                registration_number="REG123456"
            )
        
        with self.assertRaises(ValueError):
            Customer(
                customer_id="CORP456",
                customer_type=CustomerType.CORPORATE,
                status=CustomerStatus.ACTIVE,
                registration_date=date.today(),
                company_name="Acme Corp",
                # Missing registration_number
            )
    
    def test_customer_status_changes(self):
        """Test customer status change methods"""
        customer = self.valid_individual
        
        # Test deactivate
        customer.deactivate()
        self.assertEqual(customer.status, CustomerStatus.INACTIVE)
        
        # Test activate
        customer.activate()
        self.assertEqual(customer.status, CustomerStatus.ACTIVE)
        
        # Test block
        customer.block()
        self.assertEqual(customer.status, CustomerStatus.BLOCKED)
        
        # Test close
        customer.close()
        self.assertEqual(customer.status, CustomerStatus.CLOSED)
    
    def test_address_management(self):
        """Test adding and managing addresses"""
        customer = self.valid_individual
        
        # Initially one address
        self.assertEqual(len(customer.addresses), 1)
        self.assertTrue(customer.addresses[0].is_primary)
        
        # Add a new primary address of the same type
        new_address = Address(
            street="789 Second St",
            city="Chicago",
            state="IL",
            postal_code="60601",
            country="US",
            address_type="residential",
            is_primary=True
        )
        customer.add_address(new_address)
        
        # Should now have two addresses, with only the new one as primary
        self.assertEqual(len(customer.addresses), 2)
        self.assertFalse(customer.addresses[0].is_primary)
        self.assertTrue(customer.addresses[1].is_primary)
    
    def test_document_management(self):
        """Test adding documents"""
        customer = self.valid_individual
        
        # Initially no documents
        self.assertEqual(len(customer.documents), 0)
        
        # Add a document
        customer.add_document(
            doc_type="passport",
            doc_id="P123456",
            expiry_date=date.today() + timedelta(days=3650)
        )
        
        # Should now have one document
        self.assertEqual(len(customer.documents), 1)
        self.assertEqual(customer.documents[0]["doc_type"], "passport")
        self.assertEqual(customer.documents[0]["doc_id"], "P123456")
    
    def test_is_active(self):
        """Test is_active method"""
        customer = self.valid_individual
        self.assertTrue(customer.is_active())
        
        customer.deactivate()
        self.assertFalse(customer.is_active())
        
        customer.block()
        self.assertFalse(customer.is_active())
    
    def test_is_compliant(self):
        """Test is_compliant method"""
        customer = self.valid_individual
        
        # Initially not compliant
        self.assertFalse(customer.is_compliant())
        
        # Mark as compliant
        customer.mark_kyc_verified()
        customer.mark_aml_cleared()
        
        # Now should be compliant
        self.assertTrue(customer.is_compliant())


class TestKycRulesService(unittest.TestCase):
    """Test cases for the KYC Rules Service"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create KYC rules service
        self.kyc_service = KycRulesService()
        
        # Create a test customer
        self.customer = Customer(
            customer_id="CUST123",
            customer_type=CustomerType.INDIVIDUAL,
            status=CustomerStatus.ACTIVE,
            registration_date=date.today(),
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            risk_category=RiskCategory.MEDIUM
        )
    
    def test_risk_category_determination(self):
        """Test risk category determination"""
        # Low risk case
        risk = self.kyc_service.determine_risk_category(
            self.customer,
            avg_monthly_balance=10000,
            transaction_volume=5000
        )
        self.assertEqual(risk, RiskCategory.LOW)
        
        # Medium risk case
        risk = self.kyc_service.determine_risk_category(
            self.customer,
            avg_monthly_balance=200000,
            transaction_volume=150000
        )
        self.assertEqual(risk, RiskCategory.MEDIUM)
        
        # High risk case
        risk = self.kyc_service.determine_risk_category(
            self.customer,
            avg_monthly_balance=2000000,
            transaction_volume=1500000
        )
        self.assertEqual(risk, RiskCategory.HIGH)
        
        # High risk due to PEP status
        self.customer.pep_status = True
        risk = self.kyc_service.determine_risk_category(
            self.customer,
            avg_monthly_balance=10000,
            transaction_volume=5000
        )
        self.assertEqual(risk, RiskCategory.HIGH)
    
    def test_document_requirements(self):
        """Test document requirements for different customer types"""
        # Test individual requirements
        individual = Customer(
            customer_id="IND123",
            customer_type=CustomerType.INDIVIDUAL,
            status=CustomerStatus.ACTIVE,
            registration_date=date.today(),
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15)
        )
        reqs = self.kyc_service.evaluate_document_requirements(individual)
        self.assertIn("national_id", reqs)
        self.assertIn("proof_of_address", reqs)
        
        # Test corporate requirements
        corporate = Customer(
            customer_id="CORP456",
            customer_type=CustomerType.CORPORATE,
            status=CustomerStatus.ACTIVE,
            registration_date=date.today(),
            company_name="Acme Corp",
            registration_number="REG123456"
        )
        reqs = self.kyc_service.evaluate_document_requirements(corporate)
        self.assertIn("registration_certificate", reqs)
        self.assertIn("tax_registration", reqs)
        self.assertIn("director_id", reqs)
        
        # Test high risk requirements
        high_risk = Customer(
            customer_id="HIGH789",
            customer_type=CustomerType.INDIVIDUAL,
            status=CustomerStatus.ACTIVE,
            registration_date=date.today(),
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1980, 1, 15),
            risk_category=RiskCategory.HIGH
        )
        reqs = self.kyc_service.evaluate_document_requirements(high_risk)
        self.assertIn("source_of_funds", reqs)
    
    def test_document_validity(self):
        """Test document validity calculation"""
        issue_date = date.today()
        
        # Test passport (10 years)
        expiry = self.kyc_service.calculate_document_validity("passport", issue_date)
        expected = issue_date + timedelta(days=3650)
        self.assertEqual(expiry, expected)
        
        # Test proof of address (6 months)
        expiry = self.kyc_service.calculate_document_validity("proof_of_address", issue_date)
        expected = issue_date + timedelta(days=180)
        self.assertEqual(expiry, expected)
        
        # Test default validity
        expiry = self.kyc_service.calculate_document_validity("unknown_doc", issue_date)
        expected = issue_date + timedelta(days=365)
        self.assertEqual(expiry, expected)


if __name__ == "__main__":
    unittest.main()
