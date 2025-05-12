"""
Customer Service

Provides functionality for customer management in the Core Banking System.
"""

import logging
import uuid
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

from database.connection import db_session_scope
from app.models.models import Customer
from app.lib.notification_service import notification_service

logger = logging.getLogger(__name__)

class CustomerService:
    """
    Service class for customer-related operations
    
    Features:
    - Customer registration
    - Customer profile management
    - KYC (Know Your Customer)
    - Customer search and lookup
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(CustomerService, cls).__new__(cls)
        return cls._instance
    
    def create_customer(self, first_name: str, last_name: str, email: str, 
                      phone: str, address: str, date_of_birth: str, 
                      id_type: str, id_number: str) -> Dict[str, Any]:
        """
        Register a new customer
        
        Args:
            first_name: Customer's first name
            last_name: Customer's last name
            email: Customer's email address
            phone: Customer's phone number
            address: Customer's address
            date_of_birth: Customer's date of birth (YYYY-MM-DD)
            id_type: Type of ID document (AADHAR, PAN, PASSPORT, etc.)
            id_number: ID document number
            
        Returns:
            Dict containing customer details or error information
        """
        try:
            # Validate inputs
            validation_result = self._validate_customer_inputs(
                first_name, last_name, email, phone, date_of_birth, id_type, id_number
            )
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['message']
                }
            
            with db_session_scope() as session:
                # Check if email already exists
                existing_email = session.query(Customer).filter_by(email=email).first()
                if existing_email:
                    return {
                        'success': False,
                        'error': 'Email address already registered'
                    }
                
                # Check if phone already exists
                existing_phone = session.query(Customer).filter_by(phone=phone).first()
                if existing_phone:
                    return {
                        'success': False,
                        'error': 'Phone number already registered'
                    }
                
                # Check if ID already exists
                existing_id = session.query(Customer).filter_by(
                    id_type=id_type, id_number=id_number
                ).first()
                if existing_id:
                    return {
                        'success': False,
                        'error': 'ID already registered'
                    }
                
                # Generate customer ID
                customer_id = self._generate_customer_id()
                
                # Parse date of birth
                dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
                
                # Create customer
                customer = Customer(
                    customer_id=customer_id,
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                    address=address,
                    date_of_birth=dob,
                    id_type=id_type,
                    id_number=id_number,
                    status='ACTIVE',
                    kyc_status='PENDING',
                    created_at=datetime.now()
                )
                
                session.add(customer)
                session.commit()
                
                # Send welcome email
                self._send_welcome_email(customer)
                
                return {
                    'success': True,
                    'customer_id': customer.id,
                    'customer_reference': customer_id,
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': email,
                    'phone': phone,
                    'created_at': customer.created_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_customer(self, customer_id: int) -> Dict[str, Any]:
        """
        Get customer details by ID
        
        Args:
            customer_id: Customer's database ID
            
        Returns:
            Dict containing customer details or error information
        """
        try:
            with db_session_scope() as session:
                customer = session.query(Customer).filter_by(id=customer_id).first()
                
                if not customer:
                    return {
                        'success': False,
                        'error': 'Customer not found'
                    }
                
                return {
                    'success': True,
                    'customer': {
                        'id': customer.id,
                        'customer_id': customer.customer_id,
                        'first_name': customer.first_name,
                        'last_name': customer.last_name,
                        'email': customer.email,
                        'phone': customer.phone,
                        'address': customer.address,
                        'date_of_birth': customer.date_of_birth.isoformat() if customer.date_of_birth else None,
                        'id_type': customer.id_type,
                        'id_number': self._mask_id_number(customer.id_number),
                        'status': customer.status,
                        'kyc_status': customer.kyc_status,
                        'created_at': customer.created_at.isoformat() if customer.created_at else None
                    }
                }
                
        except Exception as e:
            logger.error(f"Error retrieving customer: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_customers(self, query: str, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """
        Search for customers by name, email, phone, or customer ID
        
        Args:
            query: Search string
            limit: Maximum number of results
            offset: Offset for pagination
            
        Returns:
            Dict containing search results
        """
        try:
            with db_session_scope() as session:
                # Build search query
                search_query = f"%{query}%"
                
                # Search in multiple fields
                customers = session.query(Customer).filter(
                    (Customer.first_name.like(search_query)) |
                    (Customer.last_name.like(search_query)) |
                    (Customer.email.like(search_query)) |
                    (Customer.phone.like(search_query)) |
                    (Customer.customer_id.like(search_query))
                ).limit(limit).offset(offset).all()
                
                # Format results
                results = [{
                    'id': c.id,
                    'customer_id': c.customer_id,
                    'name': f"{c.first_name} {c.last_name}",
                    'email': c.email,
                    'phone': c.phone,
                    'status': c.status
                } for c in customers]
                
                return {
                    'success': True,
                    'results': results,
                    'count': len(results)
                }
                
        except Exception as e:
            logger.error(f"Error searching customers: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_customer(self, customer_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update customer information
        
        Args:
            customer_id: Customer's database ID
            data: Dict containing fields to update
            
        Returns:
            Dict containing updated customer details or error information
        """
        try:
            allowed_fields = [
                'first_name', 'last_name', 'email', 'phone', 
                'address', 'status'
            ]
            
            # Filter only allowed fields
            update_data = {k: v for k, v in data.items() if k in allowed_fields}
            
            if not update_data:
                return {
                    'success': False,
                    'error': 'No valid fields to update'
                }
            
            with db_session_scope() as session:
                customer = session.query(Customer).filter_by(id=customer_id).first()
                
                if not customer:
                    return {
                        'success': False,
                        'error': 'Customer not found'
                    }
                
                # Check email uniqueness if email is being updated
                if 'email' in update_data and update_data['email'] != customer.email:
                    existing_email = session.query(Customer).filter_by(
                        email=update_data['email']
                    ).first()
                    
                    if existing_email:
                        return {
                            'success': False,
                            'error': 'Email address already registered'
                        }
                
                # Check phone uniqueness if phone is being updated
                if 'phone' in update_data and update_data['phone'] != customer.phone:
                    existing_phone = session.query(Customer).filter_by(
                        phone=update_data['phone']
                    ).first()
                    
                    if existing_phone:
                        return {
                            'success': False,
                            'error': 'Phone number already registered'
                        }
                
                # Update fields
                for key, value in update_data.items():
                    setattr(customer, key, value)
                
                customer.updated_at = datetime.now()
                
                # Commit changes
                session.commit()
                
                return {
                    'success': True,
                    'customer_id': customer.id,
                    'updated_fields': list(update_data.keys()),
                    'message': 'Customer information updated successfully'
                }
                
        except Exception as e:
            logger.error(f"Error updating customer: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_kyc_status(self, customer_id: int, kyc_status: str, 
                        remarks: str = None) -> Dict[str, Any]:
        """
        Update customer KYC status
        
        Args:
            customer_id: Customer's database ID
            kyc_status: New KYC status (PENDING, VERIFIED, REJECTED)
            remarks: Optional remarks for the status change
            
        Returns:
            Dict containing status of the operation
        """
        try:
            valid_statuses = ['PENDING', 'VERIFIED', 'REJECTED', 'IN_PROGRESS']
            
            if kyc_status not in valid_statuses:
                return {
                    'success': False,
                    'error': f'Invalid KYC status. Valid statuses are: {", ".join(valid_statuses)}'
                }
            
            with db_session_scope() as session:
                customer = session.query(Customer).filter_by(id=customer_id).first()
                
                if not customer:
                    return {
                        'success': False,
                        'error': 'Customer not found'
                    }
                
                # Update KYC status
                old_status = customer.kyc_status
                customer.kyc_status = kyc_status
                customer.kyc_remarks = remarks
                customer.kyc_updated_at = datetime.now()
                
                # Commit changes
                session.commit()
                
                # Send notification if status changed to VERIFIED or REJECTED
                if kyc_status in ['VERIFIED', 'REJECTED'] and old_status != kyc_status:
                    self._send_kyc_status_notification(customer, kyc_status, remarks)
                
                return {
                    'success': True,
                    'customer_id': customer.id,
                    'old_status': old_status,
                    'new_status': kyc_status,
                    'message': 'KYC status updated successfully'
                }
                
        except Exception as e:
            logger.error(f"Error updating KYC status: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_customer_inputs(self, first_name, last_name, email, phone, 
                                date_of_birth, id_type, id_number) -> Dict[str, Any]:
        """Validate customer input data"""
        # Check for empty required fields
        if not all([first_name, last_name, email, phone, date_of_birth, id_type, id_number]):
            return {
                'valid': False,
                'message': 'All fields are required'
            }
        
        # Validate email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return {
                'valid': False,
                'message': 'Invalid email address format'
            }
        
        # Validate phone format (simple check for digits and length)
        if not phone.isdigit() or len(phone) < 10:
            return {
                'valid': False,
                'message': 'Invalid phone number format'
            }
        
        # Validate date of birth
        try:
            dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            today = datetime.now().date()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            # Check if person is at least 18 years old
            if age < 18:
                return {
                    'valid': False,
                    'message': 'Customer must be at least 18 years old'
                }
                
        except ValueError:
            return {
                'valid': False,
                'message': 'Invalid date of birth format (use YYYY-MM-DD)'
            }
        
        # Validate ID type
        valid_id_types = ['AADHAR', 'PAN', 'PASSPORT', 'VOTER_ID', 'DRIVING_LICENSE']
        if id_type not in valid_id_types:
            return {
                'valid': False,
                'message': f'Invalid ID type. Valid types are: {", ".join(valid_id_types)}'
            }
        
        return {
            'valid': True
        }
    
    def _generate_customer_id(self) -> str:
        """Generate a unique customer ID"""
        # Format: CUS-YYYYMMDD-XXXX where XXXX is a random 4-digit number
        date_part = datetime.now().strftime('%Y%m%d')
        random_part = str(uuid.uuid4().int)[:4]
        return f"CUS-{date_part}-{random_part}"
    
    def _mask_id_number(self, id_number: str) -> str:
        """Mask ID number for security"""
        if not id_number or len(id_number) <= 4:
            return id_number
        
        masked_part = '*' * (len(id_number) - 4)
        last_four = id_number[-4:]
        return f"{masked_part}{last_four}"
    
    def _send_welcome_email(self, customer):
        """Send welcome email to new customer"""
        if hasattr(customer, 'email') and customer.email:
            subject = "Welcome to Our Banking Services"
            message = f"""
            Dear {customer.first_name} {customer.last_name},
            
            Welcome to our banking services! We are delighted to have you as our customer.
            
            Your customer reference number is: {customer.customer_id}
            
            To complete your registration, we need to verify your identity. Please visit any of our branches 
            with your original ID documents to complete the KYC process.
            
            If you have any questions, please feel free to contact our customer support.
            
            Thank you for choosing our services!
            
            Sincerely,
            The Banking Team
            """
            
            notification_service.send_email(
                recipient=customer.email,
                subject=subject,
                message=message
            )
    
    def _send_kyc_status_notification(self, customer, status, remarks=None):
        """Send notification about KYC status change"""
        if hasattr(customer, 'email') and customer.email:
            if status == 'VERIFIED':
                subject = "Your KYC Verification is Successful"
                message = f"""
                Dear {customer.first_name} {customer.last_name},
                
                We are pleased to inform you that your KYC (Know Your Customer) verification has been completed successfully.
                
                You now have full access to all our banking services.
                
                Thank you for your patience during this process.
                
                Sincerely,
                The Banking Team
                """
                
            elif status == 'REJECTED':
                subject = "KYC Verification Update Required"
                message = f"""
                Dear {customer.first_name} {customer.last_name},
                
                We regret to inform you that your KYC (Know Your Customer) verification could not be completed.
                
                Reason: {remarks or 'Verification documents not acceptable'}
                
                Please visit any of our branches with valid ID documents to complete the KYC process.
                
                If you have any questions, please contact our customer support.
                
                Sincerely,
                The Banking Team
                """
                
            else:
                return
            
            notification_service.send_email(
                recipient=customer.email,
                subject=subject,
                message=message
            )

# Create singleton instance
customer_service = CustomerService()
