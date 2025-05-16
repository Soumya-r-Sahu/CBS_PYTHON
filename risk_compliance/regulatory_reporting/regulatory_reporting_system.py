"""
Regulatory Reporting System for Core Banking System

This module handles generation of regulatory reports required by financial
authorities such as RBI, SEBI, and other relevant regulatory bodies.
"""

import os
import time
import logging
import datetime
import json
import csv
from typing import Dict, Any, List, Optional, Union, Set
from pathlib import Path

# Initialize logger
logger = logging.getLogger(__name__)

# Import configuration
import os
import sys

# Try to use local config if available
try:
    # First try relative import from parent directory
    from ..config import get_config, get_environment
except ImportError:
    # Fallback to system config
    try:
        from config import get_config, get_environment
    except ImportError:
        # Use stub functions if all else fails
        def get_environment():
            return os.environ.get("CBS_ENVIRONMENT", "DEVELOPMENT").upper()
            
        def get_config(module_name):
            return {
                "report_directory": "reports/regulatory"
            }


class RegulatoryReportingSystem:
    """System for generating regulatory compliance reports"""
    
    def __init__(self):
        """Initialize the Regulatory Reporting System"""
        self.environment = get_environment()
        self.config = get_config("regulatory_reporting")
        
        # Configure reporting based on environment
        self._configure_environment_settings()
        
        # Set up report directories
        self._setup_report_directories()
        
        # Register available report types
        self._register_report_types()
        
        logger.info(f"Regulatory Reporting System initialized in {self.environment} environment")
    
    def _configure_environment_settings(self):
        """Configure environment-specific settings"""
        # Reporting intervals in days
        self.reporting_intervals = {
            "AML_CTR": 1,        # Currency Transaction Report - Daily
            "STR": 1,            # Suspicious Transaction Report - Daily
            "BALANCE_SHEET": 30, # Monthly balance sheet
            "PL_STATEMENT": 30,  # Profit & Loss - Monthly
            "LIQUIDITY": 7,      # Liquidity Report - Weekly
            "CAR": 30,           # Capital Adequacy Ratio - Monthly
            "NPA": 30,           # Non-Performing Assets - Monthly
            "FEMA": 90,          # Foreign Exchange Management Act - Quarterly
            "TDS": 90,           # Tax Deducted at Source - Quarterly
        }
        
        # Override with environment-specific settings
        if self.environment == "PRODUCTION":
            # Production uses real reporting intervals
            pass
        elif self.environment == "TEST":
            # Test uses shorter intervals for testing
            for key in self.reporting_intervals:
                self.reporting_intervals[key] = max(1, self.reporting_intervals[key] // 7)
        else:
            # Development uses very short intervals
            for key in self.reporting_intervals:
                self.reporting_intervals[key] = 1
        
        # Set report formats based on environment
        if self.environment == "PRODUCTION":
            self.report_formats = ["PDF", "XBRL", "JSON"]
        else:
            self.report_formats = ["JSON", "CSV"]
        
        logger.info(f"Configured regulatory reporting for {self.environment} environment")
    
    def _setup_report_directories(self):
        """Set up directories for storing generated reports"""
        # Base directory
        self.base_dir = self.config.get("report_directory", "reports/regulatory")
        
        # Create environment-specific directory
        self.report_dir = f"{self.base_dir}/{self.environment.lower()}"
        os.makedirs(self.report_dir, exist_ok=True)
        
        # Create subdirectories for each report type
        for report_type in self.reporting_intervals.keys():
            report_type_dir = f"{self.report_dir}/{report_type.lower()}"
            os.makedirs(report_type_dir, exist_ok=True)
        
        logger.info(f"Report directories set up at {self.report_dir}")
    
    def _register_report_types(self):
        """Register available report generators"""
        # Map of report types to their generator functions
        self.report_generators = {
            "AML_CTR": self._generate_aml_ctr_report,
            "STR": self._generate_str_report,
            "BALANCE_SHEET": self._generate_balance_sheet,
            "PL_STATEMENT": self._generate_pl_statement,
            "LIQUIDITY": self._generate_liquidity_report,
            "CAR": self._generate_capital_adequacy_report,
            "NPA": self._generate_npa_report,
            "FEMA": self._generate_fema_report,
            "TDS": self._generate_tds_report,
        }
        
        logger.info(f"Registered {len(self.report_generators)} report types")
    
    def generate_report(self, report_type: str, report_date: Optional[datetime.date] = None,
                      formats: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a specific regulatory report
        
        Args:
            report_type (str): Type of report to generate
            report_date (datetime.date, optional): Date for the report
            formats (List[str], optional): Output formats
            
        Returns:
            Dict: Report generation result with status and file paths
        """
        # Validate report type
        if report_type not in self.report_generators:
            return {
                "status": "ERROR",
                "message": f"Unknown report type: {report_type}",
                "available_types": list(self.report_generators.keys())
            }
        
        # Use current date if not specified
        if not report_date:
            report_date = datetime.date.today()
        
        # Use default formats if not specified
        if not formats:
            formats = self.report_formats
        
        try:
            # Generate the report data
            report_data = self.report_generators[report_type](report_date)
            
            # Add metadata
            report_data["metadata"] = {
                "report_type": report_type,
                "report_date": report_date.isoformat(),
                "generated_at": datetime.datetime.now().isoformat(),
                "environment": self.environment,
                "generated_by": "RegulatoryReportingSystem"
            }
            
            # Save in requested formats
            output_files = {}
            for fmt in formats:
                if fmt.upper() == "JSON":
                    file_path = self._save_json_report(report_type, report_date, report_data)
                    output_files["JSON"] = file_path
                elif fmt.upper() == "CSV":
                    file_path = self._save_csv_report(report_type, report_date, report_data)
                    output_files["CSV"] = file_path
                elif fmt.upper() == "PDF":
                    file_path = self._save_pdf_report(report_type, report_date, report_data)
                    output_files["PDF"] = file_path
                elif fmt.upper() == "XBRL":
                    file_path = self._save_xbrl_report(report_type, report_date, report_data)
                    output_files["XBRL"] = file_path
            
            return {
                "status": "SUCCESS",
                "report_type": report_type,
                "report_date": report_date.isoformat(),
                "output_files": output_files
            }
            
        except Exception as e:
            logger.error(f"Error generating {report_type} report: {str(e)}")
            return {
                "status": "ERROR",
                "report_type": report_type,
                "message": f"Failed to generate report: {str(e)}"
            }
    
    def schedule_reports(self) -> Dict[str, Any]:
        """
        Schedule all required reports based on configured intervals
        
        Returns:
            Dict: Scheduled report information
        """
        scheduled = {}
        today = datetime.date.today()
        
        for report_type, interval in self.reporting_intervals.items():
            # Calculate next report date
            last_report_date = self._get_last_report_date(report_type)
            
            if not last_report_date:
                # If no previous report, schedule for today
                next_report_date = today
            else:
                # Calculate next date based on interval
                next_report_date = last_report_date + datetime.timedelta(days=interval)
            
            # If next report date is today or in the past, generate report
            if next_report_date <= today:
                result = self.generate_report(report_type)
                scheduled[report_type] = {
                    "status": result["status"],
                    "date": today.isoformat()
                }
            else:
                scheduled[report_type] = {
                    "status": "SCHEDULED",
                    "date": next_report_date.isoformat()
                }
        
        return {
            "scheduled_reports": scheduled,
            "environment": self.environment
        }
    
    def _get_last_report_date(self, report_type: str) -> Optional[datetime.date]:
        """Get the date of the last generated report for the given type"""
        report_dir = f"{self.report_dir}/{report_type.lower()}"
        
        try:
            # List JSON reports and extract dates from filenames
            pattern = f"{report_type.lower()}_*.json"
            report_files = list(Path(report_dir).glob(pattern))
            
            if not report_files:
                return None
            
            # Extract dates from filenames and find the most recent
            dates = []
            for file_path in report_files:
                try:
                    # Extract date from filename (format: report_type_YYYY-MM-DD.json)
                    date_str = file_path.stem.split('_')[-1]
                    report_date = datetime.date.fromisoformat(date_str)
                    dates.append(report_date)
                except (ValueError, IndexError):
                    continue
            
            if not dates:
                return None
                
            return max(dates)
            
        except Exception as e:
            logger.error(f"Error getting last report date for {report_type}: {str(e)}")
            return None
    
    def _save_json_report(self, report_type: str, report_date: datetime.date,
                        report_data: Dict[str, Any]) -> str:
        """Save report as JSON"""
        report_dir = f"{self.report_dir}/{report_type.lower()}"
        date_str = report_date.isoformat()
        file_path = f"{report_dir}/{report_type.lower()}_{date_str}.json"
        
        with open(file_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return file_path
    
    def _save_csv_report(self, report_type: str, report_date: datetime.date,
                       report_data: Dict[str, Any]) -> str:
        """Save report as CSV"""
        report_dir = f"{self.report_dir}/{report_type.lower()}"
        date_str = report_date.isoformat()
        file_path = f"{report_dir}/{report_type.lower()}_{date_str}.csv"
        
        # Extract tabular data from the report
        if "data" in report_data and isinstance(report_data["data"], list):
            data_rows = report_data["data"]
            if data_rows:
                with open(file_path, 'w', newline='') as f:
                    # Assume all rows have same keys
                    if isinstance(data_rows[0], dict):
                        fieldnames = data_rows[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(data_rows)
        
        return file_path
    
    def _save_pdf_report(self, report_type: str, report_date: datetime.date,
                       report_data: Dict[str, Any]) -> str:
        """Save report as PDF"""
        # In a real implementation, this would use a PDF generation library
        report_dir = f"{self.report_dir}/{report_type.lower()}"
        date_str = report_date.isoformat()
        file_path = f"{report_dir}/{report_type.lower()}_{date_str}.pdf"
        
        # Simplified implementation - just create a dummy file
        with open(file_path, 'w') as f:
            f.write(f"PDF Report for {report_type} on {date_str}\n")
            f.write("This is a placeholder for actual PDF content")
        
        return file_path
    
    def _save_xbrl_report(self, report_type: str, report_date: datetime.date,
                        report_data: Dict[str, Any]) -> str:
        """Save report as XBRL"""
        # In a real implementation, this would use an XBRL generation library
        report_dir = f"{self.report_dir}/{report_type.lower()}"
        date_str = report_date.isoformat()
        file_path = f"{report_dir}/{report_type.lower()}_{date_str}.xbrl"
        
        # Simplified implementation - just create a dummy file
        with open(file_path, 'w') as f:
            f.write(f"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            f.write(f"<xbrl>\n")
            f.write(f"  <report type=\"{report_type}\" date=\"{date_str}\" />\n")
            f.write(f"  <!-- This is a placeholder for actual XBRL content -->\n")
            f.write(f"</xbrl>")
        
        return file_path

    # Report generator implementations
    def _generate_aml_ctr_report(self, report_date: datetime.date) -> Dict[str, Any]:
        """
        Generate Currency Transaction Report (CTR) for AML compliance
        
        This report identifies cash transactions above INR 10 lakhs
        for Anti-Money Laundering monitoring.
        """
        # In a real implementation, this would query transaction data from the database
        # Simulated data for example
        return {
            "report_name": "Currency Transaction Report",
            "report_code": "AML_CTR",
            "report_date": report_date.isoformat(),
            "threshold_amount": 1000000,  # INR 10 lakhs
            "data": [
                {
                    "transaction_id": f"TRX-{report_date.strftime('%Y%m%d')}-000001",
                    "customer_id": "CUST001",
                    "account_number": "ACCT0010001",
                    "transaction_date": report_date.isoformat(),
                    "amount": 1500000,
                    "transaction_type": "CASH_DEPOSIT",
                    "branch_code": "BR001"
                },
                {
                    "transaction_id": f"TRX-{report_date.strftime('%Y%m%d')}-000002",
                    "customer_id": "CUST002",
                    "account_number": "ACCT0010002",
                    "transaction_date": report_date.isoformat(),
                    "amount": 1250000,
                    "transaction_type": "CASH_WITHDRAWAL",
                    "branch_code": "BR002"
                }
                # Additional transactions would be included here
            ],
            "summary": {
                "total_transactions": 2,
                "total_value": 2750000,
                "reporting_branches": ["BR001", "BR002"]
            }
        }
    
    def _generate_str_report(self, report_date: datetime.date) -> Dict[str, Any]:
        """
        Generate Suspicious Transaction Report (STR)
        
        This report identifies transactions flagged as potentially suspicious
        by the fraud detection system.
        """
        # In a real implementation, this would query suspicious transactions from the database
        return {
            "report_name": "Suspicious Transaction Report",
            "report_code": "STR",
            "report_date": report_date.isoformat(),
            "data": [
                {
                    "transaction_id": f"TRX-{report_date.strftime('%Y%m%d')}-000101",
                    "customer_id": "CUST0101",
                    "account_number": "ACCT0010101",
                    "transaction_date": report_date.isoformat(),
                    "amount": 950000,
                    "transaction_type": "TRANSFER",
                    "recipient_account": "ACCT9995555",
                    "risk_score": 78,
                    "risk_factors": ["UNUSUAL_PATTERN", "NEW_BENEFICIARY"]
                }
                # Additional suspicious transactions would be included here
            ],
            "summary": {
                "total_transactions": 1,
                "total_value": 950000,
                "risk_level_distribution": {
                    "HIGH": 1,
                    "MEDIUM": 0,
                    "LOW": 0
                }
            }
        }
    
    def _generate_balance_sheet(self, report_date: datetime.date) -> Dict[str, Any]:
        """Generate bank balance sheet report"""
        # Implementation would query account balances, assets, liabilities, etc.
        return {"report_name": "Balance Sheet", "report_code": "BALANCE_SHEET"}
    
    def _generate_pl_statement(self, report_date: datetime.date) -> Dict[str, Any]:
        """Generate profit and loss statement"""
        return {"report_name": "Profit & Loss Statement", "report_code": "PL_STATEMENT"}
    
    def _generate_liquidity_report(self, report_date: datetime.date) -> Dict[str, Any]:
        """Generate liquidity coverage ratio report"""
        return {"report_name": "Liquidity Coverage Report", "report_code": "LIQUIDITY"}
    
    def _generate_capital_adequacy_report(self, report_date: datetime.date) -> Dict[str, Any]:
        """Generate capital adequacy ratio report"""
        return {"report_name": "Capital Adequacy Report", "report_code": "CAR"}
    
    def _generate_npa_report(self, report_date: datetime.date) -> Dict[str, Any]:
        """Generate non-performing assets report"""
        return {"report_name": "Non-Performing Assets Report", "report_code": "NPA"}
    
    def _generate_fema_report(self, report_date: datetime.date) -> Dict[str, Any]:
        """Generate FEMA compliance report"""
        return {"report_name": "FEMA Compliance Report", "report_code": "FEMA"}
    
    def _generate_tds_report(self, report_date: datetime.date) -> Dict[str, Any]:
        """Generate tax deducted at source report"""
        return {"report_name": "Tax Deducted at Source Report", "report_code": "TDS"}


# Create a singleton instance
regulatory_reporting = RegulatoryReportingSystem()

# Export main functions for easy access
generate_report = regulatory_reporting.generate_report
schedule_reports = regulatory_reporting.schedule_reports
