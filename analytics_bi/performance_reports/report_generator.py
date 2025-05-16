"""
Performance Reports Module

This module handles the generation and management of performance reports
for the Core Banking System.
"""

import os
import sys
from pathlib import Path
import logging
import datetime
import json
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple

# Use centralized import system to ensure project root is in path
from utils.lib.packages import fix_path
fix_path()  # Ensures the project root is in sys.path

# Use relative imports for analytics_bi modules
from ..config import REPORT_SETTINGS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('analytics-reports')

class ReportGenerator:
    """Performance report generator for the banking system"""
    
    def __init__(self):
        """Initialize the report generator"""
        self.report_templates = {}
        self.scheduled_reports = {}
        self._load_report_templates()
        self._load_scheduled_reports()
        
        # Create report directories if they don't exist
        for path in [REPORT_SETTINGS['scheduled_report_path'], 
                   REPORT_SETTINGS['on_demand_report_path']]:
            os.makedirs(path, exist_ok=True)
    
    def _load_report_templates(self):
        """Load report templates from configuration files"""
        try:
            template_dir = Path(__file__).parent / "templates"
            
            if not template_dir.exists():
                template_dir.mkdir(parents=True)
                logger.info(f"Created report templates directory: {template_dir}")
                return
            
            for file in template_dir.glob("*.json"):
                try:
                    with open(file, 'r') as f:
                        template = json.load(f)
                        template_id = template.get('id', file.stem)
                        self.report_templates[template_id] = template
                        logger.info(f"Loaded report template: {template_id}")
                except Exception as e:
                    logger.error(f"Error loading report template {file}: {e}")
        
        except Exception as e:
            logger.error(f"Error loading report templates: {e}")
    
    def _load_scheduled_reports(self):
        """Load scheduled report configurations"""
        try:
            config_file = Path(__file__).parent / "schedules.json"
            
            if not config_file.exists():
                # Create default file
                with open(config_file, 'w') as f:
                    json.dump({}, f)
                logger.info(f"Created empty schedules file: {config_file}")
                return
            
            with open(config_file, 'r') as f:
                self.scheduled_reports = json.load(f)
                logger.info(f"Loaded {len(self.scheduled_reports)} scheduled reports")
        
        except Exception as e:
            logger.error(f"Error loading scheduled reports: {e}")
            self.scheduled_reports = {}
    
    def generate_report(self, template_id: str, 
                      parameters: Optional[Dict[str, Any]] = None,
                      output_format: Optional[str] = None) -> Optional[str]:
        """
        Generate a report based on a template
        
        Args:
            template_id: Report template ID
            parameters: Report parameters
            output_format: Output format (pdf, xlsx, csv)
            
        Returns:
            Path to the generated report file
        """
        try:
            # Validate template
            if template_id not in self.report_templates:
                logger.warning(f"Report template {template_id} not found")
                return None
            
            template = self.report_templates[template_id]
            
            # Use default format if not specified
            if not output_format:
                output_format = REPORT_SETTINGS.get('default_report_format', 'pdf')
            
            # Generate a unique filename
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            report_id = f"{template_id}_{timestamp}"
            filename = f"{report_id}.{output_format}"
            
            # Determine output path
            output_path = os.path.join(REPORT_SETTINGS['on_demand_report_path'], filename)
            
            # Collect report data
            report_data = self._collect_report_data(template, parameters)
            
            # Generate the report file based on format
            self._render_report(template, report_data, output_format, output_path)
            
            logger.info(f"Generated report: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating report {template_id}: {e}")
            return None
    
    def _collect_report_data(self, template: Dict[str, Any], 
                           parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Collect data for a report
        
        Args:
            template: Report template
            parameters: Report parameters
            
        Returns:
            Report data
        """
        result = {
            "metadata": {
                "report_title": template.get('title', 'Untitled Report'),
                "report_description": template.get('description', ''),
                "generated_at": datetime.datetime.now().isoformat(),
                "parameters": parameters or {}
            },
            "sections": []
        }
        
        # Process each section in the template
        for section in template.get('sections', []):
            section_data = self._collect_section_data(section, parameters)
            result['sections'].append(section_data)
        
        return result
    
    def _collect_section_data(self, section: Dict[str, Any], 
                            parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Collect data for a report section
        
        Args:
            section: Section definition
            parameters: Report parameters
            
        Returns:
            Section data
        """
        section_result = {
            "title": section.get('title', ''),
            "description": section.get('description', ''),
            "data_tables": [],
            "charts": []
        }
        
        # Process each data source in the section
        for data_source in section.get('dataSources', []):
            try:
                source_type = data_source.get('type')
                source_id = data_source.get('id')
                
                if source_type == 'sql':
                    query = data_source.get('query', '')
                    query_data = self._execute_sql_query(query, parameters)
                    
                    data_table = {
                        "id": source_id,
                        "title": data_source.get('title', ''),
                        "data": query_data
                    }
                    
                    section_result['data_tables'].append(data_table)
                    
                    # Generate chart if specified
                    if 'chart' in data_source:
                        chart_def = data_source['chart']
                        chart = {
                            "id": f"{source_id}_chart",
                            "title": chart_def.get('title', data_source.get('title', '')),
                            "type": chart_def.get('type', 'bar'),
                            "data": query_data,
                            "config": chart_def.get('config', {})
                        }
                        section_result['charts'].append(chart)
                
                elif source_type == 'api':
                    endpoint = data_source.get('endpoint', '')
                    api_data = self._fetch_api_data(endpoint, parameters)
                    
                    data_table = {
                        "id": source_id,
                        "title": data_source.get('title', ''),
                        "data": api_data
                    }
                    
                    section_result['data_tables'].append(data_table)
                    
                elif source_type == 'python':
                    function_name = data_source.get('function', '')
                    py_data = self._execute_python_function(function_name, parameters)
                    
                    data_table = {
                        "id": source_id,
                        "title": data_source.get('title', ''),
                        "data": py_data
                    }
                    
                    section_result['data_tables'].append(data_table)
                
            except Exception as e:
                logger.error(f"Error collecting data for section {section.get('title')}: {e}")
                # Add error placeholder
                section_result['data_tables'].append({
                    "id": f"error_{uuid.uuid4().hex[:8]}",
                    "title": "Error: " + section.get('title', ''),
                    "error": str(e),
                    "data": []
                })
        
        return section_result
    
    def _execute_sql_query(self, query: str,parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results
        
        Args:
            query: SQL query template
            parameters: Optional parameters
            
        Returns:
            Query results
        """        
        try:
            # Use centralized import manager
            try:
                # First try importing from core_banking
                from core_banking.database.connection import DatabaseConnection
            except ImportError:
                try:
                    # Try using the import_module utility
                    from utils.lib.packages import import_module
                    DatabaseConnection = import_module("database.python.connection").DatabaseConnection
                except ImportError:
                    # Fallback to direct import with proper path fixing
                    from utils.lib.packages import fix_path
                    fix_path()  # Use the centralized path fixing utility
                    from database.python.connection import DatabaseConnection
            
            # Format query with parameters if needed
            formatted_query = query
            if parameters:
                # Simple parameter substitution (in real implementation, use proper SQL parameter binding)
                for key, value in parameters.items():
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
                      parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Fetch data from an API endpoint"""
        try:
            import requests
            
            # Add parameters to request if provided
            request_params = parameters or {}
            
            response = requests.get(endpoint, params=request_params, timeout=30)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error fetching API data from {endpoint}: {e}")
            return []
    
    def _execute_python_function(self, function_name: str,
                              parameters: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a Python function to get data"""
        try:
            # Attempt to find function in the reports module
            module_path = "analytics_bi.performance_reports.report_functions"
            module = __import__(module_path, fromlist=[''])
            
            if hasattr(module, function_name):
                func = getattr(module, function_name)
                return func(parameters)
            else:
                logger.error(f"Function {function_name} not found in module {module_path}")
                return []
                
        except Exception as e:
            logger.error(f"Error executing Python function {function_name}: {e}")
            return []
    
    def _render_report(self, template: Dict[str, Any], data: Dict[str, Any],
                     output_format: str, output_path: str) -> bool:
        """
        Render report to the specified output format
        
        Args:
            template: Report template
            data: Report data
            output_format: Output format (pdf, xlsx, csv)
            output_path: Path to save the report
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if output_format.lower() == 'pdf':
                return self._render_pdf_report(template, data, output_path)
            elif output_format.lower() == 'xlsx':
                return self._render_excel_report(template, data, output_path)
            elif output_format.lower() == 'csv':
                return self._render_csv_report(template, data, output_path)
            else:
                logger.error(f"Unsupported output format: {output_format}")
                return False
                
        except Exception as e:
            logger.error(f"Error rendering report: {e}")
            return False
    
    def _render_pdf_report(self, template: Dict[str, Any], 
                         data: Dict[str, Any],
                         output_path: str) -> bool:
        """Render report as PDF"""
        try:
            # This is a placeholder. In a real implementation, you'd use
            # a library like reportlab, wkhtmltopdf, or weasyprint
            
            # For demonstration, we'll create a simple text file
            with open(output_path, 'w') as f:
                f.write(f"# {data['metadata']['report_title']}\n")
                f.write(f"Generated: {data['metadata']['generated_at']}\n\n")
                
                for section in data['sections']:
                    f.write(f"## {section['title']}\n")
                    f.write(f"{section['description']}\n\n")
                    
                    for table in section['data_tables']:
                        f.write(f"### {table['title']}\n")
                        
                        if table['data']:
                            # Write headers
                            headers = table['data'][0].keys()
                            f.write(" | ".join(headers) + "\n")
                            f.write("-" * 80 + "\n")
                            
                            # Write data rows
                            for row in table['data'][:10]:  # Limit to 10 rows for demo
                                f.write(" | ".join(str(row.get(h, '')) for h in headers) + "\n")
                        
                        f.write("\n\n")
            
            logger.info(f"PDF report placeholder created at {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error rendering PDF report: {e}")
            return False
    
    def _render_excel_report(self, template: Dict[str, Any], 
                           data: Dict[str, Any],
                           output_path: str) -> bool:
        """Render report as Excel spreadsheet"""
        try:
            # This is a placeholder. In a real implementation, you'd use
            # a library like openpyxl or xlsxwriter
            
            # For demonstration, we'll create a simple text file
            with open(output_path, 'w') as f:
                f.write(f"# {data['metadata']['report_title']} (Excel format)\n")
                f.write(f"Generated: {data['metadata']['generated_at']}\n\n")
                
                for section in data['sections']:
                    f.write(f"## {section['title']}\n")
                    
                    for table in section['data_tables']:
                        f.write(f"Sheet: {table['title']}\n")
                        
                        if table['data']:
                            # Write headers
                            headers = table['data'][0].keys()
                            f.write("\t".join(headers) + "\n")
                            
                            # Write data rows
                            for row in table['data'][:10]:  # Limit to 10 rows for demo
                                f.write("\t".join(str(row.get(h, '')) for h in headers) + "\n")
                        
                        f.write("\n\n")
            
            logger.info(f"Excel report placeholder created at {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error rendering Excel report: {e}")
            return False
    
    def _render_csv_report(self, template: Dict[str, Any], 
                         data: Dict[str, Any],
                         output_path: str) -> bool:
        """Render report as CSV file"""
        try:
            # Use the csv module to write CSV data
            import csv
            
            # For multiple tables, create a zip archive of CSV files
            if len(data['sections']) > 1 or any(len(s['data_tables']) > 1 for s in data['sections']):
                import zipfile
                import tempfile
                from datetime import datetime
                
                zip_path = output_path.replace('.csv', '.zip')
                
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    # Add a README file with metadata
                    with tempfile.NamedTemporaryFile('w', delete=False) as readme:
                        readme.write(f"Report: {data['metadata']['report_title']}\n")
                        readme.write(f"Generated: {data['metadata']['generated_at']}\n")
                        readme.write(f"Parameters: {json.dumps(data['metadata']['parameters'])}\n")
                    
                    zipf.write(readme.name, "README.txt")
                    os.unlink(readme.name)
                    
                    # Add each data table as a CSV file
                    for section in data['sections']:
                        for table in section['data_tables']:
                            safe_title = "".join(c if c.isalnum() else "_" for c in table['title'])
                            
                            with tempfile.NamedTemporaryFile('w', delete=False) as temp_csv:
                                if table['data']:
                                    writer = csv.DictWriter(temp_csv, fieldnames=table['data'][0].keys())
                                    writer.writeheader()
                                    writer.writerows(table['data'])
                            
                            zipf.write(temp_csv.name, f"{safe_title}.csv")
                            os.unlink(temp_csv.name)
                
                logger.info(f"Multi-table CSV report created at {zip_path}")
                return True
            
            # For a single table, create a simple CSV file
            else:
                with open(output_path, 'w', newline='') as csv_file:
                    # Find the first data table
                    for section in data['sections']:
                        for table in section['data_tables']:
                            if table['data']:
                                writer = csv.DictWriter(csv_file, fieldnames=table['data'][0].keys())
                                writer.writeheader()
                                writer.writerows(table['data'])
                                break
                        else:
                            continue
                        break
                
                logger.info(f"CSV report created at {output_path}")
                return True
            
        except Exception as e:
            logger.error(f"Error rendering CSV report: {e}")
            return False
    
    def schedule_report(self, template_id: str, schedule: Dict[str, Any],
                      parameters: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Schedule a report for periodic generation
        
        Args:
            template_id: Report template ID
            schedule: Schedule parameters (frequency, time, etc.)
            parameters: Report parameters
            
        Returns:
            Schedule ID if successful, None otherwise
        """
        try:
            # Validate template
            if template_id not in self.report_templates:
                logger.warning(f"Report template {template_id} not found")
                return None
            
            # Generate a unique schedule ID
            schedule_id = str(uuid.uuid4())[:8]
            
            # Create schedule record
            schedule_record = {
                "id": schedule_id,
                "template_id": template_id,
                "parameters": parameters or {},
                "schedule": schedule,
                "output_format": schedule.get("output_format", REPORT_SETTINGS.get('default_report_format')),
                "created_date": datetime.datetime.now().isoformat(),
                "last_run": None,
                "next_run": self._calculate_next_run(schedule),
                "status": "ACTIVE"
            }
            
            # Add to scheduled reports
            self.scheduled_reports[schedule_id] = schedule_record
            
            # Save schedules to file
            self._save_schedules()
            
            logger.info(f"Scheduled report {template_id} with ID {schedule_id}")
            return schedule_id
            
        except Exception as e:
            logger.error(f"Error scheduling report {template_id}: {e}")
            return None
    
    def _calculate_next_run(self, schedule: Dict[str, Any]) -> str:
        """
        Calculate the next run time based on a schedule
        
        Args:
            schedule: Schedule parameters
            
        Returns:
            ISO format datetime string for next run
        """
        now = datetime.datetime.now()
        frequency = schedule.get("frequency", "daily")
        
        if frequency == "daily":
            next_run = now.replace(hour=int(schedule.get("hour", 0)), 
                                minute=int(schedule.get("minute", 0)),
                                second=0, microsecond=0)
            
            # If the time has already passed today, schedule for tomorrow
            if next_run <= now:
                next_run = next_run + datetime.timedelta(days=1)
                
        elif frequency == "weekly":
            # 0 = Monday, 6 = Sunday
            day_of_week = int(schedule.get("day_of_week", 0))
            days_ahead = day_of_week - now.weekday()
            
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
                
            next_run = now.replace(hour=int(schedule.get("hour", 0)),
                                minute=int(schedule.get("minute", 0)),
                                second=0, microsecond=0) + datetime.timedelta(days=days_ahead)
                
        elif frequency == "monthly":
            day_of_month = int(schedule.get("day_of_month", 1))
            
            # Get the target date for this month
            try:
                next_run = now.replace(day=day_of_month,
                                    hour=int(schedule.get("hour", 0)),
                                    minute=int(schedule.get("minute", 0)),
                                    second=0, microsecond=0)
            except ValueError:
                # Day is out of range for this month, use last day
                last_day = (now.replace(month=now.month % 12 + 1, day=1) if now.month < 12 
                        else now.replace(year=now.year + 1, month=1, day=1)) - datetime.timedelta(days=1)
                next_run = last_day.replace(hour=int(schedule.get("hour", 0)),
                                        minute=int(schedule.get("minute", 0)),
                                        second=0, microsecond=0)
            
            # If the date has already passed this month, move to next month
            if next_run <= now:
                if now.month == 12:
                    next_run = next_run.replace(year=now.year + 1, month=1)
                else:
                    next_run = next_run.replace(month=now.month + 1)
                    
        else:  # Default: one-time schedule for tomorrow
            next_run = now.replace(hour=int(schedule.get("hour", 0)),
                                minute=int(schedule.get("minute", 0)),
                                second=0, microsecond=0) + datetime.timedelta(days=1)
        
        return next_run.isoformat()
    
    def _save_schedules(self):
        """Save scheduled reports to configuration file"""
        try:
            config_file = Path(__file__).parent / "schedules.json"
            
            with open(config_file, 'w') as f:
                json.dump(self.scheduled_reports, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving scheduled reports: {e}")
    
    def check_and_run_scheduled_reports(self) -> List[str]:
        """
        Check for and run scheduled reports that are due
        
        Returns:
            List of schedule IDs that were run
        """
        now = datetime.datetime.now()
        executed = []
        
        try:
            for schedule_id, schedule in self.scheduled_reports.items():
                if schedule.get("status") != "ACTIVE":
                    continue
                    
                next_run = datetime.datetime.fromisoformat(schedule.get("next_run", ""))
                
                # Check if it's time to run
                if next_run <= now:
                    # Run the report
                    result = self.generate_report(
                        schedule["template_id"],
                        schedule["parameters"],
                        schedule["output_format"]
                    )
                    
                    if result:
                        # Update schedule
                        schedule["last_run"] = now.isoformat()
                        schedule["next_run"] = self._calculate_next_run(schedule["schedule"])
                        schedule["last_output"] = result
                        executed.append(schedule_id)
                        
                        logger.info(f"Successfully executed scheduled report {schedule_id}")
                    else:
                        logger.error(f"Failed to execute scheduled report {schedule_id}")
            
            # Save updated schedules
            if executed:
                self._save_schedules()
                
            return executed
                
        except Exception as e:
            logger.error(f"Error checking and running scheduled reports: {e}")
            return []
    
    def list_report_templates(self) -> List[Dict[str, Any]]:
        """
        Get a list of available report templates
        
        Returns:
            List of template metadata
        """
        result = []
        
        for template_id, template in self.report_templates.items():
            result.append({
                "id": template_id,
                "title": template.get("title", ""),
                "description": template.get("description", ""),
                "category": template.get("category", "General"),
                "author": template.get("author", "System"),
                "last_modified": template.get("last_modified", "")
            })
            
        return result
    
    def list_scheduled_reports(self) -> List[Dict[str, Any]]:
        """
        Get a list of scheduled reports
        
        Returns:
            List of scheduled report metadata
        """
        result = []
        
        for schedule_id, schedule in self.scheduled_reports.items():
            template_id = schedule.get("template_id")
            template_title = ""
            
            if template_id in self.report_templates:
                template_title = self.report_templates[template_id].get("title", "")
                
            result.append({
                "id": schedule_id,
                "template_id": template_id,
                "template_title": template_title,
                "format": schedule.get("output_format", ""),
                "frequency": schedule.get("schedule", {}).get("frequency", ""),
                "next_run": schedule.get("next_run", ""),
                "last_run": schedule.get("last_run", ""),
                "status": schedule.get("status", "")
            })
            
        return result


# Create a sample report template
def create_sample_report_templates():
    """Create sample report templates"""
    templates = [
        {
            "id": "monthly_financial_summary",
            "title": "Monthly Financial Summary",
            "description": "Summary of key financial metrics for the month",
            "category": "Financial",
            "author": "System",
            "sections": [
                {
                    "title": "Balance Sheet Summary",
                    "description": "Summary of assets and liabilities",
                    "dataSources": [
                        {
                            "id": "balance_sheet",
                            "title": "Balance Sheet Summary",
                            "type": "sql",
                            "query": """
                                SELECT 
                                    'Total Deposits' as category,
                                    SUM(balance) as amount
                                FROM cbs_accounts
                                WHERE account_type IN ('SAVINGS', 'CURRENT', 'FIXED_DEPOSIT')
                                
                                UNION ALL
                                
                                SELECT 
                                    'Total Loans' as category,
                                    SUM(outstanding_amount) as amount
                                FROM cbs_loans
                                WHERE status = 'ACTIVE'
                                
                                UNION ALL
                                
                                SELECT 
                                    'Net Position' as category,
                                    (
                                        (SELECT SUM(balance) FROM cbs_accounts WHERE account_type IN ('SAVINGS', 'CURRENT', 'FIXED_DEPOSIT')) -
                                        (SELECT SUM(outstanding_amount) FROM cbs_loans WHERE status = 'ACTIVE')
                                    ) as amount
                            """,
                            "chart": {
                                "title": "Balance Sheet Overview",
                                "type": "pie",
                                "config": {
                                    "labels": "category",
                                    "values": "amount",
                                    "colors": ["#4e73df", "#1cc88a", "#36b9cc"]
                                }
                            }
                        }
                    ]
                },
                {
                    "title": "Income Statement",
                    "description": "Summary of income and expenses",
                    "dataSources": [
                        {
                            "id": "income_statement",
                            "title": "Income Statement",
                            "type": "sql",
                            "query": """
                                SELECT 
                                    'Interest Income' as category,
                                    SUM(amount) as amount
                                FROM cbs_transactions
                                WHERE transaction_type = 'INTEREST_INCOME'
                                AND transaction_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                                
                                UNION ALL
                                
                                SELECT 
                                    'Fee Income' as category,
                                    SUM(amount) as amount
                                FROM cbs_transactions
                                WHERE transaction_type = 'FEE_INCOME'
                                AND transaction_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                                
                                UNION ALL
                                
                                SELECT 
                                    'Interest Expense' as category,
                                    SUM(amount) as amount
                                FROM cbs_transactions
                                WHERE transaction_type = 'INTEREST_EXPENSE'
                                AND transaction_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                            """,
                            "chart": {
                                "title": "Income Statement",
                                "type": "bar",
                                "config": {
                                    "x": "category",
                                    "y": "amount",
                                    "colors": ["#4e73df", "#1cc88a", "#e74a3b"]
                                }
                            }
                        }
                    ]
                }
            ]
        },
        {
            "id": "customer_activity_report",
            "title": "Customer Activity Report",
            "description": "Analysis of customer activity and engagement",
            "category": "Customer",
            "author": "System",
            "sections": [
                {
                    "title": "New Customer Acquisitions",
                    "description": "New customers by month",
                    "dataSources": [
                        {
                            "id": "new_customers",
                            "title": "New Customer Acquisitions",
                            "type": "sql",
                            "query": """
                                SELECT 
                                    DATE_FORMAT(registration_date, '%Y-%m') as month,
                                    COUNT(*) as new_customers
                                FROM cbs_customers
                                WHERE registration_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                                GROUP BY DATE_FORMAT(registration_date, '%Y-%m')
                                ORDER BY month
                            """,
                            "chart": {
                                "title": "New Customers by Month",
                                "type": "line",
                                "config": {
                                    "x": "month",
                                    "y": "new_customers",
                                    "lineColor": "#4e73df"
                                }
                            }
                        }
                    ]
                },
                {
                    "title": "Customer Segments",
                    "description": "Distribution of customers by segment",
                    "dataSources": [
                        {
                            "id": "customer_segments",
                            "title": "Customer Segments",
                            "type": "sql",
                            "query": """
                                SELECT 
                                    segment,
                                    COUNT(*) as count,
                                    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM cbs_customers) as percentage
                                FROM cbs_customers
                                GROUP BY segment
                            """,
                            "chart": {
                                "title": "Customer Segment Distribution",
                                "type": "pie",
                                "config": {
                                    "labels": "segment",
                                    "values": "count"
                                }
                            }
                        }
                    ]
                },
                {
                    "title": "Digital Channel Usage",
                    "description": "Customer activity across digital channels",
                    "dataSources": [
                        {
                            "id": "channel_usage",
                            "title": "Digital Channel Usage",
                            "type": "sql",
                            "query": """
                                SELECT 
                                    channel,
                                    COUNT(*) as sessions,
                                    COUNT(DISTINCT customer_id) as unique_customers
                                FROM dc_login_history
                                WHERE login_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                                GROUP BY channel
                            """
                        }
                    ]
                }
            ]
        }
    ]
    
    return templates


# Singleton instance
report_generator = ReportGenerator()


def get_report_generator() -> ReportGenerator:
    """Get the report generator instance"""
    return report_generator


# Initialize with sample templates if needed
def init_module():
    """Initialize the module with sample data if needed"""
    template_dir = Path(__file__).parent / "templates"
    
    if not template_dir.exists() or not list(template_dir.glob("*.json")):
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample templates
        templates = create_sample_report_templates()
        
        for template in templates:
            template_id = template['id']
            
            # Save template
            with open(template_dir / f"{template_id}.json", 'w') as f:
                json.dump(template, f, indent=2)
                logger.info(f"Created sample report template: {template_id}")


# Initialize module when imported
init_module()
