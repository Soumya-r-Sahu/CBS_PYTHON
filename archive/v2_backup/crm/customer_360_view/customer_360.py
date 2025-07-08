"""
Customer 360 View Module

This module provides comprehensive customer profiles by aggregating
data from multiple sources across the banking system.
"""

import os
import sys
from pathlib import Path
import logging
import json
import datetime
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
from crm.config import CUSTOMER_360_SETTINGS
from crm.customer_database import get_customer_database

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('crm-customer360')

class Customer360View:
    """Comprehensive 360-degree view of customer data"""
    
    def __init__(self):
        """Initialize the Customer 360 View module"""
        self.customer_db = get_customer_database()
        self.cache = {}
        self.cache_timestamp = {}
    
    def get_customer_360(self, customer_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get a comprehensive 360-degree view of a customer
        
        Args:
            customer_id: Customer ID
            force_refresh: Whether to force a refresh of data
            
        Returns:
            Dictionary with complete customer profile
        """
        # Check if we have a recent cached version
        cache_key = f"c360_{customer_id}"
        if (not force_refresh and 
            CUSTOMER_360_SETTINGS['cache_enabled'] and
            cache_key in self.cache and
            cache_key in self.cache_timestamp):
            
            # Check if cache is still valid
            cache_age = datetime.datetime.now() - self.cache_timestamp[cache_key]
            if cache_age.total_seconds() < CUSTOMER_360_SETTINGS['refresh_frequency_hours'] * 3600:
                return self.cache[cache_key]
        
        # Start with basic customer profile
        profile = self._get_basic_profile(customer_id)
        
        if not profile:
            logger.warning(f"Customer {customer_id} not found")
            return {}
        
        # Enrich with data from various sources
        profile.update(self._get_account_data(customer_id))
        profile.update(self._get_transaction_data(customer_id))
        profile.update(self._get_loan_data(customer_id))
        profile.update(self._get_card_data(customer_id))
        profile.update(self._get_digital_activity(customer_id))
        profile.update(self._get_interaction_history(customer_id))
        profile.update(self._get_product_usage(customer_id))
        
        # Calculate insights and scores
        profile.update(self._calculate_insights(profile))
        
        # Cache the result
        if CUSTOMER_360_SETTINGS['cache_enabled']:
            self.cache[cache_key] = profile
            self.cache_timestamp[cache_key] = datetime.datetime.now()
        
        return profile
    
    def _get_basic_profile(self, customer_id: str) -> Dict[str, Any]:
        """Get basic customer profile"""
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Get basic customer information
            cursor.execute("""
                SELECT *
                FROM cbs_customers
                WHERE customer_id = %s
            """, (customer_id,))
            
            customer = cursor.fetchone()
            
            if not customer:
                return {}
                
            # Get KYC information
            cursor.execute("""
                SELECT *
                FROM cbs_customer_kyc
                WHERE customer_id = %s
            """, (customer_id,))
            
            kyc = cursor.fetchone()
            if kyc:
                customer['kyc'] = kyc
            
            # Get address information
            cursor.execute("""
                SELECT *
                FROM cbs_customer_addresses
                WHERE customer_id = %s
            """, (customer_id,))
            
            addresses = cursor.fetchall()
            customer['addresses'] = addresses or []
            
            cursor.close()
            
            return {
                'profile': customer
            }
            
        except Exception as e:
            logger.error(f"Error fetching basic profile for customer {customer_id}: {e}")
            return {}
    
    def _get_account_data(self, customer_id: str) -> Dict[str, Any]:
        """Get customer account data"""
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Get account information
            cursor.execute("""
                SELECT *
                FROM cbs_accounts
                WHERE customer_id = %s
            """, (customer_id,))
            
            accounts = cursor.fetchall()
            
            # Calculate total balances
            total_balance = 0
            total_available = 0
            
            for account in accounts:
                total_balance += float(account.get('balance', 0))
                total_available += float(account.get('available_balance', 0))
            
            cursor.close()
            
            return {
                'accounts': accounts or [],
                'account_summary': {
                    'total_accounts': len(accounts),
                    'total_balance': total_balance,
                    'total_available': total_available
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching account data for customer {customer_id}: {e}")
            return {}
    
    def _get_transaction_data(self, customer_id: str) -> Dict[str, Any]:
        """Get customer transaction data"""
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Get recent transactions
            cursor.execute("""
                SELECT t.*
                FROM cbs_transactions t
                JOIN cbs_accounts a ON t.account_id = a.account_id
                WHERE a.customer_id = %s
                ORDER BY t.transaction_date DESC
                LIMIT 50
            """, (customer_id,))
            
            transactions = cursor.fetchall()
            
            # Get transaction statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_count,
                    SUM(CASE WHEN t.transaction_type = 'CREDIT' THEN t.amount ELSE 0 END) as total_credits,
                    SUM(CASE WHEN t.transaction_type = 'DEBIT' THEN t.amount ELSE 0 END) as total_debits,
                    AVG(t.amount) as average_amount,
                    MAX(t.transaction_date) as last_transaction_date
                FROM cbs_transactions t
                JOIN cbs_accounts a ON t.account_id = a.account_id
                WHERE a.customer_id = %s
                AND t.transaction_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
            """, (customer_id,))
            
            stats = cursor.fetchone()
            
            cursor.close()
            
            return {
                'recent_transactions': transactions or [],
                'transaction_summary': stats or {}
            }
            
        except Exception as e:
            logger.error(f"Error fetching transaction data for customer {customer_id}: {e}")
            return {}
    
    def _get_loan_data(self, customer_id: str) -> Dict[str, Any]:
        """Get customer loan data"""
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Get loan information
            cursor.execute("""
                SELECT *
                FROM cbs_loans
                WHERE customer_id = %s
            """, (customer_id,))
            
            loans = cursor.fetchall()
            
            # Calculate loan summary
            total_outstanding = 0
            total_overdue = 0
            
            for loan in loans:
                total_outstanding += float(loan.get('outstanding_amount', 0))
                total_overdue += float(loan.get('overdue_amount', 0))
            
            cursor.close()
            
            return {
                'loans': loans or [],
                'loan_summary': {
                    'total_loans': len(loans),
                    'total_outstanding': total_outstanding,
                    'total_overdue': total_overdue
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching loan data for customer {customer_id}: {e}")
            return {}
    
    def _get_card_data(self, customer_id: str) -> Dict[str, Any]:
        """Get customer card data"""
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Get card information
            cursor.execute("""
                SELECT *
                FROM cbs_cards
                WHERE customer_id = %s
            """, (customer_id,))
            
            cards = cursor.fetchall()
            
            # Mask card numbers for security
            for card in cards:
                if 'card_number' in card:
                    masked = '*' * (len(card['card_number']) - 4) + card['card_number'][-4:]
                    card['card_number'] = masked
            
            cursor.close()
            
            return {
                'cards': cards or []
            }
            
        except Exception as e:
            logger.error(f"Error fetching card data for customer {customer_id}: {e}")
            return {}
    
    def _get_digital_activity(self, customer_id: str) -> Dict[str, Any]:
        """Get customer digital channel activity"""
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Get recent logins
            cursor.execute("""
                SELECT *
                FROM dc_login_history
                WHERE customer_id = %s
                ORDER BY login_time DESC
                LIMIT 10
            """, (customer_id,))
            
            logins = cursor.fetchall()
            
            # Get digital channel usage
            cursor.execute("""
                SELECT 
                    channel,
                    COUNT(*) as access_count,
                    MAX(login_time) as last_access
                FROM dc_login_history
                WHERE customer_id = %s
                AND login_time >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
                GROUP BY channel
            """, (customer_id,))
            
            channel_usage = cursor.fetchall()
            
            cursor.close()
            
            return {
                'digital_activity': {
                    'recent_logins': logins or [],
                    'channel_usage': channel_usage or []
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching digital activity for customer {customer_id}: {e}")
            return {}
    
    def _get_interaction_history(self, customer_id: str) -> Dict[str, Any]:
        """Get customer interaction history"""
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Get contact history
            cursor.execute("""
                SELECT *
                FROM crm_contact_history
                WHERE customer_id = %s
                ORDER BY contact_date DESC
                LIMIT 20
            """, (customer_id,))
            
            contacts = cursor.fetchall()
            
            # Get service requests
            cursor.execute("""
                SELECT *
                FROM crm_service_requests
                WHERE customer_id = %s
                ORDER BY request_date DESC
                LIMIT 10
            """, (customer_id,))
            
            service_requests = cursor.fetchall()
            
            # Get complaints
            cursor.execute("""
                SELECT *
                FROM crm_complaints
                WHERE customer_id = %s
                ORDER BY complaint_date DESC
                LIMIT 5
            """, (customer_id,))
            
            complaints = cursor.fetchall()
            
            cursor.close()
            
            return {
                'interaction_history': {
                    'contacts': contacts or [],
                    'service_requests': service_requests or [],
                    'complaints': complaints or []
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching interaction history for customer {customer_id}: {e}")
            return {}
    
    def _get_product_usage(self, customer_id: str) -> Dict[str, Any]:
        """Get customer product usage"""
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Get product subscriptions
            cursor.execute("""
                SELECT *
                FROM cbs_product_subscriptions
                WHERE customer_id = %s
            """, (customer_id,))
            
            subscriptions = cursor.fetchall()
            
            cursor.close()
            
            # Calculate product penetration
            product_categories = {
                'SAVINGS': False,
                'CURRENT': False,
                'FIXED_DEPOSIT': False,
                'LOAN': False,
                'CREDIT_CARD': False,
                'DEBIT_CARD': False,
                'INSURANCE': False,
                'INVESTMENT': False,
                'MOBILE_BANKING': False,
                'INTERNET_BANKING': False
            }
            
            for sub in subscriptions:
                category = sub.get('product_category')
                if category in product_categories:
                    product_categories[category] = True
            
            penetration_score = sum(1 for used in product_categories.values() if used)
            penetration_percentage = (penetration_score / len(product_categories)) * 100
            
            return {
                'product_usage': {
                    'subscriptions': subscriptions or [],
                    'penetration_score': penetration_score,
                    'penetration_percentage': penetration_percentage,
                    'product_categories': product_categories
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching product usage for customer {customer_id}: {e}")
            return {}
    
    def _calculate_insights(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate customer insights and scores"""
        insights = {
            'scores': {},
            'observations': [],
            'opportunities': [],
            'risks': []
        }
        
        try:
            # Calculate overall value score (0-100)
            value_score = 50  # Default starting point
            
            # Adjust based on account balances
            account_summary = data.get('account_summary', {})
            total_balance = float(account_summary.get('total_balance', 0))
            
            if total_balance > 1000000:  # High value
                value_score += 30
            elif total_balance > 100000:
                value_score += 20
            elif total_balance > 10000:
                value_score += 10
            
            # Adjust based on loan data
            loan_summary = data.get('loan_summary', {})
            total_outstanding = float(loan_summary.get('total_outstanding', 0))
            total_overdue = float(loan_summary.get('total_overdue', 0))
            
            if total_outstanding > 0:
                value_score += 10  # Customer has loans
                
                # Penalize for overdue amounts
                if total_overdue > 0:
                    overdue_ratio = total_overdue / total_outstanding
                    if overdue_ratio > 0.1:
                        value_score -= 20
                    elif overdue_ratio > 0.05:
                        value_score -= 10
            
            # Adjust based on product usage
            product_usage = data.get('product_usage', {})
            penetration_score = product_usage.get('penetration_score', 0)
            
            value_score += penetration_score * 2  # More products = more value
            
            # Cap the score at 0-100
            value_score = max(0, min(100, value_score))
            
            insights['scores']['value_score'] = round(value_score, 1)
            
            # Calculate engagement score
            engagement_score = 50  # Default
            
            # Digital activity increases engagement
            digital_activity = data.get('digital_activity', {})
            logins = digital_activity.get('recent_logins', [])
            if logins:
                engagement_score += 10
                
            # Recent transactions increase engagement
            transactions = data.get('recent_transactions', [])
            if transactions:
                # More recent transactions = more engaged
                if len(transactions) > 20:
                    engagement_score += 20
                elif len(transactions) > 10:
                    engagement_score += 10
                else:
                    engagement_score += 5
            
            # Interaction history affects engagement
            interaction = data.get('interaction_history', {})
            contacts = interaction.get('contacts', [])
            if contacts:
                engagement_score += 15
            
            # Cap the score at 0-100
            engagement_score = max(0, min(100, engagement_score))
            
            insights['scores']['engagement_score'] = round(engagement_score, 1)
            
            # Generate observations
            profile = data.get('profile', {})
            
            if profile.get('segment') == 'PREMIUM':
                insights['observations'].append("Premium segment customer with high value")
            
            if total_balance > 500000 and penetration_score < 5:
                insights['observations'].append("High balance but low product penetration")
                insights['opportunities'].append("Cross-sell investment products")
            
            if total_overdue > 0:
                insights['observations'].append("Has overdue loan payments")
                insights['risks'].append("Credit risk - overdue payments")
            
            if not logins:
                insights['observations'].append("No recent digital channel activity")
                insights['opportunities'].append("Digital channel activation campaign")
            
            # Add more insights based on data patterns...
            
            return {
                'insights': insights
            }
            
        except Exception as e:
            logger.error(f"Error calculating insights: {e}")
            return {'insights': insights}
    
    def get_segment_overview(self, segment: str) -> Dict[str, Any]:
        """
        Get overview statistics for a customer segment
        
        Args:
            segment: Customer segment name
            
        Returns:
            Summary statistics for the segment
        """
        try:
            conn = self.customer_db.db_connection.get_connection()
            if not conn:
                logger.error("Failed to connect to database")
                return {}
            
            cursor = conn.cursor(dictionary=True)
            
            # Get segment statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as customer_count,
                    AVG(DATEDIFF(CURDATE(), registration_date)) as avg_tenure_days
                FROM cbs_customers
                WHERE segment = %s
            """, (segment,))
            
            stats = cursor.fetchone()
            
            # Get account statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as account_count,
                    SUM(balance) as total_balance,
                    AVG(balance) as avg_balance
                FROM cbs_accounts a
                JOIN cbs_customers c ON a.customer_id = c.customer_id
                WHERE c.segment = %s
            """, (segment,))
            
            account_stats = cursor.fetchone()
            
            cursor.close()
            
            return {
                'segment': segment,
                'statistics': {
                    'customer_count': stats.get('customer_count', 0) if stats else 0,
                    'avg_tenure_days': stats.get('avg_tenure_days', 0) if stats else 0,
                    'account_count': account_stats.get('account_count', 0) if account_stats else 0,
                    'total_balance': account_stats.get('total_balance', 0) if account_stats else 0,
                    'avg_balance': account_stats.get('avg_balance', 0) if account_stats else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error fetching overview for segment {segment}: {e}")
            return {}


# Singleton instance
customer_360 = Customer360View()


def get_customer_360() -> Customer360View:
    """Get the Customer 360 View instance"""
    return customer_360