"""
Configuration Updater Service

This module provides a service that listens for configuration changes in the Admin module
and propagates them to the respective modules.
"""
import os
import sys
import logging
import time
import json
import threading
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the parent directory to sys.path to import the integration interfaces
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from integration_interfaces.api.admin_client import AdminIntegrationClient

logger = logging.getLogger(__name__)

class ConfigUpdateHandler:
    """Handler for processing configuration updates from the Admin module."""
    
    def __init__(self, module_id: str, config_path: str = None):
        """
        Initialize the configuration update handler.
        
        Args:
            module_id: ID of the module
            config_path: Path to the module's configuration file
        """
        self.module_id = module_id
        self.config_path = config_path or self._get_default_config_path()
    
    def _get_default_config_path(self) -> str:
        """Get the default configuration path for the module."""
        module_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), self.module_id)
        return os.path.join(module_dir, "config.py")
    
    def apply_config_update(self, config_key: str, config_value: Any) -> bool:
        """
        Apply a configuration update to the module.
        
        Args:
            config_key: Configuration key to update
            config_value: New value for the configuration
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Applying configuration update for module {self.module_id}: {config_key} = {config_value}")
            
            # In a real implementation, this would update the module's configuration
            # in a way appropriate for that module (config file, database, environment variables, etc.)
            
            # For this example, we'll assume a simple configuration file that we can parse and update
            if os.path.exists(self.config_path):
                self._update_config_file(config_key, config_value)
            else:
                # If the config file doesn't exist, create it
                self._create_config_file({config_key: config_value})
            
            # Notify the module about the configuration change
            self._notify_module_of_config_change(config_key, config_value)
            
            return True
        except Exception as e:
            logger.error(f"Failed to apply configuration update for module {self.module_id}: {e}")
            return False
    
    def _update_config_file(self, config_key: str, config_value: Any) -> None:
        """
        Update a configuration value in the module's configuration file.
        
        Args:
            config_key: Configuration key to update
            config_value: New value for the configuration
        """
        # Read the current config file
        with open(self.config_path, "r") as f:
            config_content = f.read()
        
        # This is a simple string replacement for Python-style configuration
        # In a real implementation, you would use a proper configuration parser
        
        # Check if the key exists in the file
        if f"{config_key} = " in config_content:
            # Replace the value
            import re
            pattern = rf"{config_key}\s*=\s*.*"
            replacement = f"{config_key} = {repr(config_value)}"
            config_content = re.sub(pattern, replacement, config_content)
        else:
            # Add the key-value pair
            config_content += f"\n{config_key} = {repr(config_value)}\n"
        
        # Write the updated config back
        with open(self.config_path, "w") as f:
            f.write(config_content)
        
        logger.info(f"Updated configuration file for module {self.module_id}: {config_key} = {config_value}")
    
    def _create_config_file(self, config_dict: Dict[str, Any]) -> None:
        """
        Create a new configuration file for the module.
        
        Args:
            config_dict: Dictionary of configuration key-value pairs
        """
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Generate the configuration content
        content = "# Auto-generated configuration file\n"
        content += f"# Generated at: {datetime.now().isoformat()}\n\n"
        
        for key, value in config_dict.items():
            content += f"{key} = {repr(value)}\n"
        
        # Write the configuration file
        with open(self.config_path, "w") as f:
            f.write(content)
        
        logger.info(f"Created configuration file for module {self.module_id}")
    
    def _notify_module_of_config_change(self, config_key: str, config_value: Any) -> None:
        """
        Notify the module about a configuration change.
        
        Args:
            config_key: Configuration key that changed
            config_value: New value for the configuration
        """
        # In a real implementation, this would notify the module in a way appropriate
        # for that module (IPC, database signal, etc.)
        
        # For this example, we'll just log the notification
        logger.info(f"Notifying module {self.module_id} about configuration change: {config_key}")
        
        # If the module has a running instance, we might send an HTTP request to a special endpoint
        # This is just a placeholder for demonstration
        try:
            module_base_url = os.environ.get(f"CBS_{self.module_id.upper()}_BASE_URL")
            if module_base_url:
                url = f"{module_base_url}/api/config/refresh"
                requests.post(
                    url,
                    json={
                        "config_key": config_key,
                        "config_value": config_value
                    },
                    timeout=5
                )
        except Exception as e:
            logger.warning(f"Failed to notify module {self.module_id} about configuration change: {e}")


class ConfigurationUpdaterService:
    """Service for propagating configuration changes from Admin to modules."""
    
    def __init__(self, admin_base_url: str = None, api_key: str = None):
        """
        Initialize the configuration updater service.
        
        Args:
            admin_base_url: Base URL of the Admin module API
            api_key: API key for authentication with the Admin module
        """
        self.admin_base_url = admin_base_url or os.environ.get("CBS_ADMIN_BASE_URL", "http://localhost:8000/api/admin")
        self.api_key = api_key or os.environ.get("CBS_ADMIN_API_KEY")
        
        # Create admin client
        self.admin_client = AdminIntegrationClient(
            admin_base_url=self.admin_base_url,
            module_id="config_updater",
            api_key=self.api_key
        )
        
        # Create configuration handlers for each module
        self.config_handlers = {
            "core_banking": ConfigUpdateHandler("core_banking"),
            "payments": ConfigUpdateHandler("payments"),
            "digital_channels": ConfigUpdateHandler("digital_channels"),
            "risk_compliance": ConfigUpdateHandler("risk_compliance"),
            "treasury": ConfigUpdateHandler("treasury")
        }
        
        # Last update timestamp for each module
        self.last_update_timestamp = {}
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including authentication."""
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "X-Module-ID": "config_updater"
        }
    
    def get_config_updates(self, module_id: str = None, since: str = None) -> List[Dict[str, Any]]:
        """
        Get configuration updates from the Admin module.
        
        Args:
            module_id: Optional filter by module ID
            since: Optional timestamp to get updates since
            
        Returns:
            List of configuration update dictionaries
        """
        url = f"{self.admin_base_url}/configurations"
        params = {}
        
        if module_id:
            params["module_id"] = module_id
        
        if since:
            params["since"] = since
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                params=params
            )
            response.raise_for_status()
            return response.json().get("configurations", [])
        except Exception as e:
            logger.error(f"Failed to get configuration updates: {e}")
            return []
    
    def process_config_updates(self, updates: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Process configuration updates and apply them to the respective modules.
        
        Args:
            updates: List of configuration update dictionaries
            
        Returns:
            Dictionary mapping module IDs to lists of processed configuration keys
        """
        processed = {}
        
        for update in updates:
            module_id = update.get("module_id")
            config_key = update.get("key")
            config_value = update.get("value")
            
            if not module_id or not config_key or config_value is None:
                logger.warning(f"Invalid configuration update: {update}")
                continue
            
            handler = self.config_handlers.get(module_id)
            if not handler:
                logger.warning(f"No configuration handler for module: {module_id}")
                continue
            
            success = handler.apply_config_update(config_key, config_value)
            
            if success:
                if module_id not in processed:
                    processed[module_id] = []
                processed[module_id].append(config_key)
            
            # Update the last update timestamp
            self.last_update_timestamp[module_id] = update.get("updated_at", datetime.utcnow().isoformat())
        
        return processed
    
    def check_and_process_updates(self) -> Dict[str, List[str]]:
        """
        Check for and process configuration updates for all modules.
        
        Returns:
            Dictionary mapping module IDs to lists of processed configuration keys
        """
        all_updates = []
        
        # Check for updates for each module
        for module_id in self.config_handlers:
            since = self.last_update_timestamp.get(module_id)
            updates = self.get_config_updates(module_id, since)
            all_updates.extend(updates)
        
        # Process all updates
        return self.process_config_updates(all_updates)
    
    def start_updater(self, interval_seconds: int = 60) -> threading.Thread:
        """
        Start the configuration updater service in a background thread.
        
        Args:
            interval_seconds: Interval between update checks in seconds
            
        Returns:
            The background thread running the updater service
        """
        def updater_thread():
            logger.info(f"Configuration updater service started with interval of {interval_seconds} seconds")
            while True:
                try:
                    processed = self.check_and_process_updates()
                    if processed:
                        logger.info(f"Processed configuration updates: {processed}")
                except Exception as e:
                    logger.error(f"Error in configuration updater: {e}")
                
                # Sleep until next check
                time.sleep(interval_seconds)
        
        thread = threading.Thread(target=updater_thread, daemon=True)
        thread.start()
        return thread


def start_configuration_updater(interval_seconds: int = 60):
    """
    Start the configuration updater service.
    
    Args:
        interval_seconds: Interval between update checks in seconds
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create and start the updater
    updater = ConfigurationUpdaterService()
    
    # Start updater in a background thread
    updater_thread = updater.start_updater(interval_seconds)
    
    logger.info(f"Configuration updater service started with interval of {interval_seconds} seconds")
    return updater, updater_thread


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Configuration Updater Service")
    parser.add_argument("--interval", type=int, default=60, help="Interval between update checks in seconds")
    args = parser.parse_args()
    
    # Start updater
    updater, thread = start_configuration_updater(args.interval)
    
    # Keep the main thread running
    try:
        while thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Configuration updater service stopped by user")
