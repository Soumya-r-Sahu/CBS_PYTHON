"""
Health Check Monitoring Service

This module provides a health check monitoring service that periodically collects
health metrics from all registered modules and sends alerts when issues are detected.
"""
import os
import sys
import logging
import time
import json
import threading
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Add the parent directory to sys.path to import the integration interfaces
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from integration_interfaces.api.admin_client import AdminIntegrationClient

logger = logging.getLogger(__name__)

class HealthCheckMonitor:
    """Health check monitoring service for all CBS modules."""
    
    def __init__(self, admin_base_url: str = None, api_key: str = None):
        """
        Initialize the health check monitor.
        
        Args:
            admin_base_url: Base URL of the Admin module API
            api_key: API key for authentication with the Admin module
        """
        self.admin_base_url = admin_base_url or os.environ.get("CBS_ADMIN_BASE_URL", "http://localhost:8000/api/admin")
        self.api_key = api_key or os.environ.get("CBS_ADMIN_API_KEY")
        
        if not self.api_key:
            logger.warning("No API key provided for health check monitor. Authentication will fail.")
        
        self.admin_client = AdminIntegrationClient(
            admin_base_url=self.admin_base_url,
            module_id="health_check_monitor",
            api_key=self.api_key
        )
        
        self.modules = {}
        self.health_history = {}
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 80.0,
            "response_time": 5.0  # seconds
        }
        
        # Alert status to avoid repeated alerts
        self.alert_status = {}
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers including authentication."""
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key,
            "X-Module-ID": "health_check_monitor"
        }
    
    def get_registered_modules(self) -> Dict[str, Any]:
        """
        Get all registered modules from the Admin module.
        
        Returns:
            Dictionary of module information keyed by module ID
        """
        url = f"{self.admin_base_url}/modules"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers()
            )
            response.raise_for_status()
            modules_data = response.json()
            
            # Update the modules dictionary
            self.modules = {module["id"]: module for module in modules_data.get("modules", [])}
            
            return self.modules
        except Exception as e:
            logger.error(f"Failed to get registered modules: {e}")
            return {}
    
    def check_module_health(self, module_id: str) -> Dict[str, Any]:
        """
        Check the health of a specific module.
        
        Args:
            module_id: ID of the module to check
            
        Returns:
            Dictionary with health check results
        """
        url = f"{self.admin_base_url}/modules/{module_id}/health"
        
        try:
            start_time = time.time()
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=10
            )
            response_time = time.time() - start_time
            
            response.raise_for_status()
            health_data = response.json()
            
            # Add response time to metrics
            if "metrics" in health_data:
                health_data["metrics"]["response_time"] = response_time
            
            # Store in health history
            if module_id not in self.health_history:
                self.health_history[module_id] = []
            
            # Keep only the last 100 health checks
            if len(self.health_history[module_id]) >= 100:
                self.health_history[module_id].pop(0)
            
            self.health_history[module_id].append({
                "timestamp": datetime.utcnow().isoformat(),
                "data": health_data
            })
            
            return health_data
        except Exception as e:
            logger.error(f"Failed to check health for module {module_id}: {e}")
            return {
                "status": "unknown",
                "metrics": {"response_time": None},
                "details": {"message": f"Failed to check health: {str(e)}"},
                "alerts": [f"Health check failed: {str(e)}"],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def check_all_modules_health(self) -> Dict[str, Dict[str, Any]]:
        """
        Check the health of all registered modules.
        
        Returns:
            Dictionary of health check results keyed by module ID
        """
        # Refresh modules list if empty
        if not self.modules:
            self.get_registered_modules()
        
        health_results = {}
        
        for module_id in self.modules:
            health_results[module_id] = self.check_module_health(module_id)
        
        return health_results
    
    def analyze_health_trends(self, module_id: str, window_size: int = 10) -> Dict[str, Any]:
        """
        Analyze health trends for a specific module.
        
        Args:
            module_id: ID of the module to analyze
            window_size: Number of recent health checks to analyze
            
        Returns:
            Dictionary with trend analysis results
        """
        if module_id not in self.health_history or len(self.health_history[module_id]) < 2:
            return {"status": "insufficient_data"}
        
        # Get the most recent health checks up to window_size
        recent_checks = self.health_history[module_id][-window_size:]
        
        # Extract metrics for trend analysis
        cpu_trend = []
        memory_trend = []
        response_time_trend = []
        status_trend = []
        
        for check in recent_checks:
            data = check["data"]
            metrics = data.get("metrics", {})
            
            if "cpu_percent" in metrics:
                cpu_trend.append(metrics["cpu_percent"])
            
            if "memory_percent" in metrics:
                memory_trend.append(metrics["memory_percent"])
            
            if "response_time" in metrics and metrics["response_time"] is not None:
                response_time_trend.append(metrics["response_time"])
            
            status_trend.append(data.get("status", "unknown"))
        
        # Calculate trends (simple linear trend: increasing, decreasing, stable)
        trends = {}
        
        if len(cpu_trend) >= 2:
            cpu_change = cpu_trend[-1] - cpu_trend[0]
            if abs(cpu_change) < 5:
                trends["cpu"] = "stable"
            elif cpu_change > 0:
                trends["cpu"] = "increasing"
            else:
                trends["cpu"] = "decreasing"
        
        if len(memory_trend) >= 2:
            memory_change = memory_trend[-1] - memory_trend[0]
            if abs(memory_change) < 5:
                trends["memory"] = "stable"
            elif memory_change > 0:
                trends["memory"] = "increasing"
            else:
                trends["memory"] = "decreasing"
        
        if len(response_time_trend) >= 2:
            response_time_change = response_time_trend[-1] - response_time_trend[0]
            if abs(response_time_change) < 0.5:
                trends["response_time"] = "stable"
            elif response_time_change > 0:
                trends["response_time"] = "increasing"
            else:
                trends["response_time"] = "decreasing"
        
        # Analyze status stability
        status_changes = sum(1 for i in range(1, len(status_trend)) if status_trend[i] != status_trend[i-1])
        if status_changes == 0:
            trends["status_stability"] = "stable"
        elif status_changes <= 2:
            trends["status_stability"] = "occasional_changes"
        else:
            trends["status_stability"] = "frequent_changes"
        
        # Latest values
        latest = {}
        if cpu_trend:
            latest["cpu_percent"] = cpu_trend[-1]
        if memory_trend:
            latest["memory_percent"] = memory_trend[-1]
        if response_time_trend:
            latest["response_time"] = response_time_trend[-1]
        if status_trend:
            latest["status"] = status_trend[-1]
        
        return {
            "trends": trends,
            "latest": latest,
            "window_size": len(recent_checks)
        }
    
    def check_thresholds_and_alert(self, health_data: Dict[str, Any], module_id: str) -> List[str]:
        """
        Check health metrics against thresholds and generate alerts.
        
        Args:
            health_data: Health check data for a module
            module_id: ID of the module
            
        Returns:
            List of alert messages
        """
        alerts = []
        metrics = health_data.get("metrics", {})
        status = health_data.get("status", "unknown")
        
        # Initialize alert status if not exists
        if module_id not in self.alert_status:
            self.alert_status[module_id] = {}
        
        # Check module status
        if status == "critical" and self.alert_status.get(module_id, {}).get("status") != "critical":
            alerts.append(f"Module {module_id} is in CRITICAL state")
            self.alert_status[module_id]["status"] = "critical"
        elif status == "warning" and self.alert_status.get(module_id, {}).get("status") != "warning":
            alerts.append(f"Module {module_id} is in WARNING state")
            self.alert_status[module_id]["status"] = "warning"
        elif status == "healthy":
            self.alert_status[module_id]["status"] = "healthy"
        
        # Check CPU usage
        if "cpu_percent" in metrics and metrics["cpu_percent"] is not None:
            if metrics["cpu_percent"] > self.alert_thresholds["cpu_percent"] and not self.alert_status.get(module_id, {}).get("cpu_alert"):
                alerts.append(f"Module {module_id} CPU usage is high: {metrics['cpu_percent']}%")
                self.alert_status[module_id]["cpu_alert"] = True
            elif metrics["cpu_percent"] <= self.alert_thresholds["cpu_percent"]:
                self.alert_status[module_id]["cpu_alert"] = False
        
        # Check memory usage
        if "memory_percent" in metrics and metrics["memory_percent"] is not None:
            if metrics["memory_percent"] > self.alert_thresholds["memory_percent"] and not self.alert_status.get(module_id, {}).get("memory_alert"):
                alerts.append(f"Module {module_id} memory usage is high: {metrics['memory_percent']}%")
                self.alert_status[module_id]["memory_alert"] = True
            elif metrics["memory_percent"] <= self.alert_thresholds["memory_percent"]:
                self.alert_status[module_id]["memory_alert"] = False
        
        # Check response time
        if "response_time" in metrics and metrics["response_time"] is not None:
            if metrics["response_time"] > self.alert_thresholds["response_time"] and not self.alert_status.get(module_id, {}).get("response_time_alert"):
                alerts.append(f"Module {module_id} response time is slow: {metrics['response_time']:.2f}s")
                self.alert_status[module_id]["response_time_alert"] = True
            elif metrics["response_time"] <= self.alert_thresholds["response_time"]:
                self.alert_status[module_id]["response_time_alert"] = False
        
        # Include any alerts from the module itself
        if "alerts" in health_data and health_data["alerts"]:
            for alert in health_data["alerts"]:
                alert_key = f"module_alert_{hash(alert)}"
                if not self.alert_status.get(module_id, {}).get(alert_key):
                    alerts.append(f"Module {module_id} alert: {alert}")
                    self.alert_status[module_id][alert_key] = True
        
        return alerts
    
    def send_alerts(self, alerts: List[str]) -> None:
        """
        Send alerts through configured channels.
        
        Args:
            alerts: List of alert messages to send
        """
        if not alerts:
            return
        
        # Log alerts
        for alert in alerts:
            logger.warning(f"HEALTH ALERT: {alert}")
        
        # In a real implementation, this would send alerts through various channels:
        # - Email
        # - SMS
        # - Slack/Microsoft Teams
        # - Monitoring systems (like Nagios, Prometheus Alertmanager, etc.)
        
        # For now, we just send them to the Admin module
        try:
            url = f"{self.admin_base_url}/alerts"
            requests.post(
                url,
                headers=self._get_headers(),
                json={
                    "source": "health_check_monitor",
                    "alerts": alerts,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Failed to send alerts to Admin module: {e}")
    
    def run_scheduled_check(self) -> None:
        """Run a scheduled health check for all modules."""
        logger.info("Running scheduled health check for all modules")
        
        try:
            health_results = self.check_all_modules_health()
            
            all_alerts = []
            for module_id, health_data in health_results.items():
                # Check thresholds and generate alerts
                module_alerts = self.check_thresholds_and_alert(health_data, module_id)
                all_alerts.extend(module_alerts)
                
                # Analyze trends
                trend_analysis = self.analyze_health_trends(module_id)
                
                # If there's a concerning trend, add an alert
                trends = trend_analysis.get("trends", {})
                if trends.get("cpu") == "increasing" and trends.get("memory") == "increasing":
                    all_alerts.append(f"Module {module_id} shows increasing resource usage trend")
                
                if trends.get("response_time") == "increasing":
                    all_alerts.append(f"Module {module_id} shows increasing response time trend")
                
                if trends.get("status_stability") == "frequent_changes":
                    all_alerts.append(f"Module {module_id} has unstable health status")
            
            # Send all accumulated alerts
            if all_alerts:
                self.send_alerts(all_alerts)
            
            logger.info("Scheduled health check completed")
        except Exception as e:
            logger.error(f"Error in scheduled health check: {e}")
    
    def start_monitoring(self, interval_seconds: int = 300) -> threading.Thread:
        """
        Start the health monitoring service in a background thread.
        
        Args:
            interval_seconds: Interval between health checks in seconds
            
        Returns:
            The background thread running the monitoring service
        """
        def monitoring_thread():
            logger.info(f"Health check monitoring started with interval of {interval_seconds} seconds")
            while True:
                try:
                    self.run_scheduled_check()
                except Exception as e:
                    logger.error(f"Error in monitoring thread: {e}")
                
                # Sleep until next check
                time.sleep(interval_seconds)
        
        thread = threading.Thread(target=monitoring_thread, daemon=True)
        thread.start()
        return thread


def start_health_monitoring(interval_seconds: int = 300):
    """
    Start the health monitoring service.
    
    Args:
        interval_seconds: Interval between health checks in seconds
    """
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create and start the health monitor
    monitor = HealthCheckMonitor()
    
    # Initial check to get all modules
    monitor.get_registered_modules()
    
    # Start monitoring in a background thread
    monitor_thread = monitor.start_monitoring(interval_seconds)
    
    logger.info(f"Health monitoring service started with interval of {interval_seconds} seconds")
    return monitor, monitor_thread


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Health Check Monitoring Service")
    parser.add_argument("--interval", type=int, default=300, help="Interval between health checks in seconds")
    args = parser.parse_args()
    
    # Start monitoring
    monitor, thread = start_health_monitoring(args.interval)
    
    # Keep the main thread running
    try:
        while thread.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Health monitoring service stopped by user")
