"""
Authentication Service for Core Banking System V3.0

This service handles all authentication and authorization operations including:
- User login and logout
- JWT token generation and validation
- Password management
- Role-based access control
- Session management
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import hashlib
import secrets
import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..models.user import User, UserRole
from ..models.base import Base
from ..database.connection import get_db_session

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Authentication and authorization service."""
    
    def __init__(self, secret_key: str = None, algorithm: str = "HS256"):
        """Initialize the authentication service."""
        self.secret_key = secret_key or secrets.token_hex(32)
        self.algorithm = algorithm
        self.token_expire_minutes = 30
        self.refresh_token_expire_days = 7
    
    def hash_password(self, password: str) -> str:
        """Hash a password for storing."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def authenticate_user(self, username: str, password: str, db: Session) -> Optional[User]:
        """Authenticate a user with username and password."""
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
    
    def login(self, username: str, password: str, db: Session) -> Dict[str, Any]:
        """Login a user and return tokens."""
        user = self.authenticate_user(username, password, db)
        if not user:
            raise ValueError("Invalid username or password")
        
        if user.is_locked:
            raise ValueError("Account is locked")
        
        if not user.is_active:
            raise ValueError("Account is not active")
        
        # Update last login
        user.last_login = datetime.utcnow().isoformat()
        user.failed_login_attempts = "0"
        db.commit()
        
        # Create tokens
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value,
            "email": user.email
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token({"sub": user.username})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.token_expire_minutes * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "is_verified": user.is_verified
            }
        }
    
    def refresh_access_token(self, refresh_token: str, db: Session) -> Dict[str, Any]:
        """Refresh an access token using a refresh token."""
        payload = self.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")
        
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        
        # Create new access token
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role.value,
            "email": user.email
        }
        
        access_token = self.create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.token_expire_minutes * 60
        }
    
    def register_user(self, username: str, email: str, password: str, full_name: str, 
                     role: UserRole = UserRole.CUSTOMER, db: Session = None) -> User:
        """Register a new user."""
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            raise ValueError("Username or email already exists")
        
        # Create new user
        hashed_password = self.hash_password(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            full_name=full_name,
            role=role
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    
    def change_password(self, user_id: int, current_password: str, new_password: str, db: Session) -> bool:
        """Change a user's password."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        if not self.verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")
        
        # Update password
        user.password_hash = self.hash_password(new_password)
        db.commit()
        
        return True
    
    def get_current_user(self, token: str, db: Session) -> Optional[User]:
        """Get current user from token."""
        payload = self.verify_token(token)
        if not payload or payload.get("type") != "access":
            return None
        
        username = payload.get("sub")
        user = db.query(User).filter(User.username == username).first()
        return user
    
    def check_permission(self, user: User, required_role: UserRole) -> bool:
        """Check if user has required role permission."""
        role_hierarchy = {
            UserRole.CUSTOMER: 1,
            UserRole.TELLER: 2,
            UserRole.MANAGER: 3,
            UserRole.ADMIN: 4,
            UserRole.AUDITOR: 2  # Special case - auditor has limited access
        }
        
        user_level = role_hierarchy.get(user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        return user_level >= required_level
    
    def logout(self, token: str) -> bool:
        """Logout a user (in a real implementation, you might blacklist the token)."""
        # In a production system, you would add the token to a blacklist
        # For now, we'll just return True
        return True
