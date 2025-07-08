"""
Authentication and Authorization Framework
Shared authentication utilities for all services
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from fastapi import HTTPException, status
from passlib.context import CryptContext
from passlib.hash import argon2


class TokenData(BaseModel):
    """Token data model"""
    user_id: str
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    exp: datetime
    iat: datetime


class AuthConfig(BaseModel):
    """Authentication configuration"""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7


class AuthenticationService:
    """Authentication service for handling JWT tokens and password hashing"""
    
    def __init__(self, config: AuthConfig):
        self.config = config
        self.pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes)
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.config.secret_key, 
            algorithm=self.config.algorithm
        )
        return encoded_jwt
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=self.config.refresh_token_expire_days)
        to_encode = {
            "user_id": user_id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.config.secret_key,
            algorithm=self.config.algorithm
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.config.secret_key,
                algorithms=[self.config.algorithm]
            )
            
            # Check if token is expired
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            return TokenData(
                user_id=payload.get("user_id"),
                username=payload.get("username"),
                email=payload.get("email"),
                roles=payload.get("roles", []),
                permissions=payload.get("permissions", []),
                exp=datetime.fromtimestamp(payload.get("exp")),
                iat=datetime.fromtimestamp(payload.get("iat"))
            )
            
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    def hash_password(self, password: str) -> str:
        """Hash password using Argon2"""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return self.pwd_context.verify(plain_password, hashed_password)


class Permission:
    """Permission constants"""
    # Customer permissions
    CUSTOMER_READ = "customer:read"
    CUSTOMER_WRITE = "customer:write"
    CUSTOMER_DELETE = "customer:delete"
    
    # Account permissions
    ACCOUNT_READ = "account:read"
    ACCOUNT_WRITE = "account:write"
    ACCOUNT_DELETE = "account:delete"
    ACCOUNT_TRANSFER = "account:transfer"
    
    # Transaction permissions
    TRANSACTION_READ = "transaction:read"
    TRANSACTION_WRITE = "transaction:write"
    TRANSACTION_APPROVE = "transaction:approve"
    
    # Loan permissions
    LOAN_READ = "loan:read"
    LOAN_WRITE = "loan:write"
    LOAN_APPROVE = "loan:approve"
    LOAN_DISBURSE = "loan:disburse"
    
    # Payment permissions
    PAYMENT_READ = "payment:read"
    PAYMENT_WRITE = "payment:write"
    PAYMENT_APPROVE = "payment:approve"
    
    # Admin permissions
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"
    ADMIN_SYSTEM = "admin:system"
    
    # Audit permissions
    AUDIT_READ = "audit:read"
    AUDIT_WRITE = "audit:write"


class Role:
    """Role definitions with permissions"""
    
    CUSTOMER = {
        "name": "customer",
        "permissions": [
            Permission.ACCOUNT_READ,
            Permission.TRANSACTION_READ,
            Permission.ACCOUNT_TRANSFER,
            Permission.PAYMENT_READ,
            Permission.PAYMENT_WRITE,
        ]
    }
    
    TELLER = {
        "name": "teller",
        "permissions": [
            Permission.CUSTOMER_READ,
            Permission.CUSTOMER_WRITE,
            Permission.ACCOUNT_READ,
            Permission.ACCOUNT_WRITE,
            Permission.TRANSACTION_READ,
            Permission.TRANSACTION_WRITE,
            Permission.PAYMENT_READ,
            Permission.PAYMENT_WRITE,
        ]
    }
    
    MANAGER = {
        "name": "manager",
        "permissions": [
            Permission.CUSTOMER_READ,
            Permission.CUSTOMER_WRITE,
            Permission.ACCOUNT_READ,
            Permission.ACCOUNT_WRITE,
            Permission.ACCOUNT_DELETE,
            Permission.TRANSACTION_READ,
            Permission.TRANSACTION_WRITE,
            Permission.TRANSACTION_APPROVE,
            Permission.LOAN_READ,
            Permission.LOAN_WRITE,
            Permission.LOAN_APPROVE,
            Permission.PAYMENT_READ,
            Permission.PAYMENT_WRITE,
            Permission.PAYMENT_APPROVE,
            Permission.AUDIT_READ,
        ]
    }
    
    ADMIN = {
        "name": "admin",
        "permissions": [
            Permission.CUSTOMER_READ,
            Permission.CUSTOMER_WRITE,
            Permission.CUSTOMER_DELETE,
            Permission.ACCOUNT_READ,
            Permission.ACCOUNT_WRITE,
            Permission.ACCOUNT_DELETE,
            Permission.TRANSACTION_READ,
            Permission.TRANSACTION_WRITE,
            Permission.TRANSACTION_APPROVE,
            Permission.LOAN_READ,
            Permission.LOAN_WRITE,
            Permission.LOAN_APPROVE,
            Permission.LOAN_DISBURSE,
            Permission.PAYMENT_READ,
            Permission.PAYMENT_WRITE,
            Permission.PAYMENT_APPROVE,
            Permission.ADMIN_READ,
            Permission.ADMIN_WRITE,
            Permission.ADMIN_SYSTEM,
            Permission.AUDIT_READ,
            Permission.AUDIT_WRITE,
        ]
    }


class AuthorizationService:
    """Authorization service for checking permissions"""
    
    @staticmethod
    def has_permission(user_permissions: List[str], required_permission: str) -> bool:
        """Check if user has required permission"""
        return required_permission in user_permissions
    
    @staticmethod
    def has_any_permission(user_permissions: List[str], required_permissions: List[str]) -> bool:
        """Check if user has any of the required permissions"""
        return any(permission in user_permissions for permission in required_permissions)
    
    @staticmethod
    def has_all_permissions(user_permissions: List[str], required_permissions: List[str]) -> bool:
        """Check if user has all required permissions"""
        return all(permission in user_permissions for permission in required_permissions)
    
    @staticmethod
    def check_permission(user_permissions: List[str], required_permission: str):
        """Check permission and raise exception if not authorized"""
        if not AuthorizationService.has_permission(user_permissions, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permission}"
            )


def get_permissions_for_roles(role_names: List[str]) -> List[str]:
    """Get all permissions for given roles"""
    all_permissions = set()
    
    role_map = {
        "customer": Role.CUSTOMER,
        "teller": Role.TELLER,
        "manager": Role.MANAGER,
        "admin": Role.ADMIN,
    }
    
    for role_name in role_names:
        role = role_map.get(role_name)
        if role:
            all_permissions.update(role["permissions"])
    
    return list(all_permissions)
