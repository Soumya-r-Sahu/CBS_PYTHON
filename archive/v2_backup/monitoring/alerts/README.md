# System alerts

"""
This folder is for storing system alerts and alert utilities for the monitoring subsystem.

How to Implement:
- Use the provided `alert_utils.py` to create and save alerts in JSON format.
- Example usage:

```python
from monitoring.alerts.alert_utils import create_alert, save_alert
alert = create_alert('HIGH_CPU', 'CRITICAL', 'CPU usage exceeded 90%')
save_alert(alert, 'monitoring/alerts/alerts.json')
```

Schema Example:
- Each alert should include: timestamp, alert_type, severity, description, resolved (bool).

Sample Alert (JSON):
{
  "timestamp": "2025-05-12T10:00:00Z",
  "alert_type": "HIGH_CPU",
  "severity": "CRITICAL",
  "description": "CPU usage exceeded 90%",
  "resolved": false
}
"""
