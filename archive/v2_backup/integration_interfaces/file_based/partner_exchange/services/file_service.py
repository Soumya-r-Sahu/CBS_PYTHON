"""
Partner File Services - Core Banking System

This module provides file processing services for partner exchanges.
"""
import csv
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Union

from ..config.file_config import partner_file_config
from ..models.file_models import PartnerFileEntry, PartnerFile
import logging

# Configure logger
logger = logging.getLogger(__name__)


class PartnerFileService:
    """Handles processing and generation of partner exchange files"""
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one service instance exists"""
        if cls._instance is None:
            cls._instance = super(PartnerFileService, cls).__new__(cls)
            cls._instance._setup()
        return cls._instance
    
    def _setup(self):
        """Set up service with configuration"""
        self.config = partner_file_config
        self.base_dir = self.config.get("base_directory")
        self.incoming_dir = self.config.get_path("incoming")
        self.outgoing_dir = self.config.get_path("outgoing")
        self.archive_dir = self.config.get_path("archive")
        self.error_dir = self.config.get_path("error")
    
    def read_partner_file(self, filename: str, file_format: str = "csv") -> PartnerFile:
        """Read and parse a partner file
        
        Args:
            filename: Name of the file to read
            file_format: Format of the file (csv, json, etc.)
            
        Returns:
            PartnerFile object containing the parsed data
        """
        file_path = os.path.join(self.incoming_dir, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Partner file not found: {file_path}")
        
        logger.info(f"Reading partner file: {filename}")
        entries = []
        
        try:
            if file_format.lower() == "csv":
                entries = self._read_csv_file(file_path)
            elif file_format.lower() == "json":
                entries = self._read_json_file(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
                
            # Parse partner ID and file type from filename
            parts = filename.split('_')
            partner_id = parts[0] if len(parts) > 0 else "unknown"
            file_type = parts[2].split('.')[0] if len(parts) > 2 else "unknown"
            
            return PartnerFile(
                filename=filename,
                partner_id=partner_id,
                file_type=file_type,
                created_at=datetime.now(),
                entries=entries
            )
            
        except Exception as e:
            logger.error(f"Error reading partner file {filename}: {str(e)}")
            self._move_to_error(filename)
            raise
    
    def _read_csv_file(self, file_path: str) -> List[PartnerFileEntry]:
        """Read entries from CSV file"""
        entries = []
        with open(file_path, newline='', encoding=self.config.get("default_encoding")) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                entries.append(
                    PartnerFileEntry(
                        transaction_id=row.get('transaction_id', ''),
                        partner_id=row.get('partner_id', ''),
                        amount=float(row.get('amount', 0)),
                        status=row.get('status', ''),
                        timestamp=row.get('timestamp', '')
                    )
                )
        return entries
    
    def _read_json_file(self, file_path: str) -> List[PartnerFileEntry]:
        """Read entries from JSON file"""
        with open(file_path, 'r', encoding=self.config.get("default_encoding")) as f:
            data = json.load(f)
            entries = []
            
            if isinstance(data, list):
                for item in data:
                    entries.append(
                        PartnerFileEntry(
                            transaction_id=item.get('transaction_id', ''),
                            partner_id=item.get('partner_id', ''),
                            amount=float(item.get('amount', 0)),
                            status=item.get('status', ''),
                            timestamp=item.get('timestamp', '')
                        )
                    )
            elif isinstance(data, dict) and 'entries' in data:
                for item in data['entries']:
                    entries.append(
                        PartnerFileEntry(
                            transaction_id=item.get('transaction_id', ''),
                            partner_id=item.get('partner_id', ''),
                            amount=float(item.get('amount', 0)),
                            status=item.get('status', ''),
                            timestamp=item.get('timestamp', '')
                        )
                    )
            return entries
    
    def create_partner_file(self, partner_id: str, 
                          entries: List[PartnerFileEntry],
                          file_type: str = "settlement",
                          file_format: str = "csv") -> str:
        """Create a new partner file with provided entries
        
        Args:
            partner_id: Identifier for the partner
            entries: List of PartnerFileEntry objects to include
            file_type: Type of file (settlement, reconciliation, etc.)
            file_format: Format of output file (csv, json, etc.)
            
        Returns:
            Filename of the created file
        """
        current_date = datetime.utcnow().strftime("%Y%m%d")
        filename = f"{partner_id}_{current_date}_{file_type}.{file_format}"
        file_path = os.path.join(self.outgoing_dir, filename)
        
        logger.info(f"Creating partner file: {filename}")
        
        try:
            if file_format.lower() == "csv":
                self._write_csv_file(file_path, entries)
            elif file_format.lower() == "json":
                self._write_json_file(file_path, entries)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
                
            return filename
            
        except Exception as e:
            logger.error(f"Error creating partner file {filename}: {str(e)}")
            raise
    
    def _write_csv_file(self, file_path: str, entries: List[PartnerFileEntry]) -> None:
        """Write entries to CSV file"""
        with open(file_path, 'w', newline='', encoding=self.config.get("default_encoding")) as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            writer.writerow(['transaction_id', 'partner_id', 'amount', 'status', 'timestamp'])
            
            # Write data
            for entry in entries:
                writer.writerow([
                    entry.transaction_id,
                    entry.partner_id,
                    entry.amount,
                    entry.status,
                    entry.timestamp
                ])
    
    def _write_json_file(self, file_path: str, entries: List[PartnerFileEntry]) -> None:
        """Write entries to JSON file"""
        with open(file_path, 'w', encoding=self.config.get("default_encoding")) as f:
            data = {
                "partner_file_format_version": "1.0",
                "generated_at": datetime.utcnow().isoformat(),
                "entries": [entry.to_dict() for entry in entries]
            }
            json.dump(data, f, indent=2)
    
    def archive_file(self, filename: str, source_dir: str = None) -> None:
        """Move a file to the archive directory
        
        Args:
            filename: Name of the file to archive
            source_dir: Source directory (if not specified, checks both incoming and outgoing)
        """
        if source_dir:
            source_path = os.path.join(source_dir, filename)
        else:
            # Check both incoming and outgoing directories
            incoming_path = os.path.join(self.incoming_dir, filename)
            outgoing_path = os.path.join(self.outgoing_dir, filename)
            
            if os.path.exists(incoming_path):
                source_path = incoming_path
            elif os.path.exists(outgoing_path):
                source_path = outgoing_path
            else:
                raise FileNotFoundError(f"File not found for archiving: {filename}")
        
        dest_path = os.path.join(self.archive_dir, filename)
        shutil.move(source_path, dest_path)
        logger.info(f"Archived file: {filename}")
    
    def _move_to_error(self, filename: str) -> None:
        """Move a problematic file to the error directory"""
        source_path = os.path.join(self.incoming_dir, filename)
        if os.path.exists(source_path):
            dest_path = os.path.join(self.error_dir, filename)
            shutil.move(source_path, dest_path)
            logger.info(f"Moved file to error directory: {filename}")


# Create a service instance for import

# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
partner_file_service = PartnerFileService()
