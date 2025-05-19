"""
Admin Panel Integration for Django Admin Portal

This module integrates the standalone admin_panel module with the Django-based Admin Portal
"""

import os
import sys
import logging
from typing import Dict, Any, Optional

# Configure logger
logger = logging.getLogger(__name__)

class AdminPortalIntegration:
    """
    Integration class that connects the admin_panel module with the Django Admin Portal
    
    This class provides an adapter between the standalone admin dashboard and the 
    Django-based admin portal in app/Portals/Admin.
    """
    
    def __init__(self):
        """Initialize the integration"""
        self.admin_module_loaded = False
        try:
            from admin_panel.admin_dashboard import AdminDashboard
            self.admin_dashboard = AdminDashboard()
            self.admin_module_loaded = True
            logger.info("Successfully loaded AdminDashboard from admin_panel")
        except ImportError as e:
            logger.warning(f"Could not import AdminDashboard: {e}")
            self.admin_dashboard = None
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics from the admin dashboard"""
        if not self.admin_module_loaded or not self.admin_dashboard:
            return {"error": "Admin module not loaded"}
        
        try:
            # The admin dashboard module doesn't directly expose system stats,
            # so we're using a protected method here
            return self.admin_dashboard._get_system_info()
        except Exception as e:
            logger.error(f"Error getting system stats: {e}")
            return {"error": str(e)}
    
    def get_module_status(self) -> Dict[str, Any]:
        """Get module status information"""
        if not self.admin_module_loaded or not self.admin_dashboard:
            return {"error": "Admin module not loaded"}
        
        try:
            return {"modules": self.admin_dashboard._check_modules_status()}
        except Exception as e:
            logger.error(f"Error getting module status: {e}")
            return {"error": str(e)}
    
    def get_db_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.admin_module_loaded or not self.admin_dashboard:
            return {"error": "Admin module not loaded"}
        
        try:
            return self.admin_dashboard._get_db_stats()
        except Exception as e:
            logger.error(f"Error getting DB stats: {e}")
            return {"error": str(e)}

# Create a singleton instance for use throughout the app
admin_integration = AdminPortalIntegration()
