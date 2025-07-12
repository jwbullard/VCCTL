#!/usr/bin/env python3
"""
Particle Shape Set Model for VCCTL

Represents particle shape definitions for materials.
Converted from Java JPA entity to SQLAlchemy model.
"""

from typing import Optional, List
from sqlalchemy import Column, String
from pydantic import BaseModel, Field, validator

from app.database.base import Base


class ParticleShapeSet(Base):
    """
    Particle shape set model representing shape definitions for materials.
    
    Simple model containing shape set names for referencing
    particle shape characteristics in simulations.
    """
    
    __tablename__ = 'particle_shape_set'
    
    # Override base model id with string primary key
    id = None
    
    # Primary key - shape set name (unique identifier)
    name = Column(String(64), primary_key=True, nullable=False, unique=True)
    
    def __repr__(self) -> str:
        """String representation of the particle shape set."""
        return f"<ParticleShapeSet(name='{self.name}')>"
    
    @property
    def is_standard_shape_set(self) -> bool:
        """Check if this is a standard/predefined shape set."""
        standard_sets = [
            'sphere', 'ellipsoid', 'cube', 'irregular',
            'angular', 'rounded', 'elongated', 'flaky'
        ]
        return self.name.lower() in standard_sets
    
    @classmethod
    def get_standard_shape_sets(cls) -> List[str]:
        """Get list of standard shape set names."""
        return [
            'sphere', 'ellipsoid', 'cube', 'irregular',
            'angular', 'rounded', 'elongated', 'flaky'
        ]


class ParticleShapeSetCreate(BaseModel):
    """Pydantic model for creating particle shape set instances."""
    
    name: str = Field(..., max_length=64, description="Particle shape set name (unique)")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate particle shape set name."""
        if not v or not v.strip():
            raise ValueError('Particle shape set name cannot be empty')
        
        # Clean the name
        cleaned_name = v.strip().lower()
        
        # Check for valid characters (alphanumeric, underscore, hyphen)
        if not all(c.isalnum() or c in ['_', '-'] for c in cleaned_name):
            raise ValueError('Shape set name can only contain letters, numbers, underscore, and hyphen')
        
        return cleaned_name


class ParticleShapeSetUpdate(BaseModel):
    """Pydantic model for updating particle shape set instances."""
    
    # No fields to update - name is the primary key and shouldn't change
    pass


class ParticleShapeSetResponse(BaseModel):
    """Pydantic model for particle shape set API responses."""
    
    name: str
    is_standard_shape_set: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True