"""
Customer Repository Interface

This module defines the interface for customer data repositories.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ...domain.entities.customer import Customer, CustomerStatus

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class CustomerRepositoryInterface(ABC):
    """
    Interface for customer data repository implementations.
    
    This interface defines the contract that any customer repository
    implementation must fulfill, ensuring separation between the
    application and infrastructure layers.
    """
    
    @abstractmethod
    def create(self, customer: Customer) -> Customer:
        """
        Create a new customer record.
        
        Args:
            customer: The customer entity to store
            
        Returns:
            The stored customer entity with any system-generated values
        """
        pass
    
    @abstractmethod
    def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """
        Retrieve a customer by their ID.
        
        Args:
            customer_id: The unique identifier of the customer
            
        Returns:
            The customer entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update(self, customer: Customer) -> Customer:
        """
        Update an existing customer record.
        
        Args:
            customer: The customer entity with updated information
            
        Returns:
            The updated customer entity
        """
        pass
    
    @abstractmethod
    def delete(self, customer_id: str) -> bool:
        """
        Delete a customer record.
        
        Args:
            customer_id: The unique identifier of the customer
            
        Returns:
            True if the customer was successfully deleted, False otherwise
        """
        pass
    
    @abstractmethod
    def search(self, query: Dict[str, Any], limit: int = 100, offset: int = 0) -> List[Customer]:
        """
        Search for customers based on query parameters.
        
        Args:
            query: A dictionary of search parameters
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            A list of customer entities matching the search criteria
        """
        pass
    
    @abstractmethod
    def find_by_status(self, status: CustomerStatus) -> List[Customer]:
        """
        Find customers by their status.
        
        Args:
            status: The customer status to filter by
            
        Returns:
            A list of customers with the specified status
        """
        pass
    
    @abstractmethod
    def find_by_document(self, document_type: str, document_id: str) -> Optional[Customer]:
        """
        Find a customer by a specific document.
        
        Args:
            document_type: The type of the document (e.g., passport, national_id)
            document_id: The ID or reference number of the document
            
        Returns:
            The customer entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def count_by_criteria(self, criteria: Dict[str, Any]) -> int:
        """
        Count customers matching certain criteria.
        
        Args:
            criteria: A dictionary of criteria to count by
            
        Returns:
            The number of customers matching the criteria
        """
        pass
