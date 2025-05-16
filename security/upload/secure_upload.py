"""
Secure File Upload Handler for Core Banking System - FIXED VERSION

This module provides secure file upload handling with validation,
sanitization, and protection against common file upload vulnerabilities.

FIXED ISSUE M-04: Resource leakage in file operations using proper context managers
and try-finally blocks to ensure temporary files are always cleaned up properly.
"""

import os
import logging
import hashlib
import magic
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Union, BinaryIO
import tempfile
import uuid

# Try to import Flask if available
try:
    from flask import request, current_app
    from werkzeug.utils import secure_filename
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

# Import security components
from security.logs.audit_logger import AuditLogger

# Configure logger
logger = logging.getLogger(__name__)


class SecureFileUpload:
    """Handler for secure file uploads with validation and scanning"""
    
    def __init__(self, upload_dir: Optional[str] = None):
        """
        Initialize secure file upload handler
        
        Args:
            upload_dir (str, optional): Directory for file uploads
        """
        # Set upload directory
        if upload_dir:
            self.upload_dir = Path(upload_dir)
        else:
            self.upload_dir = Path('uploads')
        
        # Create directory if it doesn't exist
        os.makedirs(self.upload_dir, exist_ok=True)
        
        # Initialize audit logger
        self.audit_logger = AuditLogger()
        
        # Configure allowed file types and extensions
        self.allowed_mime_types = {
            # Images
            'image/jpeg', 'image/png', 'image/gif', 'image/svg+xml',
            # Documents
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'text/plain', 'text/csv'
        }
        
        self.allowed_extensions = {
            # Images
            '.jpg', '.jpeg', '.png', '.gif', '.svg',
            # Documents
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.txt', '.csv'
        }
        
        # Maximum file size (10MB by default)
        self.max_file_size = 10 * 1024 * 1024
        
        # Flag to scan files for viruses
        self.virus_scan_enabled = True
        
        # Flag to check file type vs. extension match
        self.check_content_type = True
        
        # Storage for content type vs. extension mapping
        self.content_type_map = {
            'image/jpeg': ['.jpg', '.jpeg'],
            'image/png': ['.png'],
            'image/gif': ['.gif'],
            'image/svg+xml': ['.svg'],
            'application/pdf': ['.pdf'],
            'application/msword': ['.doc'],
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
            'application/vnd.ms-excel': ['.xls'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
            'application/vnd.ms-powerpoint': ['.ppt'],
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
            'text/plain': ['.txt'],
            'text/csv': ['.csv']
        }
    
    def set_allowed_mime_types(self, mime_types: Set[str]):
        """
        Set allowed MIME types
        
        Args:
            mime_types: Set of allowed MIME types
        """
        self.allowed_mime_types = mime_types
    
    def set_allowed_extensions(self, extensions: Set[str]):
        """
        Set allowed file extensions
        
        Args:
            extensions: Set of allowed extensions
        """
        self.allowed_extensions = extensions
    
    def set_max_file_size(self, max_size: int):
        """
        Set maximum file size in bytes
        
        Args:
            max_size: Maximum file size in bytes
        """
        self.max_file_size = max_size
    
    def enable_virus_scan(self, enabled: bool = True):
        """
        Enable or disable virus scanning
        
        Args:
            enabled: Whether to enable virus scanning
        """
        self.virus_scan_enabled = enabled
    
    def enable_content_type_check(self, enabled: bool = True):
        """
        Enable or disable content type vs. extension checking
        
        Args:
            enabled: Whether to enable content type checking
        """
        self.check_content_type = enabled
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize a filename to prevent path traversal and other attacks
        
        Args:
            filename: Original filename
            
        Returns:
            str: Sanitized filename
        """
        if FLASK_AVAILABLE:
            # Use Werkzeug's secure_filename
            filename = secure_filename(filename)
        else:
            # Basic sanitization
            filename = os.path.basename(filename)
            # Replace potentially dangerous characters
            filename = re.sub(r'[^\w\.-]', '_', filename)
        
        # Add random suffix for extra security
        name, ext = os.path.splitext(filename)
        random_suffix = uuid.uuid4().hex[:8]
        return f"{name}_{random_suffix}{ext}"
    
    def is_valid_extension(self, filename: str) -> bool:
        """
        Check if file has a valid extension
        
        Args:
            filename: Filename to check
            
        Returns:
            bool: True if extension is allowed
        """
        _, ext = os.path.splitext(filename.lower())
        return ext in self.allowed_extensions
    
    def detect_mime_type(self, file_path: Union[str, Path, BinaryIO]) -> str:
        """
        Detect MIME type of a file
        
        Args:
            file_path: Path to file or file-like object
            
        Returns:
            str: Detected MIME type
        """
        try:
            if isinstance(file_path, (str, Path)):
                mime = magic.Magic(mime=True)
                return mime.from_file(str(file_path))
            else:
                # File-like object
                mime = magic.Magic(mime=True)
                file_pos = file_path.tell()
                mime_type = mime.from_buffer(file_path.read(4096))
                file_path.seek(file_pos)  # Reset position
                return mime_type
        except Exception as e:
            logger.error(f"Error detecting MIME type: {str(e)}")
            return "application/octet-stream"
    
    def is_valid_mime_type(self, mime_type: str) -> bool:
        """
        Check if MIME type is allowed
        
        Args:
            mime_type: MIME type to check
            
        Returns:
            bool: True if MIME type is allowed
        """
        return mime_type in self.allowed_mime_types
    
    def extension_matches_content(self, filename: str, mime_type: str) -> bool:
        """
        Check if file extension matches content type
        
        Args:
            filename: Filename to check
            mime_type: Detected MIME type
            
        Returns:
            bool: True if extension matches content type
        """
        _, ext = os.path.splitext(filename.lower())
        
        # Skip check if mime type is not in our map
        if mime_type not in self.content_type_map:
            return True
        
        # Check if extension is valid for this mime type
        return ext in self.content_type_map[mime_type]
    
    def scan_file_for_viruses(self, file_path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
        """
        Scan a file for viruses
        
        Args:
            file_path: Path to file to scan
            
        Returns:
            Tuple[bool, Optional[str]]: (is_clean, detection_name)
        """
        if not self.virus_scan_enabled:
            return True, None
        
        try:
            # Try to use ClamAV if available
            import clamd
            
            # Try to connect to ClamAV daemon
            try:
                cd = clamd.ClamdUnixSocket()
                result = cd.scan(str(file_path))
                
                file_result = result.get(str(file_path))
                if file_result[0] == 'OK':
                    return True, None
                else:
                    return False, file_result[1]
            
            except Exception as e:
                logger.warning(f"ClamAV scan failed, trying ClamdNetworkSocket: {str(e)}")
                
                # Try network socket as fallback
                try:
                    cd = clamd.ClamdNetworkSocket()
                    result = cd.scan(str(file_path))
                    
                    file_result = result.get(str(file_path))
                    if file_result[0] == 'OK':
                        return True, None
                    else:
                        return False, file_result[1]
                except Exception as e2:
                    logger.error(f"ClamAV network scan failed: {str(e2)}")
                    return True, None  # Assume clean if scanner fails
        
        except ImportError:
            logger.warning("clamd module not available, virus scanning disabled")
            return True, None
    
    def handle_upload(self, file) -> Dict[str, any]:
        """
        Handle file upload with security checks
        
        Args:
            file: File object (from Flask request.files or similar)
            
        Returns:
            Dict: Upload result with status and details
        """
        result = {
            "success": False,
            "errors": [],
            "file_path": None,
            "original_filename": None,
            "sanitized_filename": None,
            "mime_type": None,
            "file_size": 0
        }
        
        # Initialize temp_path to None so we can check it in finally block
        temp_path = None
        
        try:
            # Get original filename
            original_filename = file.filename
            result["original_filename"] = original_filename
            
            # Check if file was actually uploaded
            if not original_filename:
                result["errors"].append("No file selected")
                return result
            
            # Check file extension
            if not self.is_valid_extension(original_filename):
                result["errors"].append(f"File type not allowed: {original_filename}")
                return result
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            result["file_size"] = file_size
            
            if file_size > self.max_file_size:
                result["errors"].append(
                    f"File too large: {file_size} bytes (max {self.max_file_size} bytes)"
                )
                return result
                
            # Create temp file to check content type and scan for viruses
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                file.save(temp_file)
                temp_path = temp_file.name
            
            # From this point on, we need to ensure temp_path gets deleted if anything fails
            try:
                # Detect MIME type
                mime_type = self.detect_mime_type(temp_path)
                result["mime_type"] = mime_type
                
                # Check MIME type
                if not self.is_valid_mime_type(mime_type):
                    result["errors"].append(f"File content type not allowed: {mime_type}")
                    return result
                
                # Check if extension matches content type
                if self.check_content_type and not self.extension_matches_content(
                    original_filename, mime_type
                ):
                    result["errors"].append(
                        f"File extension does not match content type: {mime_type}"
                    )
                    return result
                
                # Scan for viruses
                if self.virus_scan_enabled:
                    is_clean, detection = self.scan_file_for_viruses(temp_path)
                    if not is_clean:
                        result["errors"].append(f"Malware detected: {detection}")
                        
                        # Log security event
                        self.audit_logger.log_event(
                            event_type="security_violation",
                            user_id="unknown",
                            description=f"Malware detected in uploaded file: {original_filename}",
                            metadata={
                                "filename": original_filename,
                                "mime_type": mime_type,
                                "detection": detection
                            }
                        )
                        return result
                
                # Sanitize filename
                sanitized_filename = self.sanitize_filename(original_filename)
                result["sanitized_filename"] = sanitized_filename
                
                # Generate destination path
                dest_path = self.upload_dir / sanitized_filename
                
                # Move temp file to destination
                os.rename(temp_path, dest_path)
                # After successful move, set temp_path to None so we don't try to delete it
                temp_path = None
                
                # Set permissions (read/write for owner only)
                os.chmod(dest_path, 0o600)
                
                # Calculate file hash for integrity
                file_hash = self._calculate_file_hash(dest_path)
                
                # Update result
                result["success"] = True
                result["file_path"] = str(dest_path)
                result["file_hash"] = file_hash
                
                # Log successful upload
                self.audit_logger.log_event(
                    event_type="file_upload",
                    user_id="unknown",  # Would be set from session in real app
                    description=f"File uploaded: {sanitized_filename}",
                    metadata={
                        "original_filename": original_filename,
                        "sanitized_filename": sanitized_filename,
                        "mime_type": mime_type,
                        "file_size": file_size,
                        "file_hash": file_hash
                    }
                )
                
                return result
                
            except Exception as inner_e:
                logger.error(f"Error during file processing: {str(inner_e)}")
                result["errors"].append(f"Processing failed: {str(inner_e)}")
                return result
        
        except Exception as e:
            logger.error(f"File upload error: {str(e)}")
            result["errors"].append(f"Upload failed: {str(e)}")
            return result
        
        finally:
            # Always clean up the temporary file if it still exists
            if temp_path is not None and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as cleanup_error:
                    logger.error(f"Failed to clean up temporary file: {cleanup_error}")
    
    def handle_flask_upload(self, file_field: str = 'file') -> Dict[str, any]:
        """
        Handle file upload from Flask request
        
        Args:
            file_field: Name of file field in form
            
        Returns:
            Dict: Upload result with status and details
        """
        if not FLASK_AVAILABLE:
            return {
                "success": False,
                "errors": ["Flask is not available"]
            }
        
        if file_field not in request.files:
            return {
                "success": False,
                "errors": ["No file part in request"]
            }
        
        file = request.files[file_field]
        result = self.handle_upload(file)
        
        # Add user info from session if available
        if hasattr(request, 'user_id'):
            result["user_id"] = request.user_id
        
        return result
    
    def _calculate_file_hash(self, file_path: Union[str, Path]) -> str:
        """
        Calculate SHA-256 hash of a file
        
        Args:
            file_path: Path to file
            
        Returns:
            str: Hexadecimal hash string
        """
        sha256_hash = hashlib.sha256()
        
        # Use context manager to ensure proper file closure
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()


# Create singleton instance
secure_upload = SecureFileUpload()

# Export main functions for easy access
handle_upload = secure_upload.handle_upload
handle_flask_upload = secure_upload.handle_flask_upload


# Flask extension
class SecureUpload:
    """Flask extension for SecureFileUpload"""
    
    def __init__(self, app=None, upload_dir=None):
        """
        Initialize SecureUpload extension
        
        Args:
            app: Flask application instance
            upload_dir: Directory for file uploads
        """
        self.upload_handler = SecureFileUpload(upload_dir)
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize extension with Flask app
        
        Args:
            app: Flask application instance
        """
        # Store extension in app
        app.secure_upload = self.upload_handler
        
        # Register upload route if desired
        if app.config.get('SECURE_UPLOAD_ROUTE_ENABLED', False):
            @app.route(app.config.get('SECURE_UPLOAD_ROUTE', '/upload'), methods=['POST'])
            def upload_file():
                from flask import jsonify
                
                result = self.upload_handler.handle_flask_upload()
                return jsonify(result)
        
        # Set configuration from app config
        if 'SECURE_UPLOAD_ALLOWED_EXTENSIONS' in app.config:
            self.upload_handler.set_allowed_extensions(
                set(app.config['SECURE_UPLOAD_ALLOWED_EXTENSIONS'])
            )
        
        if 'SECURE_UPLOAD_ALLOWED_MIME_TYPES' in app.config:
            self.upload_handler.set_allowed_mime_types(
                set(app.config['SECURE_UPLOAD_ALLOWED_MIME_TYPES'])
            )
        
        if 'SECURE_UPLOAD_MAX_SIZE' in app.config:
            self.upload_handler.set_max_file_size(app.config['SECURE_UPLOAD_MAX_SIZE'])
        
        if 'SECURE_UPLOAD_VIRUS_SCAN' in app.config:
            self.upload_handler.enable_virus_scan(app.config['SECURE_UPLOAD_VIRUS_SCAN'])
        
        if 'SECURE_UPLOAD_CHECK_CONTENT_TYPE' in app.config:
            self.upload_handler.enable_content_type_check(
                app.config['SECURE_UPLOAD_CHECK_CONTENT_TYPE']
            )
