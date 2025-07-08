"""
Customer Service Unit and Integration Tests
Comprehensive test suite for customer service functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, date
from decimal import Decimal

from customer_service.domain.entities import (
    Customer, CustomerType, CustomerStatus, Address, ContactInfo, 
    IdentificationDocument, RiskProfile, KYCStatus, AMLStatus
)
from customer_service.application.dto import (
    CreateCustomerRequest, UpdateCustomerRequest, AddressDTO, ContactInfoDTO,
    IdentificationDocumentDTO, CustomerResponse
)
from customer_service.application.use_cases import (
    CreateCustomerUseCase, UpdateCustomerUseCase, GetCustomerUseCase,
    DeleteCustomerUseCase, CustomerRepository, AMLService, KYCService
)
from customer_service.application.services import CustomerApplicationService


# Test Fixtures

@pytest.fixture
def sample_address():
    """Sample address for testing"""
    return Address(
        line1="123 Main Street",
        line2="Apt 4B",
        city="New York",
        state="NY",
        postal_code="10001",
        country="USA"
    )


@pytest.fixture
def sample_contact_info():
    """Sample contact information for testing"""
    return ContactInfo(
        email="john.doe@example.com",
        phone="+1-555-123-4567",
        alternate_phone="+1-555-987-6543"
    )


@pytest.fixture
def sample_identification():
    """Sample identification document for testing"""
    return IdentificationDocument(
        id_type="PASSPORT",
        id_number="P12345678",
        issue_date=date(2020, 1, 15),
        expiry_date=date(2030, 1, 15),
        issuing_authority="US State Department"
    )


@pytest.fixture
def sample_customer(sample_address, sample_contact_info, sample_identification):
    """Sample customer entity for testing"""
    return Customer(
        customer_type=CustomerType.INDIVIDUAL,
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1985, 6, 15),
        gender="MALE",
        nationality="US",
        address=sample_address,
        contact_info=sample_contact_info,
        identification=sample_identification,
        occupation="Software Engineer",
        annual_income=Decimal("75000.00"),
        risk_profile=RiskProfile.MEDIUM,
        created_by="test_user"
    )


@pytest.fixture
def mock_customer_repository():
    """Mock customer repository for testing"""
    repository = Mock(spec=CustomerRepository)
    repository.save = AsyncMock()
    repository.find_by_id = AsyncMock()
    repository.find_by_email = AsyncMock()
    repository.find_by_phone = AsyncMock()
    repository.find_by_id_number = AsyncMock()
    repository.delete = AsyncMock()
    return repository


@pytest.fixture
def mock_aml_service():
    """Mock AML service for testing"""
    service = Mock(spec=AMLService)
    service.screen_customer = AsyncMock()
    return service


@pytest.fixture
def mock_kyc_service():
    """Mock KYC service for testing"""
    service = Mock(spec=KYCService)
    service.verify_customer = AsyncMock()
    return service


# Unit Tests for Domain Entities

class TestCustomerEntity:
    """Test customer domain entity"""
    
    def test_customer_creation(self, sample_customer):
        """Test customer creation with valid data"""
        assert sample_customer.customer_id is not None
        assert sample_customer.customer_number is not None
        assert sample_customer.full_name == "John Doe"
        assert sample_customer.status == CustomerStatus.ACTIVE
        assert sample_customer.kyc_status == KYCStatus.PENDING
        assert sample_customer.aml_status == AMLStatus.CLEAR
    
    def test_customer_validation(self, sample_address, sample_contact_info, sample_identification):
        """Test customer validation"""
        # Test missing required fields
        with pytest.raises(ValueError, match="First name is required"):
            Customer(
                customer_type=CustomerType.INDIVIDUAL,
                first_name="",
                last_name="Doe",
                address=sample_address,
                contact_info=sample_contact_info,
                identification=sample_identification
            )
        
        with pytest.raises(ValueError, match="Last name is required"):
            Customer(
                customer_type=CustomerType.INDIVIDUAL,
                first_name="John",
                last_name="",
                address=sample_address,
                contact_info=sample_contact_info,
                identification=sample_identification
            )
    
    def test_customer_age_calculation(self, sample_customer):
        """Test customer age calculation"""
        age = sample_customer.get_age()
        expected_age = datetime.now().year - 1985
        assert age == expected_age or age == expected_age - 1  # Account for birthday this year
    
    def test_customer_kyc_completion(self, sample_customer):
        """Test KYC completion"""
        # Initially KYC should not be complete
        assert not sample_customer.is_kyc_complete()
        
        # Complete KYC
        sample_customer.complete_kyc("kyc_officer")
        assert sample_customer.is_kyc_complete()
        assert sample_customer.kyc_status == KYCStatus.COMPLETED
        assert sample_customer.kyc_completion_date is not None
    
    def test_customer_risk_assessment(self, sample_customer):
        """Test customer risk assessment"""
        # Test high-income customer
        sample_customer.annual_income = Decimal("200000.00")
        sample_customer.assess_risk()
        assert sample_customer.risk_profile == RiskProfile.HIGH
        
        # Test low-income customer
        sample_customer.annual_income = Decimal("25000.00")
        sample_customer.assess_risk()
        assert sample_customer.risk_profile == RiskProfile.LOW


class TestAddress:
    """Test address value object"""
    
    def test_address_creation(self):
        """Test address creation"""
        address = Address(
            line1="123 Main St",
            city="New York",
            state="NY",
            postal_code="10001",
            country="USA"
        )
        assert address.line1 == "123 Main St"
        assert address.is_valid()
    
    def test_address_validation(self):
        """Test address validation"""
        # Test invalid address
        with pytest.raises(ValueError):
            Address(line1="", city="", state="", postal_code="", country="")
    
    def test_address_formatting(self, sample_address):
        """Test address formatting"""
        formatted = sample_address.format()
        assert "123 Main Street" in formatted
        assert "New York, NY 10001" in formatted
        assert "USA" in formatted


# Unit Tests for Use Cases

class TestCreateCustomerUseCase:
    """Test create customer use case"""
    
    @pytest.mark.asyncio
    async def test_create_customer_success(self, mock_customer_repository, mock_aml_service, mock_kyc_service):
        """Test successful customer creation"""
        # Setup
        use_case = CreateCustomerUseCase(mock_customer_repository, mock_aml_service, mock_kyc_service)
        
        # Mock repository responses
        mock_customer_repository.find_by_email.return_value = None
        mock_customer_repository.find_by_phone.return_value = None
        mock_customer_repository.find_by_id_number.return_value = None
        mock_customer_repository.save.return_value = Mock(customer_id="test-id")
        
        # Create request
        request = CreateCustomerRequest(
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1985, 6, 15),
            email="john.doe@example.com",
            phone="+1-555-123-4567",
            address=AddressDTO(
                line1="123 Main St",
                city="New York",
                state="NY",
                postal_code="10001",
                country="USA"
            ),
            identification=IdentificationDocumentDTO(
                id_type="PASSPORT",
                id_number="P12345678"
            ),
            created_by="test_user"
        )
        
        # Execute
        result = await use_case.execute(request)
        
        # Verify
        assert result is not None
        mock_customer_repository.save.assert_called_once()
        mock_aml_service.screen_customer.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_customer_duplicate_email(self, mock_customer_repository, mock_aml_service, mock_kyc_service):
        """Test customer creation with duplicate email"""
        # Setup
        use_case = CreateCustomerUseCase(mock_customer_repository, mock_aml_service, mock_kyc_service)
        mock_customer_repository.find_by_email.return_value = Mock()  # Existing customer
        
        request = CreateCustomerRequest(
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            created_by="test_user"
        )
        
        # Execute and verify
        with pytest.raises(ValueError, match="Customer with email already exists"):
            await use_case.execute(request)


class TestUpdateCustomerUseCase:
    """Test update customer use case"""
    
    @pytest.mark.asyncio
    async def test_update_customer_success(self, mock_customer_repository, sample_customer):
        """Test successful customer update"""
        # Setup
        use_case = UpdateCustomerUseCase(mock_customer_repository)
        mock_customer_repository.find_by_id.return_value = sample_customer
        mock_customer_repository.save.return_value = sample_customer
        
        # Create update request
        request = UpdateCustomerRequest(
            first_name="Jane",
            occupation="Data Scientist",
            updated_by="test_user"
        )
        
        # Execute
        result = await use_case.execute(sample_customer.customer_id, request)
        
        # Verify
        assert result is not None
        mock_customer_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_customer_not_found(self, mock_customer_repository):
        """Test update customer when customer not found"""
        # Setup
        use_case = UpdateCustomerUseCase(mock_customer_repository)
        mock_customer_repository.find_by_id.return_value = None
        
        request = UpdateCustomerRequest(first_name="Jane", updated_by="test_user")
        
        # Execute and verify
        with pytest.raises(ValueError, match="Customer not found"):
            await use_case.execute("non-existent-id", request)


# Integration Tests

class TestCustomerApplicationService:
    """Test customer application service integration"""
    
    @pytest.mark.asyncio
    async def test_customer_lifecycle(self, mock_customer_repository, mock_aml_service, mock_kyc_service):
        """Test complete customer lifecycle"""
        # Setup
        service = CustomerApplicationService(
            customer_repository=mock_customer_repository,
            aml_service=mock_aml_service,
            kyc_service=mock_kyc_service
        )
        
        # Mock responses
        customer_id = "test-customer-id"
        created_customer = Mock()
        created_customer.customer_id = customer_id
        
        mock_customer_repository.find_by_email.return_value = None
        mock_customer_repository.find_by_phone.return_value = None
        mock_customer_repository.find_by_id_number.return_value = None
        mock_customer_repository.save.return_value = created_customer
        mock_customer_repository.find_by_id.return_value = created_customer
        mock_customer_repository.delete.return_value = True
        
        # 1. Create customer
        create_request = CreateCustomerRequest(
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="+1-555-123-4567",
            created_by="test_user"
        )
        
        customer_response = await service.create_customer(create_request)
        assert customer_response is not None
        
        # 2. Get customer
        retrieved_customer = await service.get_customer(customer_id)
        assert retrieved_customer is not None
        
        # 3. Update customer
        update_request = UpdateCustomerRequest(
            first_name="Jane",
            updated_by="test_user"
        )
        
        updated_customer = await service.update_customer(customer_id, update_request)
        assert updated_customer is not None
        
        # 4. Delete customer
        deleted = await service.delete_customer(customer_id)
        assert deleted is True


# Performance Tests

class TestCustomerServicePerformance:
    """Test customer service performance"""
    
    @pytest.mark.asyncio
    async def test_bulk_customer_creation_performance(self, mock_customer_repository, mock_aml_service, mock_kyc_service):
        """Test performance of bulk customer creation"""
        import time
        
        # Setup
        service = CustomerApplicationService(
            customer_repository=mock_customer_repository,
            aml_service=mock_aml_service,
            kyc_service=mock_kyc_service
        )
        
        # Mock responses for bulk creation
        mock_customer_repository.find_by_email.return_value = None
        mock_customer_repository.find_by_phone.return_value = None
        mock_customer_repository.find_by_id_number.return_value = None
        mock_customer_repository.save.return_value = Mock(customer_id="test-id")
        
        # Create multiple customers
        start_time = time.time()
        
        tasks = []
        for i in range(100):  # Create 100 customers
            request = CreateCustomerRequest(
                customer_type=CustomerType.INDIVIDUAL,
                first_name=f"Customer{i}",
                last_name="Test",
                email=f"customer{i}@test.com",
                phone=f"+1-555-000-{i:04d}",
                created_by="performance_test"
            )
            tasks.append(service.create_customer(request))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Verify results
        assert len(results) == 100
        assert execution_time < 10.0  # Should complete within 10 seconds
        print(f"Created 100 customers in {execution_time:.2f} seconds")


# Error Handling Tests

class TestCustomerServiceErrorHandling:
    """Test error handling in customer service"""
    
    @pytest.mark.asyncio
    async def test_database_connection_error(self, mock_aml_service, mock_kyc_service):
        """Test handling of database connection errors"""
        # Setup repository that raises connection error
        mock_repository = Mock(spec=CustomerRepository)
        mock_repository.save.side_effect = Exception("Database connection failed")
        
        service = CustomerApplicationService(
            customer_repository=mock_repository,
            aml_service=mock_aml_service,
            kyc_service=mock_kyc_service
        )
        
        request = CreateCustomerRequest(
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            created_by="test_user"
        )
        
        # Should handle the error gracefully
        with pytest.raises(Exception, match="Database connection failed"):
            await service.create_customer(request)
    
    @pytest.mark.asyncio
    async def test_aml_service_timeout(self, mock_customer_repository, mock_kyc_service):
        """Test handling of AML service timeout"""
        # Setup AML service that times out
        mock_aml_service = Mock(spec=AMLService)
        mock_aml_service.screen_customer.side_effect = asyncio.TimeoutError("AML service timeout")
        
        mock_customer_repository.find_by_email.return_value = None
        mock_customer_repository.find_by_phone.return_value = None
        mock_customer_repository.find_by_id_number.return_value = None
        
        use_case = CreateCustomerUseCase(mock_customer_repository, mock_aml_service, mock_kyc_service)
        
        request = CreateCustomerRequest(
            customer_type=CustomerType.INDIVIDUAL,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            created_by="test_user"
        )
        
        # Should handle timeout gracefully
        with pytest.raises(asyncio.TimeoutError):
            await use_case.execute(request)


# Test Configuration

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
