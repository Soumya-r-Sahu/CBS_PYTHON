"""
Centralization Tracker for Refactoring Progress

This module provides utilities to track the progress of function centralization
during the v1.1.2 refactoring process.
"""

import os
import json
import datetime
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logger
logger = logging.getLogger(__name__)

class CentralizationTracker:
    """
    Tracks the progress of function centralization across modules.
    
    Description:
        The CentralizationTracker helps monitor the progress of moving functions
        to centralized locations as part of the v1.1.2 code centralization effort.
        It tracks what has been moved, what's pending, and generates reports.
    
    Usage:
        # Initialize tracker
        tracker = CentralizationTracker()
        
        # Register a function that has been centralized
        tracker.register_centralized_function(
            "calculate_interest", 
            "loans/interest_calculator.py",
            "utils/common/financial.py",
            "Centralized interest calculation for reuse"
        )
        
        # Generate a report
        report = tracker.generate_report()
    """
    
    def __init__(self, tracking_file="refactoring/centralization_tracking.json"):
        """
        Initialize the centralization tracker
        
        Args:
            tracking_file (str): Path to the JSON tracking file
        """
        self.tracking_file = tracking_file
        self.data = self._load_tracking()
    
    def _load_tracking(self) -> Dict[str, Any]:
        """
        Load existing tracking data
        
        Returns:
            dict: The tracking data structure
        """
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self._create_initial_structure()
        return self._create_initial_structure()
    
    def _create_initial_structure(self) -> Dict[str, Any]:
        """
        Create the initial tracking data structure
        
        Returns:
            dict: Initial tracking data structure
        """
        return {
            "last_updated": None,
            "centralized_functions": [],
            "pending_functions": [],
            "module_progress": {},
            "summary": {
                "total_identified": 0,
                "total_centralized": 0,
                "percentage_complete": 0
            }
        }
    
    def _save_tracking(self):
        """Save tracking data to the JSON file"""
        self.data["last_updated"] = datetime.datetime.now().isoformat()
        
        # Update summary
        self.data["summary"]["total_centralized"] = len(self.data["centralized_functions"])
        total_functions = (len(self.data["centralized_functions"]) + 
                          len(self.data["pending_functions"]))
        self.data["summary"]["total_identified"] = total_functions
        
        if total_functions > 0:
            percentage = (len(self.data["centralized_functions"]) / total_functions) * 100
            self.data["summary"]["percentage_complete"] = round(percentage, 2)
        else:
            self.data["summary"]["percentage_complete"] = 0
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.tracking_file), exist_ok=True)
        
        with open(self.tracking_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def register_centralized_function(self, function_name: str, 
                                    original_location: str, 
                                    new_location: str,
                                    description: str,
                                    module: Optional[str] = None) -> bool:
        """
        Register a function that has been centralized
        
        Args:
            function_name (str): Name of the function
            original_location (str): Original file path
            new_location (str): New centralized location
            description (str): Description of the function purpose
            module (str, optional): Module the function belongs to
            
        Returns:
            bool: True if registration was successful
        """
        # Extract module from path if not provided
        if module is None:
            path_parts = original_location.split('/')
            if len(path_parts) > 0:
                module = path_parts[0]
        
        # Check if already in pending list and remove
        for i, func in enumerate(self.data["pending_functions"]):
            if func["function_name"] == function_name and func["original_location"] == original_location:
                self.data["pending_functions"].pop(i)
                break
        
        # Add to centralized list
        self.data["centralized_functions"].append({
            "function_name": function_name,
            "original_location": original_location,
            "new_location": new_location,
            "description": description,
            "module": module,
            "centralized_on": datetime.datetime.now().isoformat()
        })
        
        # Update module progress
        if module not in self.data["module_progress"]:
            self.data["module_progress"][module] = {
                "total_identified": 0,
                "centralized": 0,
                "percentage": 0
            }
        
        # Update module stats
        module_stats = self._calculate_module_stats(module)
        self.data["module_progress"][module] = module_stats
        
        self._save_tracking()
        return True
    
    def register_pending_function(self, function_name: str, 
                                original_location: str,
                                suggested_location: str,
                                description: str,
                                module: Optional[str] = None) -> bool:
        """
        Register a function that needs to be centralized
        
        Args:
            function_name (str): Name of the function
            original_location (str): Current file path
            suggested_location (str): Suggested centralized location
            description (str): Description of the function purpose
            module (str, optional): Module the function belongs to
            
        Returns:
            bool: True if registration was successful
        """
        # Extract module from path if not provided
        if module is None:
            path_parts = original_location.split('/')
            if len(path_parts) > 0:
                module = path_parts[0]
        
        # Check if already in list
        for func in self.data["pending_functions"]:
            if func["function_name"] == function_name and func["original_location"] == original_location:
                # Already registered, update it
                func["suggested_location"] = suggested_location
                func["description"] = description
                func["module"] = module
                self._save_tracking()
                return True
        
        # Add to pending list
        self.data["pending_functions"].append({
            "function_name": function_name,
            "original_location": original_location,
            "suggested_location": suggested_location,
            "description": description,
            "module": module,
            "registered_on": datetime.datetime.now().isoformat()
        })
        
        # Update module progress
        if module not in self.data["module_progress"]:
            self.data["module_progress"][module] = {
                "total_identified": 0,
                "centralized": 0,
                "percentage": 0
            }
        
        # Update module stats
        module_stats = self._calculate_module_stats(module)
        self.data["module_progress"][module] = module_stats
        
        self._save_tracking()
        return True
    
    def _calculate_module_stats(self, module: str) -> Dict[str, Any]:
        """
        Calculate statistics for a module
        
        Args:
            module (str): Module name
            
        Returns:
            dict: Module statistics
        """
        centralized = [f for f in self.data["centralized_functions"] if f["module"] == module]
        pending = [f for f in self.data["pending_functions"] if f["module"] == module]
        
        total = len(centralized) + len(pending)
        percentage = (len(centralized) / total * 100) if total > 0 else 0
        
        return {
            "total_identified": total,
            "centralized": len(centralized),
            "percentage": round(percentage, 2)
        }
    
    def get_pending_functions(self, module: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of functions pending centralization
        
        Args:
            module (str, optional): Filter by module
            
        Returns:
            list: List of pending functions
        """
        if module:
            return [f for f in self.data["pending_functions"] if f["module"] == module]
        return self.data["pending_functions"]
    
    def get_centralized_functions(self, module: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of centralized functions
        
        Args:
            module (str, optional): Filter by module
            
        Returns:
            list: List of centralized functions
        """
        if module:
            return [f for f in self.data["centralized_functions"] if f["module"] == module]
        return self.data["centralized_functions"]
    
    def get_module_progress(self) -> Dict[str, Dict[str, Any]]:
        """
        Get progress statistics by module
        
        Returns:
            dict: Module progress statistics
        """
        return self.data["module_progress"]
    
    def generate_report(self, include_details: bool = True) -> str:
        """
        Generate a progress report
        
        Args:
            include_details (bool): Whether to include detailed function listings
            
        Returns:
            str: Formatted report
        """
        now = datetime.datetime.now()
        
        lines = [
            "Centralization Progress Report",
            "=============================",
            f"Generated: {now.isoformat()}",
            "",
            "Overall Progress:",
            f"- Total Functions Identified: {self.data['summary']['total_identified']}",
            f"- Functions Centralized: {self.data['summary']['total_centralized']}",
            f"- Completion: {self.data['summary']['percentage_complete']}%",
            ""
        ]
        
        lines.extend([
            "Progress by Module:",
            "------------------"
        ])
        
        for module, stats in sorted(self.data["module_progress"].items()):
            lines.append(f"- {module}:")
            lines.append(f"  - Total: {stats['total_identified']}")
            lines.append(f"  - Centralized: {stats['centralized']}")
            lines.append(f"  - Completion: {stats['percentage']}%")
        
        lines.append("")
        
        if include_details:
            lines.extend([
                "Recently Centralized Functions:",
                "-----------------------------"
            ])
            
            # Show 10 most recent
            recent = sorted(
                self.data["centralized_functions"],
                key=lambda x: x.get("centralized_on", ""),
                reverse=True
            )[:10]
            
            if recent:
                for func in recent:
                    lines.append(f"- {func['function_name']}")
                    lines.append(f"  - From: {func['original_location']}")
                    lines.append(f"  - To: {func['new_location']}")
                    lines.append(f"  - Module: {func['module']}")
                    lines.append("")
            else:
                lines.append("No centralized functions recorded yet.")
                lines.append("")
            
            lines.extend([
                "Top Pending Functions:",
                "---------------------"
            ])
            
            # Show 10 pending
            pending = self.data["pending_functions"][:10]
            
            if pending:
                for func in pending:
                    lines.append(f"- {func['function_name']}")
                    lines.append(f"  - Current: {func['original_location']}")
                    lines.append(f"  - Suggested: {func['suggested_location']}")
                    lines.append(f"  - Module: {func['module']}")
                    lines.append("")
            else:
                lines.append("No pending functions recorded yet.")
                lines.append("")
        
        return "\n".join(lines)

# Create directory for centralization tracker
def initialize_centralization_tracking():
    """Initialize centralization tracking structure"""
    os.makedirs("d:/Vs code/CBS_PYTHON/utils/refactoring", exist_ok=True)
    
    tracker = CentralizationTracker("d:/Vs code/CBS_PYTHON/utils/refactoring/centralization_tracking.json")
    
    # Register some initial pending functions as examples
    tracker.register_pending_function(
        "calculate_interest_rate", 
        "loans/interest_calculator.py",
        "utils/common/financial.py",
        "Common interest calculation used in multiple modules"
    )
    
    tracker.register_pending_function(
        "format_account_number", 
        "accounts/formatting.py",
        "utils/common/formatters.py",
        "Account number formatting with masking"
    )
    
    tracker.register_pending_function(
        "validate_transaction", 
        "transactions/validation.py",
        "utils/validators.py",
        "Transaction validation logic used in multiple places"
    )
    
    # Register some already centralized functions as examples
    tracker.register_centralized_function(
        "hash_password", 
        "security/password_utils.py",
        "security/common/security_operations.py",
        "Password hashing using bcrypt or PBKDF2"
    )
    
    tracker.register_centralized_function(
        "execute_query", 
        "database/python/query_executor.py",
        "database/python/common/database_operations.py",
        "Database query execution with parameter binding"
    )
    
    # Generate initial report
    report = tracker.generate_report()
    
    with open("d:/Vs code/CBS_PYTHON/utils/refactoring/centralization_report.txt", "w") as f:
        f.write(report)
    
    return "Centralization tracking initialized successfully"

if __name__ == "__main__":
    print(initialize_centralization_tracking())
