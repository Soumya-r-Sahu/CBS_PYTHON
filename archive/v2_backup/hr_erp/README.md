# HR-ERP Module

## Overview
The Human Resources and Enterprise Resource Planning (HR-ERP) module provides comprehensive functionality for managing employees, payroll, recruitment, performance evaluations, and other HR-related processes within the Core Banking System.

## Key Components

### Employee Management
- Employee profiles and records
- Organization structure and reporting hierarchies
- Document management
- Attendance tracking
- Employee history

### Payroll Management
- Salary structure and components
- Tax calculations
- Payslip generation
- Bonus and increment processing
- Statutory compliance

### Recruitment
- Job posting and applicant tracking
- Interview scheduling
- Candidate evaluations
- Offer management
- Onboarding process

### Leave Management
- Leave types and quotas
- Leave application and approval workflow
- Leave balance tracking
- Holiday calendar management

### Performance Management
- Goal setting and tracking
- Performance reviews and appraisals
- Rating and feedback system
- Performance improvement plans

### Training & Development
- Training needs identification
- Course management
- Training calendar
- Employee skill matrix
- Certification tracking
- Training program management
- Training record keeping
- Training effectiveness measurement
- Career development planning

## Integration Points
- Authentication and access control with Security module
- Employee account management with Core Banking
- Payroll processing with Transactions module
- Reporting capabilities with Analytics-BI module
- Data synchronization with Finance module
- Event notification system for cross-module communication
- External system integration

## Configuration
System settings can be modified in `config.py`. Each sub-module also contains its specific configuration options.

## Usage Examples

```python
# Import employee manager
from hr_erp.employee_management import EmployeeManager

# Create employee manager instance
employee_manager = EmployeeManager()

# Get employee details
employee = employee_manager.get_employee_by_id("EMP-2025-0042")
print(f"Employee Name: {employee.first_name} {employee.last_name}")
print(f"Department: {employee.department}")
print(f"Reporting To: {employee.reporting_manager}")

# Process payroll for a specific month
from hr_erp.payroll import PayrollProcessor

payroll = PayrollProcessor()
payroll.process_monthly_payroll(month=5, year=2025)  # Process for May 2025

# Manage training programs
from hr_erp.training import TrainingManager

training_mgr = TrainingManager()

# Create a new training program
program = training_mgr.create_training_program(
    program_id="PROG-2025-001",
    name="Python Advanced Programming",
    description="Advanced Python concepts for developers",
    start_date="2025-06-01",
    end_date="2025-06-15",
    instructor="John Smith",
    capacity=20
)

# Register an employee for training
training_mgr.register_employee_for_training("EMP-2025-0042", "PROG-2025-001")

# Integration with other modules
from hr_erp.integration import IntegrationManager

integration = IntegrationManager()

# Sync employee data with other modules
result = integration.sync_employee_data()
print(f"Synced with modules: {result['modules_synced']}")

# Sync payroll data with finance module
payroll_sync = integration.sync_payroll_data("2025-05-01", "2025-05-31")
print(f"Payroll sync successful: {payroll_sync['success']}")
```

## Additional Information
For detailed documentation, see the implementation guides in the `documentation/` directory.
