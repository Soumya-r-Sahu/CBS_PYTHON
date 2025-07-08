"""
Performance Management Module

This module handles all performance-related functionalities including:
- Goal setting and tracking
- Performance reviews
- Feedback collection
- Performance improvement plans
"""

import os
import sys
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import uuid
import json

# Add parent directory to path if needed
# Removed: sys.path.insert(0, str(Path(__file__).parent.parent))
# Removed: sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import HR-ERP modules
from hr_erp.config import PERFORMANCE_SETTINGS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('hr-performance')


class PerformanceManager:
    """Performance management for HR-ERP system"""
    
    def __init__(self):
        """Initialize the performance manager"""
        self.db_connection = None
        self._initialize_db_connection()
    
    def _initialize_db_connection(self):
        """Initialize database connection"""
        try:
            # Import database connection
            # Commented out direct sys.path modification
            # # Removed: sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            from utils.lib.packages import fix_path
            fix_path()
            from utils.lib.packages import import_module
            DatabaseConnection = import_module("database.python.connection").DatabaseConnection
            
            self.db_connection = DatabaseConnection()
            logger.info("Database connection initialized for performance management")
            
        except ImportError:
            logger.error("Failed to import DatabaseConnection")
    
    def create_performance_review_cycle(self, cycle_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new performance review cycle
        
        Args:
            cycle_data: Cycle details
            
        Returns:
            Cycle ID if successful, None otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            cursor = conn.cursor()
            
            # Generate cycle ID
            cycle_id = f"CYCLE-{cycle_data.get('year', datetime.datetime.now().year)}-{uuid.uuid4().hex[:6].upper()}"
            
            # Extract cycle information
            cycle_name = cycle_data.get('name', f"Review Cycle {datetime.datetime.now().year}")
            cycle_year = cycle_data.get('year', datetime.datetime.now().year)
            cycle_type = cycle_data.get('type', 'Annual')
            start_date = cycle_data.get('start_date')
            end_date = cycle_data.get('end_date')
            goal_setting_start = cycle_data.get('goal_setting_start')
            goal_setting_end = cycle_data.get('goal_setting_end')
            self_review_start = cycle_data.get('self_review_start')
            self_review_end = cycle_data.get('self_review_end')
            manager_review_start = cycle_data.get('manager_review_start')
            manager_review_end = cycle_data.get('manager_review_end')
            calibration_start = cycle_data.get('calibration_start')
            calibration_end = cycle_data.get('calibration_end')
            finalization_date = cycle_data.get('finalization_date')
            description = cycle_data.get('description', '')
            
            # Insert cycle record
            query = """
                INSERT INTO hr_performance_cycles (
                    cycle_id, cycle_name, cycle_year, cycle_type,
                    start_date, end_date, goal_setting_start, goal_setting_end,
                    self_review_start, self_review_end, manager_review_start,
                    manager_review_end, calibration_start, calibration_end,
                    finalization_date, description, status, created_date
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
            """
            
            cursor.execute(query, (
                cycle_id, cycle_name, cycle_year, cycle_type,
                start_date, end_date, goal_setting_start, goal_setting_end,
                self_review_start, self_review_end, manager_review_start,
                manager_review_end, calibration_start, calibration_end,
                finalization_date, description, 'Created'
            ))
            
            # Add review parameters
            parameters = cycle_data.get('parameters', PERFORMANCE_SETTINGS['default_review_parameters'])
            
            for index, param in enumerate(parameters):
                param_query = """
                    INSERT INTO hr_performance_parameters (
                        cycle_id, parameter_name, parameter_description,
                        weight, display_order
                    ) VALUES (%s, %s, %s, %s, %s)
                """
                
                weight = 100.0 / len(parameters)  # Equal weight distribution
                
                cursor.execute(param_query, (
                    cycle_id, 
                    param if isinstance(param, str) else param.get('name', ''),
                    param.get('description', '') if not isinstance(param, str) else '',
                    param.get('weight', weight) if not isinstance(param, str) else weight,
                    index + 1
                ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Created performance review cycle: {cycle_id}")
            return cycle_id
            
        except Exception as e:
            logger.error(f"Error creating performance review cycle: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return None
    
    def get_active_review_cycles(self) -> List[Dict[str, Any]]:
        """
        Get active review cycles
        
        Returns:
            List of active review cycles
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Get active cycles
            query = """
                SELECT *
                FROM hr_performance_cycles
                WHERE status IN ('Created', 'In Progress', 'Goal Setting', 'Self Review', 'Manager Review')
                ORDER BY start_date DESC
            """
            
            cursor.execute(query)
            cycles = cursor.fetchall()
            cursor.close()
            
            return cycles
            
        except Exception as e:
            logger.error(f"Error getting active review cycles: {e}")
            return []
    
    def update_cycle_status(self, cycle_id: str, status: str) -> bool:
        """
        Update review cycle status
        
        Args:
            cycle_id: Cycle ID
            status: New status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Update cycle status
            query = """
                UPDATE hr_performance_cycles
                SET status = %s, last_modified = NOW()
                WHERE cycle_id = %s
            """
            
            cursor.execute(query, (status, cycle_id))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Updated cycle {cycle_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating cycle {cycle_id} status: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def assign_reviewees(self, cycle_id: str, 
                       department: Optional[str] = None, 
                       employees: Optional[List[str]] = None) -> bool:
        """
        Assign reviewees to a cycle
        
        Args:
            cycle_id: Cycle ID
            department: Department to assign (optional)
            employees: List of employee IDs (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor(dictionary=True)
            
            # Check if cycle exists
            check_query = """
                SELECT 1 FROM hr_performance_cycles
                WHERE cycle_id = %s
            """
            
            cursor.execute(check_query, (cycle_id,))
            if not cursor.fetchone():
                logger.warning(f"Cycle {cycle_id} not found")
                cursor.close()
                return False
            
            # Get employees to assign
            employee_ids = []
            
            if employees:
                # Use provided employee list
                employee_ids = employees
            elif department:
                # Get employees from department
                dept_query = """
                    SELECT employee_id
                    FROM hr_employees
                    WHERE department = %s
                    AND status = 'Active'
                """
                
                cursor.execute(dept_query, (department,))
                emp_results = cursor.fetchall()
                employee_ids = [emp['employee_id'] for emp in emp_results]
            else:
                # Get all active employees
                all_query = """
                    SELECT employee_id
                    FROM hr_employees
                    WHERE status = 'Active'
                """
                
                cursor.execute(all_query)
                emp_results = cursor.fetchall()
                employee_ids = [emp['employee_id'] for emp in emp_results]
            
            # Remove already assigned employees
            existing_query = """
                SELECT employee_id
                FROM hr_performance_reviews
                WHERE cycle_id = %s
            """
            
            cursor.execute(existing_query, (cycle_id,))
            existing = cursor.fetchall()
            existing_ids = [e['employee_id'] for e in existing]
            
            to_assign = [e_id for e_id in employee_ids if e_id not in existing_ids]
            
            # Create review records for each employee
            for emp_id in to_assign:
                # Get employee's manager
                manager_query = """
                    SELECT reporting_manager_id
                    FROM hr_employees
                    WHERE employee_id = %s
                """
                
                cursor.execute(manager_query, (emp_id,))
                emp_data = cursor.fetchone()
                manager_id = emp_data['reporting_manager_id'] if emp_data else None
                
                # Generate review ID
                review_id = f"REV-{cycle_id.split('-')[1]}-{uuid.uuid4().hex[:6].upper()}"
                
                # Insert review record
                insert_query = """
                    INSERT INTO hr_performance_reviews (
                        review_id, cycle_id, employee_id, reviewer_id,
                        status, created_date
                    ) VALUES (%s, %s, %s, %s, %s, NOW())
                """
                
                cursor.execute(insert_query, (
                    review_id, cycle_id, emp_id, manager_id, 'Not Started'
                ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Assigned {len(to_assign)} employees to cycle {cycle_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error assigning reviewees to cycle {cycle_id}: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def set_employee_goals(self, review_id: str, goals: List[Dict[str, Any]]) -> bool:
        """
        Set goals for an employee's review
        
        Args:
            review_id: Review ID
            goals: List of goal details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor(dictionary=True)
            
            # Check if review exists
            check_query = """
                SELECT r.review_id, r.employee_id, r.cycle_id, c.status AS cycle_status
                FROM hr_performance_reviews r
                JOIN hr_performance_cycles c ON r.cycle_id = c.cycle_id
                WHERE r.review_id = %s
            """
            
            cursor.execute(check_query, (review_id,))
            review = cursor.fetchone()
            
            if not review:
                logger.warning(f"Review {review_id} not found")
                cursor.close()
                return False
            
            # Check if goals can be set for this cycle
            if review['cycle_status'] not in ('Created', 'In Progress', 'Goal Setting'):
                logger.warning(f"Cannot set goals for cycle in '{review['cycle_status']}' status")
                cursor.close()
                return False
            
            # Delete existing goals
            delete_query = """
                DELETE FROM hr_employee_goals
                WHERE review_id = %s
            """
            
            cursor.execute(delete_query, (review_id,))
            
            # Insert new goals
            for index, goal in enumerate(goals):
                goal_query = """
                    INSERT INTO hr_employee_goals (
                        review_id, employee_id, goal_title,
                        description, measurement_criteria, weight,
                        goal_type, start_date, end_date,
                        display_order, status
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(goal_query, (
                    review_id,
                    review['employee_id'],
                    goal.get('title', ''),
                    goal.get('description', ''),
                    goal.get('measurement', ''),
                    goal.get('weight', 100.0 / len(goals)),
                    goal.get('type', 'Individual'),
                    goal.get('start_date'),
                    goal.get('end_date'),
                    index + 1,
                    'Not Started'
                ))
            
            # Update review status
            update_query = """
                UPDATE hr_performance_reviews
                SET status = 'Goals Set'
                WHERE review_id = %s
            """
            
            cursor.execute(update_query, (review_id,))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Set {len(goals)} goals for review {review_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting goals for review {review_id}: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def submit_self_review(self, review_id: str, 
                         self_ratings: Dict[str, Any]) -> bool:
        """
        Submit self-review
        
        Args:
            review_id: Review ID
            self_ratings: Self-assessment ratings
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor(dictionary=True)
            
            # Check if review exists and is in the right state
            check_query = """
                SELECT r.review_id, r.employee_id, r.cycle_id, r.status AS review_status,
                       c.status AS cycle_status
                FROM hr_performance_reviews r
                JOIN hr_performance_cycles c ON r.cycle_id = c.cycle_id
                WHERE r.review_id = %s
            """
            
            cursor.execute(check_query, (review_id,))
            review = cursor.fetchone()
            
            if not review:
                logger.warning(f"Review {review_id} not found")
                cursor.close()
                return False
            
            # Check if self-review is allowed in this cycle
            if review['cycle_status'] not in ('Self Review', 'In Progress', 'Manager Review'):
                logger.warning(f"Self-review not allowed for cycle in '{review['cycle_status']}' status")
                cursor.close()
                return False
            
            # Process parameter ratings
            if 'parameters' in self_ratings:
                for param_rating in self_ratings['parameters']:
                    # Check if parameter exists for this cycle
                    param_check_query = """
                        SELECT parameter_id
                        FROM hr_performance_parameters
                        WHERE cycle_id = %s AND parameter_name = %s
                    """
                    
                    cursor.execute(param_check_query, (
                        review['cycle_id'], param_rating.get('name', '')
                    ))
                    
                    param_result = cursor.fetchone()
                    
                    if not param_result:
                        continue
                        
                    # Save parameter rating
                    param_id = param_result['parameter_id']
                    
                    # Check if rating already exists
                    rating_check_query = """
                        SELECT 1
                        FROM hr_performance_ratings
                        WHERE review_id = %s AND parameter_id = %s
                    """
                    
                    cursor.execute(rating_check_query, (review_id, param_id))
                    
                    if cursor.fetchone():
                        # Update existing rating
                        update_query = """
                            UPDATE hr_performance_ratings
                            SET self_rating = %s, self_comments = %s,
                                last_modified = NOW()
                            WHERE review_id = %s AND parameter_id = %s
                        """
                        
                        cursor.execute(update_query, (
                            param_rating.get('rating', 3),
                            param_rating.get('comments', ''),
                            review_id,
                            param_id
                        ))
                    else:
                        # Create new rating
                        insert_query = """
                            INSERT INTO hr_performance_ratings (
                                review_id, parameter_id, self_rating,
                                self_comments, created_date
                            ) VALUES (%s, %s, %s, %s, NOW())
                        """
                        
                        cursor.execute(insert_query, (
                            review_id,
                            param_id,
                            param_rating.get('rating', 3),
                            param_rating.get('comments', '')
                        ))
            
            # Process goal self-assessments
            if 'goals' in self_ratings:
                for goal_assessment in self_ratings['goals']:
                    goal_id = goal_assessment.get('goal_id')
                    
                    if not goal_id:
                        continue
                        
                    # Update goal with self-assessment
                    goal_update_query = """
                        UPDATE hr_employee_goals
                        SET self_assessment = %s, self_rating = %s,
                            status = %s, last_modified = NOW()
                        WHERE goal_id = %s AND review_id = %s
                    """
                    
                    cursor.execute(goal_update_query, (
                        goal_assessment.get('assessment', ''),
                        goal_assessment.get('rating', 3),
                        goal_assessment.get('status', 'In Progress'),
                        goal_id,
                        review_id
                    ))
            
            # Update review status
            update_query = """
                UPDATE hr_performance_reviews
                SET status = 'Self Review Completed', self_review_date = NOW()
                WHERE review_id = %s
            """
            
            cursor.execute(update_query, (review_id,))
            
            # Add review summary comments if provided
            if 'summary' in self_ratings:
                summary_query = """
                    UPDATE hr_performance_reviews
                    SET self_summary = %s
                    WHERE review_id = %s
                """
                
                cursor.execute(summary_query, (
                    self_ratings['summary'],
                    review_id
                ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Submitted self-review for {review_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting self-review for {review_id}: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def submit_manager_review(self, review_id: str, 
                            manager_ratings: Dict[str, Any]) -> bool:
        """
        Submit manager review
        
        Args:
            review_id: Review ID
            manager_ratings: Manager assessment ratings
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor(dictionary=True)
            
            # Check if review exists and is in the right state
            check_query = """
                SELECT r.review_id, r.employee_id, r.cycle_id, r.status AS review_status,
                       c.status AS cycle_status
                FROM hr_performance_reviews r
                JOIN hr_performance_cycles c ON r.cycle_id = c.cycle_id
                WHERE r.review_id = %s
            """
            
            cursor.execute(check_query, (review_id,))
            review = cursor.fetchone()
            
            if not review:
                logger.warning(f"Review {review_id} not found")
                cursor.close()
                return False
            
            # Check if manager review is allowed in this cycle
            allowed_statuses = ('Manager Review', 'In Progress')
            
            if review['cycle_status'] not in allowed_statuses:
                logger.warning(f"Manager review not allowed for cycle in '{review['cycle_status']}' status")
                cursor.close()
                return False
            
            # Process parameter ratings
            if 'parameters' in manager_ratings:
                for param_rating in manager_ratings['parameters']:
                    # Check if parameter exists for this cycle
                    param_check_query = """
                        SELECT parameter_id
                        FROM hr_performance_parameters
                        WHERE cycle_id = %s AND parameter_name = %s
                    """
                    
                    cursor.execute(param_check_query, (
                        review['cycle_id'], param_rating.get('name', '')
                    ))
                    
                    param_result = cursor.fetchone()
                    
                    if not param_result:
                        continue
                        
                    # Save parameter rating
                    param_id = param_result['parameter_id']
                    
                    # Check if rating already exists
                    rating_check_query = """
                        SELECT 1
                        FROM hr_performance_ratings
                        WHERE review_id = %s AND parameter_id = %s
                    """
                    
                    cursor.execute(rating_check_query, (review_id, param_id))
                    
                    if cursor.fetchone():
                        # Update existing rating
                        update_query = """
                            UPDATE hr_performance_ratings
                            SET manager_rating = %s, manager_comments = %s,
                                last_modified = NOW()
                            WHERE review_id = %s AND parameter_id = %s
                        """
                        
                        cursor.execute(update_query, (
                            param_rating.get('rating', 3),
                            param_rating.get('comments', ''),
                            review_id,
                            param_id
                        ))
                    else:
                        # Create new rating
                        insert_query = """
                            INSERT INTO hr_performance_ratings (
                                review_id, parameter_id, manager_rating,
                                manager_comments, created_date
                            ) VALUES (%s, %s, %s, %s, NOW())
                        """
                        
                        cursor.execute(insert_query, (
                            review_id,
                            param_id,
                            param_rating.get('rating', 3),
                            param_rating.get('comments', '')
                        ))
            
            # Process goal assessments
            if 'goals' in manager_ratings:
                for goal_assessment in manager_ratings['goals']:
                    goal_id = goal_assessment.get('goal_id')
                    
                    if not goal_id:
                        continue
                        
                    # Update goal with manager assessment
                    goal_update_query = """
                        UPDATE hr_employee_goals
                        SET manager_assessment = %s, manager_rating = %s,
                            status = %s, last_modified = NOW()
                        WHERE goal_id = %s AND review_id = %s
                    """
                    
                    cursor.execute(goal_update_query, (
                        goal_assessment.get('assessment', ''),
                        goal_assessment.get('rating', 3),
                        goal_assessment.get('status', 'Completed'),
                        goal_id,
                        review_id
                    ))
            
            # Update overall rating if provided
            if 'overall_rating' in manager_ratings:
                overall_query = """
                    UPDATE hr_performance_reviews
                    SET overall_rating = %s, last_modified = NOW()
                    WHERE review_id = %s
                """
                
                cursor.execute(overall_query, (
                    manager_ratings['overall_rating'],
                    review_id
                ))
            
            # Update review status
            update_query = """
                UPDATE hr_performance_reviews
                SET status = 'Manager Review Completed', manager_review_date = NOW()
                WHERE review_id = %s
            """
            
            cursor.execute(update_query, (review_id,))
            
            # Add review summary comments if provided
            if 'summary' in manager_ratings:
                summary_query = """
                    UPDATE hr_performance_reviews
                    SET manager_summary = %s
                    WHERE review_id = %s
                """
                
                cursor.execute(summary_query, (
                    manager_ratings['summary'],
                    review_id
                ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Submitted manager review for {review_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting manager review for {review_id}: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def finalize_review(self, review_id: str, 
                      final_ratings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Finalize a performance review
        
        Args:
            review_id: Review ID
            final_ratings: Final ratings adjustments (optional)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor(dictionary=True)
            
            # Check if review exists and is ready for finalization
            check_query = """
                SELECT r.review_id, r.employee_id, r.cycle_id, r.status AS review_status,
                       c.status AS cycle_status
                FROM hr_performance_reviews r
                JOIN hr_performance_cycles c ON r.cycle_id = c.cycle_id
                WHERE r.review_id = %s
            """
            
            cursor.execute(check_query, (review_id,))
            review = cursor.fetchone()
            
            if not review:
                logger.warning(f"Review {review_id} not found")
                cursor.close()
                return False
            
            # Check if review can be finalized
            if review['review_status'] not in ('Manager Review Completed', 'Calibrated'):
                logger.warning(f"Review {review_id} is not ready for finalization")
                cursor.close()
                return False
            
            # Apply final rating adjustments if provided
            if final_ratings:
                # Update overall rating if provided
                if 'overall_rating' in final_ratings:
                    overall_query = """
                        UPDATE hr_performance_reviews
                        SET overall_rating = %s, last_modified = NOW()
                        WHERE review_id = %s
                    """
                    
                    cursor.execute(overall_query, (
                        final_ratings['overall_rating'],
                        review_id
                    ))
                
                # Update parameter ratings if provided
                if 'parameters' in final_ratings:
                    for param_rating in final_ratings['parameters']:
                        param_name = param_rating.get('name', '')
                        
                        # Get parameter ID
                        param_query = """
                            SELECT parameter_id
                            FROM hr_performance_parameters
                            WHERE cycle_id = %s AND parameter_name = %s
                        """
                        
                        cursor.execute(param_query, (review['cycle_id'], param_name))
                        param_result = cursor.fetchone()
                        
                        if param_result:
                            # Update final rating
                            rating_query = """
                                UPDATE hr_performance_ratings
                                SET final_rating = %s, calibration_comments = %s
                                WHERE review_id = %s AND parameter_id = %s
                            """
                            
                            cursor.execute(rating_query, (
                                param_rating.get('rating'),
                                param_rating.get('comments', ''),
                                review_id,
                                param_result['parameter_id']
                            ))
            
            # Update review status
            update_query = """
                UPDATE hr_performance_reviews
                SET status = 'Finalized', finalized_date = NOW()
                WHERE review_id = %s
            """
            
            cursor.execute(update_query, (review_id,))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Finalized review {review_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error finalizing review {review_id}: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def get_review_data(self, review_id: str) -> Dict[str, Any]:
        """
        Get complete review data
        
        Args:
            review_id: Review ID
            
        Returns:
            Complete review data
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Get review details
            review_query = """
                SELECT r.*, c.cycle_name, c.cycle_type,
                    e.first_name, e.last_name, e.job_title, e.department,
                    CONCAT(m.first_name, ' ', m.last_name) AS manager_name
                FROM hr_performance_reviews r
                JOIN hr_performance_cycles c ON r.cycle_id = c.cycle_id
                JOIN hr_employees e ON r.employee_id = e.employee_id
                LEFT JOIN hr_employees m ON e.reporting_manager_id = m.employee_id
                WHERE r.review_id = %s
            """
            
            cursor.execute(review_query, (review_id,))
            review = cursor.fetchone()
            
            if not review:
                logger.warning(f"Review {review_id} not found")
                cursor.close()
                return {}
            
            # Get parameter ratings
            ratings_query = """
                SELECT r.*, p.parameter_name, p.parameter_description, p.weight
                FROM hr_performance_ratings r
                JOIN hr_performance_parameters p ON r.parameter_id = p.parameter_id
                WHERE r.review_id = %s
                ORDER BY p.display_order
            """
            
            cursor.execute(ratings_query, (review_id,))
            ratings = cursor.fetchall()
            
            # Get goals
            goals_query = """
                SELECT *
                FROM hr_employee_goals
                WHERE review_id = %s
                ORDER BY display_order
            """
            
            cursor.execute(goals_query, (review_id,))
            goals = cursor.fetchall()
            
            # Calculate overall ratings
            parameter_ratings = {
                'self': 0,
                'manager': 0,
                'final': 0,
                'parameter_count': 0,
                'rated_count': 0
            }
            
            for rating in ratings:
                if rating['self_rating']:
                    parameter_ratings['self'] += rating['self_rating'] * (rating['weight'] / 100)
                    
                if rating['manager_rating']:
                    parameter_ratings['manager'] += rating['manager_rating'] * (rating['weight'] / 100)
                    
                if rating['final_rating']:
                    parameter_ratings['final'] += rating['final_rating'] * (rating['weight'] / 100)
                    
                parameter_ratings['parameter_count'] += 1
                if rating['manager_rating']:
                    parameter_ratings['rated_count'] += 1
            
            # Compile review data
            review_data = {
                'review_id': review['review_id'],
                'cycle': {
                    'id': review['cycle_id'],
                    'name': review['cycle_name'],
                    'type': review['cycle_type']
                },
                'employee': {
                    'id': review['employee_id'],
                    'name': f"{review['first_name']} {review['last_name']}",
                    'job_title': review['job_title'],
                    'department': review['department']
                },
                'manager': {
                    'name': review['manager_name']
                },
                'status': review['status'],
                'overall_rating': review['overall_rating'],
                'calculated_ratings': parameter_ratings,
                'dates': {
                    'created': review['created_date'],
                    'self_review': review['self_review_date'],
                    'manager_review': review['manager_review_date'],
                    'finalized': review['finalized_date']
                },
                'summaries': {
                    'self': review['self_summary'],
                    'manager': review['manager_summary']
                },
                'parameters': ratings,
                'goals': goals
            }
            
            cursor.close()
            return review_data
            
        except Exception as e:
            logger.error(f"Error getting review data for {review_id}: {e}")
            return {}
    
    def create_improvement_plan(self, employee_id: str, 
                              plan_data: Dict[str, Any]) -> Optional[str]:
        """
        Create performance improvement plan
        
        Args:
            employee_id: Employee ID
            plan_data: Plan details
            
        Returns:
            Plan ID if successful, None otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            cursor = conn.cursor()
            
            # Generate plan ID
            plan_id = f"PIP-{datetime.datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            
            # Extract plan information
            initiator_id = plan_data.get('initiator_id', '')
            start_date = plan_data.get('start_date')
            end_date = plan_data.get('end_date')
            reason = plan_data.get('reason', '')
            areas_for_improvement = plan_data.get('areas_for_improvement', '')
            success_criteria = plan_data.get('success_criteria', '')
            review_frequency = plan_data.get('review_frequency', 'Weekly')
            
            # Insert plan record
            query = """
                INSERT INTO hr_performance_improvement_plans (
                    plan_id, employee_id, initiator_id, start_date,
                    end_date, reason, areas_for_improvement,
                    success_criteria, review_frequency, status,
                    created_date
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
            """
            
            cursor.execute(query, (
                plan_id, employee_id, initiator_id, start_date,
                end_date, reason, areas_for_improvement,
                success_criteria, review_frequency, 'Created'
            ))
            
            # Add action items
            if 'action_items' in plan_data:
                items = plan_data['action_items']
                
                for index, item in enumerate(items):
                    item_query = """
                        INSERT INTO hr_pip_action_items (
                            plan_id, action_description, target_date,
                            resources_needed, support_required,
                            measurement_criteria, display_order
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(item_query, (
                        plan_id,
                        item.get('description', ''),
                        item.get('target_date'),
                        item.get('resources', ''),
                        item.get('support', ''),
                        item.get('measurement', ''),
                        index + 1
                    ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Created improvement plan {plan_id} for employee {employee_id}")
            return plan_id
            
        except Exception as e:
            logger.error(f"Error creating improvement plan: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return None
    
    def update_improvement_plan_status(self, plan_id: str, 
                                     status: str, comments: str = "") -> bool:
        """
        Update improvement plan status
        
        Args:
            plan_id: Plan ID
            status: New status
            comments: Status update comments
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Update plan status
            query = """
                UPDATE hr_performance_improvement_plans
                SET status = %s, last_modified = NOW()
                WHERE plan_id = %s
            """
            
            cursor.execute(query, (status, plan_id))
            
            # Add status history
            history_query = """
                INSERT INTO hr_pip_status_history (
                    plan_id, status, change_date, comments
                ) VALUES (%s, %s, NOW(), %s)
            """
            
            cursor.execute(history_query, (plan_id, status, comments))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Updated improvement plan {plan_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating improvement plan {plan_id}: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def record_pip_review_meeting(self, plan_id: str, 
                                meeting_data: Dict[str, Any]) -> bool:
        """
        Record improvement plan review meeting
        
        Args:
            plan_id: Plan ID
            meeting_data: Meeting details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Extract meeting information
            meeting_date = meeting_data.get('meeting_date')
            attendees = meeting_data.get('attendees', '')
            progress_notes = meeting_data.get('progress_notes', '')
            challenges = meeting_data.get('challenges', '')
            action_items = meeting_data.get('action_items', '')
            next_meeting_date = meeting_data.get('next_meeting_date')
            
            # Insert meeting record
            query = """
                INSERT INTO hr_pip_review_meetings (
                    plan_id, meeting_date, attendees, progress_notes,
                    challenges, action_items, next_meeting_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                plan_id, meeting_date, attendees, progress_notes,
                challenges, action_items, next_meeting_date
            ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Recorded review meeting for plan {plan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording meeting for plan {plan_id}: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def get_performance_metrics(self, department: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance metrics
        
        Args:
            department: Optional department filter
            
        Returns:
            Performance metrics data
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Build WHERE condition for department filter
            dept_condition = ""
            params = []
            
            if department:
                dept_condition = "WHERE e.department = %s"
                params = [department]
            
            # Get rating distribution
            rating_query = f"""
                SELECT COUNT(*) AS total,
                    SUM(CASE WHEN r.overall_rating >= 4.5 THEN 1 ELSE 0 END) AS outstanding,
                    SUM(CASE WHEN r.overall_rating >= 3.5 AND r.overall_rating < 4.5 THEN 1 ELSE 0 END) AS exceeds,
                    SUM(CASE WHEN r.overall_rating >= 2.5 AND r.overall_rating < 3.5 THEN 1 ELSE 0 END) AS meets,
                    SUM(CASE WHEN r.overall_rating >= 1.5 AND r.overall_rating < 2.5 THEN 1 ELSE 0 END) AS below,
                    SUM(CASE WHEN r.overall_rating < 1.5 THEN 1 ELSE 0 END) AS unsatisfactory
                FROM hr_performance_reviews r
                JOIN hr_employees e ON r.employee_id = e.employee_id
                {dept_condition}
                AND r.status = 'Finalized'
            """
            
            cursor.execute(rating_query, params)
            rating_distribution = cursor.fetchone()
            
            # Get department averages
            dept_query = """
                SELECT e.department, COUNT(*) AS review_count,
                    AVG(r.overall_rating) AS avg_rating
                FROM hr_performance_reviews r
                JOIN hr_employees e ON r.employee_id = e.employee_id
                WHERE r.status = 'Finalized'
                GROUP BY e.department
                ORDER BY avg_rating DESC
            """
            
            cursor.execute(dept_query)
            department_averages = cursor.fetchall()
            
            # Get goal achievement rates
            goal_query = f"""
                SELECT COUNT(*) AS total_goals,
                    SUM(CASE WHEN g.status = 'Completed' AND g.manager_rating >= 3 THEN 1 ELSE 0 END) AS achieved_goals
                FROM hr_employee_goals g
                JOIN hr_performance_reviews r ON g.review_id = r.review_id
                JOIN hr_employees e ON r.employee_id = e.employee_id
                {dept_condition}
            """
            
            cursor.execute(goal_query, params)
            goal_data = cursor.fetchone()
            
            # Get improvement plan metrics
            pip_query = f"""
                SELECT COUNT(*) AS total_pips,
                    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed,
                    SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) AS failed,
                    SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress
                FROM hr_performance_improvement_plans p
                JOIN hr_employees e ON p.employee_id = e.employee_id
                {dept_condition}
            """
            
            cursor.execute(pip_query, params)
            pip_data = cursor.fetchone()
            
            cursor.close()
            
            # Calculate goal achievement rate
            goal_achievement_rate = 0
            if goal_data and goal_data['total_goals'] > 0:
                goal_achievement_rate = (goal_data['achieved_goals'] / goal_data['total_goals']) * 100
            
            # Compile metrics
            metrics = {
                'rating_distribution': rating_distribution,
                'department_averages': department_averages,
                'goal_metrics': {
                    'total_goals': goal_data['total_goals'] if goal_data else 0,
                    'achieved_goals': goal_data['achieved_goals'] if goal_data else 0,
                    'achievement_rate': round(goal_achievement_rate, 2)
                },
                'improvement_plan_metrics': pip_data or {
                    'total_pips': 0,
                    'completed': 0,
                    'failed': 0,
                    'in_progress': 0
                }
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}


# Singleton instance
performance_manager = PerformanceManager()


def get_performance_manager() -> PerformanceManager:
    """Get the performance manager instance"""
    return performance_manager
