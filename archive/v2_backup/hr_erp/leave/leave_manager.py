"""
Leave Management Module

This module handles all leave-related functionalities including:
- Leave applications
- Approval workflows
- Leave balances
- Holiday calendar management
"""

import os
import sys
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import uuid
import calendar
from decimal import Decimal

# Add parent directory to path if needed
# Removed: sys.path.insert(0, str(Path(__file__).parent.parent))
# Removed: sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import HR-ERP modules
from hr_erp.config import LEAVE_SETTINGS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('hr-leave')


class LeaveManager:
    """Leave management for HR-ERP system"""
    def __init__(self):
        """Initialize the leave manager"""
        self.db_connection = None
        self._initialize_db_connection()
        self.leave_types = {lt['code']: lt for lt in LEAVE_SETTINGS['leave_types']}
        
    def _initialize_db_connection(self):
        """Initialize database connection"""
        try:
            # Import database connection using centralized import system
            from utils.lib.packages import fix_path, import_module
            fix_path()  # Ensures project root is in sys.path
            DatabaseConnection = import_module("database.python.connection").DatabaseConnection
            
            self.db_connection = DatabaseConnection()
            logger.info("Database connection initialized for leave management")
            
        except ImportError:
            logger.error("Failed to import DatabaseConnection")
    
    def apply_for_leave(self, leave_data: Dict[str, Any]) -> Optional[str]:
        """
        Apply for leave
        
        Args:
            leave_data: Leave application details
            
        Returns:
            Leave application ID if successful, None otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            cursor = conn.cursor()
            
            # Generate leave ID
            leave_id = f"LV-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Extract leave application information
            employee_id = leave_data.get('employee_id')
            leave_type = leave_data.get('leave_type')
            start_date = leave_data.get('start_date')
            end_date = leave_data.get('end_date')
            half_day = leave_data.get('half_day', False)
            reason = leave_data.get('reason', '')
            contact_during_leave = leave_data.get('contact_during_leave', '')
            
            # Validate dates
            if not start_date or not end_date:
                logger.error(f"Invalid leave dates: {start_date} - {end_date}")
                return None
                
            start_date_obj = start_date if isinstance(start_date, datetime.date) else datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = end_date if isinstance(end_date, datetime.date) else datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            
            # Calculate number of days
            number_of_days = (end_date_obj - start_date_obj).days + 1
            if half_day:
                number_of_days = 0.5
                
            # Check employee eligibility for this leave type
            eligibility = self._check_leave_eligibility(
                employee_id, leave_type, number_of_days, start_date_obj
            )
            
            if not eligibility['eligible']:
                logger.warning(eligibility['reason'])
                return None
            
            # Check leave policy compliance
            policy_check = self._check_leave_policy_compliance(
                leave_type, start_date_obj, end_date_obj, half_day
            )
            
            if not policy_check['compliant']:
                logger.warning(policy_check['reason'])
                return None
            
            # Get approver
            approver = self._get_first_approver(employee_id)
            
            # Insert leave application
            query = """
                INSERT INTO hr_leave_applications (
                    leave_id, employee_id, leave_type, start_date,
                    end_date, half_day, number_of_days, reason,
                    contact_during_leave, current_approver, application_date,
                    status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s
                )
            """
            
            cursor.execute(query, (
                leave_id, employee_id, leave_type, start_date_obj,
                end_date_obj, half_day, number_of_days, reason,
                contact_during_leave, approver, 'Pending'
            ))
            
            # Create approval workflow
            for level, approver_role in enumerate(LEAVE_SETTINGS['approval_chain']):
                status = 'Pending' if level == 0 else 'Waiting'
                
                workflow_query = """
                    INSERT INTO hr_leave_approvals (
                        leave_id, approval_level, approver_role,
                        status, created_date
                    ) VALUES (%s, %s, %s, %s, NOW())
                """
                
                cursor.execute(workflow_query, (
                    leave_id, level, approver_role, status
                ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Created leave application: {leave_id} for {employee_id}")
            return leave_id
            
        except Exception as e:
            logger.error(f"Error creating leave application: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return None
    
    def _check_leave_eligibility(self, employee_id: str, leave_type: str, 
                               days: float, start_date: datetime.date) -> Dict[str, Any]:
        """
        Check if employee is eligible for leave
        
        Args:
            employee_id: Employee ID
            leave_type: Type of leave
            days: Number of days
            start_date: Start date
            
        Returns:
            Eligibility status and reason
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {'eligible': False, 'reason': 'Database connection failed'}
            
            cursor = conn.cursor(dictionary=True)
            
            # Check if employee exists and is active
            emp_query = """
                SELECT gender, joining_date
                FROM hr_employees
                WHERE employee_id = %s AND status = 'Active'
            """
            
            cursor.execute(emp_query, (employee_id,))
            employee = cursor.fetchone()
            
            if not employee:
                cursor.close()
                return {'eligible': False, 'reason': 'Employee not found or not active'}
            
            # Check gender-specific leaves
            if leave_type in self.leave_types:
                leave_info = self.leave_types[leave_type]
                
                if 'gender_specific' in leave_info and leave_info['gender_specific'] != employee['gender']:
                    cursor.close()
                    return {
                        'eligible': False, 
                        'reason': f"This leave type is only available for {leave_info['gender_specific']} employees"
                    }
            
            # Check leave balance
            balance = self.get_leave_balance(employee_id, leave_type)
            
            if balance['available'] < days:
                cursor.close()
                return {
                    'eligible': False, 
                    'reason': f"Insufficient leave balance. Available: {balance['available']}, Requested: {days}"
                }
            
            # Check for overlapping leave applications
            overlap_query = """
                SELECT 1
                FROM hr_leave_applications
                WHERE employee_id = %s
                AND status IN ('Pending', 'Approved')
                AND (
                    (start_date <= %s AND end_date >= %s)
                    OR (start_date <= %s AND end_date >= %s)
                    OR (start_date >= %s AND end_date <= %s)
                )
            """
            
            cursor.execute(overlap_query, (
                employee_id, 
                start_date, start_date,  # Check if start_date falls within another leave
                start_date + datetime.timedelta(days=days-1), start_date + datetime.timedelta(days=days-1),  # Check if end_date falls within another leave
                start_date, start_date + datetime.timedelta(days=days-1)  # Check if another leave falls within this one
            ))
            
            overlap = cursor.fetchone()
            
            if overlap:
                cursor.close()
                return {
                    'eligible': False, 
                    'reason': "Leave dates overlap with an existing leave application"
                }
            
            cursor.close()
            return {'eligible': True, 'reason': ''}
            
        except Exception as e:
            logger.error(f"Error checking eligibility: {e}")
            return {'eligible': False, 'reason': str(e)}
    
    def _check_leave_policy_compliance(self, leave_type: str, 
                                     start_date: datetime.date,
                                     end_date: datetime.date, 
                                     half_day: bool) -> Dict[str, Any]:
        """
        Check if leave application complies with policy
        
        Args:
            leave_type: Type of leave
            start_date: Start date
            end_date: End date
            half_day: Whether this is a half-day leave
            
        Returns:
            Compliance status and reason
        """
        try:
            # Check if leave type exists
            if leave_type not in self.leave_types:
                return {
                    'compliant': False, 
                    'reason': f"Invalid leave type: {leave_type}"
                }
            
            # Get leave type settings
            leave_info = self.leave_types[leave_type]
            
            # Check minimum notice period
            if leave_type in LEAVE_SETTINGS['minimum_notice_days']:
                min_notice = LEAVE_SETTINGS['minimum_notice_days'][leave_type]
                today = datetime.date.today()
                notice_given = (start_date - today).days
                
                if notice_given < min_notice:
                    return {
                        'compliant': False, 
                        'reason': f"Minimum notice period for {leave_type} is {min_notice} day(s)"
                    }
            
            # Check maximum consecutive days
            if not half_day and leave_type in LEAVE_SETTINGS['maximum_consecutive_days']:
                max_days = LEAVE_SETTINGS['maximum_consecutive_days'][leave_type]
                requested_days = (end_date - start_date).days + 1
                
                if requested_days > max_days:
                    return {
                        'compliant': False, 
                        'reason': f"Maximum consecutive days for {leave_type} is {max_days}"
                    }
            
            # Check weekend/holiday (basic implementation)
            # A more sophisticated implementation would check against a holiday calendar
            
            return {'compliant': True, 'reason': ''}
            
        except Exception as e:
            logger.error(f"Error checking policy compliance: {e}")
            return {'compliant': False, 'reason': str(e)}
    
    def _get_first_approver(self, employee_id: str) -> str:
        """
        Get the first approver for leave application
        
        Args:
            employee_id: Employee ID
            
        Returns:
            First approver role
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return LEAVE_SETTINGS['approval_chain'][0]
            
            cursor = conn.cursor()
            
            # Get reporting manager
            query = """
                SELECT reporting_manager_id 
                FROM hr_employees
                WHERE employee_id = %s
            """
            
            cursor.execute(query, (employee_id,))
            result = cursor.fetchone()
            cursor.close()
            
            if result and result[0]:
                return "Immediate Supervisor"
            
            # Fall back to first approver in chain
            return LEAVE_SETTINGS['approval_chain'][0]
            
        except Exception as e:
            logger.error(f"Error getting first approver: {e}")
            return LEAVE_SETTINGS['approval_chain'][0]
    
    def approve_leave(self, leave_id: str, approver_id: str, 
                    comments: str = "") -> bool:
        """
        Approve a leave application
        
        Args:
            leave_id: Leave application ID
            approver_id: Approver's employee ID
            comments: Optional comments
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor(dictionary=True)
            
            # Get leave application
            leave_query = """
                SELECT * FROM hr_leave_applications
                WHERE leave_id = %s AND status = 'Pending'
            """
            
            cursor.execute(leave_query, (leave_id,))
            leave = cursor.fetchone()
            
            if not leave:
                logger.warning(f"Leave {leave_id} not found or not pending")
                cursor.close()
                return False
            
            # Get current approval level
            approval_query = """
                SELECT * FROM hr_leave_approvals
                WHERE leave_id = %s AND status = 'Pending'
                ORDER BY approval_level ASC
                LIMIT 1
            """
            
            cursor.execute(approval_query, (leave_id,))
            approval = cursor.fetchone()
            
            if not approval:
                logger.warning(f"No pending approvals found for leave {leave_id}")
                cursor.close()
                return False
            
            # Update approval status
            update_query = """
                UPDATE hr_leave_approvals
                SET status = 'Approved', approver_id = %s,
                    approval_date = NOW(), comments = %s
                WHERE leave_id = %s AND approval_level = %s
            """
            
            cursor.execute(update_query, (
                approver_id, comments, leave_id, approval['approval_level']
            ))
            
            # Check if this was the final approval
            next_level = approval['approval_level'] + 1
            
            next_query = """
                SELECT * FROM hr_leave_approvals
                WHERE leave_id = %s AND approval_level = %s
            """
            
            cursor.execute(next_query, (leave_id, next_level))
            next_approval = cursor.fetchone()
            
            if next_approval:
                # Update next approval to Pending
                next_update_query = """
                    UPDATE hr_leave_approvals
                    SET status = 'Pending'
                    WHERE leave_id = %s AND approval_level = %s
                """
                
                cursor.execute(next_update_query, (leave_id, next_level))
                
                # Update leave application with new approver
                app_update_query = """
                    UPDATE hr_leave_applications
                    SET current_approver = %s
                    WHERE leave_id = %s
                """
                
                cursor.execute(app_update_query, (
                    next_approval['approver_role'], leave_id
                ))
                
            else:
                # Final approval - update leave status
                final_query = """
                    UPDATE hr_leave_applications
                    SET status = 'Approved', approved_date = NOW()
                    WHERE leave_id = %s
                """
                
                cursor.execute(final_query, (leave_id,))
                
                # Deduct from leave balance
                self._update_leave_balance(
                    leave['employee_id'], leave['leave_type'], 
                    leave['number_of_days'], 'deduct'
                )
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Approved leave {leave_id} at level {approval['approval_level']}")
            return True
            
        except Exception as e:
            logger.error(f"Error approving leave {leave_id}: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def reject_leave(self, leave_id: str, approver_id: str, 
                   reason: str = "") -> bool:
        """
        Reject a leave application
        
        Args:
            leave_id: Leave application ID
            approver_id: Approver's employee ID
            reason: Rejection reason
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor(dictionary=True)
            
            # Get leave application
            leave_query = """
                SELECT * FROM hr_leave_applications
                WHERE leave_id = %s AND status = 'Pending'
            """
            
            cursor.execute(leave_query, (leave_id,))
            leave = cursor.fetchone()
            
            if not leave:
                logger.warning(f"Leave {leave_id} not found or not pending")
                cursor.close()
                return False
            
            # Get current approval level
            approval_query = """
                SELECT * FROM hr_leave_approvals
                WHERE leave_id = %s AND status = 'Pending'
                ORDER BY approval_level ASC
                LIMIT 1
            """
            
            cursor.execute(approval_query, (leave_id,))
            approval = cursor.fetchone()
            
            if not approval:
                logger.warning(f"No pending approvals found for leave {leave_id}")
                cursor.close()
                return False
            
            # Update approval status
            update_query = """
                UPDATE hr_leave_approvals
                SET status = 'Rejected', approver_id = %s,
                    approval_date = NOW(), comments = %s
                WHERE leave_id = %s AND approval_level = %s
            """
            
            cursor.execute(update_query, (
                approver_id, reason, leave_id, approval['approval_level']
            ))
            
            # Update leave application status
            app_update_query = """
                UPDATE hr_leave_applications
                SET status = 'Rejected', rejection_reason = %s
                WHERE leave_id = %s
            """
            
            cursor.execute(app_update_query, (reason, leave_id))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Rejected leave {leave_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error rejecting leave {leave_id}: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def cancel_leave(self, leave_id: str, requester_id: str, 
                   reason: str = "") -> bool:
        """
        Cancel a leave application
        
        Args:
            leave_id: Leave application ID
            requester_id: Employee ID of person requesting cancellation
            reason: Cancellation reason
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor(dictionary=True)
            
            # Get leave application
            leave_query = """
                SELECT * FROM hr_leave_applications
                WHERE leave_id = %s
            """
            
            cursor.execute(leave_query, (leave_id,))
            leave = cursor.fetchone()
            
            if not leave:
                logger.warning(f"Leave {leave_id} not found")
                cursor.close()
                return False
            
            # Check if cancelation is possible
            if leave['status'] not in ('Pending', 'Approved'):
                logger.warning(f"Leave {leave_id} cannot be canceled (status: {leave['status']})")
                cursor.close()
                return False
            
            # If leave has started, mark as partial cancellation
            today = datetime.date.today()
            leave_start = leave['start_date'] if isinstance(leave['start_date'], datetime.date) else datetime.datetime.strptime(leave['start_date'], '%Y-%m-%d').date()
            leave_end = leave['end_date'] if isinstance(leave['end_date'], datetime.date) else datetime.datetime.strptime(leave['end_date'], '%Y-%m-%d').date()
            
            status = 'Canceled'
            days_to_refund = leave['number_of_days']
            
            if today > leave_start:
                if today <= leave_end:
                    # Partial cancellation
                    status = 'Partially Canceled'
                    days_taken = (today - leave_start).days
                    days_to_refund = leave['number_of_days'] - days_taken
                else:
                    # Leave already completed
                    cursor.close()
                    return False
            
            # Update leave status
            update_query = """
                UPDATE hr_leave_applications
                SET status = %s, cancellation_reason = %s,
                    canceled_by = %s, cancellation_date = NOW()
                WHERE leave_id = %s
            """
            
            cursor.execute(update_query, (
                status, reason, requester_id, leave_id
            ))
            
            # If leave was approved, refund the balance
            if leave['status'] == 'Approved' and days_to_refund > 0:
                self._update_leave_balance(
                    leave['employee_id'], leave['leave_type'], 
                    days_to_refund, 'add'
                )
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Canceled leave {leave_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error canceling leave {leave_id}: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def _update_leave_balance(self, employee_id: str, leave_type: str, 
                            days: float, operation: str) -> bool:
        """
        Update leave balance
        
        Args:
            employee_id: Employee ID
            leave_type: Leave type code
            days: Number of days
            operation: 'add' or 'deduct'
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Check if balance record exists for current year
            current_year = datetime.date.today().year
            
            check_query = """
                SELECT * FROM hr_employee_leave_balances
                WHERE employee_id = %s AND leave_type = %s AND year = %s
            """
            
            cursor.execute(check_query, (employee_id, leave_type, current_year))
            balance_record = cursor.fetchone()
            
            days = float(days)
            
            if balance_record:
                # Update existing record
                if operation == 'add':
                    update_query = """
                        UPDATE hr_employee_leave_balances
                        SET available = available + %s,
                            last_updated = NOW()
                        WHERE employee_id = %s AND leave_type = %s AND year = %s
                    """
                else:  # deduct
                    update_query = """
                        UPDATE hr_employee_leave_balances
                        SET available = available - %s,
                            used = used + %s,
                            last_updated = NOW()
                        WHERE employee_id = %s AND leave_type = %s AND year = %s
                    """
                
                if operation == 'add':
                    cursor.execute(update_query, (
                        days, employee_id, leave_type, current_year
                    ))
                else:
                    cursor.execute(update_query, (
                        days, days, employee_id, leave_type, current_year
                    ))
                    
            else:
                # Create new record
                quota = 0
                if leave_type in self.leave_types:
                    quota = self.leave_types[leave_type].get('annual_quota', 0)
                
                available = quota - days if operation == 'deduct' else quota + days
                used = days if operation == 'deduct' else 0
                
                insert_query = """
                    INSERT INTO hr_employee_leave_balances (
                        employee_id, leave_type, year, quota,
                        available, used, last_updated
                    ) VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """
                
                cursor.execute(insert_query, (
                    employee_id, leave_type, current_year,
                    quota, available, used
                ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"{operation.capitalize()}ed {days} days from {employee_id}'s {leave_type} balance")
            return True
            
        except Exception as e:
            logger.error(f"Error updating leave balance: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def get_leave_balance(self, employee_id: str, leave_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get employee leave balance
        
        Args:
            employee_id: Employee ID
            leave_type: Optional specific leave type
            
        Returns:
            Leave balance information
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            current_year = datetime.date.today().year
            
            if leave_type:
                # Get balance for specific leave type
                query = """
                    SELECT * FROM hr_employee_leave_balances
                    WHERE employee_id = %s AND leave_type = %s AND year = %s
                """
                
                cursor.execute(query, (employee_id, leave_type, current_year))
                balance = cursor.fetchone()
                
                if balance:
                    result = {
                        'leave_type': leave_type,
                        'quota': balance['quota'],
                        'available': balance['available'],
                        'used': balance['used']
                    }
                else:
                    # Get quota from settings
                    quota = 0
                    if leave_type in self.leave_types:
                        quota = self.leave_types[leave_type].get('annual_quota', 0)
                        
                    result = {
                        'leave_type': leave_type,
                        'quota': quota,
                        'available': quota,
                        'used': 0
                    }
                    
                cursor.close()
                return result
                
            else:
                # Get balance for all leave types
                query = """
                    SELECT * FROM hr_employee_leave_balances
                    WHERE employee_id = %s AND year = %s
                """
                
                cursor.execute(query, (employee_id, current_year))
                balances = cursor.fetchall()
                
                # Convert to dictionary by leave type
                result = {}
                existing_types = set()
                
                for balance in balances:
                    lt = balance['leave_type']
                    existing_types.add(lt)
                    result[lt] = {
                        'quota': balance['quota'],
                        'available': balance['available'],
                        'used': balance['used']
                    }
                
                # Add missing leave types
                for lt_code, lt_info in self.leave_types.items():
                    if lt_code not in existing_types:
                        # Check gender-specific leaves
                        if 'gender_specific' in lt_info:
                            # Get employee gender
                            gender_query = """
                                SELECT gender FROM hr_employees
                                WHERE employee_id = %s
                            """
                            
                            cursor.execute(gender_query, (employee_id,))
                            emp = cursor.fetchone()
                            
                            if not emp or emp['gender'] != lt_info['gender_specific']:
                                continue
                        
                        quota = lt_info.get('annual_quota', 0)
                        result[lt_code] = {
                            'quota': quota,
                            'available': quota,
                            'used': 0
                        }
                
                cursor.close()
                return result
                
        except Exception as e:
            logger.error(f"Error getting leave balance: {e}")
            return {}
    
    def get_leave_applications(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get leave applications based on filters
        
        Args:
            filters: Filter criteria
            
        Returns:
            List of leave applications
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Build WHERE conditions based on filters
            conditions = []
            params = []
            
            if 'employee_id' in filters:
                conditions.append("l.employee_id = %s")
                params.append(filters['employee_id'])
            
            if 'status' in filters:
                conditions.append("l.status = %s")
                params.append(filters['status'])
            
            if 'leave_type' in filters:
                conditions.append("l.leave_type = %s")
                params.append(filters['leave_type'])
            
            if 'from_date' in filters:
                conditions.append("l.start_date >= %s")
                params.append(filters['from_date'])
            
            if 'to_date' in filters:
                conditions.append("l.end_date <= %s")
                params.append(filters['to_date'])
            
            if 'approver_id' in filters:
                conditions.append("l.current_approver = %s OR a.approver_id = %s")
                params.append(filters['approver_id'])
                params.append(filters['approver_id'])
            
            # Build the full query
            query = """
                SELECT l.*, e.first_name, e.last_name
                FROM hr_leave_applications l
                JOIN hr_employees e ON l.employee_id = e.employee_id
                LEFT JOIN hr_leave_approvals a ON l.leave_id = a.leave_id
            """
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            # Add order by
            query += " ORDER BY l.application_date DESC"
            
            # Add limit if specified
            if 'limit' in filters:
                query += " LIMIT %s"
                params.append(filters['limit'])
            else:
                # Default limit
                query += " LIMIT 100"
            
            # Execute the query
            cursor.execute(query, params)
            applications = cursor.fetchall()
            cursor.close()
            
            return applications
            
        except Exception as e:
            logger.error(f"Error getting leave applications: {e}")
            return []
    
    def add_holiday(self, holiday_data: Dict[str, Any]) -> bool:
        """
        Add a holiday to the calendar
        
        Args:
            holiday_data: Holiday details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Extract holiday information
            name = holiday_data.get('name', '')
            date = holiday_data.get('date')
            description = holiday_data.get('description', '')
            recurring = holiday_data.get('recurring', False)
            
            # Insert holiday
            query = """
                INSERT INTO hr_holidays (
                    name, date, description, recurring
                ) VALUES (%s, %s, %s, %s)
            """
            
            cursor.execute(query, (name, date, description, recurring))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Added holiday: {name} on {date}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding holiday: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def get_holidays(self, year: int) -> List[Dict[str, Any]]:
        """
        Get holidays for a specific year
        
        Args:
            year: Year
            
        Returns:
            List of holidays
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Get holidays for specified year
            query = """
                SELECT * FROM hr_holidays
                WHERE (YEAR(date) = %s)
                OR recurring = 1
                ORDER BY date            """
            
            cursor.execute(query, (year,))
            holidays_data = cursor.fetchall()
            cursor.close()
            
            # Process recurring holidays
            holidays = []
            
            for holiday in holidays_data:
                if holiday['recurring']:
                    # For recurring holidays, adjust the year
                    date = holiday['date']
                    if isinstance(date, str):
                        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
                    elif isinstance(date, datetime.datetime):
                        date = date.date()
                        
                    updated_date = date.replace(year=year)
                    holiday['date'] = updated_date
                    
                holidays.append(holiday)
                
            return holidays
            
        except Exception as e:
            logger.error(f"Error getting holidays for {year}: {e}")
            return []
    def initialize_leave_balances(self, year: Optional[int] = None) -> bool:
        """
        Initialize leave balances for all active employees
        
        Args:
            year: Year (defaults to current year)
            
        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor(dictionary=True)
            
            # Use current year if not specified
            if not year:
                year = datetime.date.today().year
            
            # Get all active employees
            query = """
                SELECT employee_id, first_name, last_name, gender
                FROM hr_employees
                WHERE status = 'Active'
            """
            
            cursor.execute(query)
            employees = cursor.fetchall()
            
            for employee in employees:
                emp_id = employee['employee_id']
                gender = employee['gender']
                
                # Process each leave type
                for lt_code, lt_info in self.leave_types.items():
                    # Skip gender-specific leaves that don't apply
                    if 'gender_specific' in lt_info and lt_info['gender_specific'] != gender:
                        continue
                    
                    # Check if balance already exists
                    check_query = """
                        SELECT 1 FROM hr_employee_leave_balances
                        WHERE employee_id = %s AND leave_type = %s AND year = %s
                    """
                    
                    cursor.execute(check_query, (emp_id, lt_code, year))
                    exists = cursor.fetchone()
                    
                    if not exists:
                        quota = lt_info.get('annual_quota', 0)
                        
                        # Calculate carried forward days if applicable
                        carried_forward = 0
                        if lt_info.get('carry_forward', False) and year > 2023:  # Assume system started in 2023
                            # Get previous year's balance
                            prev_query = """
                                SELECT available FROM hr_employee_leave_balances
                                WHERE employee_id = %s AND leave_type = %s AND year = %s
                            """
                            
                            cursor.execute(prev_query, (emp_id, lt_code, year - 1))
                            prev_balance = cursor.fetchone()
                            
                            if prev_balance and prev_balance['available'] > 0:
                                max_carry = lt_info.get('max_carry_forward', 0)
                                carried_forward = min(prev_balance['available'], max_carry)
                        
                        # Insert new balance record
                        insert_query = """
                            INSERT INTO hr_employee_leave_balances (
                                employee_id, leave_type, year, quota,
                                carried_forward, available, used, last_updated
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                        """
                        
                        cursor.execute(insert_query, (
                            emp_id, lt_code, year, quota,
                            carried_forward, quota + carried_forward, 0
                        ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Initialized leave balances for {len(employees)} employees for year {year}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing leave balances: {e}")
            
            # Rollback if needed
            if conn:
                try:
                    conn.rollback()
                except Exception as rollback_error:
                    logger.error(f"Error during rollback: {rollback_error}")
                
            return False
        finally:
            # Close cursor if needed
            if 'cursor' in locals() and cursor:
                try:
                    cursor.close()
                except Exception as cursor_error:
                    logger.error(f"Error closing cursor: {cursor_error}")
    def get_leave_analytics(self, year: int = None) -> Dict[str, Any]:
        """
        Get leave analytics
        
        Args:
            year: Year (defaults to current year)
            
        Returns:
            Leave analytics data with usage by leave type, department statistics,
            monthly patterns, and top leave takers
        """
        conn = None
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Use current year if not specified
            if not year:
                year = datetime.date.today().year
            
            # Get leave usage by type
            usage_query = """
                SELECT leave_type, 
                    COUNT(*) AS application_count,
                    SUM(number_of_days) AS total_days
                FROM hr_leave_applications
                WHERE status = 'Approved'
                AND YEAR(start_date) = %s
                GROUP BY leave_type
            """
            
            cursor.execute(usage_query, (year,))
            usage_data = cursor.fetchall()
            
            # Get department-wise leave statistics
            dept_query = """
                SELECT e.department,
                    COUNT(DISTINCT l.employee_id) AS employee_count,
                    SUM(l.number_of_days) AS total_days
                FROM hr_leave_applications l
                JOIN hr_employees e ON l.employee_id = e.employee_id
                WHERE l.status = 'Approved'
                AND YEAR(l.start_date) = %s
                GROUP BY e.department
                ORDER BY total_days DESC
            """
            
            cursor.execute(dept_query, (year,))
            department_data = cursor.fetchall()
            
            # Get monthly leave pattern
            monthly_query = """
                SELECT MONTH(start_date) AS month,
                    COUNT(*) AS application_count,
                    SUM(number_of_days) AS total_days
                FROM hr_leave_applications
                WHERE status = 'Approved'
                AND YEAR(start_date) = %s
                GROUP BY MONTH(start_date)
                ORDER BY MONTH(start_date)
            """
            
            cursor.execute(monthly_query, (year,))
            monthly_data = cursor.fetchall()
            
            # Get top leave takers
            top_query = """
                SELECT e.employee_id, e.first_name, e.last_name,
                    e.department, COUNT(l.leave_id) AS leave_count,
                    SUM(l.number_of_days) AS total_days
                FROM hr_leave_applications l
                JOIN hr_employees e ON l.employee_id = e.employee_id
                WHERE l.status = 'Approved'
                AND YEAR(l.start_date) = %s
                GROUP BY e.employee_id
                ORDER BY total_days DESC
                LIMIT 10
            """
            
            cursor.execute(top_query, (year,))
            top_employees = cursor.fetchall()
            
            cursor.close()
            
            # Create month names for readable months
            month_names = [
                'January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December'
            ]
            
            for month_data in monthly_data:
                if 'month' in month_data and 1 <= month_data['month'] <= 12:
                    month_data['month_name'] = month_names[month_data['month'] - 1]
            
            # Compile analytics
            analytics = {
                'year': year,
                'leave_usage_by_type': usage_data,
                'department_statistics': department_data,
                'monthly_pattern': monthly_data,
                'top_leave_takers': top_employees
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting leave analytics: {e}")
            return {}
        finally:
            # Close cursor if it exists
            if 'cursor' in locals() and cursor:
                try:
                    cursor.close()
                except Exception as cursor_error:
                    logger.error(f"Error closing cursor: {cursor_error}")


# Singleton instance
leave_manager = LeaveManager()


def get_leave_manager() -> LeaveManager:
    """Get the leave manager instance"""
    return leave_manager
