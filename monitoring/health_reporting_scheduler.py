"""
Health Reporting Scheduler

This module implements scheduled tasks to periodically report health metrics
from all modules to the Admin module.
"""
import os
import sys
import logging
import time
import json
import threading
import schedule
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the parent directory to sys.path to import the integration interfaces
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from integration_interfaces.api.admin_client import AdminIntegrationClient

# Import module registry implementations
from core_banking.admin_integration import CoreBankingModuleRegistry
from payments.admin_integration import PaymentsModuleRegistry
from digital_channels.admin_integration import DigitalChannelsModuleRegistry
from risk_compliance.admin_integration import RiskComplianceModuleRegistry
from treasury.admin_integration import TreasuryModuleRegistry

logger = logging.getLogger(__name__)

class HealthReportingScheduler:
    """Scheduler for reporting health metrics from all modules."""
    
    def __init__(self, admin_base_url: str = None, api_key: str = None):
        """
        Initialize the health reporting scheduler.
        
        Args:
            admin_base_url: Base URL of the Admin module API
            api_key: API key for authentication with the Admin module
        """
        self.admin_base_url = admin_base_url or os.environ.get("CBS_ADMIN_BASE_URL", "http://localhost:8000/api/admin")
        self.api_key = api_key or os.environ.get("CBS_ADMIN_API_KEY", "dummy-key")
        
        # Create module registries
        self.module_registries = {
            "core_banking": CoreBankingModuleRegistry(),
            "payments": PaymentsModuleRegistry(),
            "digital_channels": DigitalChannelsModuleRegistry(),
            "risk_compliance": RiskComplianceModuleRegistry(),
            "treasury": TreasuryModuleRegistry()
        }
        
        # Create admin clients for each module
        self.admin_clients = {}
        for module_id, registry in self.module_registries.items():
            self.admin_clients[module_id] = AdminIntegrationClient(
                admin_base_url=self.admin_base_url,
                module_id=module_id,
                api_key=self.api_key
            )
    
    def report_health_for_module(self, module_id: str) -> bool:
        """
        Report health metrics for a specific module.
        
        Args:
            module_id: ID of the module to report health for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            registry = self.module_registries.get(module_id)
            client = self.admin_clients.get(module_id)
            
            if not registry or not client:
                logger.error(f"Module registry or client not found for module: {module_id}")
                return False
            
            # Get health metrics from the registry
            health_metrics = registry.health_check()
            
            # Send health metrics to Admin module
            result = client.send_health_metrics(health_metrics)
            
            logger.info(f"Reported health metrics for module {module_id}: {result.get('status', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to report health for module {module_id}: {e}")
            return False
    
    def report_health_for_all_modules(self) -> Dict[str, bool]:
        """
        Report health metrics for all registered modules.
        
        Returns:
            Dictionary mapping module IDs to success/failure status
        """
        results = {}
        for module_id in self.module_registries:
            results[module_id] = self.report_health_for_module(module_id)
        
        logger.info(f"Reported health metrics for all modules: {results}")
        return results
    
    def start_scheduler(self) -> None:
        """Start the health reporting scheduler."""
        # Schedule health reporting at different intervals for different modules
        schedule.every(5).minutes.do(self.report_health_for_module, module_id="core_banking")
        schedule.every(5).minutes.do(self.report_health_for_module, module_id="payments")
        schedule.every(5).minutes.do(self.report_health_for_module, module_id="digital_channels")
        schedule.every(10).minutes.do(self.report_health_for_module, module_id="risk_compliance")
        schedule.every(10).minutes.do(self.report_health_for_module, module_id="treasury")
        
        # Also schedule a full report every 15 minutes
        schedule.every(15).minutes.do(self.report_health_for_all_modules)
        
        logger.info("Health reporting scheduler started")
        
        # Run the scheduler
        while True:
            schedule.run_pending()
            time.sleep(1)


def start_health_reporting_scheduler():
    """Start the health reporting scheduler."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create and start the scheduler
    scheduler = HealthReportingScheduler()
    
    # Run an initial health report for all modules
    scheduler.report_health_for_all_modules()
    
    # Start the scheduler in a background thread
    thread = threading.Thread(target=scheduler.start_scheduler, daemon=True)
    thread.start()
    
    logger.info("Health reporting scheduler started in background thread")
    return scheduler, thread


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Start the scheduler
    scheduler, thread = start_health_reporting_scheduler()
    
    # Keep the main thread running
    try:
        while thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Health reporting scheduler stopped by user")
