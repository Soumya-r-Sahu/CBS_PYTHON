"""
Database Base Classes for Core Banking System V3.0

This module provides base classes and utilities for database models.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID

# Create base class
Base = declarative_base()

class BaseModel(Base):
    """
    Abstract base model that provides common fields for all entities.
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, uuid={self.uuid})>"
