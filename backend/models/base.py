"""
Base model classes for the Core Banking System.
"""

import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

# Create base class
Base = declarative_base()

class BaseModel(Base):
    """
    Abstract base model that provides common fields for all entities.
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(
        UUID(as_uuid=True), 
        default=uuid.uuid4, 
        unique=True, 
        nullable=False,
        index=True
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )
    is_active = Column(Boolean, default=True, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            result[column.name] = value
        return result
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id}, uuid={self.uuid})>"
