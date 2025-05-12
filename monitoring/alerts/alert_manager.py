"""
System monitoring and alert manager for the Core Banking System
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

class SystemAlert:
    def __init__(self, alerts_dir="monitoring/alerts"):
        self.alerts_dir = alerts_dir
        os.makedirs(alerts_dir, exist_ok=True)
        
    def create_alert(self, alert_type: str, severity: str, message: str, 
                     source: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create and save a system alert
        
        Parameters:
        - alert_type: Type of alert (e.g., 'security', 'performance', 'availability')
        - severity: Severity level ('critical', 'high', 'medium', 'low')
        - message: Alert message description
        - source: Component that generated the alert
        - details: Additional alert details
        """
        alert = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "type": alert_type,
            "severity": severity,
            "message": message,
            "source": source,
            "details": details or {},
            "status": "active",
            "alert_id": f"{alert_type}_{int(datetime.utcnow().timestamp())}"
        }
        
        # Save alert to file
        alert_file = f"{self.alerts_dir}/alerts.json"
        
        # Append or create alerts file
        if os.path.exists(alert_file):
            with open(alert_file, 'r') as f:
                try:
                    alerts = json.load(f)
                except json.JSONDecodeError:
                    alerts = {"alerts": []}
        else:
            alerts = {"alerts": []}
            
        alerts["alerts"].append(alert)
        
        with open(alert_file, 'w') as f:
            json.dump(alerts, f, indent=2)
        
        # For critical alerts, create a separate file for immediate attention
        if severity == "critical":
            critical_file = f"{self.alerts_dir}/critical_{alert['alert_id']}.json"
            with open(critical_file, 'w') as f:
                json.dump(alert, f, indent=2)
        
        return alert
    
    def get_active_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active alerts, optionally filtered by severity"""
        alert_file = f"{self.alerts_dir}/alerts.json"
        
        if not os.path.exists(alert_file):
            return []
        
        with open(alert_file, 'r') as f:
            try:
                alerts = json.load(f)
            except json.JSONDecodeError:
                return []
        
        active_alerts = [a for a in alerts.get("alerts", []) if a["status"] == "active"]
        
        if severity:
            active_alerts = [a for a in active_alerts if a["severity"] == severity]
            
        return active_alerts
    
    def resolve_alert(self, alert_id: str, resolution_notes: str) -> bool:
        """Mark an alert as resolved"""
        alert_file = f"{self.alerts_dir}/alerts.json"
        
        if not os.path.exists(alert_file):
            return False
        
        with open(alert_file, 'r') as f:
            try:
                alerts = json.load(f)
            except json.JSONDecodeError:
                return False
        
        resolved = False
        for alert in alerts.get("alerts", []):
            if alert.get("alert_id") == alert_id and alert["status"] == "active":
                alert["status"] = "resolved"
                alert["resolution_timestamp"] = datetime.utcnow().isoformat() + "Z"
                alert["resolution_notes"] = resolution_notes
                resolved = True
        
        if resolved:
            with open(alert_file, 'w') as f:
                json.dump(alerts, f, indent=2)
            
            # Remove critical alert file if it exists
            critical_file = f"{self.alerts_dir}/critical_{alert_id}.json"
            if os.path.exists(critical_file):
                os.remove(critical_file)
                
        return resolved

if __name__ == "__main__":
    # Example usage
    alert_system = SystemAlert()
    
    # Create sample alerts
    alert1 = alert_system.create_alert(
        alert_type="security",
        severity="high",
        message="Multiple failed login attempts detected",
        source="auth_service",
        details={"ip_address": "192.168.1.100", "attempts": 5}
    )
    
    alert2 = alert_system.create_alert(
        alert_type="performance",
        severity="medium",
        message="Database response time exceeds threshold",
        source="db_monitor",
        details={"response_time_ms": 1200, "threshold_ms": 1000}
    )
    
    print(f"Created alerts with IDs: {alert1['alert_id']} and {alert2['alert_id']}")
    
    # Get active alerts
    active_alerts = alert_system.get_active_alerts()
    print(f"Active alerts: {len(active_alerts)}")
    
    # Resolve one alert
    resolved = alert_system.resolve_alert(
        alert1["alert_id"], 
        "IP was added to whitelist after verification"
    )
    print(f"Alert {alert1['alert_id']} resolved: {resolved}")
    
    # Check remaining active alerts
    active_alerts = alert_system.get_active_alerts()
    print(f"Remaining active alerts: {len(active_alerts)}")
