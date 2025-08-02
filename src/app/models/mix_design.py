#!/usr/bin/env python3
"""
Mix Design Model for VCCTL

Represents saved concrete mix designs with components, properties, and metadata.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, Integer, Boolean, DateTime, JSON
from pydantic import BaseModel, Field, field_validator, model_validator

from app.database.base import Base


class MixDesign(Base):
    """
    Mix Design model representing saved concrete mix formulations.
    
    Contains mix composition data, component information, water-binder ratios,
    air content, and other mix design parameters.
    """
    
    __tablename__ = 'mix_design'
    
    # Primary key - auto-incrementing integer ID
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Mix design identification
    name = Column(String(128), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Mix design metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Mix design parameters
    water_binder_ratio = Column(Float, nullable=False, default=0.0)
    total_water_content = Column(Float, nullable=False, default=0.0)  # kg/m³
    air_content = Column(Float, nullable=False, default=0.0)  # %
    water_volume_fraction = Column(Float, nullable=False, default=0.0)
    air_volume_fraction = Column(Float, nullable=False, default=0.0)
    
    # System size for microstructure generation
    system_size = Column(Integer, nullable=False, default=100)
    
    # Random seed for reproducibility
    random_seed = Column(Integer, nullable=False, default=-1)
    
    # Cement and aggregate shape settings
    cement_shape_set = Column(String(64), nullable=True, default="spherical")
    aggregate_shape_set = Column(String(64), nullable=True, default="spherical")
    
    # Component data stored as JSON
    # Format: [{"material_name": str, "material_type": str, "mass_fraction": float, "volume_fraction": float, "specific_gravity": float}, ...]
    components = Column(JSON, nullable=False, default=list)
    
    # Calculated properties stored as JSON
    # Format: {"paste_volume_fraction": float, "powder_volume_fraction": float, "aggregate_volume_fraction": float, ...}
    calculated_properties = Column(JSON, nullable=True, default=dict)
    
    # Additional metadata
    notes = Column(Text, nullable=True)
    is_template = Column(Boolean, nullable=False, default=False)  # Mark as template for reuse
    
    def __repr__(self):
        return f"<MixDesign(id={self.id}, name='{self.name}', w/b={self.water_binder_ratio:.3f})>"


# Pydantic models for API and validation

class MixDesignComponentData(BaseModel):
    """Represents a single component in a mix design."""
    material_name: str = Field(..., min_length=1, max_length=128)
    material_type: str = Field(..., min_length=1, max_length=64)
    mass_fraction: float = Field(ge=0.0, le=1.0)
    volume_fraction: float = Field(ge=0.0, le=1.0)
    specific_gravity: float = Field(gt=0.0, le=10.0)


class MixDesignPropertiesData(BaseModel):
    """Represents calculated properties of a mix design."""
    paste_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0)
    powder_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0)
    aggregate_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0)
    binder_content: Optional[float] = Field(None, ge=0.0)
    water_content: Optional[float] = Field(None, ge=0.0)


class MixDesignCreate(BaseModel):
    """Schema for creating a new mix design."""
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=2000)
    water_binder_ratio: float = Field(ge=0.0, le=2.0)
    total_water_content: float = Field(ge=0.0, le=1000.0)  # kg/m³
    air_content: float = Field(ge=0.0, le=20.0)  # %
    water_volume_fraction: float = Field(ge=0.0, le=1.0)
    air_volume_fraction: float = Field(ge=0.0, le=1.0)
    system_size: int = Field(ge=50, le=500, default=100)
    random_seed: int = Field(ge=-2147483647, le=-1, default=-1)
    cement_shape_set: Optional[str] = Field(default="spherical", max_length=64)
    aggregate_shape_set: Optional[str] = Field(default="spherical", max_length=64)
    components: List[MixDesignComponentData] = Field(default_factory=list)
    calculated_properties: Optional[MixDesignPropertiesData] = Field(None)
    notes: Optional[str] = Field(None, max_length=2000)
    is_template: bool = Field(default=False)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate mix design name."""
        if not v or not v.strip():
            raise ValueError('Mix design name cannot be empty')
        # Remove potentially problematic characters for file names
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in v:
                raise ValueError(f'Mix design name cannot contain "{char}"')
        return v.strip()
    
    @model_validator(mode='after')
    def validate_components(self):
        """Validate mix design components."""
        if not self.components:
            raise ValueError('Mix design must have at least one component')
        
        # Check for duplicate material names
        material_names = [comp.material_name for comp in self.components]
        if len(material_names) != len(set(material_names)):
            raise ValueError('Mix design cannot have duplicate material names')
        
        # Check mass fractions sum
        total_mass_fraction = sum(comp.mass_fraction for comp in self.components)
        if abs(total_mass_fraction - 1.0) > 0.001:  # Allow small floating-point errors
            raise ValueError(f'Total mass fractions must sum to 1.0, got {total_mass_fraction:.3f}')
        
        return self


class MixDesignUpdate(BaseModel):
    """Schema for updating an existing mix design."""
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=2000)
    water_binder_ratio: Optional[float] = Field(None, ge=0.0, le=2.0)
    total_water_content: Optional[float] = Field(None, ge=0.0, le=1000.0)
    air_content: Optional[float] = Field(None, ge=0.0, le=20.0)
    water_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0)
    air_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0)
    system_size: Optional[int] = Field(None, ge=50, le=500)
    random_seed: Optional[int] = Field(None, ge=-2147483647, le=-1)
    cement_shape_set: Optional[str] = Field(None, max_length=64)
    aggregate_shape_set: Optional[str] = Field(None, max_length=64)
    components: Optional[List[MixDesignComponentData]] = None
    calculated_properties: Optional[MixDesignPropertiesData] = None
    notes: Optional[str] = Field(None, max_length=2000)
    is_template: Optional[bool] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate mix design name."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError('Mix design name cannot be empty')
            # Remove potentially problematic characters for file names
            invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
            for char in invalid_chars:
                if char in v:
                    raise ValueError(f'Mix design name cannot contain "{char}"')
            return v.strip()
        return v


class MixDesignResponse(BaseModel):
    """Schema for mix design responses."""
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    water_binder_ratio: float
    total_water_content: float
    air_content: float
    water_volume_fraction: float
    air_volume_fraction: float
    system_size: int
    random_seed: int
    cement_shape_set: Optional[str]
    aggregate_shape_set: Optional[str]
    components: List[MixDesignComponentData]
    calculated_properties: Optional[MixDesignPropertiesData]
    notes: Optional[str]
    is_template: bool
    
    class Config:
        from_attributes = True