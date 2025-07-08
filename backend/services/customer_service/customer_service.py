"""
Customer Service for Core Banking System V3.0

This service handles all customer management operations including:
- Customer registration and profile management
- Customer data validation
- Customer search and listing
- Customer status management
- KYC (Know Your Customer) operations
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.customer import Customer
from ..models.user import User, UserRole
from ..database.connection import get_db_session

class CustomerService:
    """Customer management service."""
    
    def __init__(self):
        """Initialize the customer service."""
        pass
    
    def create_customer(self, customer_data: Dict[str, Any], user_id: int, db: Session) -> Customer:
        """Create a new customer."""
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'date_of_birth', 'email', 'phone', 'address_line1', 'city', 'state', 'postal_code']
        for field in required_fields:
            if field not in customer_data or not customer_data[field]:
                raise ValueError(f"Field '{field}' is required")
        
        # Check if customer already exists
        existing_customer = db.query(Customer).filter(
            or_(
                Customer.email == customer_data['email'],
                Customer.pan_number == customer_data.get('pan_number'),
                Customer.aadhar_number == customer_data.get('aadhar_number')
            )
        ).first()
        
        if existing_customer:
            raise ValueError("Customer already exists with this email, PAN, or Aadhar number")
        
        # Generate customer ID
        customer_id = self._generate_customer_id(db)
        
        # Create customer
        customer = Customer(
            customer_id=customer_id,
            first_name=customer_data['first_name'],
            last_name=customer_data['last_name'],
            date_of_birth=datetime.strptime(customer_data['date_of_birth'], '%Y-%m-%d').date(),
            gender=customer_data.get('gender'),
            pan_number=customer_data.get('pan_number'),
            aadhar_number=customer_data.get('aadhar_number'),
            email=customer_data['email'],
            phone=customer_data['phone'],
            address_line1=customer_data['address_line1'],
            address_line2=customer_data.get('address_line2'),
            city=customer_data['city'],
            state=customer_data['state'],
            postal_code=customer_data['postal_code'],
            country=customer_data.get('country', 'India'),
            user_id=user_id
        )
        
        db.add(customer)
        db.commit()
        db.refresh(customer)
        
        return customer
    
    def get_customer(self, customer_id: str, db: Session) -> Optional[Customer]:
        """Get a customer by customer ID."""
        return db.query(Customer).filter(Customer.customer_id == customer_id).first()
    
    def get_customer_by_id(self, id: int, db: Session) -> Optional[Customer]:
        """Get a customer by internal ID."""
        return db.query(Customer).filter(Customer.id == id).first()
    
    def get_customer_by_user_id(self, user_id: int, db: Session) -> Optional[Customer]:
        """Get a customer by user ID."""
        return db.query(Customer).filter(Customer.user_id == user_id).first()
    
    def update_customer(self, customer_id: str, update_data: Dict[str, Any], db: Session) -> Customer:
        """Update customer information."""
        customer = self.get_customer(customer_id, db)
        if not customer:
            raise ValueError("Customer not found")
        
        # Update allowed fields
        allowed_fields = [
            'first_name', 'last_name', 'gender', 'email', 'phone',
            'address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country'
        ]
        
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(customer, field):
                setattr(customer, field, value)
        
        db.commit()
        db.refresh(customer)
        
        return customer
    
    def search_customers(self, search_query: str, limit: int = 50, offset: int = 0, db: Session = None) -> List[Customer]:
        """Search customers by name, email, or customer ID."""
        query = db.query(Customer).filter(Customer.is_active == True)
        
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                or_(
                    Customer.first_name.ilike(search_pattern),
                    Customer.last_name.ilike(search_pattern),
                    Customer.email.ilike(search_pattern),
                    Customer.customer_id.ilike(search_pattern),
                    Customer.phone.ilike(search_pattern)
                )
            )
        
        return query.offset(offset).limit(limit).all()
    
    def get_all_customers(self, limit: int = 50, offset: int = 0, db: Session = None) -> List[Customer]:
        """Get all active customers with pagination."""
        return db.query(Customer).filter(Customer.is_active == True).offset(offset).limit(limit).all()
    
    def deactivate_customer(self, customer_id: str, db: Session) -> bool:
        """Deactivate a customer (soft delete)."""
        customer = self.get_customer(customer_id, db)
        if not customer:
            raise ValueError("Customer not found")
        
        customer.is_active = False
        db.commit()
        
        return True
    
    def activate_customer(self, customer_id: str, db: Session) -> bool:
        """Activate a customer."""
        customer = self.get_customer(customer_id, db)
        if not customer:
            raise ValueError("Customer not found")
        
        customer.is_active = True
        db.commit()
        
        return True
    
    def validate_kyc_documents(self, customer_id: str, pan_number: str = None, aadhar_number: str = None, db: Session = None) -> bool:
        """Validate KYC documents for a customer."""
        customer = self.get_customer(customer_id, db)
        if not customer:
            raise ValueError("Customer not found")
        
        # Update KYC information
        if pan_number:
            # Validate PAN format (basic validation)
            if not self._validate_pan_format(pan_number):
                raise ValueError("Invalid PAN format")
            customer.pan_number = pan_number
        
        if aadhar_number:
            # Validate Aadhar format (basic validation)
            if not self._validate_aadhar_format(aadhar_number):
                raise ValueError("Invalid Aadhar format")
            customer.aadhar_number = aadhar_number
        
        db.commit()
        return True
    
    def get_customer_statistics(self, db: Session) -> Dict[str, Any]:
        """Get customer statistics."""
        total_customers = db.query(Customer).filter(Customer.is_active == True).count()
        total_inactive = db.query(Customer).filter(Customer.is_active == False).count()
        
        # Customers registered today
        today = datetime.utcnow().date()
        customers_today = db.query(Customer).filter(
            Customer.created_at >= today,
            Customer.is_active == True
        ).count()
        
        # Customers by state (top 10)
        state_stats = db.query(
            Customer.state,
            db.func.count(Customer.id).label('count')
        ).filter(Customer.is_active == True).group_by(Customer.state).order_by(
            db.func.count(Customer.id).desc()
        ).limit(10).all()
        
        return {
            "total_active_customers": total_customers,
            "total_inactive_customers": total_inactive,
            "customers_registered_today": customers_today,
            "customers_by_state": [{"state": state, "count": count} for state, count in state_stats]
        }
    
    def _generate_customer_id(self, db: Session) -> str:
        """Generate a unique customer ID."""
        today = datetime.now()
        prefix = f"CUS{today.strftime('%Y%m%d')}"
        
        # Find the last customer ID for today
        last_customer = db.query(Customer).filter(
            Customer.customer_id.startswith(prefix)
        ).order_by(Customer.customer_id.desc()).first()
        
        if last_customer:
            # Extract the sequence number and increment
            last_seq = int(last_customer.customer_id[-4:])
            new_seq = last_seq + 1
        else:
            new_seq = 1
        
        return f"{prefix}{new_seq:04d}"
    
    def _validate_pan_format(self, pan: str) -> bool:
        """Validate PAN number format (basic validation)."""
        import re
        pan_pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        return bool(re.match(pan_pattern, pan))
    
    def _validate_aadhar_format(self, aadhar: str) -> bool:
        """Validate Aadhar number format (basic validation)."""
        import re
        aadhar_pattern = r'^[0-9]{12}$'
        return bool(re.match(aadhar_pattern, aadhar))
