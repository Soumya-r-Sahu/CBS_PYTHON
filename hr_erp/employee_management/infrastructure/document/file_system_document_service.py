"""
File System Document Service

This module implements the document service interface using
the file system for storing and retrieving employee documents.
"""

import os
import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path

from ...application.interfaces.document_service import DocumentService
from ....config import DOCUMENT_SETTINGS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileSystemDocumentService(DocumentService):
    """
    Implementation of DocumentService using the file system.
    
    This class handles the infrastructure concerns of storing and retrieving
    documents from the file system.
    """
    
    def __init__(self):
        """Initialize the file system document service"""
        self.base_path = DOCUMENT_SETTINGS.get("storage_path", "/tmp/hr_documents")
        self._ensure_storage_path_exists()
    
    def create_employee_document_requirements(self, employee_id: UUID) -> List[Dict]:
        """
        Create document requirements for a new employee
        
        Args:
            employee_id: The unique identifier of the employee
            
        Returns:
            List of document requirements with type and deadline
        """
        try:
            # Create standard document requirements - in a real system this might be
            # configurable or based on employee type, position, etc.
            today = datetime.now()
            
            requirements = [
                {
                    "type": "ID_PROOF",
                    "name": "Identity Proof",
                    "required": True,
                    "deadline": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
                    "status": "PENDING"
                },
                {
                    "type": "ADDRESS_PROOF",
                    "name": "Address Proof",
                    "required": True,
                    "deadline": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
                    "status": "PENDING"
                },
                {
                    "type": "QUALIFICATION",
                    "name": "Educational Certificates",
                    "required": True,
                    "deadline": (today + timedelta(days=14)).strftime("%Y-%m-%d"),
                    "status": "PENDING"
                },
                {
                    "type": "EXPERIENCE",
                    "name": "Experience Certificates",
                    "required": True,
                    "deadline": (today + timedelta(days=14)).strftime("%Y-%m-%d"),
                    "status": "PENDING"
                },
                {
                    "type": "BANK_DETAILS",
                    "name": "Bank Account Details",
                    "required": True,
                    "deadline": (today + timedelta(days=7)).strftime("%Y-%m-%d"),
                    "status": "PENDING"
                }
            ]
            
            # Store requirements in employee metadata
            self._save_requirements(employee_id, requirements)
            
            return requirements
            
        except Exception as e:
            logger.error(f"Failed to create document requirements: {str(e)}")
            return []
    
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
        try:
            document_id = str(uuid.uuid4())
            employee_folder = self._get_employee_folder(employee_id)
            
            # Save document metadata
            metadata = {
                "id": document_id,
                "type": document_type,
                "uploaded_at": datetime.now().isoformat(),
                "filename": f"{document_type}_{document_id}.pdf"
            }
            
            metadata_path = os.path.join(employee_folder, f"{document_id}.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            # Save document content
            file_path = os.path.join(employee_folder, f"{document_id}.pdf")
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Update requirements status
            self._update_requirement_status(employee_id, document_type, "SUBMITTED")
            
            logger.info(f"Document uploaded for {employee_id}: {document_type}")
            return document_id
            
        except Exception as e:
            logger.error(f"Failed to upload document: {str(e)}")
            raise
    
    def get_employee_documents(self, employee_id: UUID) -> List[Dict]:
        """
        Get all documents for an employee
        
        Args:
            employee_id: The unique identifier of the employee
            
        Returns:
            List of documents with metadata
        """
        try:
            employee_folder = self._get_employee_folder(employee_id)
            documents = []
            
            # Find all JSON metadata files
            if os.path.exists(employee_folder):
                for filename in os.listdir(employee_folder):
                    if filename.endswith(".json") and not filename == "requirements.json":
                        with open(os.path.join(employee_folder, filename), 'r') as f:
                            metadata = json.load(f)
                            documents.append(metadata)
            
            return documents
            
        except Exception as e:
            logger.error(f"Failed to get employee documents: {str(e)}")
            return []
    
    def _ensure_storage_path_exists(self):
        """Ensure the document storage path exists"""
        try:
            Path(self.base_path).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create document storage path: {str(e)}")
            # In a real system, this would be a critical error
            raise
    
    def _get_employee_folder(self, employee_id: UUID) -> str:
        """
        Get the document folder path for an employee
        
        Args:
            employee_id: The unique identifier of the employee
            
        Returns:
            Path to the employee's document folder
        """
        folder_path = os.path.join(self.base_path, str(employee_id))
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        return folder_path
    
    def _save_requirements(self, employee_id: UUID, requirements: List[Dict]):
        """
        Save document requirements for an employee
        
        Args:
            employee_id: The unique identifier of the employee
            requirements: List of document requirements
        """
        employee_folder = self._get_employee_folder(employee_id)
        requirements_path = os.path.join(employee_folder, "requirements.json")
        
        with open(requirements_path, 'w') as f:
            json.dump(requirements, f)
    
    def _update_requirement_status(self, employee_id: UUID, document_type: str, status: str):
        """
        Update the status of a document requirement
        
        Args:
            employee_id: The unique identifier of the employee
            document_type: The type of document
            status: The new status
        """
        employee_folder = self._get_employee_folder(employee_id)
        requirements_path = os.path.join(employee_folder, "requirements.json")
        
        if os.path.exists(requirements_path):
            with open(requirements_path, 'r') as f:
                requirements = json.load(f)
            
            for req in requirements:
                if req["type"] == document_type:
                    req["status"] = status
            
            with open(requirements_path, 'w') as f:
                json.dump(requirements, f)
