"""
Analytics and BI Configuration Module

This module contains configuration settings for the Analytics & BI system.
"""

import os
from pathlib import Path

# Use centralized import system
from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment
fix_path()  # Ensures the project root is in sys.path


# Try importing from main config
try:
    from config import DATABASE_CONFIG, ANALYTICS_CONFIG
    
    # Extract Analytics specific configuration
    ANALYTICS_SETTINGS = ANALYTICS_CONFIG if 'ANALYTICS_CONFIG' in locals() else {}
    
except ImportError:
    # Default configuration
    ANALYTICS_SETTINGS = {
        'data_refresh_interval_hours': 24,
        'historical_data_retention_days': 1095,  # 3 years
        'cache_enabled': True,
        'reporting_output_formats': ['PDF', 'XLSX', 'CSV']
    }
    
    DATABASE_CONFIG = {
        'host': 'localhost',
        'database': 'CBS_PYTHON',
        'user': 'root',
        'password': '',
        'port': 3307,
    }

# Dashboard settings
DASHBOARD_SETTINGS = {
    'refresh_interval_seconds': 300,
    'default_timespan_days': 30,
    'cache_timeout_minutes': 60,
    'allowed_visualization_types': ['line', 'bar', 'pie', 'table', 'gauge', 'scatter', 'heatmap']
}

# Performance reports settings
REPORT_SETTINGS = {
    'scheduled_report_path': str(Path(__file__).parent / 'performance-reports' / 'scheduled'),
    'on_demand_report_path': str(Path(__file__).parent / 'performance-reports' / 'on-demand'),
    'report_formats': ['pdf', 'xlsx', 'csv'],
    'default_report_format': 'xlsx'
}

# Predictive model settings
MODEL_SETTINGS = {
    'model_path': str(Path(__file__).parent / 'predictive-models' / 'trained-models'),
    'training_data_path': str(Path(__file__).parent / 'predictive-models' / 'training-data'),
    'retrain_frequency_days': 30,
    'minimum_training_samples': 1000,
    'validation_split_ratio': 0.2
}