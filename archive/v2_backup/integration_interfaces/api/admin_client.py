"""
Admin Integration Client

This module provides a client for integrating with the CBS Admin module.
It allows modules to register themselves, their API endpoints, feature flags,
and configurations with the Admin module.
"""
import requests
import logging
from typing import Dict, List, Any, Optional
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class AdminIntegrationClient:
    """Client for integrating with the CBS Admin module."""
    
    def __init__(self, admin_base_url: str = None, module_id: str = None, api_key: str = None):
        """
        Initialize the Admin Integration Client.
        
        Args:
            admin_base_url: Base URL of the Admin module API
            module_id: ID of the module using this client
            api_key: API key for authentication with the Admin module
        """
        self.admin_base_url = admin_base_url or os.environ.get("CBS_ADMIN_BASE_URL", "http://localhost:8000/api/admin")
        self.module_id = module_id
        self.api_key = api_key or os.environ.get("CBS_ADMIN_API_KEY")
        
        if not self.api_key:
            logger.warning("No API key provided for Admin integration. Authentication will fail.")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including authentication."""
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "X-Module-ID": self.module_id
        }
    
    def register_module(self, module_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Register or update a module with the Admin module.
        
        Args:
            module_info: Dictionary containing module information
            
        Returns:
            Response from the Admin module
        """
        url = f"{self.admin_base_url}/modules"
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=module_info
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to register module: {e}")
            return {"status": "error", "message": str(e)}
    
    def register_api_endpoints(self, endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Register or update API endpoints with the Admin module.
        
        Args:
            endpoints: List of dictionaries containing endpoint information
            
        Returns:
            Response from the Admin module
        """
        url = f"{self.admin_base_url}/api/endpoints"
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={"module_id": self.module_id, "endpoints": endpoints}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to register API endpoints: {e}")
            return {"status": "error", "message": str(e)}
    
    def register_feature_flags(self, flags: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Register or update feature flags with the Admin module.
        
        Args:
            flags: List of dictionaries containing feature flag information
            
        Returns:
            Response from the Admin module
        """
        url = f"{self.admin_base_url}/features"
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={"module_id": self.module_id, "features": flags}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to register feature flags: {e}")
            return {"status": "error", "message": str(e)}
    
    def register_configurations(self, configs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Register or update configurations with the Admin module.
        
        Args:
            configs: List of dictionaries containing configuration information
            
        Returns:
            Response from the Admin module
        """
        url = f"{self.admin_base_url}/configurations"
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={"module_id": self.module_id, "configurations": configs}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to register configurations: {e}")
            return {"status": "error", "message": str(e)}
    
    def send_health_metrics(self, health_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send health metrics to the Admin module.
        
        Args:
            health_data: Dictionary containing health metrics
            
        Returns:
            Response from the Admin module
        """
        url = f"{self.admin_base_url}/health"
        
        # Ensure timestamp is included
        if "timestamp" not in health_data:
            health_data["timestamp"] = datetime.utcnow().isoformat()
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={"module_id": self.module_id, "health": health_data}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send health metrics: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_module_status(self) -> Dict[str, Any]:
        """
        Get the current status of this module from the Admin module.
        
        Returns:
            Dictionary containing module status information
        """
        url = f"{self.admin_base_url}/modules/{self.module_id}"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get module status: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_configuration(self, key: str = None) -> Dict[str, Any]:
        """
        Get configuration from the Admin module.
        
        Args:
            key: Optional specific configuration key to fetch
            
        Returns:
            Dictionary containing configuration values
        """
        url = f"{self.admin_base_url}/configurations/{self.module_id}"
        if key:
            url += f"/{key}"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get configuration: {e}")
            return {"status": "error", "message": str(e)}
