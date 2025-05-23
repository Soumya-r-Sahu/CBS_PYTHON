"""
Document Service Interface

This module defines the interface for document management services
that can be used by application use cases.
"""

from abc import ABC, abstractmethod
from typing import List, Dict
from uuid import UUID


class DocumentService(ABC):
    """
    Interface for document management operations.
    
    This abstract class defines the contract that any document service
    implementation must follow to be used by application use cases.
    """
    
    @abstractmethod
    def create_employee_document_requirements(self, employee_id: UUID) -> List[Dict]:
        """
        Create document requirements for a new employee
        
        Args:
            employee_id: The unique identifier of the employee
            
        Returns:
            List of document requirements with type and deadline
        """
        pass
    
    @abstractmethod
    def upload_document(self, employee_id: UUID, document_type: str, file_data: bytes) -> str:
        """
        Upload a document for an employee
        
        Args:
            employee_id: The unique identifier of the employee
            document_type: The type of document being uploaded
            file_data: The binary content of the document
            
        Returns:
            Document ID of the uploaded document
        """
        pass
    
    @abstractmethod
    def get_employee_documents(self, employee_id: UUID) -> List[Dict]:
        """
        Get all documents for an employee
        
        Args:
            employee_id: The unique identifier of the employee
            
        Returns:
            List of documents with metadata
        """
        pass
