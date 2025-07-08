"""
Transaction Monitoring System for Fraud Detection

This module monitors transactions in real-time to detect and flag
potentially fraudulent activities based on transaction patterns.
"""

import time
import logging
import datetime
from typing import Dict, Any, List, Optional, Set, Union
import threading
import queue
import os
import sys

# Add current directory to path to ensure local imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)  # Add the missing code block here

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


# Import fraud_detection from local module (using relative import)
from .fraud_detection_system import fraud_detection

# Initialize logger
logger = logging.getLogger(__name__)


class TransactionMonitor:
    """
    Real-time transaction monitoring system that works alongside 
    the main fraud detection system to provide continuous monitoring.
    """
    
    def __init__(self):
        """Initialize the transaction monitoring system"""
        self.is_running = False
        self.processing_queue = queue.Queue()
        self.monitor_thread = None
        self.alert_handlers = []
        
        # Stats tracking
        self.stats = {
            "transactions_processed": 0,
            "alerts_generated": 0,
            "monitoring_start_time": None,
            "high_risk_transactions": 0,
            "transaction_volume_by_hour": {}
        }
        
        logger.info("Transaction Monitor initialized")
    
    def start_monitoring(self):
        """Start the transaction monitoring process"""
        if self.is_running:
            logger.warning("Transaction monitor is already running")
            return False
        
        self.is_running = True
        self.stats["monitoring_start_time"] = time.time()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitoring_worker,
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("Transaction monitoring started")
        return True
    
    def stop_monitoring(self):
        """Stop the transaction monitoring process"""
        if not self.is_running:
            logger.warning("Transaction monitor is not running")
            return False
        
        self.is_running = False
        
        # Wait for thread to finish
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        logger.info("Transaction monitoring stopped")
        return True
    
    def submit_transaction(self, transaction_data: Dict[str, Any]):
        """
        Submit a transaction for monitoring
        
        Args:
            transaction_data (Dict): Transaction details
        """
        if not self.is_running:
            logger.warning("Transaction monitor is not running - starting now")
            self.start_monitoring()
        
        # Add timestamp if not present
        if "timestamp" not in transaction_data:
            transaction_data["timestamp"] = time.time()
        
        # Add to processing queue
        self.processing_queue.put(transaction_data)
    
    def register_alert_handler(self, handler_func):
        """
        Register a function to be called when alerts are generated
        
        Args:
            handler_func: Function taking an alert dictionary as parameter
        """
        self.alert_handlers.append(handler_func)
        logger.debug(f"Alert handler registered: {handler_func.__name__}")
    
    def _monitoring_worker(self):
        """Worker thread for processing transactions"""
        logger.info("Transaction monitoring worker started")
        
        while self.is_running:
            try:
                # Get transaction from queue with timeout
                try:
                    transaction = self.processing_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process the transaction
                self._process_transaction(transaction)
                
                # Mark task as done
                self.processing_queue.task_done()
            
            except Exception as e:
                logger.error(f"Error in transaction monitoring worker: {str(e)}")
        
        logger.info("Transaction monitoring worker stopped")
    
    def _process_transaction(self, transaction: Dict[str, Any]):
        """Process a transaction and check for suspicious activity"""
        # Update stats
        self.stats["transactions_processed"] += 1
        
        # Track transaction volume by hour
        transaction_hour = datetime.datetime.fromtimestamp(
            transaction.get("timestamp", time.time())
        ).strftime("%Y-%m-%d %H:00")
        
        if transaction_hour not in self.stats["transaction_volume_by_hour"]:
            self.stats["transaction_volume_by_hour"][transaction_hour] = 0
        self.stats["transaction_volume_by_hour"][transaction_hour] += 1
        
        # Check for fraud using fraud detection system
        result = fraud_detection.check_transaction(transaction)
        
        # Handle the result
        if result["is_suspicious"]:
            self._handle_suspicious_transaction(transaction, result)
    
    def _handle_suspicious_transaction(self, transaction: Dict[str, Any], 
                                     fraud_result: Dict[str, Any]):
        """Handle a transaction flagged as suspicious"""
        # Update high risk stats
        if fraud_result["risk_score"] >= 70:
            self.stats["high_risk_transactions"] += 1
        
        # Generate alert
        alert = self._generate_alert(transaction, fraud_result)
        
        # Update alert stats
        self.stats["alerts_generated"] += 1
        
        # Send alert to registered handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler {handler.__name__}: {str(e)}")
    
    def _generate_alert(self, transaction: Dict[str, Any], 
                       fraud_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a standardized alert from transaction and fraud result"""
        user_id = transaction.get("user_id", "unknown")
        amount = transaction.get("amount", 0)
        
        return {
            "alert_id": f"FD-{int(time.time())}-{self.stats['alerts_generated']}",
            "timestamp": time.time(),
            "alert_type": "SUSPICIOUS_TRANSACTION",
            "severity": self._get_severity(fraud_result["risk_score"]),
            "user_id": user_id,
            "transaction_id": transaction.get("transaction_id", "unknown"),
            "amount": amount,
            "currency": transaction.get("currency", "INR"),
            "risk_score": fraud_result["risk_score"],
            "risk_factors": fraud_result["risk_factors"],
            "recommended_action": fraud_result["action"],
            "transaction_details": {
                "type": transaction.get("transaction_type", "unknown"),
                "channel": transaction.get("channel", "unknown"),
                "recipient_id": transaction.get("recipient_id", "unknown"),
                "timestamp": transaction.get("timestamp", time.time())
            }
        }
    
    def _get_severity(self, risk_score: float) -> str:
        """Convert risk score to severity level"""
        if risk_score >= 80:
            return "CRITICAL"
        elif risk_score >= 60:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        # Calculate additional stats
        stats = self.stats.copy()
        
        # Calculate uptime if monitoring is active
        if stats["monitoring_start_time"]:
            stats["uptime_seconds"] = time.time() - stats["monitoring_start_time"]
        else:
            stats["uptime_seconds"] = 0
        
        # Calculate transactions per second
        if stats["uptime_seconds"] > 0:
            stats["transactions_per_second"] = (
                stats["transactions_processed"] / stats["uptime_seconds"]
            )
        else:
            stats["transactions_per_second"] = 0
        
        # Calculate alert rate
        if stats["transactions_processed"] > 0:
            stats["alert_rate_percent"] = (
                (stats["alerts_generated"] / stats["transactions_processed"]) * 100
            )
        else:
            stats["alert_rate_percent"] = 0
        
        # Add current queue size
        stats["queue_size"] = self.processing_queue.qsize()
        
        # Add current status
        stats["is_running"] = self.is_running
        
        return stats


# Create a singleton instance
transaction_monitor = TransactionMonitor()

# Export main functions for easy access
start_monitoring = transaction_monitor.start_monitoring
stop_monitoring = transaction_monitor.stop_monitoring
submit_transaction = transaction_monitor.submit_transaction
register_alert_handler = transaction_monitor.register_alert_handler
get_monitoring_stats = transaction_monitor.get_stats

# Sample alert handler implementation
def log_alert_to_file(alert):
    """Sample alert handler that logs to file"""
    logger.warning(
        f"FRAUD ALERT: {alert['severity']} risk (score: {alert['risk_score']}) "
        f"for user {alert['user_id']} - {', '.join(alert['risk_factors'])}"
    )

# Register the sample handler
register_alert_handler(log_alert_to_file)