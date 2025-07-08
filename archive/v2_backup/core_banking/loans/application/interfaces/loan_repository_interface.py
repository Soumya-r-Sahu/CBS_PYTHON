"""
Loan Repository Interface

This module defines the interface for loan data repositories.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
from datetime import date

from ...domain.entities.loan import Loan, LoanStatus, LoanType

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class LoanRepositoryInterface(ABC):
    """
    Interface for loan data repository implementations.
    
    This interface defines the contract that any loan repository
    implementation must fulfill, ensuring separation between the
    application and infrastructure layers.
    """
    
    @abstractmethod
    def create(self, loan: Loan) -> Loan:
        """
        Create a new loan record.
        
        Args:
            loan: The loan entity to store
            
        Returns:
            The stored loan entity with any system-generated values
        """
        pass
    
    @abstractmethod
    def get_by_id(self, loan_id: str) -> Optional[Loan]:
        """
        Get a loan by its ID.
        
        Args:
            loan_id: The loan ID
            
        Returns:
            The loan entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update(self, loan: Loan) -> Loan:
        """
        Update an existing loan record.
        
        Args:
            loan: The loan entity to update
            
        Returns:
            The updated loan entity
        """
        pass
    
    @abstractmethod
    def get_by_customer_id(self, customer_id: str) -> List[Loan]:
        """
        Get all loans for a customer.
        
        Args:
            customer_id: The customer ID
            
        Returns:
            List of loan entities for the customer
        """
        pass
    
    @abstractmethod
    def get_by_status(self, status: LoanStatus) -> List[Loan]:
        """
        Get loans by status.
        
        Args:
            status: The loan status
            
        Returns:
            List of loan entities with the specified status
        """
        pass
    
    @abstractmethod
    def search(self, 
              customer_id: Optional[str] = None,
              loan_type: Optional[LoanType] = None,
              min_amount: Optional[Decimal] = None,
              max_amount: Optional[Decimal] = None,
              status: Optional[LoanStatus] = None,
              application_date_from: Optional[date] = None,
              application_date_to: Optional[date] = None) -> List[Loan]:
        """
        Search loans based on criteria.
        
        Args:
            customer_id: Optional customer ID filter
            loan_type: Optional loan type filter
            min_amount: Optional minimum amount filter
            max_amount: Optional maximum amount filter
            status: Optional status filter
            application_date_from: Optional application date from filter
            application_date_to: Optional application date to filter
            
        Returns:
            List of loan entities matching the criteria
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get loan statistics.
        
        Returns:
            Dictionary containing statistics about loans
        """
        pass
    
    @abstractmethod
    def get_overdue_loans(self) -> List[Loan]:
        """
        Get overdue loans.
        
        Returns:
            List of loan entities that are overdue
        """
        pass
