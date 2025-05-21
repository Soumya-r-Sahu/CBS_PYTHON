"""
SQL Employee Repository Implementation

This module implements the EmployeeRepository interface using an SQL database
for persistence in the HR-ERP system.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from ...domain.entities.employee import Employee
from ...domain.value_objects.employee_id import EmployeeId
from ...domain.value_objects.address import Address
from ...domain.value_objects.contact_info import ContactInfo
from ...domain.repositories.employee_repository import EmployeeRepository


class SqlEmployeeRepository(EmployeeRepository):
    """
    SQL implementation of the EmployeeRepository interface
    
    This class handles the persistence of Employee entities to a
    relational database using SQL queries.
    """
    
    def __init__(self, db_connection):
        """
        Initialize the repository
        
        Args:
            db_connection: Database connection manager
        """
        self._db_connection = db_connection
        self._logger = logging.getLogger('hr-employee-repository')
    
    def get_by_id(self, employee_id: UUID) -> Optional[Employee]:
        """
        Retrieve an employee by their internal UUID
        
        Args:
            employee_id: The UUID of the employee
            
        Returns:
            The employee if found, None otherwise
        """
        try:
            conn = self._db_connection.get_connection()
            if not conn:
                self._logger.error("Failed to connect to database")
                return None
            
            cursor = conn.cursor(dictionary=True)
            
            # Query basic employee information
            query = """
                SELECT * 
                FROM hr_employees
                WHERE id = %s
            """
            
            cursor.execute(query, (str(employee_id),))
            employee_data = cursor.fetchone()
            
            if not employee_data:
                cursor.close()
                return None
                
            # Query address information
            address_query = """
                SELECT * 
                FROM hr_employee_addresses
                WHERE employee_id = %s AND address_type = 'Primary'
            """
            
            cursor.execute(address_query, (employee_data['employee_id'],))
            address_data = cursor.fetchone()
            
            # Query contact information (using employee data)
            
            cursor.close()
            
            # Convert database data to domain objects
            return self._map_to_entity(employee_data, address_data)
            
        except Exception as e:
            self._logger.error(f"Error retrieving employee by ID: {e}")
            return None
    
    def get_by_employee_id(self, employee_id: EmployeeId) -> Optional[Employee]:
        """
        Retrieve an employee by their employee ID (EMP-YYYY-NNNN)
        
        Args:
            employee_id: The employee ID value object
            
        Returns:
            The employee if found, None otherwise
        """
        try:
            conn = self._db_connection.get_connection()
            if not conn:
                self._logger.error("Failed to connect to database")
                return None
            
            cursor = conn.cursor(dictionary=True)
            
            # Query basic employee information
            query = """
                SELECT * 
                FROM hr_employees
                WHERE employee_id = %s
            """
            
            cursor.execute(query, (str(employee_id),))
            employee_data = cursor.fetchone()
            
            if not employee_data:
                cursor.close()
                return None
                
            # Query address information
            address_query = """
                SELECT * 
                FROM hr_employee_addresses
                WHERE employee_id = %s AND address_type = 'Primary'
            """
            
            cursor.execute(address_query, (str(employee_id),))
            address_data = cursor.fetchone()
            
            cursor.close()
            
            # Convert database data to domain objects
            return self._map_to_entity(employee_data, address_data)
            
        except Exception as e:
            self._logger.error(f"Error retrieving employee by employee ID: {e}")
            return None
    
    def get_all(self) -> List[Employee]:
        """
        Retrieve all employees
        
        Returns:
            List of all employees
        """
        try:
            conn = self._db_connection.get_connection()
            if not conn:
                self._logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Query basic employee information
            query = """
                SELECT * 
                FROM hr_employees
                WHERE status != 'Terminated'
            """
            
            cursor.execute(query)
            employee_records = cursor.fetchall()
            
            employees = []
            for employee_data in employee_records:
                # Query address information for each employee
                address_query = """
                    SELECT * 
                    FROM hr_employee_addresses
                    WHERE employee_id = %s AND address_type = 'Primary'
                """
                
                cursor.execute(address_query, (employee_data['employee_id'],))
                address_data = cursor.fetchone()
                
                # Convert database data to domain objects
                employee = self._map_to_entity(employee_data, address_data)
                if employee:
                    employees.append(employee)
            
            cursor.close()
            return employees
            
        except Exception as e:
            self._logger.error(f"Error retrieving all employees: {e}")
            return []
    
    def save(self, employee: Employee) -> Employee:
        """
        Save an employee (create or update)
        
        Args:
            employee: The employee to save
            
        Returns:
            The saved employee with any updates (e.g., ID)
        """
        try:
            conn = self._db_connection.get_connection()
            if not conn:
                self._logger.error("Failed to connect to database")
                raise Exception("Database connection failed")
            
            cursor = conn.cursor()
            
            # Start transaction
            conn.start_transaction()
            
            # Check if employee already exists
            check_query = """
                SELECT id 
                FROM hr_employees
                WHERE id = %s OR employee_id = %s
            """
            
            cursor.execute(check_query, (str(employee.id), str(employee.employee_id)))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing employee
                update_query = """
                    UPDATE hr_employees
                    SET first_name = %s,
                        last_name = %s,
                        date_of_birth = %s,
                        joining_date = %s,
                        department = %s,
                        job_title = %s,
                        status = %s,
                        reporting_manager_id = %s,
                        updated_date = NOW()
                    WHERE id = %s
                """
                
                cursor.execute(update_query, (
                    employee.first_name,
                    employee.last_name,
                    employee.date_of_birth,
                    employee.hire_date,
                    employee.department,
                    employee.position,
                    employee.status,
                    str(employee.manager_id) if employee.manager_id else None,
                    str(employee.id)
                ))
                
                # Update address
                update_address_query = """
                    UPDATE hr_employee_addresses
                    SET address_line1 = %s,
                        address_line2 = %s,
                        city = %s,
                        state = %s,
                        country = %s,
                        postal_code = %s
                    WHERE employee_id = %s AND address_type = 'Primary'
                """
                
                cursor.execute(update_address_query, (
                    employee.address.street,
                    employee.address.street2,
                    employee.address.city,
                    employee.address.state,
                    employee.address.country,
                    employee.address.postal_code,
                    str(employee.employee_id)
                ))
                
            else:
                # Create new employee
                insert_query = """
                    INSERT INTO hr_employees (
                        id, employee_id, first_name, last_name, email, phone,
                        date_of_birth, department, job_title,
                        reporting_manager_id, joining_date, employment_type,
                        status, created_date
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                    )
                """
                
                cursor.execute(insert_query, (
                    str(employee.id),
                    str(employee.employee_id),
                    employee.first_name,
                    employee.last_name,
                    employee.contact_info.email,
                    employee.contact_info.phone,
                    employee.date_of_birth,
                    employee.department,
                    employee.position,
                    str(employee.manager_id) if employee.manager_id else None,
                    employee.hire_date,
                    'Full-time',  # Default employment type
                    employee.status
                ))
                
                # Insert address
                insert_address_query = """
                    INSERT INTO hr_employee_addresses (
                        employee_id, address_type, address_line1, address_line2,
                        city, state, country, postal_code
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_address_query, (
                    str(employee.employee_id),
                    'Primary',
                    employee.address.street,
                    employee.address.street2,
                    employee.address.city,
                    employee.address.state,
                    employee.address.country,
                    employee.address.postal_code
                ))
            
            # Commit transaction
            conn.commit()
            cursor.close()
            
            return employee
            
        except Exception as e:
            self._logger.error(f"Error saving employee: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            raise
    
    def delete(self, employee_id: UUID) -> bool:
        """
        Delete an employee by UUID
        
        Args:
            employee_id: The UUID of the employee to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._db_connection.get_connection()
            if not conn:
                self._logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Start transaction
            conn.start_transaction()
            
            # Set employee status to 'Terminated' instead of deleting
            update_query = """
                UPDATE hr_employees
                SET status = 'Terminated',
                    updated_date = NOW()
                WHERE id = %s
            """
            
            cursor.execute(update_query, (str(employee_id),))
            affected = cursor.rowcount
            
            # Commit transaction
            conn.commit()
            cursor.close()
            
            return affected > 0
            
        except Exception as e:
            self._logger.error(f"Error deleting employee: {e}")
            
            # Rollback if needed
            if conn:
                conn.rollback()
                
            return False
    
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[Employee]:
        """
        Find employees matching specific criteria
        
        Args:
            criteria: Dict of field names and values to filter by
            
        Returns:
            List of matching employees
        """
        try:
            conn = self._db_connection.get_connection()
            if not conn:
                self._logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Build dynamic query based on criteria
            base_query = "SELECT * FROM hr_employees WHERE "
            conditions = []
            params = []
            
            for field, value in criteria.items():
                conditions.append(f"{field} = %s")
                params.append(value)
            
            if not conditions:
                return self.get_all()
                
            query = base_query + " AND ".join(conditions)
            
            cursor.execute(query, params)
            employee_records = cursor.fetchall()
            
            employees = []
            for employee_data in employee_records:
                # Query address information for each employee
                address_query = """
                    SELECT * 
                    FROM hr_employee_addresses
                    WHERE employee_id = %s AND address_type = 'Primary'
                """
                
                cursor.execute(address_query, (employee_data['employee_id'],))
                address_data = cursor.fetchone()
                
                # Convert database data to domain objects
                employee = self._map_to_entity(employee_data, address_data)
                if employee:
                    employees.append(employee)
            
            cursor.close()
            return employees
            
        except Exception as e:
            self._logger.error(f"Error finding employees by criteria: {e}")
            return []
    
    def get_by_department(self, department: str) -> List[Employee]:
        """
        Retrieve employees by department
        
        Args:
            department: Department name
            
        Returns:
            List of employees in the department
        """
        return self.find_by_criteria({"department": department})
    
    def get_by_manager(self, manager_id: EmployeeId) -> List[Employee]:
        """
        Retrieve employees reporting to a specific manager
        
        Args:
            manager_id: Manager's employee ID
            
        Returns:
            List of employees reporting to the manager
        """
        try:
            conn = self._db_connection.get_connection()
            if not conn:
                self._logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT * 
                FROM hr_employees
                WHERE reporting_manager_id = %s
            """
            
            cursor.execute(query, (str(manager_id),))
            employee_records = cursor.fetchall()
            
            employees = []
            for employee_data in employee_records:
                # Query address information for each employee
                address_query = """
                    SELECT * 
                    FROM hr_employee_addresses
                    WHERE employee_id = %s AND address_type = 'Primary'
                """
                
                cursor.execute(address_query, (employee_data['employee_id'],))
                address_data = cursor.fetchone()
                
                # Convert database data to domain objects
                employee = self._map_to_entity(employee_data, address_data)
                if employee:
                    employees.append(employee)
            
            cursor.close()
            return employees
            
        except Exception as e:
            self._logger.error(f"Error retrieving employees by manager: {e}")
            return []
    
    def get_next_employee_number(self, year: int) -> int:
        """
        Get the next available employee number for the given year
        
        Args:
            year: The year to generate the employee number for
            
        Returns:
            The next available employee number
        """
        try:
            conn = self._db_connection.get_connection()
            if not conn:
                self._logger.error("Failed to connect to database")
                return 1  # Default to 1 if database connection fails
            
            cursor = conn.cursor()
            
            # Find max employee number for this year
            query = """
                SELECT MAX(SUBSTRING_INDEX(employee_id, '-', -1))
                FROM hr_employees
                WHERE employee_id LIKE %s
            """
            
            cursor.execute(query, (f"EMP-{year}-%",))
            result = cursor.fetchone()
            
            cursor.close()
            
            if result and result[0]:
                return int(result[0]) + 1
            else:
                return 1
                
        except Exception as e:
            self._logger.error(f"Error generating employee number: {e}")
            return 1  # Default to 1 if an error occurs
    
    def _map_to_entity(self, employee_data: Dict[str, Any], address_data: Dict[str, Any]) -> Optional[Employee]:
        """
        Map database records to domain entity
        
        Args:
            employee_data: Employee database record
            address_data: Address database record
            
        Returns:
            Employee entity
        """
        try:
            # Create value objects
            employee_id = EmployeeId(employee_data['employee_id'])
            
            address = Address(
                street=address_data['address_line1'] if address_data else '',
                street2=address_data['address_line2'] if address_data and address_data['address_line2'] else None,
                city=address_data['city'] if address_data else '',
                state=address_data['state'] if address_data else '',
                postal_code=address_data['postal_code'] if address_data else '',
                country=address_data['country'] if address_data else ''
            )
            
            contact_info = ContactInfo(
                email=employee_data['email'],
                phone=employee_data['phone'],
                alternate_email=None,  # Add to database schema if needed
                mobile=None  # Add to database schema if needed
            )
            
            # Create manager ID if available
            manager_id = None
            if employee_data['reporting_manager_id']:
                manager_id = EmployeeId(employee_data['reporting_manager_id'])
            
            # Create Employee entity
            employee = Employee(
                id=UUID(employee_data['id']) if isinstance(employee_data['id'], str) else employee_data['id'],
                employee_id=employee_id,
                first_name=employee_data['first_name'],
                last_name=employee_data['last_name'],
                date_of_birth=employee_data['date_of_birth'],
                hire_date=employee_data['joining_date'],
                department=employee_data['department'],
                position=employee_data['job_title'],
                status=employee_data['status'],
                manager_id=manager_id,
                address=address,
                contact_info=contact_info
            )
            
            return employee
            
        except Exception as e:
            self._logger.error(f"Error mapping employee data to entity: {e}")
            return None

