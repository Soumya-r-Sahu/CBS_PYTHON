"""
Lead Management Module

This module provides functionality for managing sales leads,
tracking lead progression, and managing conversions.
"""

import os
import sys
from pathlib import Path
import logging
import datetime
import uuid
from typing import Dict, List, Any, Optional

# Add parent directory to path if needed

# Use centralized import manager
try:
    from utils.lib.packages import fix_path, import_module, is_production, is_development, is_test, is_debug_enabled, Environment, get_database_connection
    fix_path()  # Ensures the project root is in sys.path
except ImportError:
    # Fallback for when the import manager is not available
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))  # Adjust levels as needed


# Import CRM modules
from crm.config import LEAD_SETTINGS
from crm.customer_database import get_customer_database

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crm-lead')

class LeadManager:
    """Lead management for sales and marketing"""
    
    def __init__(self):
        """Initialize the lead manager"""
        self.customer_db = get_customer_database()
        
    def create_lead(self, source: str, name: str, email: str, 
                  phone: str, product_interest: str,
                  details: str, assigned_to: Optional[str] = None) -> Optional[str]:
        """
        Create a new sales lead
        
        Args:
            source: Lead source (WEB, REFERRAL, CAMPAIGN, etc.)
            name: Lead name
            email: Lead email
            phone: Lead phone number
            product_interest: Product the lead is interested in
            details: Additional details
            assigned_to: Employee ID to assign lead to (optional)
            
        Returns:
            Lead ID if successful, None otherwise
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            # Generate a unique lead ID
            lead_id = str(uuid.uuid4())[:8].upper()
            
            cursor = conn.cursor()
            
            # Calculate lead score based on information provided
            score = self._calculate_initial_score(source, email, phone, product_interest, details)
            
            # Auto-assign if needed
            if assigned_to is None and LEAD_SETTINGS['auto_assign']:
                assigned_to = self._get_next_available_agent()
            
            # Create lead record
            query = """
                INSERT INTO crm_leads
                (lead_id, source, name, email, phone, product_interest, 
                 details, score, status, created_date, assigned_to)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            """
            
            cursor.execute(query, (
                lead_id, source, name, email, phone, product_interest,
                details, score, 'NEW', assigned_to
            ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Created lead {lead_id}: {name} ({email})")
            return lead_id
            
        except Exception as e:
            logger.error(f"Error creating lead for {name}: {e}")
            return None
    
    def _calculate_initial_score(self, source: str, email: str, 
                                phone: str, product_interest: str, 
                                details: str) -> int:
        """
        Calculate initial lead score based on available information
        
        Args:
            source: Lead source
            email: Lead email
            phone: Lead phone number
            product_interest: Product interest
            details: Additional details
            
        Returns:
            Score between 0-100
        """
        score = 50  # Start with base score
        
        # Score based on source
        source_scores = {
            'REFERRAL': 20,  # Referrals are high quality
            'CAMPAIGN': 15,  # Campaign leads are good
            'WEB': 10,       # Web leads are moderate
            'WALK_IN': 20,   # Walk-ins show high intent
            'SOCIAL_MEDIA': 5  # Social media leads vary in quality
        }
        score += source_scores.get(source.upper(), 0)
        
        # Score based on information completeness
        if email and '@' in email:
            score += 5
        if phone and len(phone) >= 10:
            score += 5
        if product_interest:
            score += 10
        if details and len(details) > 50:
            score += 5
        
        # Cap score at 100
        return min(score, 100)
    
    def _get_next_available_agent(self) -> Optional[str]:
        """
        Get the next available agent for lead assignment
        using round-robin or workload balancing
        
        Returns:
            Employee ID of agent or None
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
                
            cursor = conn.cursor(dictionary=True)
            
            # Find agent with least number of active leads
            query = """
                SELECT e.employee_id, COUNT(l.lead_id) as lead_count
                FROM hr_employees e
                LEFT JOIN crm_leads l ON e.employee_id = l.assigned_to 
                     AND l.status IN ('NEW', 'CONTACTED', 'QUALIFIED')
                WHERE e.role = 'SALES_AGENT' AND e.status = 'ACTIVE'
                GROUP BY e.employee_id
                ORDER BY lead_count ASC
                LIMIT 1
            """
            
            cursor.execute(query)
            agent = cursor.fetchone()
            cursor.close()
            
            if agent:
                return agent['employee_id']
            return None
            
        except Exception as e:
            logger.error(f"Error finding available agent: {e}")
            return None
    
    def update_lead_status(self, lead_id: str, new_status: str, 
                         comments: Optional[str] = None) -> bool:
        """
        Update lead status
        
        Args:
            lead_id: Lead ID
            new_status: New status (NEW, CONTACTED, QUALIFIED, CONVERTED, LOST)
            comments: Optional comments about status change
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Update lead status
            query = """
                UPDATE crm_leads
                SET status = %s, last_modified = NOW()
                WHERE lead_id = %s
            """
            
            cursor.execute(query, (new_status, lead_id))
            
            # Record activity
            activity_query = """
                INSERT INTO crm_lead_activities
                (lead_id, activity_type, activity_date, details, performed_by)
                VALUES (%s, %s, NOW(), %s, %s)
            """
            
            # Get user from system context (placeholder)
            current_user = "SYSTEM"
            
            cursor.execute(activity_query, (
                lead_id, f"STATUS_CHANGE_{new_status}", 
                comments or f"Status changed to {new_status}", 
                current_user
            ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Updated lead {lead_id} status to {new_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating lead {lead_id} status: {e}")
            return False
    
    def get_lead_details(self, lead_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full lead details including activities
        
        Args:
            lead_id: Lead ID
            
        Returns:
            Lead details or None if not found
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            cursor = conn.cursor(dictionary=True)
            
            # Get basic lead information
            cursor.execute("""
                SELECT * 
                FROM crm_leads 
                WHERE lead_id = %s
            """, (lead_id,))
            
            lead_data = cursor.fetchone()
            
            if not lead_data:
                logger.warning(f"Lead {lead_id} not found")
                return None
            
            # Get activities
            cursor.execute("""
                SELECT *
                FROM crm_lead_activities
                WHERE lead_id = %s
                ORDER BY activity_date DESC
            """, (lead_id,))
            
            activities = cursor.fetchall()
            lead_data['activities'] = activities or []
            
            cursor.close()
            
            return lead_data
            
        except Exception as e:
            logger.error(f"Error fetching lead {lead_id}: {e}")
            return None
    
    def record_lead_activity(self, lead_id: str, activity_type: str,
                           details: str, performed_by: Optional[str] = None) -> bool:
        """
        Record a new activity for a lead
        
        Args:
            lead_id: Lead ID
            activity_type: Type of activity (CALL, EMAIL, MEETING, etc.)
            details: Activity details
            performed_by: Employee who performed the activity
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Get user from system context if not provided
            if performed_by is None:
                performed_by = "SYSTEM"
            
            # Record activity
            query = """
                INSERT INTO crm_lead_activities
                (lead_id, activity_type, activity_date, details, performed_by)
                VALUES (%s, %s, NOW(), %s, %s)
            """
            
            cursor.execute(query, (lead_id, activity_type, details, performed_by))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Recorded {activity_type} activity for lead {lead_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording activity for lead {lead_id}: {e}")
            return False
    
    def convert_lead_to_customer(self, lead_id: str, product_purchased: str) -> Optional[str]:
        """
        Convert a lead to a customer
        
        Args:
            lead_id: Lead ID
            product_purchased: Product that was purchased
            
        Returns:
            New customer ID if successful, None otherwise
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            cursor = conn.cursor(dictionary=True)
            
            # Get lead information
            cursor.execute("""
                SELECT * 
                FROM crm_leads 
                WHERE lead_id = %s
            """, (lead_id,))
            
            lead = cursor.fetchone()
            
            if not lead:
                logger.warning(f"Lead {lead_id} not found")
                return None
            
            # Generate customer ID
            customer_id = str(uuid.uuid4())[:8].upper()
            
            # Create customer record
            customer_query = """
                INSERT INTO cbs_customers
                (customer_id, name, email, phone, status, 
                 registration_date, segment, referral_source, kyc_status)
                VALUES (%s, %s, %s, %s, %s, NOW(), %s, %s, %s)
            """
            
            cursor.execute(customer_query, (
                customer_id, lead['name'], lead['email'], lead['phone'],
                'ACTIVE', 'STANDARD', lead['source'], 'PENDING'
            ))
            
            # Update lead status
            update_query = """
                UPDATE crm_leads
                SET status = 'CONVERTED', conversion_date = NOW(),
                    customer_id = %s, converted_product = %s
                WHERE lead_id = %s
            """
            
            cursor.execute(update_query, (customer_id, product_purchased, lead_id))
            
            # Record activity
            activity_query = """
                INSERT INTO crm_lead_activities
                (lead_id, activity_type, activity_date, details, performed_by)
                VALUES (%s, %s, NOW(), %s, %s)
            """
            
            cursor.execute(activity_query, (
                lead_id, 'CONVERSION', 
                f"Converted to customer {customer_id}. Product: {product_purchased}", 
                lead['assigned_to'] or 'SYSTEM'
            ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Converted lead {lead_id} to customer {customer_id}")
            return customer_id
            
        except Exception as e:
            logger.error(f"Error converting lead {lead_id}: {e}")
            return None
    
    def reassign_lead(self, lead_id: str, new_agent_id: str) -> bool:
        """
        Reassign a lead to a different agent
        
        Args:
            lead_id: Lead ID
            new_agent_id: New agent's employee ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Get current assignment
            cursor.execute("""
                SELECT assigned_to
                FROM crm_leads
                WHERE lead_id = %s
            """, (lead_id,))
            
            result = cursor.fetchone()
            if not result:
                logger.warning(f"Lead {lead_id} not found")
                return False
                
            old_agent_id = result[0]
            
            # Update assignment
            query = """
                UPDATE crm_leads
                SET assigned_to = %s, last_modified = NOW()
                WHERE lead_id = %s
            """
            
            cursor.execute(query, (new_agent_id, lead_id))
            
            # Record activity
            activity_query = """
                INSERT INTO crm_lead_activities
                (lead_id, activity_type, activity_date, details, performed_by)
                VALUES (%s, %s, NOW(), %s, %s)
            """
            
            # Get user from system context (placeholder)
            current_user = "SYSTEM"
            
            cursor.execute(activity_query, (
                lead_id, 'REASSIGNMENT', 
                f"Reassigned from {old_agent_id} to {new_agent_id}", 
                current_user
            ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Reassigned lead {lead_id} from {old_agent_id} to {new_agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error reassigning lead {lead_id}: {e}")
            return False
    
    def get_leads_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get leads by status
        
        Args:
            status: Lead status
            limit: Maximum number of leads to return
            
        Returns:
            List of lead records
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Get leads by status
            cursor.execute("""
                SELECT *
                FROM crm_leads
                WHERE status = %s
                ORDER BY created_date DESC
                LIMIT %s
            """, (status, limit))
            
            leads = cursor.fetchall()
            cursor.close()
            
            return leads or []
            
        except Exception as e:
            logger.error(f"Error fetching leads with status {status}: {e}")
            return []
    
    def get_leads_by_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get leads assigned to a specific agent
        
        Args:
            agent_id: Agent's employee ID
            
        Returns:
            List of lead records
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Get leads by agent
            cursor.execute("""
                SELECT *
                FROM crm_leads
                WHERE assigned_to = %s AND status NOT IN ('CONVERTED', 'LOST')
                ORDER BY created_date DESC
            """, (agent_id,))
            
            leads = cursor.fetchall()
            cursor.close()
            
            return leads or []
            
        except Exception as e:
            logger.error(f"Error fetching leads for agent {agent_id}: {e}")
            return []


# Singleton instance
lead_manager = LeadManager()


def get_lead_manager() -> LeadManager:
    """Get the lead manager instance"""
    return lead_manager