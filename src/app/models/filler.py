#!/usr/bin/env python3
"""
Filler Model for VCCTL

Represents filler materials with basic properties.
Simplified from InertFiller model for cleaner UI terminology.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, CheckConstraint, Text, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, field_validator, model_validator

from app.database.base import Base


class Filler(Base):
    """
    Filler model representing fine filler materials.
    
    Contains basic properties like specific gravity, particle size distribution,
    and descriptive information for filler materials used in concrete mixtures.
    """
    
    __tablename__ = 'filler'
    
    # Use integer ID as primary key (inherited from Base)
    # Name is now just a regular field that can be updated
    name = Column(String(64), nullable=False, unique=True)
    
    # Basic material properties
    specific_gravity = Column(Float, CheckConstraint('specific_gravity > 0 AND specific_gravity < 10'))
    specific_surface_area = Column(Float, CheckConstraint('specific_surface_area >= 0 AND specific_surface_area <= 10000'))
    
    # PSD relationship (replaces embedded PSD fields)
    psd_data_id = Column(Integer, ForeignKey('psd_data.id'), nullable=True)
    psd_data = relationship('PSDData', backref='filler_materials')
    
    # Additional material properties
    water_absorption = Column(Float, CheckConstraint('water_absorption >= 0 AND water_absorption <= 100'))
    filler_type = Column(String(64))  # quartz, glass
    
    # Descriptive properties
    description = Column(Text)
    color = Column(String(64))
    source = Column(String(255))
    notes = Column(Text)  # Additional metadata notes


class FillerCreate(BaseModel):
    """Schema for creating a new filler material."""
    name: str = Field(..., min_length=1, max_length=64, description="Name of the filler material")
    specific_gravity: Optional[float] = Field(None, gt=0, lt=10, description="Specific gravity")
    specific_surface_area: Optional[float] = Field(None, ge=0, le=10000, description="Specific surface area in m²/kg")
    water_absorption: Optional[float] = Field(None, ge=0, le=100, description="Water absorption percentage")
    filler_type: Optional[str] = Field(None, max_length=64, description="Filler type (quartz, glass)")
    
    # PSD data will be managed through separate PSD service
    # No embedded PSD fields in create schema
    
    description: Optional[str] = Field(None, description="Description of the filler material")
    color: Optional[str] = Field(None, max_length=64, description="Color of the filler")
    source: Optional[str] = Field(None, max_length=255, description="Source or manufacturer")
    notes: Optional[str] = Field(None, description="Additional metadata notes")

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class FillerUpdate(BaseModel):
    """Schema for updating an existing filler material."""
    name: Optional[str] = Field(None, min_length=1, max_length=64, description="Name of the filler material")
    specific_gravity: Optional[float] = Field(None, gt=0, lt=10, description="Specific gravity")
    specific_surface_area: Optional[float] = Field(None, ge=0, le=10000, description="Specific surface area in m²/kg")
    water_absorption: Optional[float] = Field(None, ge=0, le=100, description="Water absorption percentage")
    filler_type: Optional[str] = Field(None, max_length=64, description="Filler type (quartz, glass)")
    
    # PSD data managed through separate PSD service
    # No embedded PSD fields in update schema
    
    description: Optional[str] = Field(None, description="Description of the filler material")
    color: Optional[str] = Field(None, max_length=64, description="Color of the filler")
    source: Optional[str] = Field(None, max_length=255, description="Source or manufacturer")
    notes: Optional[str] = Field(None, description="Additional metadata notes")


class FillerResponse(BaseModel):
    """Schema for filler material responses."""
    name: str = Field(..., description="Name of the filler material")
    specific_gravity: Optional[float] = Field(None, description="Specific gravity")
    specific_surface_area: Optional[float] = Field(None, description="Specific surface area in m²/kg")
    water_absorption: Optional[float] = Field(None, description="Water absorption percentage")
    filler_type: Optional[str] = Field(None, description="Filler type (quartz, glass)")
    
    # PSD data accessed through relationship
    psd_data_id: Optional[int] = Field(None, description="PSD data ID")
    
    description: Optional[str] = Field(None, description="Description of the filler material")
    color: Optional[str] = Field(None, description="Color of the filler")
    source: Optional[str] = Field(None, description="Source or manufacturer")
    notes: Optional[str] = Field(None, description="Additional metadata notes")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True