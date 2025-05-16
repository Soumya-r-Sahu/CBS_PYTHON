"""
HR-ERP Configuration Module

This module contains configuration settings for the HR and ERP system.
"""

import os
from pathlib import Path

# Add parent directory to path if needed

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    # Removed: sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


# Try importing from main config
try:
    from config import DATABASE_CONFIG, HR_ERP_CONFIG
    
    # Extract HR-ERP specific configuration
    HR_ERP_SETTINGS = HR_ERP_CONFIG if 'HR_ERP_CONFIG' in locals() else {}
    
except ImportError:
    # Default configuration
    HR_ERP_SETTINGS = {
        'leave_approval_levels': 2,
        'performance_review_frequency_months': 6,
        'probation_period_months': 3,
        'default_leave_days': 24,
        'payroll_process_day': 25
    }
    
    DATABASE_CONFIG = {
        'host': 'localhost',
        'database': 'CBS_PYTHON',
        'user': 'root',
        'password': '',
        'port': 3307,
    }

# Employee management settings
EMPLOYEE_SETTINGS = {
    'id_format': 'EMP-{year}-{number:04d}',
    'default_documents_required': ['id_proof', 'address_proof', 'education_certificates', 'previous_employment_docs'],
    'org_structure_levels': ['Executive', 'Manager', 'Supervisor', 'Staff'],
    'employee_statuses': ['Active', 'On Leave', 'Suspended', 'Terminated', 'Retired']
}

# Payroll settings
PAYROLL_SETTINGS = {
    'salary_components': [
        {'name': 'Basic', 'percentage': 50, 'taxable': True},
        {'name': 'HRA', 'percentage': 20, 'taxable': False},
        {'name': 'Conveyance', 'percentage': 10, 'taxable': True},
        {'name': 'Medical', 'percentage': 5, 'taxable': False},
        {'name': 'Special Allowance', 'percentage': 15, 'taxable': True}
    ],
    'deductions': [
        {'name': 'Provident Fund', 'percentage': 12, 'max_amount': 1800},
        {'name': 'Professional Tax', 'flat_amount': 200},
        {'name': 'Income Tax', 'calculate_based_on_slab': True}
    ],
    'payment_methods': ['Bank Transfer', 'Check', 'Cash'],
    'default_payment_method': 'Bank Transfer',
    'salary_processing_date': 25,
    'tax_year_start_month': 4  # April
}

# Recruitment settings
RECRUITMENT_SETTINGS = {
    'stages': [
        'Application', 
        'Screening', 
        'First Interview', 
        'Second Interview', 
        'HR Interview', 
        'Offer', 
        'Onboarding'
    ],
    'required_approvals_for_hiring': ['Department Head', 'HR Manager', 'Finance Manager'],
    'default_probation_period_months': 3,
    'resume_storage_path': str(Path(__file__).parent / 'recruitment' / 'resumes')
}

# Leave management settings
LEAVE_SETTINGS = {
    'leave_types': [
        {'name': 'Casual Leave', 'annual_quota': 12, 'carry_forward': False, 'code': 'CL'},
        {'name': 'Sick Leave', 'annual_quota': 12, 'carry_forward': True, 'max_carry_forward': 6, 'code': 'SL'},
        {'name': 'Privilege Leave', 'annual_quota': 15, 'carry_forward': True, 'max_carry_forward': 15, 'code': 'PL'},
        {'name': 'Maternity Leave', 'annual_quota': 180, 'carry_forward': False, 'gender_specific': 'Female', 'code': 'ML'},
        {'name': 'Paternity Leave', 'annual_quota': 15, 'carry_forward': False, 'gender_specific': 'Male', 'code': 'PTL'}
    ],
    'minimum_notice_days': {
        'Casual Leave': 1,
        'Sick Leave': 0,
        'Privilege Leave': 7,
        'Maternity Leave': 30,
        'Paternity Leave': 15
    },
    'maximum_consecutive_days': {
        'Casual Leave': 3,
        'Sick Leave': 5,
        'Privilege Leave': 15
    },
    'approval_chain': ['Immediate Supervisor', 'Department Head', 'HR Manager']
}

# Performance management settings
PERFORMANCE_SETTINGS = {
    'rating_scale': [
        {'value': 1, 'description': 'Needs Improvement'},
        {'value': 2, 'description': 'Meets Some Expectations'},
        {'value': 3, 'description': 'Meets Expectations'},
        {'value': 4, 'description': 'Exceeds Expectations'},
        {'value': 5, 'description': 'Outstanding'}
    ],
    'review_cycles': ['Mid-year', 'Annual'],
    'default_review_parameters': [
        'Job Knowledge',
        'Quality of Work',
        'Quantity of Work',
        'Initiative',
        'Communication',
        'Teamwork',
        'Leadership',
        'Decision Making',
        'Planning & Organization',
        'Adaptability'
    ],
    'goal_types': ['Individual', 'Team', 'Department', 'Organization'],
    'default_goals_per_employee': 5
}

# Training and development settings
TRAINING_SETTINGS = {
    'training_types': [
        'Induction',
        'Technical',
        'Soft Skills',
        'Leadership',
        'Compliance',
        'Product Knowledge'
    ],
    'training_modes': ['Classroom', 'Online', 'Workshop', 'On-the-job', 'External'],
    'certificate_validity_years': {
        'Compliance': 1,
        'Technical': 3
    },
    'mandatory_trainings': {
        'New Employee': ['Induction', 'Banking Basics', 'Compliance Fundamentals', 'Customer Service'],
        'Teller': ['Cash Handling', 'Fraud Detection', 'KYC & AML'],
        'Loan Officer': ['Credit Assessment', 'Loan Products', 'Risk Management'],
        'Manager': ['Leadership Training', 'Performance Management', 'Business Strategy']
    }
}