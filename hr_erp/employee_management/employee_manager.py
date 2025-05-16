"""
Employee Management Module

This module handles core employee management functions including:
- Employee records and profiles
- Organization structure
- Document management
- Employee history
"""

import os
import sys
from pathlib import Path
import logging
import datetime
import uuid
from typing import Dict, List, Any, Optional, Union

# Add parent directory to path if needed
# Removed: sys.path.insert(0, str(Path(__file__).parent.parent))
# Removed: sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import HR-ERP modules
from hr_erp.config import EMPLOYEE_SETTINGS

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('hr-employee')

class EmployeeManager:
    """Employee management for HR-ERP system"""
    def __init__(self):
        """Initialize the employee manager"""
        self.db_connection = None
        self._initialize_db_connection()
        
    def _initialize_db_connection(self):
        """Initialize database connection"""
        try:
            # Import database connection using centralized import system
            from utils.lib.packages import fix_path, import_module
            fix_path()  # Ensures project root is in sys.path
            DatabaseConnection = import_module("database.python.connection").DatabaseConnection
            
            self.db_connection = DatabaseConnection()
            logger.info("Database connection initialized")
            
        except ImportError:
            logger.error("Failed to import DatabaseConnection")
    
    def create_employee(self, employee_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new employee record
        
        Args:
            employee_data: Dictionary containing employee information
            
        Returns:
            Employee ID if successful, None otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            # Generate employee ID
            employee_id = self._generate_employee_id()
            
            # Extract basic employee information
            first_name = employee_data.get('first_name', '')
            last_name = employee_data.get('last_name', '')
            email = employee_data.get('email', '')
            phone = employee_data.get('phone', '')
            date_of_birth = employee_data.get('date_of_birth')
            gender = employee_data.get('gender', '')
            
            # Extract employment information
            department = employee_data.get('department', '')
            job_title = employee_data.get('job_title', '')
            reporting_manager_id = employee_data.get('reporting_manager_id')
            joining_date = employee_data.get('joining_date')
            employment_type = employee_data.get('employment_type', 'Full-time')
            
            # Start transaction
            cursor = conn.cursor()
            
            # Insert employee record
            query = """
                INSERT INTO hr_employees (
                    employee_id, first_name, last_name, email, phone,
                    date_of_birth, gender, department, job_title,
                    reporting_manager_id, joining_date, employment_type,
                    status, created_date
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
            """
            
            cursor.execute(query, (
                employee_id, first_name, last_name, email, phone,
                date_of_birth, gender, department, job_title,
                reporting_manager_id, joining_date, employment_type,
                'Active'
            ))
            
            # Insert address information if provided
            if 'address' in employee_data:
                address = employee_data['address']
                address_query = """
                    INSERT INTO hr_employee_addresses (
                        employee_id, address_type, address_line1, address_line2,
                        city, state, country, postal_code
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                # Insert permanent address
                if 'permanent' in address:
                    perm = address['permanent']
                    cursor.execute(address_query, (
                        employee_id, 'Permanent',
                        perm.get('line1', ''), perm.get('line2', ''),
                        perm.get('city', ''), perm.get('state', ''),
                        perm.get('country', ''), perm.get('postal_code', '')
                    ))
                
                # Insert current address
                if 'current' in address:
                    curr = address['current']
                    cursor.execute(address_query, (
                        employee_id, 'Current',
                        curr.get('line1', ''), curr.get('line2', ''),
                        curr.get('city', ''), curr.get('state', ''),
                        curr.get('country', ''), curr.get('postal_code', '')
                    ))
            
            # Insert emergency contact information if provided
            if 'emergency_contact' in employee_data:
                contacts = employee_data['emergency_contact']
                if not isinstance(contacts, list):
                    contacts = [contacts]
                    
                contact_query = """
                    INSERT INTO hr_employee_emergency_contacts (
                        employee_id, contact_name, relationship, phone,
                        alternative_phone, email
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                for contact in contacts:
                    cursor.execute(contact_query, (
                        employee_id,
                        contact.get('name', ''),
                        contact.get('relationship', ''),
                        contact.get('phone', ''),
                        contact.get('alternative_phone', ''),
                        contact.get('email', '')
                    ))
            
            # Insert education information if provided
            if 'education' in employee_data:
                education_records = employee_data['education']
                if not isinstance(education_records, list):
                    education_records = [education_records]
                    
                education_query = """
                    INSERT INTO hr_employee_education (
                        employee_id, degree, institution, major, start_year,
                        end_year, grade
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                
                for edu in education_records:
                    cursor.execute(education_query, (
                        employee_id,
                        edu.get('degree', ''),
                        edu.get('institution', ''),
                        edu.get('major', ''),
                        edu.get('start_year'),
                        edu.get('end_year'),
                        edu.get('grade', '')
                    ))
            
            # Insert work experience if provided
            if 'work_experience' in employee_data:
                experiences = employee_data['work_experience']
                if not isinstance(experiences, list):
                    experiences = [experiences]
                    
                experience_query = """
                    INSERT INTO hr_employee_work_experience (
                        employee_id, company_name, job_title, start_date,
                        end_date, responsibilities
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                """
                
                for exp in experiences:
                    cursor.execute(experience_query, (
                        employee_id,
                        exp.get('company', ''),
                        exp.get('job_title', ''),
                        exp.get('start_date'),
                        exp.get('end_date'),
                        exp.get('responsibilities', '')
                    ))
            
            # Commit transaction
            conn.commit()
            cursor.close()
            
            logger.info(f"Created new employee: {employee_id}")
            return employee_id
            
        except Exception as e:
            logger.error(f"Error creating employee: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return None
    
    def _generate_employee_id(self) -> str:
        """
        Generate a new employee ID
        
        Returns:
            Unique employee ID
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                # Fallback to timestamp-based ID
                timestamp = datetime.datetime.now()
                return EMPLOYEE_SETTINGS['id_format'].format(
                    year=timestamp.year,
                    number=int(timestamp.strftime('%j%H%M'))
                )
            
            cursor = conn.cursor()
            
            # Get current year
            current_year = datetime.datetime.now().year
            
            # Find max employee number for this year
            query = """
                SELECT MAX(SUBSTRING_INDEX(employee_id, '-', -1))
                FROM hr_employees
                WHERE employee_id LIKE %s
            """
            
            cursor.execute(query, (f"EMP-{current_year}-%",))
            result = cursor.fetchone()
            
            if result and result[0]:
                next_number = int(result[0]) + 1
            else:
                next_number = 1
                
            cursor.close()
            
            # Format employee ID
            return EMPLOYEE_SETTINGS['id_format'].format(
                year=current_year,
                number=next_number
            )
            
        except Exception as e:
            # Fallback to timestamp-based ID
            logger.error(f"Error generating employee ID: {e}")
            timestamp = datetime.datetime.now()
            return EMPLOYEE_SETTINGS['id_format'].format(
                year=timestamp.year,
                number=int(timestamp.strftime('%j%H%M'))
            )
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """
        Get employee details by ID
        
        Args:
            employee_id: Employee ID
            
        Returns:
            Employee data dictionary
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            cursor = conn.cursor(dictionary=True)
            
            # Get basic employee information
            query = """
                SELECT * 
                FROM hr_employees 
                WHERE employee_id = %s
            """
            
            cursor.execute(query, (employee_id,))
            employee_data = cursor.fetchone()
            
            if not employee_data:
                logger.warning(f"Employee {employee_id} not found")
                return None
            
            # Get address information
            address_query = """
                SELECT * 
                FROM hr_employee_addresses 
                WHERE employee_id = %s
            """
            
            cursor.execute(address_query, (employee_id,))
            addresses = cursor.fetchall()
            
            if addresses:
                employee_data['addresses'] = {}
                for addr in addresses:
                    address_type = addr.get('address_type', '').lower()
                    employee_data['addresses'][address_type] = addr
            
            # Get emergency contacts
            contact_query = """
                SELECT * 
                FROM hr_employee_emergency_contacts 
                WHERE employee_id = %s
            """
            
            cursor.execute(contact_query, (employee_id,))
            contacts = cursor.fetchall()
            employee_data['emergency_contacts'] = contacts or []
            
            # Get education information
            education_query = """
                SELECT * 
                FROM hr_employee_education 
                WHERE employee_id = %s
                ORDER BY end_year DESC
            """
            
            cursor.execute(education_query, (employee_id,))
            education = cursor.fetchall()
            employee_data['education'] = education or []
            
            # Get work experience
            experience_query = """
                SELECT * 
                FROM hr_employee_work_experience 
                WHERE employee_id = %s
                ORDER BY end_date DESC
            """
            
            cursor.execute(experience_query, (employee_id,))
            experience = cursor.fetchall()
            employee_data['work_experience'] = experience or []
            
            # Get reporting manager
            if employee_data.get('reporting_manager_id'):
                manager_query = """
                    SELECT employee_id, CONCAT(first_name, ' ', last_name) AS manager_name,
                           job_title, email, phone
                    FROM hr_employees
                    WHERE employee_id = %s
                """
                
                cursor.execute(manager_query, (employee_data.get('reporting_manager_id'),))
                manager = cursor.fetchone()
                employee_data['reporting_manager'] = manager or {}
            
            # Get subordinates
            subordinates_query = """
                SELECT employee_id, CONCAT(first_name, ' ', last_name) AS employee_name,
                       job_title, email, phone
                FROM hr_employees
                WHERE reporting_manager_id = %s
                AND status = 'Active'
            """
            
            cursor.execute(subordinates_query, (employee_id,))
            subordinates = cursor.fetchall()
            employee_data['subordinates'] = subordinates or []
            
            cursor.close()
            
            return employee_data
            
        except Exception as e:
            logger.error(f"Error fetching employee {employee_id}: {e}")
            return None
    
    def update_employee(self, employee_id: str, data: Dict[str, Any]) -> bool:
        """
        Update employee information
        
        Args:
            employee_id: Employee ID
            data: Dictionary with fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Start transaction
            conn.autocommit = False
            
            # Check if employee exists
            check_query = "SELECT 1 FROM hr_employees WHERE employee_id = %s"
            cursor.execute(check_query, (employee_id,))
            
            if not cursor.fetchone():
                logger.warning(f"Employee {employee_id} not found")
                return False
            
            # Update basic employee information
            basic_fields = [
                'first_name', 'last_name', 'email', 'phone', 'date_of_birth', 
                'gender', 'department', 'job_title', 'reporting_manager_id',
                'employment_type', 'status'
            ]
            
            # Filter out fields that are in the data dictionary
            update_fields = {}
            for field in basic_fields:
                if field in data:
                    update_fields[field] = data[field]
            
            if update_fields:
                # Build dynamic update query
                set_clause = ", ".join([f"{field} = %s" for field in update_fields])
                set_values = list(update_fields.values())
                
                if set_clause:
                    update_query = f"""
                        UPDATE hr_employees
                        SET {set_clause}, last_modified = NOW()
                        WHERE employee_id = %s
                    """
                    
                    # Add employee ID to values
                    set_values.append(employee_id)
                    
                    # Execute update
                    cursor.execute(update_query, set_values)
            
            # Update address information if provided
            if 'addresses' in data:
                addresses = data['addresses']
                
                # Update each address type
                for addr_type, addr_data in addresses.items():
                    # Check if address exists
                    check_addr_query = """
                        SELECT 1 FROM hr_employee_addresses 
                        WHERE employee_id = %s AND address_type = %s
                    """
                    
                    cursor.execute(check_addr_query, (employee_id, addr_type.capitalize()))
                    
                    if cursor.fetchone():
                        # Update existing address
                        update_addr_query = """
                            UPDATE hr_employee_addresses
                            SET address_line1 = %s, address_line2 = %s,
                                city = %s, state = %s,
                                country = %s, postal_code = %s
                            WHERE employee_id = %s AND address_type = %s
                        """
                        
                        cursor.execute(update_addr_query, (
                            addr_data.get('line1', ''),
                            addr_data.get('line2', ''),
                            addr_data.get('city', ''),
                            addr_data.get('state', ''),
                            addr_data.get('country', ''),
                            addr_data.get('postal_code', ''),
                            employee_id,
                            addr_type.capitalize()
                        ))
                    else:
                        # Insert new address
                        insert_addr_query = """
                            INSERT INTO hr_employee_addresses (
                                employee_id, address_type, address_line1, address_line2,
                                city, state, country, postal_code
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        
                        cursor.execute(insert_addr_query, (
                            employee_id,
                            addr_type.capitalize(),
                            addr_data.get('line1', ''),
                            addr_data.get('line2', ''),
                            addr_data.get('city', ''),
                            addr_data.get('state', ''),
                            addr_data.get('country', ''),
                            addr_data.get('postal_code', '')
                        ))
            
            # Commit all changes
            conn.commit()
            conn.autocommit = True
            cursor.close()
            
            logger.info(f"Updated employee {employee_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating employee {employee_id}: {e}")
            
            # Rollback in case of error
            if conn:
                conn.rollback()
                conn.autocommit = True
                
            return False
    
    def deactivate_employee(self, employee_id: str, reason: str) -> bool:
        """
        Deactivate an employee
        
        Args:
            employee_id: Employee ID
            reason: Reason for deactivation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Update employee status
            update_query = """
                UPDATE hr_employees
                SET status = 'Inactive', last_modified = NOW()
                WHERE employee_id = %s
            """
            
            cursor.execute(update_query, (employee_id,))
            
            # Record deactivation
            history_query = """
                INSERT INTO hr_employee_history (
                    employee_id, event_type, event_date, details, recorded_by
                ) VALUES (%s, %s, NOW(), %s, %s)
            """
            
            cursor.execute(history_query, (
                employee_id,
                'DEACTIVATION',
                f"Reason: {reason}",
                'SYSTEM'
            ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Deactivated employee {employee_id}: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating employee {employee_id}: {e}")
            return False
    
    def search_employees(self, criteria: Dict[str, Any], limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search employees based on various criteria
        
        Args:
            criteria: Search criteria (name, department, status, etc.)
            limit: Maximum number of results
            
        Returns:
            List of matching employee records
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Build WHERE conditions based on criteria
            conditions = []
            params = []
            
            if 'name' in criteria:
                conditions.append("(first_name LIKE %s OR last_name LIKE %s)")
                name_pattern = f"%{criteria['name']}%"
                params.extend([name_pattern, name_pattern])
                
            if 'department' in criteria:
                conditions.append("department = %s")
                params.append(criteria['department'])
                
            if 'job_title' in criteria:
                conditions.append("job_title LIKE %s")
                params.append(f"%{criteria['job_title']}%")
                
            if 'status' in criteria:
                conditions.append("status = %s")
                params.append(criteria['status'])
                
            if 'manager_id' in criteria:
                conditions.append("reporting_manager_id = %s")
                params.append(criteria['manager_id'])
            
            # Build the full query
            query = """
                SELECT 
                    employee_id, first_name, last_name, email, phone,
                    department, job_title, status, joining_date
                FROM hr_employees
            """
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            # Add order by and limit
            query += " ORDER BY first_name, last_name LIMIT %s"
            params.append(limit)
            
            # Execute the query
            cursor.execute(query, params)
            employees = cursor.fetchall()
            cursor.close()
            
            return employees
            
        except Exception as e:
            logger.error(f"Error searching employees: {e}")
            return []
    
    def add_employee_document(self, employee_id: str, document_type: str, 
                            document_path: str, notes: str = "") -> bool:
        """
        Add a document to employee record
        
        Args:
            employee_id: Employee ID
            document_type: Type of document
            document_path: Path to the document file
            notes: Optional notes about the document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Insert document record
            query = """
                INSERT INTO hr_employee_documents (
                    employee_id, document_type, document_path, 
                    upload_date, notes
                ) VALUES (%s, %s, %s, NOW(), %s)
            """
            
            cursor.execute(query, (
                employee_id, document_type, document_path, notes
            ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Added {document_type} document for employee {employee_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding document for {employee_id}: {e}")
            return False
    
    def get_employee_documents(self, employee_id: str) -> List[Dict[str, Any]]:
        """
        Get all documents for an employee
        
        Args:
            employee_id: Employee ID
            
        Returns:
            List of document records
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Get documents
            query = """
                SELECT *
                FROM hr_employee_documents
                WHERE employee_id = %s
                ORDER BY upload_date DESC
            """
            
            cursor.execute(query, (employee_id,))
            documents = cursor.fetchall()
            cursor.close()
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting documents for {employee_id}: {e}")
            return []
    
    def record_employee_event(self, employee_id: str, event_type: str, 
                            details: str, recorded_by: Optional[str] = None) -> bool:
        """
        Record an event in employee history
        
        Args:
            employee_id: Employee ID
            event_type: Type of event
            details: Event details
            recorded_by: Person who recorded the event
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Default recorder
            if not recorded_by:
                recorded_by = "SYSTEM"
                
            # Insert history record
            query = """
                INSERT INTO hr_employee_history (
                    employee_id, event_type, event_date, details, recorded_by
                ) VALUES (%s, %s, NOW(), %s, %s)
            """
            
            cursor.execute(query, (
                employee_id, event_type, details, recorded_by
            ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Recorded {event_type} event for employee {employee_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording event for {employee_id}: {e}")
            return False
    
    def get_employee_history(self, employee_id: str) -> List[Dict[str, Any]]:
        """
        Get employee history
        
        Args:
            employee_id: Employee ID
            
        Returns:
            List of history records
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Get history records
            query = """
                SELECT *
                FROM hr_employee_history
                WHERE employee_id = %s
                ORDER BY event_date DESC
            """
            
            cursor.execute(query, (employee_id,))
            history = cursor.fetchall()
            cursor.close()
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting history for {employee_id}: {e}")
            return []
    
    def get_organization_structure(self, top_level_manager_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get organization structure
        
        Args:
            top_level_manager_id: Start from specific manager (optional)
            
        Returns:
            Organizational hierarchy
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            # Use recursive query to get hierarchy
            if top_level_manager_id:
                # Get hierarchy starting from specified manager
                org_data = self._get_org_hierarchy_for_manager(conn, top_level_manager_id)
                return org_data
            else:
                # Get all top-level managers
                cursor = conn.cursor(dictionary=True)
                query = """
                    SELECT *
                    FROM hr_employees
                    WHERE reporting_manager_id IS NULL
                    AND status = 'Active'
                """
                
                cursor.execute(query)
                top_managers = cursor.fetchall()
                cursor.close()
                
                # Build complete hierarchy
                org_structure = {
                    'type': 'organization',
                    'managers': []
                }
                
                for manager in top_managers:
                    manager_hierarchy = self._get_org_hierarchy_for_manager(conn, manager['employee_id'])
                    org_structure['managers'].append(manager_hierarchy)
                
                return org_structure
                
        except Exception as e:
            logger.error(f"Error getting organization structure: {e}")
            return {}
    
    def _get_org_hierarchy_for_manager(self, conn, manager_id: str) -> Dict[str, Any]:
        """
        Get hierarchy for a specific manager
        
        Args:
            conn: Database connection
            manager_id: Manager's employee ID
            
        Returns:
            Manager's organizational hierarchy
        """
        cursor = conn.cursor(dictionary=True)
        
        # Get manager details
        query = """
            SELECT employee_id, first_name, last_name, job_title, department
            FROM hr_employees
            WHERE employee_id = %s
        """
        
        cursor.execute(query, (manager_id,))
        manager = cursor.fetchone()
        
        if not manager:
            return {}
        
        # Get direct reports
        reports_query = """
            SELECT employee_id, first_name, last_name, job_title, department
            FROM hr_employees
            WHERE reporting_manager_id = %s
            AND status = 'Active'
        """
        
        cursor.execute(reports_query, (manager_id,))
        direct_reports = cursor.fetchall()
        cursor.close()
        
        # Build hierarchy
        manager_data = {
            'employee_id': manager['employee_id'],
            'name': f"{manager['first_name']} {manager['last_name']}",
            'title': manager['job_title'],
            'department': manager['department'],
            'direct_reports': []
        }
        
        # Recursively get reports for each subordinate
        for report in direct_reports:
            subordinate_hierarchy = self._get_org_hierarchy_for_manager(conn, report['employee_id'])
            manager_data['direct_reports'].append(subordinate_hierarchy)
        
        return manager_data


# Singleton instance
employee_manager = EmployeeManager()


def get_employee_manager() -> EmployeeManager:
    """Get the employee manager instance"""
    return employee_manager
