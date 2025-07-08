"""
Customer Service for Core Banking System V3.0

This service handles customer management, registration, and profile operations.
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
from datetime import datetime, date
import random
import string

from ..shared.database import get_db_session
from ..shared.models import Customer, Account, Gender, CustomerStatus, AccountType
from ..auth_service.main import get_current_user, User

app = FastAPI(
    title="Customer Service",
    description="Core Banking Customer Management Service",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class CustomerCreateRequest(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    date_of_birth: date
    gender: Gender
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    pan_number: Optional[str] = Field(None, min_length=10, max_length=10)
    aadhar_number: Optional[str] = Field(None, min_length=12, max_length=12)
    address_line1: str = Field(..., min_length=10, max_length=100)
    address_line2: Optional[str] = Field(None, max_length=100)
    city: str = Field(..., min_length=2, max_length=50)
    state: str = Field(..., min_length=2, max_length=50)
    postal_code: str = Field(..., min_length=5, max_length=10)
    country: str = Field(default="India", max_length=50)

class CustomerUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    address_line1: Optional[str] = Field(None, min_length=10, max_length=100)
    address_line2: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, min_length=2, max_length=50)
    state: Optional[str] = Field(None, min_length=2, max_length=50)
    postal_code: Optional[str] = Field(None, min_length=5, max_length=10)
    country: Optional[str] = Field(None, max_length=50)

class CustomerResponse(BaseModel):
    id: int
    customer_id: str
    first_name: str
    last_name: str
    full_name: str
    date_of_birth: date
    age: int
    gender: str
    email: str
    phone: str
    pan_number: Optional[str] = None
    aadhar_number: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    status: str
    created_at: datetime
    updated_at: datetime

class CustomerSummaryResponse(BaseModel):
    id: int
    customer_id: str
    full_name: str
    email: str
    phone: str
    status: str
    account_count: int
    created_at: datetime

class CustomerSearchResponse(BaseModel):
    customers: List[CustomerSummaryResponse]
    total: int
    page: int
    per_page: int
    pages: int

# Utility Functions
def generate_customer_id() -> str:
    """Generate unique customer ID"""
    prefix = "CUS"
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = ''.join(random.choices(string.digits, k=5))
    return f"{prefix}-{date_part}-{random_part}"

def validate_pan_number(pan: str) -> bool:
    """Validate PAN number format"""
    if not pan or len(pan) != 10:
        return False
    
    # PAN format: 5 letters, 4 numbers, 1 letter
    return (pan[:5].isalpha() and 
            pan[5:9].isdigit() and 
            pan[9].isalpha())

def validate_aadhar_number(aadhar: str) -> bool:
    """Validate Aadhar number format"""
    if not aadhar or len(aadhar) != 12:
        return False
    return aadhar.isdigit()

def calculate_age(birth_date: date) -> int:
    """Calculate age from birth date"""
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

# Customer Endpoints
@app.post("/customers", response_model=CustomerResponse)
async def create_customer(
    request: CustomerCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Create new customer"""
    # Check if user has permission to create customers
    if not current_user.is_employee():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only bank employees can create customers"
        )
    
    # Validate PAN number if provided
    if request.pan_number and not validate_pan_number(request.pan_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PAN number format"
        )
    
    # Validate Aadhar number if provided
    if request.aadhar_number and not validate_aadhar_number(request.aadhar_number):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Aadhar number format"
        )
    
    # Check for duplicate email
    if db.query(Customer).filter(Customer.email == request.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    
    # Check for duplicate PAN
    if request.pan_number and db.query(Customer).filter(Customer.pan_number == request.pan_number).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PAN number already exists"
        )
    
    # Check for duplicate Aadhar
    if request.aadhar_number and db.query(Customer).filter(Customer.aadhar_number == request.aadhar_number).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aadhar number already exists"
        )
    
    # Validate age (minimum 18 years)
    age = calculate_age(request.date_of_birth)
    if age < 18:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer must be at least 18 years old"
        )
    
    # Generate unique customer ID
    customer_id = generate_customer_id()
    while db.query(Customer).filter(Customer.customer_id == customer_id).first():
        customer_id = generate_customer_id()
    
    # Create customer
    customer = Customer(
        customer_id=customer_id,
        first_name=request.first_name,
        last_name=request.last_name,
        date_of_birth=request.date_of_birth,
        gender=request.gender,
        email=request.email,
        phone=request.phone,
        pan_number=request.pan_number,
        aadhar_number=request.aadhar_number,
        address_line1=request.address_line1,
        address_line2=request.address_line2,
        city=request.city,
        state=request.state,
        postal_code=request.postal_code,
        country=request.country,
        status=CustomerStatus.ACTIVE
    )
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return CustomerResponse(
        id=customer.id,
        customer_id=customer.customer_id,
        first_name=customer.first_name,
        last_name=customer.last_name,
        full_name=customer.get_full_name(),
        date_of_birth=customer.date_of_birth,
        age=customer.get_age(),
        gender=customer.gender.value,
        email=customer.email,
        phone=customer.phone,
        pan_number=customer.pan_number,
        aadhar_number=customer.aadhar_number,
        address_line1=customer.address_line1,
        address_line2=customer.address_line2,
        city=customer.city,
        state=customer.state,
        postal_code=customer.postal_code,
        country=customer.country,
        status=customer.status.value,
        created_at=customer.created_at,
        updated_at=customer.updated_at
    )

@app.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get customer by ID"""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return CustomerResponse(
        id=customer.id,
        customer_id=customer.customer_id,
        first_name=customer.first_name,
        last_name=customer.last_name,
        full_name=customer.get_full_name(),
        date_of_birth=customer.date_of_birth,
        age=customer.get_age(),
        gender=customer.gender.value,
        email=customer.email,
        phone=customer.phone,
        pan_number=customer.pan_number,
        aadhar_number=customer.aadhar_number,
        address_line1=customer.address_line1,
        address_line2=customer.address_line2,
        city=customer.city,
        state=customer.state,
        postal_code=customer.postal_code,
        country=customer.country,
        status=customer.status.value,
        created_at=customer.created_at,
        updated_at=customer.updated_at
    )

@app.put("/customers/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    request: CustomerUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Update customer information"""
    # Check permissions
    if not current_user.is_employee():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only bank employees can update customer information"
        )
    
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Update fields if provided
    update_data = request.dict(exclude_unset=True)
    
    # Check for email uniqueness if being updated
    if 'email' in update_data and update_data['email'] != customer.email:
        if db.query(Customer).filter(Customer.email == update_data['email']).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
    
    # Apply updates
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    customer.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(customer)
    
    return CustomerResponse(
        id=customer.id,
        customer_id=customer.customer_id,
        first_name=customer.first_name,
        last_name=customer.last_name,
        full_name=customer.get_full_name(),
        date_of_birth=customer.date_of_birth,
        age=customer.get_age(),
        gender=customer.gender.value,
        email=customer.email,
        phone=customer.phone,
        pan_number=customer.pan_number,
        aadhar_number=customer.aadhar_number,
        address_line1=customer.address_line1,
        address_line2=customer.address_line2,
        city=customer.city,
        state=customer.state,
        postal_code=customer.postal_code,
        country=customer.country,
        status=customer.status.value,
        created_at=customer.created_at,
        updated_at=customer.updated_at
    )

@app.get("/customers", response_model=CustomerSearchResponse)
async def search_customers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
    query: Optional[str] = Query(None),
    status: Optional[CustomerStatus] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Search customers with pagination"""
    # Build base query
    base_query = db.query(Customer)
    
    # Apply filters
    if query:
        search_filter = or_(
            Customer.first_name.ilike(f"%{query}%"),
            Customer.last_name.ilike(f"%{query}%"),
            Customer.email.ilike(f"%{query}%"),
            Customer.phone.ilike(f"%{query}%"),
            Customer.customer_id.ilike(f"%{query}%")
        )
        base_query = base_query.filter(search_filter)
    
    if status:
        base_query = base_query.filter(Customer.status == status)
    
    # Get total count
    total = base_query.count()
    
    # Apply pagination
    offset = (page - 1) * per_page
    customers = base_query.offset(offset).limit(per_page).all()
    
    # Get account counts for each customer
    customer_summaries = []
    for customer in customers:
        account_count = db.query(Account).filter(Account.customer_id == customer.id).count()
        customer_summaries.append(CustomerSummaryResponse(
            id=customer.id,
            customer_id=customer.customer_id,
            full_name=customer.get_full_name(),
            email=customer.email,
            phone=customer.phone,
            status=customer.status.value,
            account_count=account_count,
            created_at=customer.created_at
        ))
    
    pages = (total + per_page - 1) // per_page
    
    return CustomerSearchResponse(
        customers=customer_summaries,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages
    )

@app.get("/customers/{customer_id}/accounts")
async def get_customer_accounts(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Get all accounts for a customer"""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    accounts = db.query(Account).filter(Account.customer_id == customer.id).all()
    
    return [
        {
            "account_number": acc.account_number,
            "account_type": acc.account_type.value,
            "balance": acc.balance,
            "currency": acc.currency,
            "status": acc.status.value,
            "created_at": acc.created_at
        }
        for acc in accounts
    ]

@app.patch("/customers/{customer_id}/status")
async def update_customer_status(
    customer_id: str,
    new_status: CustomerStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Update customer status"""
    # Check permissions
    if not current_user.can_access_admin_panel():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers and admins can update customer status"
        )
    
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    customer.status = new_status
    customer.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": f"Customer status updated to {new_status.value}"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "customer-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
