"""
Card Service

Provides functionality for card management in the Core Banking System.
"""

import logging
import time
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple
import random

from database.connection import db_session_scope
from app.models.models import Card, Account, Customer, Transaction
from app.lib.notification_service import notification_service
from app.lib.id_generator import generate_card_number, CardType
from security.encryption import encrypt_data, decrypt_data
from security.password_manager import hash_password, verify_password

logger = logging.getLogger(__name__)

class CardService:
    """
    Service class for card management
    
    Features:
    - Card issuance and activation
    - PIN management
    - Card blocking and unblocking
    - Limit management
    - Card replacement
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(CardService, cls).__new__(cls)
        return cls._instance
    
    def issue_card(self, account_number: str, card_type: str = "DEBIT", 
                card_network: str = "RUPAY", holder_name: str = None) -> Dict[str, Any]:
        """
        Issue a new card for an account
        
        Args:
            account_number: Account number
            card_type: Type of card (DEBIT, CREDIT, etc.)
            card_network: Card network (RUPAY, VISA, MASTERCARD)
            holder_name: Name to appear on card
            
        Returns:
            Dict containing card issuance status and details
        """
        try:
            # Validate inputs
            if not account_number:
                return {
                    'success': False,
                    'error': 'Account number is required'
                }
            
            with db_session_scope() as session:
                # Check if account exists
                account = session.query(Account).filter_by(account_number=account_number).first()
                
                if not account:
                    return {
                        'success': False,
                        'error': 'Account not found'
                    }
                
                # Check if account is active
                if not account.is_active:
                    return {
                        'success': False,
                        'error': 'Account is not active'
                    }
                
                # If holder name not provided, get it from customer
                if not holder_name:
                    customer = session.query(Customer).filter_by(id=account.customer_id).first()
                    if customer:
                        holder_name = f"{customer.first_name} {customer.last_name}"
                    else:
                        return {
                            'success': False,
                            'error': 'Customer information not found'
                        }
                
                # Generate card number
                card_number = generate_card_number(card_type, card_network)
                
                # Calculate expiry date (5 years from now)
                expiry_date = datetime.now() + timedelta(days=365 * 5)
                
                # Generate CVV
                cvv = ''.join(random.choices('0123456789', k=3))
                
                # Generate initial PIN
                initial_pin = ''.join(random.choices('0123456789', k=4))
                pin_hash = hash_password(initial_pin)  # This will be reset by user during activation
                
                # Generate card ID
                card_id = f"CARD{int(time.time())}{random.randint(1000, 9999)}"
                
                # Create new card
                new_card = Card(
                    card_id=card_id,
                    card_number=card_number,
                    account_id=account.id,
                    card_type=card_type,
                    card_network=card_network,
                    holder_name=holder_name,
                    expiry_date=expiry_date,
                    cvv=encrypt_data(cvv),  # Store encrypted
                    pin=encrypt_data(pin_hash),  # Store encrypted hash
                    is_active=False,  # Needs activation
                    issued_date=datetime.now(),
                    daily_atm_limit=10000.0 if card_type == "DEBIT" else 20000.0,
                    daily_pos_limit=25000.0 if card_type == "DEBIT" else 50000.0,
                    daily_online_limit=50000.0 if card_type == "DEBIT" else 100000.0,
                    domestic_usage=True,
                    international_usage=False,
                    contactless_enabled=True,
                    status="PENDING_ACTIVATION"
                )
                
                session.add(new_card)
                session.commit()
                
                # Send card issuance notification
                self._send_card_issuance_notification(account, new_card, initial_pin)
                
                return {
                    'success': True,
                    'card_id': card_id,
                    'card_number': f"XXXX XXXX XXXX {card_number[-4:]}",  # Show only last 4 digits
                    'card_type': card_type,
                    'card_network': card_network,
                    'holder_name': holder_name,
                    'expiry_date': expiry_date.strftime('%m/%y'),
                    'issued_date': datetime.now().strftime('%Y-%m-%d'),
                    'status': 'PENDING_ACTIVATION',
                    'message': 'Card has been issued successfully. PIN will be shared securely. Please activate the card.'
                }
                
        except Exception as e:
            logger.error(f"Error issuing card: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def activate_card(self, card_number: str, cvv: str, new_pin: str) -> Dict[str, Any]:
        """
        Activate a newly issued card
        
        Args:
            card_number: Card number
            cvv: Card verification value
            new_pin: New PIN to set
            
        Returns:
            Dict containing activation status
        """
        try:
            # Validate inputs
            if not all([card_number, cvv, new_pin]):
                return {
                    'success': False,
                    'error': 'Card number, CVV and new PIN are required'
                }
            
            # Validate PIN format
            if not new_pin.isdigit() or len(new_pin) != 4:
                return {
                    'success': False,
                    'error': 'PIN must be 4 digits'
                }
                
            with db_session_scope() as session:
                # Get card details
                card = session.query(Card).filter_by(card_number=card_number).first()
                
                if not card:
                    return {
                        'success': False,
                        'error': 'Card not found'
                    }
                
                # Check if card is already active
                if card.status != "PENDING_ACTIVATION":
                    return {
                        'success': False,
                        'error': f'Card is already {card.status.lower()}'
                    }
                
                # Verify CVV
                stored_cvv = decrypt_data(card.cvv)
                if cvv != stored_cvv:
                    logger.warning(f"Failed card activation attempt with invalid CVV: {card_number}")
                    return {
                        'success': False,
                        'error': 'Invalid CVV'
                    }
                
                # Update card status and PIN
                card.status = "ACTIVE"
                card.is_active = True
                card.pin = encrypt_data(hash_password(new_pin))
                card.activation_date = datetime.now()
                card.updated_at = datetime.now()
                
                # Commit changes
                session.commit()
                
                # Get account details for notification
                account = session.query(Account).filter_by(id=card.account_id).first()
                
                # Send activation notification
                self._send_card_activation_notification(account, card)
                
                return {
                    'success': True,
                    'card_number': f"XXXX XXXX XXXX {card_number[-4:]}",
                    'status': 'ACTIVE',
                    'activation_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'message': 'Card has been activated successfully'
                }
                
        except Exception as e:
            logger.error(f"Error activating card: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def block_card(self, card_number: str, reason: str) -> Dict[str, Any]:
        """
        Block a card
        
        Args:
            card_number: Card number
            reason: Reason for blocking
            
        Returns:
            Dict containing block status
        """
        try:
            # Validate inputs
            if not card_number:
                return {
                    'success': False,
                    'error': 'Card number is required'
                }
            
            with db_session_scope() as session:
                # Get card details
                card = session.query(Card).filter_by(card_number=card_number).first()
                
                if not card:
                    return {
                        'success': False,
                        'error': 'Card not found'
                    }
                
                # Check if card is already blocked
                if card.status == "BLOCKED":
                    return {
                        'success': False,
                        'error': 'Card is already blocked'
                    }
                
                # Update card status
                old_status = card.status
                card.status = "BLOCKED"
                card.is_active = False
                card.updated_at = datetime.now()
                
                # Commit changes
                session.commit()
                
                # Get account details for notification
                account = session.query(Account).filter_by(id=card.account_id).first()
                
                # Send block notification
                self._send_card_status_notification(account, card, old_status, "BLOCKED", reason)
                
                return {
                    'success': True,
                    'card_number': f"XXXX XXXX XXXX {card_number[-4:]}",
                    'old_status': old_status,
                    'new_status': 'BLOCKED',
                    'block_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'reason': reason,
                    'message': 'Card has been blocked successfully'
                }
                
        except Exception as e:
            logger.error(f"Error blocking card: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def unblock_card(self, card_number: str) -> Dict[str, Any]:
        """
        Unblock a previously blocked card
        
        Args:
            card_number: Card number
            
        Returns:
            Dict containing unblock status
        """
        try:
            # Validate inputs
            if not card_number:
                return {
                    'success': False,
                    'error': 'Card number is required'
                }
            
            with db_session_scope() as session:
                # Get card details
                card = session.query(Card).filter_by(card_number=card_number).first()
                
                if not card:
                    return {
                        'success': False,
                        'error': 'Card not found'
                    }
                
                # Check if card is blocked
                if card.status != "BLOCKED":
                    return {
                        'success': False,
                        'error': f'Card is not blocked, current status: {card.status}'
                    }
                
                # Update card status
                card.status = "ACTIVE"
                card.is_active = True
                card.updated_at = datetime.now()
                
                # Commit changes
                session.commit()
                
                # Get account details for notification
                account = session.query(Account).filter_by(id=card.account_id).first()
                
                # Send unblock notification
                self._send_card_status_notification(account, card, "BLOCKED", "ACTIVE", "Card unblocked on request")
                
                return {
                    'success': True,
                    'card_number': f"XXXX XXXX XXXX {card_number[-4:]}",
                    'old_status': 'BLOCKED',
                    'new_status': 'ACTIVE',
                    'unblock_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'message': 'Card has been unblocked successfully'
                }
                
        except Exception as e:
            logger.error(f"Error unblocking card: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def change_pin(self, card_number: str, old_pin: str, new_pin: str) -> Dict[str, Any]:
        """
        Change card PIN
        
        Args:
            card_number: Card number
            old_pin: Current PIN
            new_pin: New PIN
            
        Returns:
            Dict containing PIN change status
        """
        try:
            # Validate inputs
            if not all([card_number, old_pin, new_pin]):
                return {
                    'success': False,
                    'error': 'Card number, old PIN and new PIN are required'
                }
            
            # Validate PIN format
            if not new_pin.isdigit() or len(new_pin) != 4:
                return {
                    'success': False,
                    'error': 'PIN must be 4 digits'
                }
            
            # Prevent common PINs
            common_pins = {'0000', '1111', '1234', '2580', '5683', '0852', '1010', '2000', '2222'}
            if new_pin in common_pins:
                return {
                    'success': False,
                    'error': 'PIN is too common and easily guessable'
                }
            
            with db_session_scope() as session:
                # Get card details
                card = session.query(Card).filter_by(card_number=card_number).first()
                
                if not card:
                    return {
                        'success': False,
                        'error': 'Card not found'
                    }
                
                # Check if card is active
                if not card.is_active or card.status != "ACTIVE":
                    return {
                        'success': False,
                        'error': f'Card is not active, current status: {card.status}'
                    }
                
                # Verify old PIN
                stored_pin_hash = decrypt_data(card.pin)  # Decrypt the stored PIN hash
                if not verify_password(old_pin, stored_pin_hash):
                    logger.warning(f"Failed PIN change attempt with invalid old PIN: {card_number}")
                    return {
                        'success': False,
                        'error': 'Invalid old PIN'
                    }
                
                # Update PIN
                card.pin = encrypt_data(hash_password(new_pin))  # Store encrypted hash of new PIN
                card.updated_at = datetime.now()
                
                # Commit changes
                session.commit()
                
                # Get account details for notification
                account = session.query(Account).filter_by(id=card.account_id).first()
                
                # Send PIN change notification
                self._send_pin_change_notification(account, card)
                
                return {
                    'success': True,
                    'card_number': f"XXXX XXXX XXXX {card_number[-4:]}",
                    'change_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'message': 'Card PIN has been changed successfully'
                }
                
        except Exception as e:
            logger.error(f"Error changing card PIN: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_card_limits(self, card_number: str, 
                         atm_limit: float = None, 
                         pos_limit: float = None, 
                         online_limit: float = None) -> Dict[str, Any]:
        """
        Update card transaction limits
        
        Args:
            card_number: Card number
            atm_limit: Daily ATM withdrawal limit
            pos_limit: Daily POS transaction limit
            online_limit: Daily online transaction limit
            
        Returns:
            Dict containing limit update status
        """
        try:
            # Validate inputs
            if not card_number:
                return {
                    'success': False,
                    'error': 'Card number is required'
                }
            
            # Validate that at least one limit is provided
            if all(limit is None for limit in [atm_limit, pos_limit, online_limit]):
                return {
                    'success': False,
                    'error': 'At least one limit must be provided'
                }
            
            with db_session_scope() as session:
                # Get card details
                card = session.query(Card).filter_by(card_number=card_number).first()
                
                if not card:
                    return {
                        'success': False,
                        'error': 'Card not found'
                    }
                
                # Check if card is active
                if not card.is_active:
                    return {
                        'success': False,
                        'error': f'Card is not active, current status: {card.status}'
                    }
                
                # Store old limits for notification
                old_limits = {
                    'atm_limit': card.daily_atm_limit,
                    'pos_limit': card.daily_pos_limit,
                    'online_limit': card.daily_online_limit
                }
                
                # Update limits
                changes_made = False
                
                if atm_limit is not None:
                    card.daily_atm_limit = atm_limit
                    changes_made = True
                    
                if pos_limit is not None:
                    card.daily_pos_limit = pos_limit
                    changes_made = True
                    
                if online_limit is not None:
                    card.daily_online_limit = online_limit
                    changes_made = True
                
                if changes_made:
                    card.updated_at = datetime.now()
                    
                    # Commit changes
                    session.commit()
                    
                    # Get account details for notification
                    account = session.query(Account).filter_by(id=card.account_id).first()
                    
                    # Send limit update notification
                    self._send_limit_update_notification(account, card, old_limits)
                    
                    return {
                        'success': True,
                        'card_number': f"XXXX XXXX XXXX {card_number[-4:]}",
                        'updated_limits': {
                            'daily_atm_limit': card.daily_atm_limit,
                            'daily_pos_limit': card.daily_pos_limit,
                            'daily_online_limit': card.daily_online_limit
                        },
                        'update_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'message': 'Card limits have been updated successfully'
                    }
                else:
                    return {
                        'success': True,
                        'message': 'No changes made to card limits'
                    }
                
        except Exception as e:
            logger.error(f"Error updating card limits: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_card_details(self, card_number: str) -> Dict[str, Any]:
        """
        Get card details
        
        Args:
            card_number: Card number
            
        Returns:
            Dict containing card details
        """
        try:
            with db_session_scope() as session:
                # Get card details
                card = session.query(Card).filter_by(card_number=card_number).first()
                
                if not card:
                    return {
                        'success': False,
                        'error': 'Card not found'
                    }
                
                # Get account details
                account = session.query(Account).filter_by(id=card.account_id).first()
                
                # Format card details
                card_details = {
                    'success': True,
                    'card': {
                        'card_id': card.card_id,
                        'card_number': f"XXXX XXXX XXXX {card_number[-4:]}",
                        'card_type': card.card_type,
                        'card_network': card.card_network,
                        'holder_name': card.holder_name,
                        'expiry_date': card.expiry_date.strftime('%m/%y'),
                        'status': card.status,
                        'is_active': card.is_active,
                        'issued_date': card.issued_date.strftime('%Y-%m-%d'),
                        'activation_date': card.activation_date.strftime('%Y-%m-%d') if card.activation_date else None,
                        'limits': {
                            'daily_atm_limit': card.daily_atm_limit,
                            'daily_pos_limit': card.daily_pos_limit,
                            'daily_online_limit': card.daily_online_limit
                        },
                        'features': {
                            'domestic_usage': card.domestic_usage,
                            'international_usage': card.international_usage,
                            'contactless_enabled': card.contactless_enabled
                        }
                    },
                    'account': {
                        'account_number': account.account_number if account else None,
                        'account_type': account.account_type if account else None
                    }
                }
                
                return card_details
                
        except Exception as e:
            logger.error(f"Error retrieving card details: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_customer_cards(self, customer_id: int) -> Dict[str, Any]:
        """
        Get all cards for a customer
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dict containing list of customer cards
        """
        try:
            with db_session_scope() as session:
                # Check if customer exists
                customer = session.query(Customer).filter_by(id=customer_id).first()
                
                if not customer:
                    return {
                        'success': False,
                        'error': 'Customer not found'
                    }
                
                # Get all accounts for the customer
                accounts = session.query(Account).filter_by(customer_id=customer_id).all()
                account_ids = [account.id for account in accounts]
                
                # Get all cards for these accounts
                cards = session.query(Card).filter(Card.account_id.in_(account_ids)).all()
                
                # Format card information
                card_list = []
                for card in cards:
                    account = session.query(Account).filter_by(id=card.account_id).first()
                    
                    card_list.append({
                        'card_id': card.card_id,
                        'card_number': f"XXXX XXXX XXXX {card.card_number[-4:]}",
                        'card_type': card.card_type,
                        'card_network': card.card_network,
                        'status': card.status,
                        'expiry_date': card.expiry_date.strftime('%m/%y'),
                        'account_number': account.account_number if account else None,
                        'account_type': account.account_type if account else None
                    })
                
                return {
                    'success': True,
                    'customer_id': customer_id,
                    'customer_name': f"{customer.first_name} {customer.last_name}",
                    'card_count': len(card_list),
                    'cards': card_list
                }
                
        except Exception as e:
            logger.error(f"Error retrieving customer cards: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def toggle_international_usage(self, card_number: str, enable: bool) -> Dict[str, Any]:
        """
        Enable or disable international usage for a card
        
        Args:
            card_number: Card number
            enable: Boolean indicating whether to enable or disable
            
        Returns:
            Dict containing toggle status
        """
        try:
            with db_session_scope() as session:
                # Get card details
                card = session.query(Card).filter_by(card_number=card_number).first()
                
                if not card:
                    return {
                        'success': False,
                        'error': 'Card not found'
                    }
                
                # Check if card is active
                if not card.is_active:
                    return {
                        'success': False,
                        'error': f'Card is not active, current status: {card.status}'
                    }
                
                # Check if setting is already in desired state
                if card.international_usage == enable:
                    return {
                        'success': True,
                        'message': f"International usage is already {'enabled' if enable else 'disabled'}"
                    }
                
                # Update international usage setting
                card.international_usage = enable
                card.updated_at = datetime.now()
                
                # Commit changes
                session.commit()
                
                # Get account details for notification
                account = session.query(Account).filter_by(id=card.account_id).first()
                
                # Send notification
                self._send_feature_update_notification(account, card, 'international_usage', enable)
                
                return {
                    'success': True,
                    'card_number': f"XXXX XXXX XXXX {card_number[-4:]}",
                    'international_usage': enable,
                    'update_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'message': f"International usage has been {'enabled' if enable else 'disabled'} successfully"
                }
                
        except Exception as e:
            logger.error(f"Error toggling international usage: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def toggle_contactless_feature(self, card_number: str, enable: bool) -> Dict[str, Any]:
        """
        Enable or disable contactless feature for a card
        
        Args:
            card_number: Card number
            enable: Boolean indicating whether to enable or disable
            
        Returns:
            Dict containing toggle status
        """
        try:
            with db_session_scope() as session:
                # Get card details
                card = session.query(Card).filter_by(card_number=card_number).first()
                
                if not card:
                    return {
                        'success': False,
                        'error': 'Card not found'
                    }
                
                # Check if card is active
                if not card.is_active:
                    return {
                        'success': False,
                        'error': f'Card is not active, current status: {card.status}'
                    }
                
                # Check if setting is already in desired state
                if card.contactless_enabled == enable:
                    return {
                        'success': True,
                        'message': f"Contactless feature is already {'enabled' if enable else 'disabled'}"
                    }
                
                # Update contactless setting
                card.contactless_enabled = enable
                card.updated_at = datetime.now()
                
                # Commit changes
                session.commit()
                
                # Get account details for notification
                account = session.query(Account).filter_by(id=card.account_id).first()
                
                # Send notification
                self._send_feature_update_notification(account, card, 'contactless', enable)
                
                return {
                    'success': True,
                    'card_number': f"XXXX XXXX XXXX {card_number[-4:]}",
                    'contactless_enabled': enable,
                    'update_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'message': f"Contactless feature has been {'enabled' if enable else 'disabled'} successfully"
                }
                
        except Exception as e:
            logger.error(f"Error toggling contactless feature: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _send_card_issuance_notification(self, account, card, pin):
        """Send notification about card issuance"""
        try:
            with db_session_scope() as session:
                customer = session.query(Customer).filter_by(id=account.customer_id).first()
                
                if customer and (hasattr(customer, 'email') or hasattr(customer, 'phone')):
                    customer_data = {
                        'email': getattr(customer, 'email', None),
                        'phone_number': getattr(customer, 'phone', None)
                    }
                    
                    # Email notification
                    if customer_data['email']:
                        subject = f"Your new {card.card_type} Card has been issued"
                        message = f"""
                        Dear {customer.first_name if hasattr(customer, 'first_name') else 'Valued Customer'},
                        
                        Your new {card.card_type} Card has been issued for your {account.account_type} account ({account.account_number}).
                        
                        Card Details:
                        - Card Number: XXXX XXXX XXXX {card.card_number[-4:]}
                        - Card Type: {card.card_type}
                        - Card Network: {card.card_network}
                        - Expiry Date: {card.expiry_date.strftime('%m/%y')}
                        
                        To ensure security, your initial PIN will be sent to you separately.
                        
                        Important:
                        1. You need to activate your card before using it.
                        2. Please change the initial PIN during activation.
                        
                        For card activation, please visit your nearest branch or use our mobile banking application.
                        
                        Thank you for banking with us.
                        
                        Regards,
                        Core Banking System
                        """
                        
                        notification_service.send_email(
                            recipient=customer_data['email'],
                            subject=subject,
                            message=message
                        )
                    
                    # SMS notification
                    if customer_data['phone_number']:
                        sms_message = (
                            f"Your {card.card_type} Card (XXXX {card.card_number[-4:]}) has been issued. "
                            f"Please activate it before use. PIN sent separately."
                        )
                        
                        notification_service.send_sms(
                            phone_number=customer_data['phone_number'],
                            message=sms_message
                        )
                    
                    # Send pin separately (this would be via a secure channel in a real system)
                    # In a production system, PIN would typically be sent via mail or a secure PIN mailer
                    logger.info(f"PIN for card {card.card_number} would be securely delivered to the customer")
        except Exception as e:
            logger.error(f"Failed to send card issuance notification: {str(e)}")
    
    def _send_card_activation_notification(self, account, card):
        """Send notification about card activation"""
        try:
            with db_session_scope() as session:
                customer = session.query(Customer).filter_by(id=account.customer_id).first()
                
                if customer and (hasattr(customer, 'email') or hasattr(customer, 'phone')):
                    customer_data = {
                        'email': getattr(customer, 'email', None),
                        'phone_number': getattr(customer, 'phone', None)
                    }
                    
                    # Email notification
                    if customer_data['email']:
                        subject = f"Your {card.card_type} Card has been activated"
                        message = f"""
                        Dear {customer.first_name if hasattr(customer, 'first_name') else 'Valued Customer'},
                        
                        Your {card.card_type} Card (XXXX XXXX XXXX {card.card_number[-4:]}) has been successfully activated.
                        
                        You can now use your card for:
                        - ATM withdrawals (Daily limit: {card.daily_atm_limit})
                        - POS transactions (Daily limit: {card.daily_pos_limit})
                        - Online purchases (Daily limit: {card.daily_online_limit})
                        
                        For security reasons, please never share your PIN with anyone and regularly monitor your transactions.
                        
                        Thank you for banking with us.
                        
                        Regards,
                        Core Banking System
                        """
                        
                        notification_service.send_email(
                            recipient=customer_data['email'],
                            subject=subject,
                            message=message
                        )
                    
                    # SMS notification
                    if customer_data['phone_number']:
                        sms_message = (
                            f"Your {card.card_type} Card (XXXX {card.card_number[-4:]}) is now active. "
                            f"ATM Limit: {card.daily_atm_limit}, POS Limit: {card.daily_pos_limit}"
                        )
                        
                        notification_service.send_sms(
                            phone_number=customer_data['phone_number'],
                            message=sms_message
                        )
        except Exception as e:
            logger.error(f"Failed to send card activation notification: {str(e)}")
    
    def _send_card_status_notification(self, account, card, old_status, new_status, reason=None):
        """Send notification about card status change"""
        try:
            with db_session_scope() as session:
                customer = session.query(Customer).filter_by(id=account.customer_id).first()
                
                if customer and (hasattr(customer, 'email') or hasattr(customer, 'phone')):
                    customer_data = {
                        'email': getattr(customer, 'email', None),
                        'phone_number': getattr(customer, 'phone', None)
                    }
                    
                    status_message = f"Your {card.card_type} Card (XXXX XXXX XXXX {card.card_number[-4:]}) has been {new_status.lower()}."
                    if reason:
                        status_message += f" Reason: {reason}"
                    
                    # Email notification
                    if customer_data['email']:
                        subject = f"Your Card has been {new_status.title()}"
                        message = f"""
                        Dear {customer.first_name if hasattr(customer, 'first_name') else 'Valued Customer'},
                        
                        {status_message}
                        
                        If you did not request this change or have any questions, please contact our customer support immediately.
                        
                        Thank you for banking with us.
                        
                        Regards,
                        Core Banking System
                        """
                        
                        notification_service.send_email(
                            recipient=customer_data['email'],
                            subject=subject,
                            message=message
                        )
                    
                    # SMS notification
                    if customer_data['phone_number']:
                        sms_message = status_message + " Contact support if needed."
                        
                        notification_service.send_sms(
                            phone_number=customer_data['phone_number'],
                            message=sms_message
                        )
        except Exception as e:
            logger.error(f"Failed to send card status notification: {str(e)}")
    
    def _send_pin_change_notification(self, account, card):
        """Send notification about PIN change"""
        try:
            with db_session_scope() as session:
                customer = session.query(Customer).filter_by(id=account.customer_id).first()
                
                if customer and (hasattr(customer, 'email') or hasattr(customer, 'phone')):
                    customer_data = {
                        'email': getattr(customer, 'email', None),
                        'phone_number': getattr(customer, 'phone', None)
                    }
                    
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Email notification
                    if customer_data['email']:
                        subject = "Your Card PIN has been changed"
                        message = f"""
                        Dear {customer.first_name if hasattr(customer, 'first_name') else 'Valued Customer'},
                        
                        The PIN for your {card.card_type} Card (XXXX XXXX XXXX {card.card_number[-4:]}) has been changed successfully at {timestamp}.
                        
                        If you did not initiate this change, please contact our customer support immediately.
                        
                        Thank you for banking with us.
                        
                        Regards,
                        Core Banking System
                        """
                        
                        notification_service.send_email(
                            recipient=customer_data['email'],
                            subject=subject,
                            message=message
                        )
                    
                    # SMS notification
                    if customer_data['phone_number']:
                        sms_message = (
                            f"PIN changed for your card ending with {card.card_number[-4:]} at {timestamp}. "
                            "If unauthorized, call customer care immediately."
                        )
                        
                        notification_service.send_sms(
                            phone_number=customer_data['phone_number'],
                            message=sms_message
                        )
        except Exception as e:
            logger.error(f"Failed to send PIN change notification: {str(e)}")
    
    def _send_limit_update_notification(self, account, card, old_limits):
        """Send notification about limit updates"""
        try:
            with db_session_scope() as session:
                customer = session.query(Customer).filter_by(id=account.customer_id).first()
                
                if customer and (hasattr(customer, 'email') or hasattr(customer, 'phone')):
                    customer_data = {
                        'email': getattr(customer, 'email', None),
                        'phone_number': getattr(customer, 'phone', None)
                    }
                    
                    # Create message showing changes
                    limit_changes = []
                    if card.daily_atm_limit != old_limits['atm_limit']:
                        limit_changes.append(f"ATM limit: {old_limits['atm_limit']} → {card.daily_atm_limit}")
                    if card.daily_pos_limit != old_limits['pos_limit']:
                        limit_changes.append(f"POS limit: {old_limits['pos_limit']} → {card.daily_pos_limit}")
                    if card.daily_online_limit != old_limits['online_limit']:
                        limit_changes.append(f"Online limit: {old_limits['online_limit']} → {card.daily_online_limit}")
                    
                    changes_text = "\n- " + "\n- ".join(limit_changes)
                    
                    # Email notification
                    if customer_data['email']:
                        subject = "Your Card Limits Have Been Updated"
                        message = f"""
                        Dear {customer.first_name if hasattr(customer, 'first_name') else 'Valued Customer'},
                        
                        The transaction limits for your {card.card_type} Card (XXXX XXXX XXXX {card.card_number[-4:]}) have been updated.
                        
                        Changes:{changes_text}
                        
                        If you did not request these changes, please contact our customer support immediately.
                        
                        Thank you for banking with us.
                        
                        Regards,
                        Core Banking System
                        """
                        
                        notification_service.send_email(
                            recipient=customer_data['email'],
                            subject=subject,
                            message=message
                        )
                    
                    # SMS notification
                    if customer_data['phone_number']:
                        sms_message = (
                            f"Limits updated for your card ending with {card.card_number[-4:]}. "
                            f"New limits: ATM={card.daily_atm_limit}, POS={card.daily_pos_limit}, Online={card.daily_online_limit}"
                        )
                        
                        notification_service.send_sms(
                            phone_number=customer_data['phone_number'],
                            message=sms_message
                        )
        except Exception as e:
            logger.error(f"Failed to send limit update notification: {str(e)}")
    
    def _send_feature_update_notification(self, account, card, feature, enabled):
        """Send notification about feature update"""
        try:
            with db_session_scope() as session:
                customer = session.query(Customer).filter_by(id=account.customer_id).first()
                
                if customer and (hasattr(customer, 'email') or hasattr(customer, 'phone')):
                    customer_data = {
                        'email': getattr(customer, 'email', None),
                        'phone_number': getattr(customer, 'phone', None)
                    }
                    
                    feature_name = "International Usage" if feature == 'international_usage' else "Contactless Payments"
                    action = "enabled" if enabled else "disabled"
                    
                    # Email notification
                    if customer_data['email']:
                        subject = f"Card Feature Update: {feature_name}"
                        message = f"""
                        Dear {customer.first_name if hasattr(customer, 'first_name') else 'Valued Customer'},
                        
                        {feature_name} has been {action} for your {card.card_type} Card (XXXX XXXX XXXX {card.card_number[-4:]}).
                        
                        If you did not request this change, please contact our customer support immediately.
                        
                        Thank you for banking with us.
                        
                        Regards,
                        Core Banking System
                        """
                        
                        notification_service.send_email(
                            recipient=customer_data['email'],
                            subject=subject,
                            message=message
                        )
                    
                    # SMS notification
                    if customer_data['phone_number']:
                        sms_message = (
                            f"{feature_name} has been {action} for your card ending with {card.card_number[-4:]}. "
                            "Contact support if unauthorized."
                        )
                        
                        notification_service.send_sms(
                            phone_number=customer_data['phone_number'],
                            message=sms_message
                        )
        except Exception as e:
            logger.error(f"Failed to send feature update notification: {str(e)}")

# Create singleton instance
card_service = CardService()
