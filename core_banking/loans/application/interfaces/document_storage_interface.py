"""
Document Storage Interface

This module defines the interface for document storage services.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, BinaryIO

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class DocumentStorageInterface(ABC):
    """
    Interface for document storage service implementations.
    
    This interface defines the contract that any document storage service
    implementation must fulfill, ensuring separation between the
    application and infrastructure layers.
    """
    
    @abstractmethod
    def store_document(self, 
                     document_id: str, 
                     document_type: str, 
                     file_data: BinaryIO,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store a document in the storage system.
        
        Args:
            document_id: The document identifier
            document_type: Type of document
            file_data: File data as a binary stream
            metadata: Additional metadata about the document
            
        Returns:
            True if storage was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def retrieve_document(self, document_id: str) -> Optional[BinaryIO]:
        """
        Retrieve a document from storage.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Document data as a binary stream, or None if not found
        """
        pass
    
    @abstractmethod
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a document.
        
        Args:
            document_id: The document identifier
            
        Returns:
            Document metadata dictionary, or None if not found
        """
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from storage.
        
        Args:
            document_id: The document identifier
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_documents_by_entity(self, entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents associated with an entity.
        
        Args:
            entity_type: The type of entity (e.g., "loan", "customer")
            entity_id: The entity identifier
            
        Returns:
            List of document metadata dictionaries
        """
        pass
    
    @abstractmethod
    def update_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a document.
        
        Args:
            document_id: The document identifier
            metadata: New metadata to update or add
            
        Returns:
            True if update was successful, False otherwise
        """
        pass
