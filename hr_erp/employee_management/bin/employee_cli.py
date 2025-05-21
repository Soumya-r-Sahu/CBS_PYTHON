#!/usr/bin/env python
"""
Employee Management CLI Script

This script provides a command-line interface to the employee management
module of the HR-ERP system.
"""

import sys
import os
import logging
from pathlib import Path

# Ensure parent directory is in path
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import CLI processor
from hr_erp.employee_management.presentation.cli import EmployeeCliProcessor


def main():
    """Main entry point for the employee management CLI"""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create CLI processor
    processor = EmployeeCliProcessor()
    
    # Process command (skip script name in sys.argv)
    exit_code = processor.process_command(sys.argv[1:])
    
    # Exit with appropriate code
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
