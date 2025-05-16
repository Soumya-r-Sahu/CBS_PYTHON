"""
Campaign Management Module

This module provides functionality for creating, managing, 
and tracking marketing campaigns.
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
from crm.config import CAMPAIGN_SETTINGS
from crm.customer_database import get_customer_database

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crm-campaign')

class CampaignManager:
    """Campaign management for marketing activities"""
    
    def __init__(self):
        """Initialize the campaign manager"""
        self.customer_db = get_customer_database()
        
    def create_campaign(self, name: str, description: str, 
                        start_date: datetime.datetime, 
                        end_date: datetime.datetime,
                        target_segment: str, 
                        channel: str,
                        budget: float) -> Optional[str]:
        """
        Create a new marketing campaign
        
        Args:
            name: Campaign name
            description: Campaign description
            start_date: Campaign start date
            end_date: Campaign end date
            target_segment: Target customer segment
            channel: Communication channel
            budget: Campaign budget
            
        Returns:
            Campaign ID if successful, None otherwise
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            # Generate a unique campaign ID
            campaign_id = str(uuid.uuid4())[:8].upper()
            
            cursor = conn.cursor()
            
            # Create campaign record
            query = """
                INSERT INTO crm_campaigns
                (campaign_id, name, description, start_date, end_date, 
                 target_segment, channel, budget, status, created_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """
            
            # Set initial status based on dates
            today = datetime.datetime.now().date()
            if start_date.date() <= today <= end_date.date():
                status = 'ACTIVE'
            elif start_date.date() > today:
                status = 'SCHEDULED'
            else:
                status = 'EXPIRED'
                
            cursor.execute(query, (
                campaign_id, name, description, 
                start_date, end_date, target_segment, 
                channel, budget, status
            ))
            
            # Assign customers to campaign
            self._assign_customers_to_campaign(cursor, campaign_id, target_segment)
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Created campaign {campaign_id}: {name}")
            return campaign_id
            
        except Exception as e:
            logger.error(f"Error creating campaign {name}: {e}")
            return None
    
    def _assign_customers_to_campaign(self, cursor, campaign_id: str, target_segment: str):
        """
        Assign customers to a campaign based on segment
        
        Args:
            cursor: Database cursor
            campaign_id: Campaign ID
            target_segment: Target customer segment
        """
        # Get customers in segment
        query = """
            SELECT customer_id 
            FROM cbs_customers 
            WHERE segment = %s
        """
        
        cursor.execute(query, (target_segment,))
        customers = cursor.fetchall()
        
        # Assign each customer to campaign
        for customer in customers:
            customer_id = customer[0]
            assign_query = """
                INSERT INTO crm_campaign_customers
                (campaign_id, customer_id, assigned_date, status)
                VALUES (%s, %s, NOW(), 'ASSIGNED')
            """
            
            cursor.execute(assign_query, (campaign_id, customer_id))
    
    def update_campaign_status(self, campaign_id: str, new_status: str) -> bool:
        """
        Update campaign status
        
        Args:
            campaign_id: Campaign ID
            new_status: New campaign status
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Update campaign status
            query = """
                UPDATE crm_campaigns
                SET status = %s, last_modified = NOW()
                WHERE campaign_id = %s
            """
            
            cursor.execute(query, (new_status, campaign_id))
            conn.commit()
            cursor.close()
            
            logger.info(f"Updated campaign {campaign_id} status to {new_status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating campaign {campaign_id} status: {e}")
            return False
    
    def get_campaign_details(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Get campaign details including performance metrics
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Campaign details or None if not found
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return None
            
            cursor = conn.cursor(dictionary=True)
            
            # Get basic campaign information
            cursor.execute("""
                SELECT * 
                FROM crm_campaigns 
                WHERE campaign_id = %s
            """, (campaign_id,))
            
            campaign_data = cursor.fetchone()
            
            if not campaign_data:
                logger.warning(f"Campaign {campaign_id} not found")
                return None
            
            # Get statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_customers,
                    SUM(CASE WHEN status = 'CONTACTED' THEN 1 ELSE 0 END) as contacted_count,
                    SUM(CASE WHEN status = 'RESPONDED' THEN 1 ELSE 0 END) as responded_count,
                    SUM(CASE WHEN status = 'CONVERTED' THEN 1 ELSE 0 END) as converted_count
                FROM crm_campaign_customers
                WHERE campaign_id = %s
            """, (campaign_id,))
            
            stats = cursor.fetchone()
            campaign_data.update(stats or {})
            
            # Calculate response and conversion rates
            if stats and stats['total_customers'] > 0:
                campaign_data['response_rate'] = (stats['responded_count'] / stats['total_customers']) * 100
                campaign_data['conversion_rate'] = (stats['converted_count'] / stats['total_customers']) * 100
            else:
                campaign_data['response_rate'] = 0
                campaign_data['conversion_rate'] = 0
            
            cursor.close()
            
            return campaign_data
            
        except Exception as e:
            logger.error(f"Error fetching campaign {campaign_id}: {e}")
            return None
    
    def record_customer_response(self, campaign_id: str, customer_id: str,
                               response_type: str, response_details: str) -> bool:
        """
        Record a customer response to a campaign
        
        Args:
            campaign_id: Campaign ID
            customer_id: Customer ID
            response_type: Response type (RESPONDED, CONVERTED, DECLINED)
            response_details: Details of the response
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return False
            
            cursor = conn.cursor()
            
            # Update campaign customer status
            query = """
                UPDATE crm_campaign_customers
                SET status = %s, response_date = NOW(), response_details = %s
                WHERE campaign_id = %s AND customer_id = %s
            """
            
            cursor.execute(query, (response_type, response_details, campaign_id, customer_id))
            
            # Record contact history
            contact_query = """
                INSERT INTO crm_contact_history
                (customer_id, contact_type, contact_date, contact_details, outcome)
                VALUES (%s, %s, NOW(), %s, %s)
            """
            
            cursor.execute(contact_query, (
                customer_id, 'CAMPAIGN_RESPONSE', 
                f"Response to campaign {campaign_id}", 
                f"{response_type}: {response_details}"
            ))
            
            conn.commit()
            cursor.close()
            
            logger.info(f"Recorded {response_type} response from customer {customer_id} for campaign {campaign_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error recording response for campaign {campaign_id}, customer {customer_id}: {e}")
            return False
    
    def list_active_campaigns(self) -> List[Dict[str, Any]]:
        """
        Get a list of all active campaigns
        
        Returns:
            List of active campaign records
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Get all active campaigns
            cursor.execute("""
                SELECT *
                FROM crm_campaigns
                WHERE status = 'ACTIVE'
                ORDER BY start_date DESC
            """)
            
            campaigns = cursor.fetchall()
            cursor.close()
            
            return campaigns or []
            
        except Exception as e:
            logger.error(f"Error fetching active campaigns: {e}")
            return []
    
    def get_campaign_customers(self, campaign_id: str, 
                             status: Optional[str] = None, 
                             limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get customers assigned to a campaign, optionally filtered by status
        
        Args:
            campaign_id: Campaign ID
            status: Optional filter by customer status
            limit: Maximum number of records to return
            
        Returns:
            List of customer records
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return []
            
            cursor = conn.cursor(dictionary=True)
            
            # Build query based on whether status is provided
            if status:
                query = """
                    SELECT c.*, cc.status as campaign_status, 
                           cc.assigned_date, cc.response_date, cc.response_details
                    FROM cbs_customers c
                    JOIN crm_campaign_customers cc ON c.customer_id = cc.customer_id
                    WHERE cc.campaign_id = %s AND cc.status = %s
                    LIMIT %s
                """
                cursor.execute(query, (campaign_id, status, limit))
            else:
                query = """
                    SELECT c.*, cc.status as campaign_status,
                           cc.assigned_date, cc.response_date, cc.response_details
                    FROM cbs_customers c
                    JOIN crm_campaign_customers cc ON c.customer_id = cc.customer_id
                    WHERE cc.campaign_id = %s
                    LIMIT %s
                """
                cursor.execute(query, (campaign_id, limit))
            
            customers = cursor.fetchall()
            cursor.close()
            
            return customers or []
            
        except Exception as e:
            logger.error(f"Error fetching customers for campaign {campaign_id}: {e}")
            return []


# Singleton instance
campaign_manager = CampaignManager()


def get_campaign_manager() -> CampaignManager:
    """Get the campaign manager instance"""
    return campaign_manager