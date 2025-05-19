"""
File System Document Storage Service

This module implements document storage using the file system.
"""
import os
import json
import shutil
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, BinaryIO, IO
from ...application.interfaces.document_storage_interface import DocumentStorageInterface

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path



class FileSystemDocumentStorage(DocumentStorageInterface):
    """
    File System Document Storage Service
    
    This service implements document storage using the local file system.
    """
    
    def __init__(self, base_path: str = None):
        """
        Initialize the File System Document Storage
        
        Args:
            base_path: Base path for document storage
        """
        self.base_path = base_path or os.path.join(os.getcwd(), 'document_storage')
        
        # Ensure storage directories exist
        self._ensure_directory_exists(self.base_path)
        self._ensure_directory_exists(os.path.join(self.base_path, 'metadata'))
        self._ensure_directory_exists(os.path.join(self.base_path, 'files'))
    
    def _ensure_directory_exists(self, directory_path: str) -> None:
        """
        Ensure a directory exists, creating it if needed
        
        Args:
            directory_path: Path to check/create
        """
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
    
    def _get_file_path(self, document_id: str) -> str:
        """
        Get the file path for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            File path
        """
        return os.path.join(self.base_path, 'files', document_id)
    
    def _get_metadata_path(self, document_id: str) -> str:
        """
        Get the metadata path for a document
        
        Args:
            document_id: Document identifier
            
        Returns:
            Metadata file path
        """
        return os.path.join(self.base_path, 'metadata', f"{document_id}.json")
    
    def store_document(self, 
                     document_id: str, 
                     document_type: str, 
                     file_data: BinaryIO,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Store a document in the file system
        
        Args:
            document_id: The document identifier
            document_type: Type of document
            file_data: File data as a binary stream
            metadata: Additional metadata about the document
            
        Returns:
            True if storage was successful, False otherwise
        """
        try:
            # Generate document ID if not provided
            if not document_id:
                document_id = str(uuid.uuid4())
            
            # Store file
            file_path = self._get_file_path(document_id)
            with open(file_path, 'wb') as dest_file:
                shutil.copyfileobj(file_data, dest_file)
            
            # Prepare metadata
            metadata = metadata or {}
            metadata.update({
                'document_id': document_id,
                'document_type': document_type,
                'created_at': datetime.now().isoformat(),
                'size_bytes': os.path.getsize(file_path)
            })
            
            # Store metadata
            metadata_path = self._get_metadata_path(document_id)
            with open(metadata_path, 'w') as meta_file:
                json.dump(metadata, meta_file, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error storing document: {str(e)}")
            return False
    
    def retrieve_document(self, document_id: str) -> Optional[BinaryIO]:
        """
        Retrieve a document from storage
        
        Args:
            document_id: The document identifier
            
        Returns:
            Document data as a binary stream, or None if not found
        """
        file_path = self._get_file_path(document_id)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            return open(file_path, 'rb')
        except Exception as e:
            print(f"Error retrieving document: {str(e)}")
            return None
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a document
        
        Args:
            document_id: The document identifier
            
        Returns:
            Document metadata dictionary, or None if not found
        """
        metadata_path = self._get_metadata_path(document_id)
        
        if not os.path.exists(metadata_path):
            return None
        
        try:
            with open(metadata_path, 'r') as meta_file:
                return json.load(meta_file)
        except Exception as e:
            print(f"Error reading document metadata: {str(e)}")
            return None
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from storage
        
        Args:
            document_id: The document identifier
            
        Returns:
            True if deletion was successful, False otherwise
        """
        file_path = self._get_file_path(document_id)
        metadata_path = self._get_metadata_path(document_id)
        
        success = True
        
        # Delete file if it exists
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting document file: {str(e)}")
                success = False
        
        # Delete metadata if it exists
        if os.path.exists(metadata_path):
            try:
                os.remove(metadata_path)
            except Exception as e:
                print(f"Error deleting document metadata: {str(e)}")
                success = False
        
        return success
    
    def get_documents_by_entity(self, entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents associated with an entity
        
        Args:
            entity_type: The type of entity (e.g., "loan", "customer")
            entity_id: The entity identifier
            
        Returns:
            List of document metadata dictionaries
        """
        metadata_dir = os.path.join(self.base_path, 'metadata')
        results = []
        
        # Iterate through all metadata files
        for filename in os.listdir(metadata_dir):
            if not filename.endswith('.json'):
                continue
                
            try:
                metadata_path = os.path.join(metadata_dir, filename)
                with open(metadata_path, 'r') as meta_file:
                    metadata = json.load(meta_file)
                    
                    # Check if this document is associated with the entity
                    if metadata.get('entity_type') == entity_type and metadata.get('entity_id') == entity_id:
                        results.append(metadata)
                        
            except Exception as e:
                print(f"Error reading metadata file {filename}: {str(e)}")
        
        return results
    
    def update_document_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        """
        Update metadata for a document
        
        Args:
            document_id: The document identifier
            metadata: New metadata to update or add
            
        Returns:
            True if update was successful, False otherwise
        """
        metadata_path = self._get_metadata_path(document_id)
        
        if not os.path.exists(metadata_path):
            return False
        
        try:
            # Read existing metadata
            with open(metadata_path, 'r') as meta_file:
                existing_metadata = json.load(meta_file)
            
            # Update with new metadata
            existing_metadata.update(metadata)
            existing_metadata['updated_at'] = datetime.now().isoformat()
            
            # Write back to file
            with open(metadata_path, 'w') as meta_file:
                json.dump(existing_metadata, meta_file, indent=2)
                
            return True
            
        except Exception as e:
            print(f"Error updating document metadata: {str(e)}")
            return False
