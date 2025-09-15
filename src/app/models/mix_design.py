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
# Import centralized validation
from app.validation import MixDesignValidator, ComponentData


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
    
    # System size for microstructure generation (individual X, Y, Z dimensions)
    system_size_x = Column(Integer, nullable=False, default=100)
    system_size_y = Column(Integer, nullable=False, default=100)
    system_size_z = Column(Integer, nullable=False, default=100)
    system_size = Column(Integer, nullable=False, default=100)  # Keep for backward compatibility
    
    # Resolution for microstructure generation
    resolution = Column(Float, nullable=False, default=1.0)
    
    # Random seed for reproducibility
    random_seed = Column(Integer, nullable=False, default=-1)
    
    # Cement and aggregate shape settings
    cement_shape_set = Column(String(64), nullable=True, default="spherical")
    fine_aggregate_shape_set = Column(String(64), nullable=True, default="spherical")  # Fine aggregate shapes
    coarse_aggregate_shape_set = Column(String(64), nullable=True, default="spherical")  # Coarse aggregate shapes
    aggregate_shape_set = Column(String(64), nullable=True, default="spherical")  # Keep for backward compatibility
    
    # Flocculation parameters
    flocculation_enabled = Column(Boolean, nullable=False, default=False)
    flocculation_degree = Column(Float, nullable=False, default=0.0)
    
    # Dispersion parameters
    dispersion_factor = Column(Integer, nullable=False, default=0)
    
    # Auto-calculation setting
    auto_calculation_enabled = Column(Boolean, nullable=False, default=True)
    
    # Fine aggregate parameters
    fine_aggregate_name = Column(String(128), nullable=True)
    fine_aggregate_mass = Column(Float, nullable=False, default=0.0)
    
    # Coarse aggregate parameters
    coarse_aggregate_name = Column(String(128), nullable=True)
    coarse_aggregate_mass = Column(Float, nullable=False, default=0.0)
    
    # Grading template associations
    fine_aggregate_grading_template = Column(String(64), nullable=True)
    coarse_aggregate_grading_template = Column(String(64), nullable=True)
    
    # Component data stored as JSON
    # Format: [{"material_name": str, "material_type": str, "mass_fraction": float, "volume_fraction": float, "specific_gravity": float}, ...]
    components = Column(JSON, nullable=False, default=list)
    
    # Reference water mass for exact mass reconstruction (in kg)
    # Used to calculate exact total mass: total_mass = water_reference_mass / water_mass_fraction
    water_reference_mass = Column(Float, nullable=True, default=None)
    
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
    # Optional grading data for aggregates
    grading_data: Optional[List[List[float]]] = Field(None, description="Grading curve data as list of [sieve_size, percent_retained] pairs")
    grading_template: Optional[str] = Field(None, max_length=64, description="Name of grading template used")


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
    
    # System size parameters (individual X, Y, Z dimensions)
    system_size_x: int = Field(ge=25, le=400, default=100)
    system_size_y: int = Field(ge=25, le=400, default=100)
    system_size_z: int = Field(ge=25, le=400, default=100)
    system_size: int = Field(ge=50, le=500, default=100)  # Keep for backward compatibility
    
    # Resolution parameter
    resolution: float = Field(ge=0.01, le=100.0, default=1.0)
    
    # Random seed
    random_seed: int = Field(ge=-2147483647, le=-1, default=-1)
    
    # Shape set parameters
    cement_shape_set: Optional[str] = Field(default="spherical", max_length=64)
    fine_aggregate_shape_set: Optional[str] = Field(default="spherical", max_length=64)
    coarse_aggregate_shape_set: Optional[str] = Field(default="spherical", max_length=64)
    aggregate_shape_set: Optional[str] = Field(default="spherical", max_length=64)  # Keep for backward compatibility
    
    # Flocculation parameters
    flocculation_enabled: bool = Field(default=False)
    flocculation_degree: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Dispersion parameters
    dispersion_factor: int = Field(ge=0, le=2, default=0)
    
    # Auto-calculation setting
    auto_calculation_enabled: bool = Field(default=True)
    
    # Fine aggregate parameters
    fine_aggregate_name: Optional[str] = Field(None, max_length=128)
    fine_aggregate_mass: float = Field(ge=0.0, le=10.0, default=0.0)
    
    # Coarse aggregate parameters
    coarse_aggregate_name: Optional[str] = Field(None, max_length=128)
    coarse_aggregate_mass: float = Field(ge=0.0, le=10.0, default=0.0)
    
    # Grading template associations
    fine_aggregate_grading_template: Optional[str] = Field(None, max_length=64)
    coarse_aggregate_grading_template: Optional[str] = Field(None, max_length=64)
    
    # Component and properties data
    components: List[MixDesignComponentData] = Field(default_factory=list)
    calculated_properties: Optional[MixDesignPropertiesData] = Field(None)
    notes: Optional[str] = Field(None, max_length=2000)
    
    # Reference water mass for exact mass reconstruction
    water_reference_mass: Optional[float] = Field(None, ge=0.0)
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
        """Validate mix design components using centralized validation."""
        if not self.components:
            raise ValueError('Mix design must have at least one component')
        
        # Convert to standardized format for centralized validation
        validation_components = [
            ComponentData(
                material_name=comp.material_name,
                material_type=comp.material_type,
                mass_fraction=comp.mass_fraction,
                volume_fraction=comp.volume_fraction,
                specific_gravity=comp.specific_gravity
            )
            for comp in self.components
        ]
        
        # Use centralized validation for mass fractions
        is_valid, error = MixDesignValidator.validate_mass_fractions_only(validation_components)
        if not is_valid:
            raise ValueError(error)
        
        # Use centralized validation for component uniqueness
        is_unique, error = MixDesignValidator.validate_component_uniqueness_only(validation_components)
        if not is_unique:
            raise ValueError(error)
        
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
    
    # System size parameters
    system_size_x: Optional[int] = Field(None, ge=25, le=400)
    system_size_y: Optional[int] = Field(None, ge=25, le=400)
    system_size_z: Optional[int] = Field(None, ge=25, le=400)
    system_size: Optional[int] = Field(None, ge=50, le=500)
    
    # Resolution parameter
    resolution: Optional[float] = Field(None, ge=0.01, le=100.0)
    
    # Random seed
    random_seed: Optional[int] = Field(None, ge=-2147483647, le=-1)
    
    # Shape set parameters
    cement_shape_set: Optional[str] = Field(None, max_length=64)
    fine_aggregate_shape_set: Optional[str] = Field(None, max_length=64)
    coarse_aggregate_shape_set: Optional[str] = Field(None, max_length=64)
    aggregate_shape_set: Optional[str] = Field(None, max_length=64)
    
    # Flocculation parameters
    flocculation_enabled: Optional[bool] = None
    flocculation_degree: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Dispersion parameters
    dispersion_factor: Optional[int] = Field(None, ge=0, le=2)
    
    # Auto-calculation setting
    auto_calculation_enabled: Optional[bool] = None
    
    # Fine aggregate parameters
    fine_aggregate_name: Optional[str] = Field(None, max_length=128)
    fine_aggregate_mass: Optional[float] = Field(None, ge=0.0, le=10.0)
    
    # Coarse aggregate parameters
    coarse_aggregate_name: Optional[str] = Field(None, max_length=128)
    coarse_aggregate_mass: Optional[float] = Field(None, ge=0.0, le=10.0)
    
    # Grading template associations
    fine_aggregate_grading_template: Optional[str] = Field(None, max_length=64)
    coarse_aggregate_grading_template: Optional[str] = Field(None, max_length=64)
    
    # Component and properties data
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
    
    # System size parameters
    system_size_x: int
    system_size_y: int
    system_size_z: int
    system_size: int  # Keep for backward compatibility
    
    # Resolution parameter
    resolution: float
    
    # Random seed
    random_seed: int
    
    # Shape set parameters
    cement_shape_set: Optional[str]
    fine_aggregate_shape_set: Optional[str]
    coarse_aggregate_shape_set: Optional[str]
    aggregate_shape_set: Optional[str]  # Keep for backward compatibility
    
    # Flocculation parameters
    flocculation_enabled: bool
    flocculation_degree: float
    
    # Dispersion parameters
    dispersion_factor: int
    
    # Auto-calculation setting
    auto_calculation_enabled: bool
    
    # Fine aggregate parameters
    fine_aggregate_name: Optional[str]
    fine_aggregate_mass: float
    
    # Coarse aggregate parameters
    coarse_aggregate_name: Optional[str]
    coarse_aggregate_mass: float
    
    # Grading template associations
    fine_aggregate_grading_template: Optional[str]
    coarse_aggregate_grading_template: Optional[str]
    
    components: List[MixDesignComponentData]
    calculated_properties: Optional[MixDesignPropertiesData]
    notes: Optional[str]
    is_template: bool
    
    class Config:
        from_attributes = True