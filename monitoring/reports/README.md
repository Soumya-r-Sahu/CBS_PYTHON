# Performance metrics and system health reports

"""
This folder is for storing system monitoring reports and report utilities.

How to Implement:
- Use the provided `report_utils.py` to generate and save monitoring reports in Markdown format.
- Example usage:

```python
from monitoring.reports.report_utils import generate_report, save_report
report = generate_report('System running smoothly', '99.99%', 0, 120)
save_report(report, 'monitoring/reports/reports.md')
```

Schema Example:
- Each report should include: report_date, summary, key metrics (uptime, errors, usage).

Sample Report (Markdown):
# Monitoring Report - 2025-05-12
- Uptime: 99.99%
- Errors: 0
- Active Users: 120
- Summary: System running smoothly
"""
