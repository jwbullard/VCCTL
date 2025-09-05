#!/usr/bin/env python3
"""
Filler Model for VCCTL

Represents filler materials with basic properties.
Simplified from InertFiller model for cleaner UI terminology.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import Column, String, Float, CheckConstraint, Text
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
    blaine_fineness = Column(Float, CheckConstraint('blaine_fineness >= 0 AND blaine_fineness <= 10000'))
    
    # Particle size distribution
    diameter_percentile_10 = Column(Float, CheckConstraint('diameter_percentile_10 >= 0 AND diameter_percentile_10 <= 1000'))
    diameter_percentile_50 = Column(Float, CheckConstraint('diameter_percentile_50 >= 0 AND diameter_percentile_50 <= 1000'))
    diameter_percentile_90 = Column(Float, CheckConstraint('diameter_percentile_90 >= 0 AND diameter_percentile_90 <= 1000'))
    
    # Additional material properties
    water_absorption = Column(Float, CheckConstraint('water_absorption >= 0 AND water_absorption <= 100'))
    filler_type = Column(String(64))  # limestone, quartz, glass, other
    
    # Descriptive properties
    description = Column(Text)
    color = Column(String(64))
    source = Column(String(255))
    notes = Column(Text)  # Additional metadata notes


class FillerCreate(BaseModel):
    """Schema for creating a new filler material."""
    name: str = Field(..., min_length=1, max_length=64, description="Name of the filler material")
    specific_gravity: Optional[float] = Field(None, gt=0, lt=10, description="Specific gravity")
    blaine_fineness: Optional[float] = Field(None, ge=0, le=10000, description="Blaine fineness in cm2/g")
    diameter_percentile_10: Optional[float] = Field(None, ge=0, le=1000, description="10th percentile diameter in μm")
    diameter_percentile_50: Optional[float] = Field(None, ge=0, le=1000, description="50th percentile diameter in μm")
    diameter_percentile_90: Optional[float] = Field(None, ge=0, le=1000, description="90th percentile diameter in μm")
    water_absorption: Optional[float] = Field(None, ge=0, le=100, description="Water absorption percentage")
    filler_type: Optional[str] = Field(None, max_length=64, description="Filler type (limestone, quartz, glass, other)")
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
    blaine_fineness: Optional[float] = Field(None, ge=0, le=10000, description="Blaine fineness in cm2/g")
    diameter_percentile_10: Optional[float] = Field(None, ge=0, le=1000, description="10th percentile diameter in μm")
    diameter_percentile_50: Optional[float] = Field(None, ge=0, le=1000, description="50th percentile diameter in μm")
    diameter_percentile_90: Optional[float] = Field(None, ge=0, le=1000, description="90th percentile diameter in μm")
    water_absorption: Optional[float] = Field(None, ge=0, le=100, description="Water absorption percentage")
    filler_type: Optional[str] = Field(None, max_length=64, description="Filler type (limestone, quartz, glass, other)")
    description: Optional[str] = Field(None, description="Description of the filler material")
    color: Optional[str] = Field(None, max_length=64, description="Color of the filler")
    source: Optional[str] = Field(None, max_length=255, description="Source or manufacturer")
    notes: Optional[str] = Field(None, description="Additional metadata notes")


class FillerResponse(BaseModel):
    """Schema for filler material responses."""
    name: str = Field(..., description="Name of the filler material")
    specific_gravity: Optional[float] = Field(None, description="Specific gravity")
    blaine_fineness: Optional[float] = Field(None, description="Blaine fineness in cm2/g")
    diameter_percentile_10: Optional[float] = Field(None, description="10th percentile diameter in μm")
    diameter_percentile_50: Optional[float] = Field(None, description="50th percentile diameter in μm")
    diameter_percentile_90: Optional[float] = Field(None, description="90th percentile diameter in μm")
    water_absorption: Optional[float] = Field(None, description="Water absorption percentage")
    filler_type: Optional[str] = Field(None, description="Filler type (limestone, quartz, glass, other)")
    description: Optional[str] = Field(None, description="Description of the filler material")
    color: Optional[str] = Field(None, description="Color of the filler")
    source: Optional[str] = Field(None, description="Source or manufacturer")
    notes: Optional[str] = Field(None, description="Additional metadata notes")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True