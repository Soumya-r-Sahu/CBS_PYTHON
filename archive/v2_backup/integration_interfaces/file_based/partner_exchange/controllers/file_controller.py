"""
Partner File Controllers - Core Banking System

This module provides controller interfaces for partner file exchanges.
"""
from typing import List, Dict, Any, Optional
import logging

from ..services.file_service import partner_file_service
from ..models.file_models import PartnerFileEntry, PartnerFile


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
# Configure logger
logger = logging.getLogger(__name__)


class PartnerFileController:
    """Controller for partner file exchange operations"""
    
    @staticmethod
    def process_incoming_file(filename: str, file_format: str = "csv") -> Dict[str, Any]:
        """Process an incoming partner file
        
        Args:
            filename: Name of the file to process
            file_format: Format of the file (csv, json, etc.)
            
        Returns:
            Dictionary with processing results
        """
        logger.info(f"Processing incoming file: {filename}")
        try:
            # Read and parse the file
            partner_file = partner_file_service.read_partner_file(filename, file_format)
            
            # Process the entries (in a real system, this might update the database, etc.)
            processed_count = len(partner_file.entries)
            
            # Archive the file after successful processing
            partner_file_service.archive_file(filename)
            
            return {
                "status": "success",
                "filename": filename,
                "partner_id": partner_file.partner_id,
                "processed_entries": processed_count,
                "message": f"Successfully processed {processed_count} entries from {filename}"
            }
            
        except Exception as e:
            logger.error(f"Failed to process file {filename}: {str(e)}")
            return {
                "status": "error",
                "filename": filename,
                "error": str(e),
                "message": f"Failed to process file: {str(e)}"
            }
    
    @staticmethod
    def generate_partner_file(partner_id: str, 
                            entries: List[Dict[str, Any]], 
                            file_type: str = "settlement",
                            file_format: str = "csv") -> Dict[str, Any]:
        """Generate a new partner file
        
        Args:
            partner_id: Identifier for the partner
            entries: List of entry data to include
            file_type: Type of file (settlement, reconciliation, etc.)
            file_format: Format of output file (csv, json, etc.)
            
        Returns:
            Dictionary with generation results
        """
        logger.info(f"Generating {file_type} file for partner {partner_id}")
        
        try:
            # Convert raw entry dictionaries to PartnerFileEntry objects
            file_entries = []
            for entry in entries:
                file_entries.append(
                    PartnerFileEntry(
                        transaction_id=entry.get("transaction_id", ""),
                        partner_id=partner_id,
                        amount=float(entry.get("amount", 0)),
                        status=entry.get("status", "PENDING"),
                        timestamp=entry.get("timestamp", "")
                    )
                )
            
            # Create the file
            filename = partner_file_service.create_partner_file(
                partner_id=partner_id,
                entries=file_entries,
                file_type=file_type,
                file_format=file_format
            )
            
            return {
                "status": "success",
                "filename": filename,
                "partner_id": partner_id,
                "entry_count": len(entries),
                "file_type": file_type,
                "message": f"Successfully generated {file_type} file: {filename}"
            }
            
        except Exception as e:
            logger.error(f"Failed to generate partner file: {str(e)}")
            return {
                "status": "error",
                "partner_id": partner_id,
                "error": str(e),
                "message": f"Failed to generate partner file: {str(e)}"
            }
