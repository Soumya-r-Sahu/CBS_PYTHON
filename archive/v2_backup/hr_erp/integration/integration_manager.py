"""
Integration Manager module for connecting HR-ERP with other Core Banking System modules.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union
import datetime
from pathlib import Path
import os


# Use centralized import system
from utils.lib.packages import fix_path
fix_path()  # Ensures project root is in sys.path
logger = logging.getLogger(__name__)

class IntegrationManager:
    """
    Manager class for handling integration with other CBS modules.
    
    This class provides methods for data exchange, API interactions, and event handling
    between the HR-ERP module and other modules in the Core Banking System.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the integration manager.
        
        Args:
            config_path: Path to integration configuration file (optional)
        """
        self.modules = {}  # Dictionary to store connected module interfaces
        self.event_handlers = {}  # Dictionary to store event handlers
        self.config = {}
        
        # Load configuration if provided
        if config_path:
            self._load_configuration(config_path)
        
        logger.info("Integration Manager initialized")
    
    def _load_configuration(self, config_path: str) -> None:
        """
        Load integration configuration from a file.
        
        Args:
            config_path: Path to the configuration file
        """
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Loaded integration configuration from {config_path}")
            else:
                logger.warning(f"Configuration file {config_path} not found")
        except Exception as e:
            logger.error(f"Error loading integration configuration: {str(e)}")
    
    def register_module(self, module_name: str, module_interface: Any) -> bool:
        """
        Register a CBS module interface for integration.
        
        Args:
            module_name: Name of the module to register
            module_interface: Interface object for the module
            
        Returns:
            bool: True if registered successfully, False if already registered
        """
        if module_name in self.modules:
            logger.warning(f"Module {module_name} already registered")
            return False
            
        self.modules[module_name] = module_interface
        logger.info(f"Module {module_name} registered for integration")
        return True
    
    def unregister_module(self, module_name: str) -> bool:
        """
        Unregister a CBS module interface.
        
        Args:
            module_name: Name of the module to unregister
            
        Returns:
            bool: True if unregistered successfully, False if not found
        """
        if module_name not in self.modules:
            logger.warning(f"Module {module_name} not registered")
            return False
            
        del self.modules[module_name]
        logger.info(f"Module {module_name} unregistered")
        return True
    
    def get_module_interface(self, module_name: str) -> Optional[Any]:
        """
        Get the interface for a registered module.
        
        Args:
            module_name: Name of the module
            
        Returns:
            Any: The module interface or None if not registered
        """
        if module_name not in self.modules:
            logger.warning(f"Module {module_name} not registered")
            return None
            
        return self.modules[module_name]
    
    def register_event_handler(self, event_name: str, handler_function: callable) -> bool:
        """
        Register a handler function for an event.
        
        Args:
            event_name: Name of the event to handle
            handler_function: Function to call when the event occurs
            
        Returns:
            bool: True if registered successfully
        """
        if event_name not in self.event_handlers:
            self.event_handlers[event_name] = []
            
        self.event_handlers[event_name].append(handler_function)
        logger.info(f"Handler registered for event {event_name}")
        return True
    
    def trigger_event(self, event_name: str, event_data: Dict) -> bool:
        """
        Trigger an event and execute all registered handlers.
        
        Args:
            event_name: Name of the event to trigger
            event_data: Data associated with the event
            
        Returns:
            bool: True if event was triggered and had handlers, False otherwise
        """
        if event_name not in self.event_handlers or not self.event_handlers[event_name]:
            logger.warning(f"No handlers registered for event {event_name}")
            return False
            
        for handler in self.event_handlers[event_name]:
            try:
                handler(event_data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_name}: {str(e)}")
                
        logger.info(f"Event {event_name} triggered with {len(self.event_handlers[event_name])} handlers")
        return True
    
    def send_data_to_module(self, module_name: str, endpoint: str, data: Dict) -> Dict:
        """
        Send data to a specific module endpoint.
        
        Args:
            module_name: Name of the target module
            endpoint: Specific endpoint or function in the module
            data: Data to send to the module
            
        Returns:
            dict: Response from the module or error information
        """
        module = self.get_module_interface(module_name)
        if not module:
            return {"success": False, "error": f"Module {module_name} not registered"}
            
        try:
            if hasattr(module, endpoint) and callable(getattr(module, endpoint)):
                method = getattr(module, endpoint)
                response = method(data)
                logger.info(f"Data sent to {module_name}.{endpoint}")
                return {"success": True, "response": response}
            else:
                logger.error(f"Endpoint {endpoint} not found in module {module_name}")
                return {"success": False, "error": f"Endpoint {endpoint} not found"}
        except Exception as e:
            logger.error(f"Error sending data to {module_name}.{endpoint}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_data_from_module(self, module_name: str, endpoint: str, params: Dict = None) -> Dict:
        """
        Get data from a specific module endpoint.
        
        Args:
            module_name: Name of the source module
            endpoint: Specific endpoint or function in the module
            params: Parameters for the request (optional)
            
        Returns:
            dict: Data from the module or error information
        """
        module = self.get_module_interface(module_name)
        if not module:
            return {"success": False, "error": f"Module {module_name} not registered"}
            
        try:
            if hasattr(module, endpoint) and callable(getattr(module, endpoint)):
                method = getattr(module, endpoint)
                params = params or {}
                data = method(**params)
                logger.info(f"Data retrieved from {module_name}.{endpoint}")
                return {"success": True, "data": data}
            else:
                logger.error(f"Endpoint {endpoint} not found in module {module_name}")
                return {"success": False, "error": f"Endpoint {endpoint} not found"}
        except Exception as e:
            logger.error(f"Error getting data from {module_name}.{endpoint}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def sync_employee_data(self) -> Dict:
        """
        Synchronize employee data with other modules.
        
        Returns:
            dict: Results of the synchronization
        """
        results = {
            "success": True,
            "modules_synced": [],
            "errors": []
        }
        
        # Get employee data from HR-ERP
        try:
            # This would typically come from the employee management module
            # For now we'll assume we have some dummy way to get it
            employee_data = self._get_employee_data()
            
            # Sync with each registered module that needs employee data
            for module_name, module in self.modules.items():
                if hasattr(module, 'update_employee_data') and callable(getattr(module, 'update_employee_data')):
                    try:
                        module.update_employee_data(employee_data)
                        results["modules_synced"].append(module_name)
                        logger.info(f"Employee data synced with {module_name}")
                    except Exception as e:
                        error = f"Error syncing with {module_name}: {str(e)}"
                        results["errors"].append(error)
                        logger.error(error)
        except Exception as e:
            results["success"] = False
            results["errors"].append(f"Error retrieving employee data: {str(e)}")
            logger.error(f"Error in sync_employee_data: {str(e)}")
        
        return results
    
    def _get_employee_data(self) -> List[Dict]:
        """
        Get employee data from the HR-ERP employee management module.
        
        This is a placeholder method. In a real implementation, it would interface
        with the actual employee management module.
        
        Returns:
            list: List of employee data dictionaries
        """
        # In a real implementation, this would retrieve data from the employee management module
        # This is just a placeholder
        return []
    
    def sync_payroll_data(self, period_start: Union[str, datetime.date], 
                          period_end: Union[str, datetime.date]) -> Dict:
        """
        Synchronize payroll data with finance modules.
        
        Args:
            period_start: Start date of the payroll period
            period_end: End date of the payroll period
            
        Returns:
            dict: Results of the synchronization
        """
        # Convert string dates to datetime objects if needed
        if isinstance(period_start, str):
            period_start = datetime.date.fromisoformat(period_start)
        if isinstance(period_end, str):
            period_end = datetime.date.fromisoformat(period_end)
            
        results = {
            "success": True,
            "modules_synced": [],
            "errors": []
        }
        
        # Get payroll data
        try:
            # This would typically come from the payroll module
            payroll_data = self._get_payroll_data(period_start, period_end)
            
            # Look for finance module to sync with
            finance_module = self.get_module_interface("finance")
            if finance_module and hasattr(finance_module, 'process_payroll'):
                try:
                    finance_module.process_payroll(payroll_data)
                    results["modules_synced"].append("finance")
                    logger.info("Payroll data synced with finance module")
                except Exception as e:
                    error = f"Error syncing payroll with finance module: {str(e)}"
                    results["errors"].append(error)
                    logger.error(error)
            else:
                results["errors"].append("Finance module not registered or missing process_payroll method")
                logger.warning("Finance module not available for payroll sync")
        except Exception as e:
            results["success"] = False
            results["errors"].append(f"Error retrieving payroll data: {str(e)}")
            logger.error(f"Error in sync_payroll_data: {str(e)}")
        
        return results
    
    def _get_payroll_data(self, period_start: datetime.date, period_end: datetime.date) -> Dict:
        """
        Get payroll data for a specific period.
        
        This is a placeholder method. In a real implementation, it would interface
        with the actual payroll module.
        
        Args:
            period_start: Start date of the payroll period
            period_end: End date of the payroll period
            
        Returns:
            dict: Payroll data for the specified period
        """
        # In a real implementation, this would retrieve data from the payroll module
        # This is just a placeholder
        return {
            "period": {
                "start": period_start.isoformat(),
                "end": period_end.isoformat()
            },
            "payroll_entries": []
        }
    
    def notify_external_systems(self, event_type: str, data: Dict) -> Dict:
        """
        Send notifications to external systems about HR-ERP events.
        
        Args:
            event_type: Type of event (e.g., 'new_hire', 'promotion', 'termination')
            data: Event data to send
            
        Returns:
            dict: Results of the notification process
        """
        results = {
            "success": True,
            "systems_notified": [],
            "errors": []
        }
        
        # Check for notification configurations in the loaded config
        if "external_notifications" not in self.config:
            results["success"] = False
            results["errors"].append("No external notification configuration found")
            logger.warning("No external notification configuration found")
            return results
        
        # Process notifications for each configured external system
        for system_name, system_config in self.config.get("external_notifications", {}).items():
            if event_type in system_config.get("subscribed_events", []):
                try:
                    # In a real implementation, this would use the appropriate
                    # mechanism (API call, message queue, etc.) to notify the external system
                    # This is just a placeholder
                    logger.info(f"Notifying {system_name} of {event_type} event")
                    results["systems_notified"].append(system_name)
                except Exception as e:
                    error = f"Error notifying {system_name}: {str(e)}"
                    results["errors"].append(error)
                    logger.error(error)
        
        return results
    
    def import_data(self, source_module: str, data_type: str, data: Any) -> Dict:
        """
        Import data from another module into HR-ERP.
        
        Args:
            source_module: Name of the source module
            data_type: Type of data being imported
            data: The data to import
            
        Returns:
            dict: Results of the import operation
        """
        results = {
            "success": True,
            "records_imported": 0,
            "errors": []
        }
        
        try:
            if data_type == "employees":
                # This would process employee data imports
                results["records_imported"] = self._import_employee_data(data)
            elif data_type == "training":
                # This would process training data imports
                results["records_imported"] = self._import_training_data(data)
            else:
                results["success"] = False
                results["errors"].append(f"Unsupported data type: {data_type}")
                logger.warning(f"Unsupported data type for import: {data_type}")
        except Exception as e:
            results["success"] = False
            results["errors"].append(f"Error importing {data_type} data: {str(e)}")
            logger.error(f"Error importing data: {str(e)}")
        
        logger.info(f"Imported {results['records_imported']} {data_type} records from {source_module}")
        return results
    
    def _import_employee_data(self, data: List[Dict]) -> int:
        """
        Import employee data into the HR-ERP system.
        
        This is a placeholder method. In a real implementation, it would process
        the data and update the employee management module.
        
        Args:
            data: List of employee data dictionaries
            
        Returns:
            int: Number of records imported
        """
        # In a real implementation, this would process and store the data
        # This is just a placeholder
        return len(data)
    
    def _import_training_data(self, data: List[Dict]) -> int:
        """
        Import training data into the HR-ERP system.
        
        This is a placeholder method. In a real implementation, it would process
        the data and update the training module.
        
        Args:
            data: List of training data dictionaries
            
        Returns:
            int: Number of records imported
        """
        # In a real implementation, this would process and store the data
        # This is just a placeholder
        return len(data)
