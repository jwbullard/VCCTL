#!/usr/bin/env python3
"""
Database File Model for VCCTL

Represents stored files with binary data and metadata.
Converted from Java JPA entity to SQLAlchemy model.
"""

from typing import Optional
from sqlalchemy import Column, String, LargeBinary
from pydantic import BaseModel, Field, field_validator, model_validator

from app.database.base import Base


class DbFile(Base):
    """
    Database file model representing stored files with binary data.
    
    Contains file data, type information, and associated metadata
    for various types of files used in VCCTL simulations.
    """
    
    __tablename__ = 'db_file'
    
    # Override base model id with string primary key
    id = None
    
    # Primary key - file name (unique identifier)
    name = Column(String(64), primary_key=True, nullable=False, unique=True)
    
    # File type
    type = Column(String(23), nullable=True, doc="File type classification")
    
    # Binary data columns
    data = Column(LargeBinary, nullable=True, doc="Main file data")
    inf = Column(LargeBinary, nullable=True, doc="Information/metadata file")
    
    def __repr__(self) -> str:
        """String representation of the database file."""
        return f"<DbFile(name='{self.name}', type='{self.type}')>"
    
    @property
    def has_data(self) -> bool:
        """Check if file has main data."""
        return self.data is not None and len(self.data) > 0
    
    @property
    def has_info(self) -> bool:
        """Check if file has information data."""
        return self.inf is not None and len(self.inf) > 0
    
    @property
    def data_size(self) -> int:
        """Get size of main data in bytes."""
        return len(self.data) if self.data else 0
    
    @property
    def info_size(self) -> int:
        """Get size of info data in bytes."""
        return len(self.inf) if self.inf else 0
    
    @property
    def total_size(self) -> int:
        """Get total size of all data in bytes."""
        return self.data_size + self.info_size
    
    @property
    def is_alkali_file(self) -> bool:
        """Check if this is an alkali characteristics file."""
        return self.type == 'alkali_characteristics'
    
    @property
    def is_psd_file(self) -> bool:
        """Check if this is a particle size distribution file."""
        return self.type == 'psd'
    
    def get_data_as_text(self, encoding: str = 'utf-8') -> Optional[str]:
        """
        Get main data as text string.
        
        Args:
            encoding: Text encoding to use for decoding
            
        Returns:
            Decoded text or None if data is not text
        """
        if not self.data:
            return None
        
        try:
            return self.data.decode(encoding)
        except (UnicodeDecodeError, AttributeError):
            return None
    
    def get_info_as_text(self, encoding: str = 'utf-8') -> Optional[str]:
        """
        Get info data as text string.
        
        Args:
            encoding: Text encoding to use for decoding
            
        Returns:
            Decoded text or None if data is not text
        """
        if not self.inf:
            return None
        
        try:
            return self.inf.decode(encoding)
        except (UnicodeDecodeError, AttributeError):
            return None
    
    def set_data_from_text(self, text: str, encoding: str = 'utf-8') -> None:
        """
        Set main data from text string.
        
        Args:
            text: Text content to store
            encoding: Text encoding to use for encoding
        """
        if text:
            self.data = text.encode(encoding)
        else:
            self.data = None
    
    def set_info_from_text(self, text: str, encoding: str = 'utf-8') -> None:
        """
        Set info data from text string.
        
        Args:
            text: Text content to store
            encoding: Text encoding to use for encoding
        """
        if text:
            self.inf = text.encode(encoding)
        else:
            self.inf = None


class DbFileCreate(BaseModel):
    """Pydantic model for creating database file instances."""
    
    name: str = Field(..., max_length=64, description="File name (unique identifier)")
    type: Optional[str] = Field(None, max_length=23, description="File type")
    data_text: Optional[str] = Field(None, description="File data as text")
    info_text: Optional[str] = Field(None, description="Info data as text")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate file name."""
        if not v or not v.strip():
            raise ValueError('File name cannot be empty')
        return v.strip()
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Validate file type."""
        if v is not None:
            valid_types = ['alkali_characteristics', 'psd', 'image', 'data', 'config']
            if v not in valid_types:
                # Allow any type but warn about unknown types
                pass
        return v


class DbFileUpdate(BaseModel):
    """Pydantic model for updating database file instances."""
    
    type: Optional[str] = Field(None, max_length=23, description="File type")
    data_text: Optional[str] = Field(None, description="File data as text")
    info_text: Optional[str] = Field(None, description="Info data as text")


class DbFileResponse(BaseModel):
    """Pydantic model for database file API responses."""
    
    name: str
    type: Optional[str]
    has_data: bool
    has_info: bool
    data_size: int
    info_size: int
    total_size: int
    is_alkali_file: bool
    is_psd_file: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True