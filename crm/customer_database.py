"""
Customer Database Manager

This module handles customer data management for the CRM system.
It provides functions to read, write, and update customer information.
"""

import os
import sys
from pathlib import Path
import logging
import datetime
from typing import Dict, List, Any, Optional

# Add parent directory to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import DATABASE_CONFIG
    from utils.lib.packages import import_module
            DatabaseConnection = import_module("database.python.connection").DatabaseConnection
except ImportError:
    print("Warning: Could not import DatabaseConnection")
    # Create a placeholder class
    class DatabaseConnection:
        def __init__(self):
            pass
        def get_connection(self):
            return None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crm-database')

class CustomerDatabase:
    """Customer database management class for CRM"""
    
    def __init__(self):
        """Initialize the customer database manager"""
        self.db_connection = DatabaseConnection()
        
    def get_customer_profile(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a complete customer profile including all CRM-related information
        
        Args:
            customer_id: Unique customer identifier
            
        Returns:
            Dictionary with customer data or None if customer not found
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            cursor = conn.cursor(dictionary=True)
            
            # Get basic customer information
            cursor.execute("""
                SELECT * 
                FROM cbs_customers 
                WHERE customer_id = %s
            """, (customer_id,))
            
            customer_data = cursor.fetchone()
            
            if not customer_data:
                logger.warning(f"Customer {customer_id} not found")
                return None
            
            # Get contact history
            cursor.execute("""
                SELECT *
                FROM crm_contact_history
                WHERE customer_id = %s
                ORDER BY contact_date DESC
                LIMIT 10
            """, (customer_id,))
            
            contact_history = cursor.fetchall()
            customer_data['contact_history'] = contact_history or []
            
            # Get assigned campaigns
            cursor.execute("""
                SELECT c.*
                FROM crm_campaigns c
                JOIN crm_campaign_customers cc ON c.campaign_id = cc.campaign_id
                WHERE cc.customer_id = %s AND c.status = 'ACTIVE'
            """, (customer_id,))
            
            campaigns = cursor.fetchall()
            customer_data['active_campaigns'] = campaigns or []
            
            # Get product recommendations
            cursor.execute("""
                SELECT *
                FROM crm_product_recommendations
                WHERE customer_id = %s AND status = 'PENDING'
            """, (customer_id,))
            
            recommendations = cursor.fetchall()
            customer_data['recommendations'] = recommendations or []
            
            # Close cursor
            cursor.close()
            
            return customer_data
            
        except Exception as e:
            logger.error(f"Error fetching customer {customer_id}: {e}")
            return None

    def update_customer_profile(self, customer_id: str, data: Dict[str, Any]) -> bool:
        """
        Update customer profile data
        
        Args:
            customer_id: Unique customer identifier
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
            
            # Build the update query dynamically
            fields = []
            values = []
            
            for field, value in data.items():
                fields.append(f"{field} = %s")
                values.append(value)
            
            # Add customer_id to values
            values.append(customer_id)
            
            # Create and execute the query
            query = f"""
                UPDATE cbs_customers
                SET {', '.join(fields)}, last_modified = NOW()
                WHERE customer_id = %s
            """
            
            cursor.execute(query, values)
            conn.commit()
            cursor.close()
            
            logger.info(f"Updated profile for customer {customer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating customer {customer_id}: {e}")
            return False

    def add_contact_record(self, customer_id: str, contact_type: str, 
                          contact_details: str, outcome: str) -> bool:
        """
        Add a new contact record to customer history
        
        Args:
            customer_id: Unique customer identifier
            contact_type: Type of contact (CALL, EMAIL, SMS, etc.)
            contact_details: Details of the contact
            outcome: Outcome of the contact
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Insert contact record
            query = """
                INSERT INTO crm_contact_history
                (customer_id, contact_type, contact_date, contact_details, outcome)
                VALUES (%s, %s, NOW(), %s, %s)
            """
            
            cursor.execute(query, (customer_id, contact_type, contact_details, outcome))
            conn.commit()
            cursor.close()
            
            logger.info(f"Added {contact_type} contact record for customer {customer_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding contact record for customer {customer_id}: {e}")
            return False

    def get_customers_by_segment(self, segment: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get customers by segment
        
        Args:
            segment: Customer segment (PREMIUM, STANDARD, etc.)
            limit: Maximum number of customers to return
            
        Returns:
            List of customer records
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Get customers by segment
            cursor.execute("""
                SELECT *
                FROM cbs_customers
                WHERE segment = %s
                LIMIT %s
            """, (segment, limit))
            
            customers = cursor.fetchall()
            cursor.close()
            
            return customers or []
            
        except Exception as e:
            logger.error(f"Error fetching customers for segment {segment}: {e}")
            return []

    def search_customers(self, search_term: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search for customers by name, email, phone, etc.
        
        Args:
            search_term: Text to search for
            limit: Maximum number of results to return
            
        Returns:
            List of matching customer records
        """
        try:
            conn = self.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Search term with wildcards
            search_pattern = f"%{search_term}%"
            
            # Search customers
            cursor.execute("""
                SELECT *
                FROM cbs_customers
                WHERE name LIKE %s
                OR email LIKE %s
                OR phone LIKE %s
                OR customer_id LIKE %s
                LIMIT %s
            """, (search_pattern, search_pattern, search_pattern, search_pattern, limit))
            
            customers = cursor.fetchall()
            cursor.close()
            
            return customers or []
            
        except Exception as e:
            logger.error(f"Error searching customers for '{search_term}': {e}")
            return []


# Singleton instance
customer_db = CustomerDatabase()


def get_customer_database() -> CustomerDatabase:
    """Get the customer database manager instance"""
    return customer_db
