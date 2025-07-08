"""
Monitoring report utilities for the Core Banking System.

This module provides functions to generate and save monitoring reports.
"""
from datetime import datetime

def generate_report(summary, uptime, errors, active_users):
    """Generate a monitoring report as a dictionary."""
    return {
        "report_date": datetime.utcnow().strftime('%Y-%m-%d'),
        "summary": summary,
        "uptime": uptime,
        "errors": errors,
        "active_users": active_users
    }

def save_report(report, path):
    """Save a report to a Markdown file."""
    with open(path, 'a') as f:
        f.write(f"# Monitoring Report - {report['report_date']}\n")
        f.write(f"- Uptime: {report['uptime']}\n")
        f.write(f"- Errors: {report['errors']}\n")
        f.write(f"- Active Users: {report['active_users']}\n")
        f.write(f"- Summary: {report['summary']}\n\n")
