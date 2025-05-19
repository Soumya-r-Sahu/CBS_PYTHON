"""
API Key Management Service

This module provides services for managing API keys in the Admin module.
"""
import os
import logging
import secrets
import string
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Service for managing API keys."""
    
    def __init__(self, api_key_store_path: str = None):
        """
        Initialize the API key manager.
        
        Args:
            api_key_store_path: Path to the API key store file
        """
        self.api_key_store_path = api_key_store_path or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "data",
            "api_keys.json"
        )
        
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(self.api_key_store_path), exist_ok=True)
        
        # Load API keys
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """
        Load API keys from the store file.
        
        Returns:
            Dictionary mapping module IDs to API key information
        """
        import json
        
        try:
            if os.path.exists(self.api_key_store_path):
                with open(self.api_key_store_path, "r") as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Failed to load API keys: {e}")
            return {}
    
    def _save_api_keys(self) -> bool:
        """
        Save API keys to the store file.
        
        Returns:
            True if successful, False otherwise
        """
        import json
        
        try:
            with open(self.api_key_store_path, "w") as f:
                json.dump(self.api_keys, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save API keys: {e}")
            return False
    
    def generate_api_key(self, length: int = 32) -> str:
        """
        Generate a new API key.
        
        Args:
            length: Length of the API key
            
        Returns:
            A new API key
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def create_api_key(self, module_id: str, description: str = None) -> Dict[str, Any]:
        """
        Create a new API key for a module.
        
        Args:
            module_id: ID of the module
            description: Optional description of the API key
            
        Returns:
            Dictionary with API key information
        """
        # Generate a new API key
        api_key = self.generate_api_key()
        
        # Create API key information
        api_key_info = {
            "key": api_key,
            "created_at": datetime.utcnow().isoformat(),
            "description": description or f"API key for {module_id}",
            "is_active": True
        }
        
        # Store the API key
        self.api_keys[module_id] = api_key_info
        self._save_api_keys()
        
        return api_key_info
    
    def get_api_key(self, module_id: str) -> Optional[Dict[str, Any]]:
        """
        Get API key information for a module.
        
        Args:
            module_id: ID of the module
            
        Returns:
            Dictionary with API key information, or None if not found
        """
        return self.api_keys.get(module_id)
    
    def validate_api_key(self, api_key: str, module_id: str = None) -> bool:
        """
        Validate an API key.
        
        Args:
            api_key: The API key to validate
            module_id: Optional module ID to validate against
            
        Returns:
            True if valid, False otherwise
        """
        if module_id:
            # Check specific module
            module_info = self.api_keys.get(module_id)
            if module_info and module_info.get("is_active") and module_info.get("key") == api_key:
                return True
            return False
        
        # Check all modules
        for module_id, module_info in self.api_keys.items():
            if module_info.get("is_active") and module_info.get("key") == api_key:
                return True
        
        return False
    
    def rotate_api_key(self, module_id: str) -> Optional[Dict[str, Any]]:
        """
        Rotate (regenerate) the API key for a module.
        
        Args:
            module_id: ID of the module
            
        Returns:
            Dictionary with new API key information, or None if not found
        """
        if module_id not in self.api_keys:
            return None
        
        # Get existing API key info
        api_key_info = self.api_keys[module_id].copy()
        
        # Generate a new API key
        api_key_info["key"] = self.generate_api_key()
        api_key_info["created_at"] = datetime.utcnow().isoformat()
        
        # Store the updated API key
        self.api_keys[module_id] = api_key_info
        self._save_api_keys()
        
        return api_key_info
    
    def revoke_api_key(self, module_id: str) -> bool:
        """
        Revoke the API key for a module.
        
        Args:
            module_id: ID of the module
            
        Returns:
            True if successful, False otherwise
        """
        if module_id not in self.api_keys:
            return False
        
        # Mark the API key as inactive
        self.api_keys[module_id]["is_active"] = False
        self._save_api_keys()
        
        return True
    
    def list_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """
        List all API keys.
        
        Returns:
            Dictionary mapping module IDs to API key information
        """
        # Return a copy to prevent modification
        return {module_id: info.copy() for module_id, info in self.api_keys.items()}


# Create a singleton instance
api_key_manager = APIKeyManager()
