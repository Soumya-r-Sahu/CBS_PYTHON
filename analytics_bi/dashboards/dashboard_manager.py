"""
Dashboard Module for Analytics and BI

This module handles the creation and management of interactive dashboards
for business intelligence and analytics.
"""

import os
import sys
from pathlib import Path
import logging
import datetime
import json
from typing import Dict, List, Any, Optional, Union

# Use relative imports instead of modifying sys.path
# Import Analytics modules
from ..config import DASHBOARD_SETTINGS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('analytics-dashboards')

class DashboardManager:
    """Dashboard manager for creating and rendering business intelligence dashboards"""
    
    def __init__(self):
        """Initialize the dashboard manager"""
        self.dashboards = {}
        self.cache = {}
        self.cache_timestamps = {}
        self._load_dashboard_definitions()
    
    def _load_dashboard_definitions(self):
        """Load dashboard definitions from configuration files"""
        try:
            dashboard_dir = Path(__file__).parent / "definitions"
            
            if not dashboard_dir.exists():
                dashboard_dir.mkdir(parents=True)
                logger.info(f"Created dashboard definitions directory: {dashboard_dir}")
                return
            
            for file in dashboard_dir.glob("*.json"):
                try:
                    with open(file, 'r') as f:
                        dashboard_def = json.load(f)
                        dashboard_id = dashboard_def.get('id', file.stem)
                        self.dashboards[dashboard_id] = dashboard_def
                        logger.info(f"Loaded dashboard definition: {dashboard_id}")
                except Exception as e:
                    logger.error(f"Error loading dashboard definition {file}: {e}")
        
        except Exception as e:
            logger.error(f"Error loading dashboard definitions: {e}")
    
    def get_dashboard_data(self, dashboard_id: str, 
                          params: Optional[Dict[str, Any]] = None,
                          force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get data for a specific dashboard
        
        Args:
            dashboard_id: Dashboard identifier
            params: Optional parameters for dashboard (filters, time ranges)
            force_refresh: Whether to force a data refresh
            
        Returns:
            Dashboard data including metrics and visualization data
        """
        # Check if we can use cached data
        cache_key = f"{dashboard_id}_{json.dumps(params) if params else 'default'}"
        
        if (not force_refresh and 
            DASHBOARD_SETTINGS['cache_enabled'] and
            cache_key in self.cache and
            cache_key in self.cache_timestamps):
            
            # Check if cache is still valid
            cache_age = datetime.datetime.now() - self.cache_timestamps[cache_key]
            if cache_age.total_seconds() < DASHBOARD_SETTINGS['refresh_interval_seconds']:
                logger.info(f"Returning cached data for dashboard {dashboard_id}")
                return self.cache[cache_key]
        
        # Get dashboard definition
        dashboard_def = self.dashboards.get(dashboard_id)
        if not dashboard_def:
            logger.warning(f"Dashboard {dashboard_id} not found")
            return {"error": f"Dashboard {dashboard_id} not found"}
        
        # Generate dashboard data
        try:
            dashboard_data = self._generate_dashboard_data(dashboard_def, params)
            
            # Cache the result
            self.cache[cache_key] = dashboard_data
            self.cache_timestamps[cache_key] = datetime.datetime.now()
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating data for dashboard {dashboard_id}: {e}")
            return {"error": f"Failed to generate dashboard data: {str(e)}"}
    
    def _generate_dashboard_data(self, dashboard_def: Dict[str, Any], 
                               params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate data for a dashboard based on its definition
        
        Args:
            dashboard_def: Dashboard definition
            params: Optional parameters
            
        Returns:
            Dashboard data
        """
        result = {
            "id": dashboard_def.get('id', ''),
            "title": dashboard_def.get('title', ''),
            "description": dashboard_def.get('description', ''),
            "last_updated": datetime.datetime.now().isoformat(),
            "panels": []
        }
        
        # Process each panel in the dashboard
        for panel_def in dashboard_def.get('panels', []):
            panel_data = self._generate_panel_data(panel_def, params)
            result['panels'].append(panel_data)
        
        return result
    
    def _generate_panel_data(self, panel_def: Dict[str, Any], 
                           params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate data for a single dashboard panel
        
        Args:
            panel_def: Panel definition
            params: Optional parameters
            
        Returns:
            Panel data
        """
        panel_type = panel_def.get('type', 'unknown')
        panel_id = panel_def.get('id', '')
        
        panel_result = {
            "id": panel_id,
            "title": panel_def.get('title', ''),
            "type": panel_type,
            "data": [],
            "metadata": panel_def.get('metadata', {})
        }
        
        try:
            # Get data source information
            data_source = panel_def.get('dataSource', {})
            source_type = data_source.get('type', 'sql')
            
            # Generate data based on source type
            if source_type == 'sql':
                panel_result['data'] = self._execute_sql_query(data_source.get('query', ''), params)
            elif source_type == 'api':
                panel_result['data'] = self._fetch_api_data(data_source.get('endpoint', ''), params)
            elif source_type == 'file':
                panel_result['data'] = self._read_data_file(data_source.get('path', ''))
            elif source_type == 'static':
                panel_result['data'] = data_source.get('data', [])
            else:
                logger.warning(f"Unknown data source type: {source_type} for panel {panel_id}")
                panel_result['data'] = []
                
        except Exception as e:
            logger.error(f"Error generating data for panel {panel_id}: {e}")
            panel_result['error'] = str(e)
            panel_result['data'] = []
        
        return panel_result
    
    def _execute_sql_query(self, query: str, 
                         params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results
        
        Args:
            query: SQL query template
            params: Optional parameters
            
        Returns:
            Query results
        """        
        try:
            # Import database connection using centralized import manager
            from utils.lib.packages import fix_path, import_module
            fix_path()
            DatabaseConnection = import_module("database.python.connection").DatabaseConnection
            
            # Format query with parameters if needed
            formatted_query = query
            if params:
                # Simple parameter substitution (in real implementation, use proper SQL parameter binding)
                for key, value in params.items():
                    placeholder = f"{{${key}}}"
                    if placeholder in formatted_query:
                        formatted_query = formatted_query.replace(placeholder, str(value))
            
            # Execute query
            db_connection = DatabaseConnection()
            conn = db_connection.get_connection()
            
            if not conn:
                logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute(formatted_query)
            results = cursor.fetchall()
            cursor.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}")
            return []
    
    def _fetch_api_data(self, endpoint: str, 
                      params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Fetch data from an API endpoint
        
        Args:
            endpoint: API endpoint
            params: Optional parameters
            
        Returns:
            API response data
        """
        try:
            import requests
            
            # Add parameters to request if provided
            request_params = params or {}
            
            response = requests.get(endpoint, params=request_params, timeout=30)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching API data from {endpoint}: {e}")
            return []
    
    def _read_data_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Read data from a file
        
        Args:
            file_path: Path to data file
            
        Returns:
            File data
        """
        try:
            # Handle relative paths
            if not os.path.isabs(file_path):
                file_path = os.path.join(Path(__file__).parent.parent, file_path)
                
            # Get file extension
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.json':
                with open(file_path, 'r') as f:
                    return json.load(f)
            elif ext == '.csv':
                import pandas as pd
                df = pd.read_csv(file_path)
                return df.to_dict('records')
            elif ext == '.xlsx':
                import pandas as pd
                df = pd.read_excel(file_path)
                return df.to_dict('records')
            else:
                logger.warning(f"Unsupported file type: {ext}")
                return []
                
        except Exception as e:
            logger.error(f"Error reading data file {file_path}: {e}")
            return []
    
    def list_available_dashboards(self) -> List[Dict[str, Any]]:
        """
        Get list of all available dashboards
        
        Returns:
            List of dashboard metadata
        """
        result = []
        
        for dashboard_id, dashboard in self.dashboards.items():
            result.append({
                "id": dashboard_id,
                "title": dashboard.get('title', ''),
                "description": dashboard.get('description', ''),
                "category": dashboard.get('category', 'General'),
                "panels_count": len(dashboard.get('panels', [])),
                "created_by": dashboard.get('created_by', 'System'),
                "last_modified": dashboard.get('last_modified', '')
            })
        
        return result
    
    def create_dashboard(self, dashboard_def: Dict[str, Any]) -> bool:
        """
        Create a new dashboard
        
        Args:
            dashboard_def: Dashboard definition
            
        Returns:
            True if successful, False otherwise
        """
        try:
            dashboard_id = dashboard_def.get('id')
            if not dashboard_id:
                dashboard_id = f"dashboard_{len(self.dashboards) + 1}"
                dashboard_def['id'] = dashboard_id
            
            # Add creation timestamp
            dashboard_def['created'] = datetime.datetime.now().isoformat()
            dashboard_def['last_modified'] = dashboard_def['created']
            
            # Save dashboard definition
            dashboard_dir = Path(__file__).parent / "definitions"
            if not dashboard_dir.exists():
                dashboard_dir.mkdir(parents=True)
                
            file_path = dashboard_dir / f"{dashboard_id}.json"
            with open(file_path, 'w') as f:
                json.dump(dashboard_def, f, indent=2)
            
            # Add to in-memory collection
            self.dashboards[dashboard_id] = dashboard_def
            
            logger.info(f"Created new dashboard: {dashboard_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            return False
    
    def update_dashboard(self, dashboard_id: str, 
                       dashboard_def: Dict[str, Any]) -> bool:
        """
        Update an existing dashboard
        
        Args:
            dashboard_id: Dashboard ID
            dashboard_def: Updated dashboard definition
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if dashboard exists
            if dashboard_id not in self.dashboards:
                logger.warning(f"Dashboard {dashboard_id} not found")
                return False
            
            # Update timestamp
            dashboard_def['last_modified'] = datetime.datetime.now().isoformat()
            
            # Preserve creation date
            if 'created' in self.dashboards[dashboard_id]:
                dashboard_def['created'] = self.dashboards[dashboard_id]['created']
            
            # Save updated dashboard definition
            dashboard_dir = Path(__file__).parent / "definitions"
            file_path = dashboard_dir / f"{dashboard_id}.json"
            with open(file_path, 'w') as f:
                json.dump(dashboard_def, f, indent=2)
            
            # Update in-memory collection
            self.dashboards[dashboard_id] = dashboard_def
            
            # Invalidate cache for this dashboard
            for key in list(self.cache.keys()):
                if key.startswith(f"{dashboard_id}_"):
                    del self.cache[key]
                    if key in self.cache_timestamps:
                        del self.cache_timestamps[key]
            
            logger.info(f"Updated dashboard: {dashboard_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating dashboard {dashboard_id}: {e}")
            return False
            
    def delete_dashboard(self, dashboard_id: str) -> bool:
        """
        Delete a dashboard
        
        Args:
            dashboard_id: Dashboard ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if dashboard exists
            if dashboard_id not in self.dashboards:
                logger.warning(f"Dashboard {dashboard_id} not found")
                return False
            
            # Delete dashboard file
            dashboard_dir = Path(__file__).parent / "definitions"
            file_path = dashboard_dir / f"{dashboard_id}.json"
            
            if file_path.exists():
                file_path.unlink()
            
            # Remove from in-memory collection
            del self.dashboards[dashboard_id]
            
            # Invalidate cache for this dashboard
            for key in list(self.cache.keys()):
                if key.startswith(f"{dashboard_id}_"):
                    del self.cache[key]
                    if key in self.cache_timestamps:
                        del self.cache_timestamps[key]
            
            logger.info(f"Deleted dashboard: {dashboard_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting dashboard {dashboard_id}: {e}")
            return False


# Create a sample dashboard definition
def create_sample_dashboard():
    """Create a sample executive dashboard definition"""
    dashboard_def = {
        "id": "executive_summary",
        "title": "Executive Summary Dashboard",
        "description": "Key performance metrics for executive management",
        "category": "Executive",
        "created_by": "System",
        "panels": [
            {
                "id": "total_deposits",
                "title": "Total Deposits",
                "type": "gauge",
                "dataSource": {
                    "type": "sql",
                    "query": "SELECT SUM(balance) AS total_deposits FROM cbs_accounts WHERE account_type IN ('SAVINGS', 'CURRENT', 'FIXED_DEPOSIT')"
                },
                "metadata": {
                    "format": "currency",
                    "thresholds": [1000000, 5000000, 10000000]
                }
            },
            {
                "id": "total_loans",
                "title": "Total Loans",
                "type": "gauge",
                "dataSource": {
                    "type": "sql",
                    "query": "SELECT SUM(outstanding_amount) AS total_loans FROM cbs_loans WHERE status = 'ACTIVE'"
                },
                "metadata": {
                    "format": "currency",
                    "thresholds": [1000000, 5000000, 10000000]
                }
            },
            {
                "id": "monthly_transactions",
                "title": "Monthly Transactions",
                "type": "line",
                "dataSource": {
                    "type": "sql",
                    "query": "SELECT DATE_FORMAT(transaction_date, '%Y-%m') AS month, COUNT(*) AS transaction_count, SUM(amount) AS transaction_amount FROM cbs_transactions WHERE transaction_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH) GROUP BY DATE_FORMAT(transaction_date, '%Y-%m') ORDER BY month"
                },
                "metadata": {
                    "xaxis": "month",
                    "yaxis": ["transaction_count", "transaction_amount"],
                    "yaxis_formats": ["number", "currency"]
                }
            },
            {
                "id": "new_customers",
                "title": "New Customers",
                "type": "bar",
                "dataSource": {
                    "type": "sql",
                    "query": "SELECT DATE_FORMAT(registration_date, '%Y-%m') AS month, COUNT(*) AS new_customers FROM cbs_customers WHERE registration_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH) GROUP BY DATE_FORMAT(registration_date, '%Y-%m') ORDER BY month"
                },
                "metadata": {
                    "xaxis": "month",
                    "yaxis": "new_customers"
                }
            }
        ]
    }
    
    return dashboard_def


# Singleton instance
dashboard_manager = DashboardManager()


def get_dashboard_manager() -> DashboardManager:
    """Get the dashboard manager instance"""
    return dashboard_manager


# Initialize with a sample dashboard if needed
def init_module():
    """Initialize the module with sample data if needed"""
    dashboard_dir = Path(__file__).parent / "definitions"
    
    if not dashboard_dir.exists() or not list(dashboard_dir.glob("*.json")):
        dashboard_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample dashboard
        sample = create_sample_dashboard()
        
        # Save sample dashboard
        with open(dashboard_dir / f"{sample['id']}.json", 'w') as f:
            json.dump(sample, f, indent=2)
            logger.info(f"Created sample dashboard: {sample['id']}")


# Initialize module when imported
init_module()
