"""
Authentication Service for Core Banking System V3.0

This service handles user authentication, JWT tokens, and authorization.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import jwt
import os

from ..shared.database import get_db_session
from ..shared.models import User, UserRole, UserStatus

app = FastAPI(
    title="Authentication Service",
    description="Core Banking Authentication and Authorization Service",
    version="3.0.0"
)

# Security
security = HTTPBearer()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Pydantic Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    username: str
    role: str

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class UserCreateRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: UserRole
    employee_id: Optional[str] = None
    phone: Optional[str] = None
    branch_code: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    status: str
    created_at: datetime

# JWT Token Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db_session)
):
    """Get current authenticated user"""
    try:
        payload = verify_token(credentials.credentials)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user information"
            )
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not active"
            )
        
        return user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

# Authentication Endpoints
@app.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db_session)):
    """User login endpoint"""
    # Find user by username
    user = db.query(User).filter(User.username == request.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Check if account is locked
    if user.is_account_locked():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is locked due to multiple failed login attempts"
        )
    
    # Verify password
    if not user.check_password(request.password):
        # Increment failed login attempts
        user.failed_login_attempts += 1
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Check user status
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not active"
        )
    
    # Reset failed login attempts and update last login
    user.failed_login_attempts = 0
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create tokens
    token_data = {"sub": str(user.id), "username": user.username, "role": user.role.value}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user_id=user.id,
        username=user.username,
        role=user.role.value
    )

@app.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: TokenRefreshRequest, db: Session = Depends(get_db_session)):
    """Refresh access token"""
    try:
        payload = verify_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = payload.get("sub")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new tokens
        token_data = {"sub": str(user.id), "username": user.username, "role": user.role.value}
        access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            username=user.username,
            role=user.role.value
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not refresh token"
        )

@app.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """User logout endpoint"""
    # In a production system, you might want to blacklist the token
    return {"message": "Successfully logged out"}

@app.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role.value,
        status=current_user.status.value,
        created_at=current_user.created_at
    )

@app.post("/users", response_model=UserResponse)
async def create_user(
    request: UserCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """Create new user (Admin only)"""
    # Check if current user is admin
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create users"
        )
    
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == request.username) | (User.email == request.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists"
        )
    
    # Create new user
    new_user = User(
        username=request.username,
        email=request.email,
        first_name=request.first_name,
        last_name=request.last_name,
        role=request.role,
        employee_id=request.employee_id,
        phone=request.phone,
        branch_code=request.branch_code,
        created_by=current_user.username
    )
    
    new_user.set_password(request.password)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        role=new_user.role.value,
        status=new_user.status.value,
        created_at=new_user.created_at
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "auth-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
