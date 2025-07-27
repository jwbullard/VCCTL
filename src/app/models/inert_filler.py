#!/usr/bin/env python3
"""
Inert Filler Model for VCCTL

Represents inert filler materials with basic properties.
Converted from Java JPA entity to SQLAlchemy model.
"""

from typing import Optional
from sqlalchemy import Column, String, Float, CheckConstraint, Text
from pydantic import BaseModel, Field, field_validator, model_validator

from app.database.base import Base


class InertFiller(Base):
    """
    Inert filler model representing non-reactive fine materials.
    
    Contains basic properties like specific gravity, particle size distribution,
    and descriptive information for inert fillers used in concrete mixtures.
    """
    
    __tablename__ = 'inert_filler'
    
    # Override base model id with string primary key
    id = None
    
    # Primary key - filler name (unique identifier)
    name = Column(String(64), primary_key=True, nullable=False)
    
    # Physical properties
    specific_gravity = Column(Float, nullable=False, default=3.0,
                            doc="Specific gravity of inert filler")
    
    # Particle size distribution reference
    psd = Column(String(64), nullable=False, default='cement141',
                doc="Particle size distribution reference")
    
    # Custom PSD data points (JSON format)
    psd_custom_points = Column(Text, nullable=True, 
                              doc="Custom PSD points stored as JSON")
    
    # Description and metadata
    description = Column(String(32700), nullable=True,
                        doc="Inert filler description and notes")
    source = Column(String(255), nullable=True, doc="Material source")
    notes = Column(String(1000), nullable=True, doc="Additional notes")
    
    # Add constraint for specific gravity
    __table_args__ = (
        CheckConstraint('specific_gravity >= 0.0', name='check_inert_filler_specific_gravity_positive'),
    )
    
    def __repr__(self) -> str:
        """String representation of the inert filler."""
        return f"<InertFiller(name='{self.name}', specific_gravity={self.specific_gravity})>"
    
    @property
    def is_valid_specific_gravity(self) -> bool:
        """Check if specific gravity is in a reasonable range for fillers."""
        if self.specific_gravity is None:
            return False
        # Typical range for mineral fillers: 2.0 - 5.0
        return 2.0 <= self.specific_gravity <= 5.0
    
    @property
    def has_description(self) -> bool:
        """Check if filler has description."""
        return self.description is not None and len(self.description.strip()) > 0
    
    def get_volume_per_unit_mass(self) -> Optional[float]:
        """Calculate volume per unit mass based on specific gravity."""
        if self.specific_gravity and self.specific_gravity > 0:
            # Volume per unit mass = 1 / (specific_gravity * density_of_water)
            # Assuming water density = 1000 kg/m³
            return 1.0 / (self.specific_gravity * 1000.0)
        return None


class InertFillerCreate(BaseModel):
    """Pydantic model for creating inert filler instances."""
    
    name: str = Field(..., max_length=64, description="Inert filler name (unique identifier)")
    specific_gravity: float = Field(3.0, gt=0.0, le=10.0, 
                                   description="Specific gravity (must be positive)")
    psd: str = Field('cement141', max_length=64,
                    description="Particle size distribution reference")
    psd_custom_points: Optional[str] = Field(None, 
                                           description="Custom PSD points stored as JSON")
    description: Optional[str] = Field(None, max_length=32700,
                                     description="Filler description and notes")
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate inert filler name."""
        if not v or not v.strip():
            raise ValueError('Inert filler name cannot be empty')
        return v.strip()
    
    @field_validator('specific_gravity')
    @classmethod
    def validate_specific_gravity(cls, v):
        """Validate specific gravity is reasonable for fillers."""
        if v <= 0:
            raise ValueError('Specific gravity must be positive')
        if v < 1.0 or v > 10.0:
            raise ValueError('Specific gravity should be between 1.0 and 10.0 for mineral fillers')
        return v
    
    @field_validator('psd')
    @classmethod
    def validate_psd(cls, v):
        """Validate PSD reference."""
        if not v or not v.strip():
            raise ValueError('PSD reference cannot be empty')
        return v.strip()


class InertFillerUpdate(BaseModel):
    """Pydantic model for updating inert filler instances."""
    
    specific_gravity: Optional[float] = Field(None, gt=0.0, le=10.0,
                                            description="Specific gravity")
    psd: Optional[str] = Field(None, max_length=64,
                              description="Particle size distribution reference")
    psd_custom_points: Optional[str] = Field(None, 
                                           description="Custom PSD points stored as JSON")
    description: Optional[str] = Field(None, max_length=32700,
                                     description="Filler description and notes")
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    @field_validator('specific_gravity')
    @classmethod
    def validate_specific_gravity(cls, v):
        """Validate specific gravity."""
        if v is not None and (v <= 0 or v > 10.0):
            raise ValueError('Specific gravity must be positive and reasonable for fillers')
        return v


class InertFillerResponse(BaseModel):
    """Pydantic model for inert filler API responses."""
    
    name: str
    specific_gravity: float
    psd: str
    description: Optional[str]
    source: Optional[str]
    notes: Optional[str]
    is_valid_specific_gravity: bool
    has_description: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True