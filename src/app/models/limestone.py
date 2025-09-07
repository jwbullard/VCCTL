#!/usr/bin/env python3
"""
Limestone Model for VCCTL

Represents limestone materials with single-phase composition and properties.
"""

from typing import Optional
from sqlalchemy import Column, String, Float, Integer, CheckConstraint, Text, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, field_validator

from app.database.base import Base


class Limestone(Base):
    """
    Limestone model representing limestone filler materials.
    
    Contains limestone composition data and physical properties.
    Limestone is treated as a single-phase material.
    """
    
    __tablename__ = 'limestone'
    
    # Use integer ID as primary key (inherited from Base)
    # Name is now just a regular field that can be updated
    name = Column(String(64), nullable=False, unique=True)
    
    # Physical properties
    specific_gravity = Column(Float, nullable=True, default=2.71, 
                            doc="Specific gravity of limestone material")
    specific_surface_area = Column(Float, nullable=True, default=400.0,
                                   doc="Specific surface area in m²/kg")
    
    # PSD relationship (replaces embedded PSD fields)
    psd_data_id = Column(Integer, ForeignKey('psd_data.id'), nullable=True)
    psd_data = relationship('PSDData', backref='limestone_materials')
    
    # Phase distribution parameters
    distribute_phases_by = Column(Integer, nullable=True,
                                doc="Method for phase distribution")
    
    # Chemical composition
    caco3_content = Column(Float, nullable=True, default=97.0,
                          doc="Calcium carbonate content percentage")
    
    # Reaction parameters
    activation_energy = Column(Float, nullable=True, default=54000.0,
                              doc="Activation energy (J/mol)")
    
    # Description and metadata
    description = Column(String(512), nullable=True,
                        doc="Limestone description and notes")
    source = Column(String(255), nullable=True, doc="Material source")
    notes = Column(String(1000), nullable=True, doc="Additional notes")
    
    # Add constraint for specific gravity
    __table_args__ = (
        CheckConstraint('specific_gravity >= 0.0', name='check_specific_gravity_positive'),
    )
    
    def __repr__(self) -> str:
        """String representation of the limestone."""
        return f"<Limestone(name='{self.name}', specific_gravity={self.specific_gravity})>"
    
    def build_phase_distribution_input(self) -> str:
        """
        Build phase distribution input string for simulation.
        
        Returns a formatted string with phase distribution parameters.
        """
        return (
            f"{self.distribute_phases_by or 0}\n"
            f"1.0\n"  # Limestone is pure phase
        )
    
    @property
    def phase_fractions(self) -> dict:
        """Get all phase fractions as a dictionary."""
        return {
            'limestone': 1.0  # Limestone is pure phase
        }
    
    @property
    def total_phase_fraction(self) -> Optional[float]:
        """Calculate total phase fraction."""
        return 1.0  # Limestone is pure phase
    
    @property
    def has_complete_phase_data(self) -> bool:
        """Check if limestone has complete phase composition data."""
        return True  # Limestone is always pure phase
    
    def validate_phase_fractions(self) -> bool:
        """Validate that phase fractions are reasonable (0-1 range)."""
        return True  # Limestone is always pure phase (1.0)


class LimestoneCreate(BaseModel):
    """Pydantic model for creating limestone instances."""
    
    name: str = Field(..., max_length=64, description="Limestone name (unique identifier)")
    specific_gravity: Optional[float] = Field(2.71, ge=0.0, description="Specific gravity")
    specific_surface_area: Optional[float] = Field(400.0, ge=100.0, le=10000.0, description="Specific surface area m²/kg")
    distribute_phases_by: Optional[int] = Field(None, description="Phase distribution method")
    
    # Chemical composition
    caco3_content: Optional[float] = Field(97.0, ge=0.0, le=100.0,
                                          description="Calcium carbonate content percentage")
    
    # Reaction parameters
    activation_energy: Optional[float] = Field(54000.0, gt=0.0, description="Activation energy (J/mol)")
    
    # PSD fields that can be created (will be handled via relationship)
    psd_mode: Optional[str] = Field(None, description="PSD mode (rosin_rammler, log_normal, fuller, custom)")
    psd_d50: Optional[float] = Field(None, ge=0.0, le=1000.0, description="D50 particle size (μm)")
    psd_n: Optional[float] = Field(None, ge=0.0, le=10.0, description="Distribution parameter")
    psd_dmax: Optional[float] = Field(None, ge=0.0, le=1000.0, description="Maximum particle size (μm)")
    psd_median: Optional[float] = Field(None, ge=0.0, le=1000.0, description="Median particle size (μm)")
    psd_spread: Optional[float] = Field(None, ge=0.0, le=10.0, description="Distribution spread parameter")
    psd_exponent: Optional[float] = Field(None, ge=0.0, le=2.0, description="Exponent parameter")
    psd_custom_points: Optional[str] = Field(None, description="Custom PSD points as JSON")
    
    description: Optional[str] = Field(None, max_length=512, description="Limestone description")
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate limestone name."""
        if not v or not v.strip():
            raise ValueError('Limestone name cannot be empty')
        return v.strip()
    
    @field_validator('specific_gravity')
    @classmethod
    def validate_specific_gravity(cls, v):
        """Validate specific gravity."""
        if v is not None and v < 0:
            raise ValueError('Specific gravity cannot be negative')
        return v


class LimestoneUpdate(BaseModel):
    """Pydantic model for updating limestone instances."""
    
    name: Optional[str] = Field(None, max_length=64, description="Limestone name (unique identifier)")
    specific_gravity: Optional[float] = Field(None, ge=0.0, description="Specific gravity")
    distribute_phases_by: Optional[int] = Field(None, description="Phase distribution method")
    
    # Chemical composition
    caco3_content: Optional[float] = Field(None, ge=0.0, le=100.0,
                                          description="Calcium carbonate content percentage")
    
    # Physical properties
    specific_surface_area: Optional[float] = Field(None, ge=100.0, le=10000.0, description="Specific surface area m²/kg")
    
    # Reaction parameters
    activation_energy: Optional[float] = Field(None, gt=0.0, description="Activation energy (J/mol)")
    
    # PSD fields that can be updated (will be handled via relationship)
    psd_mode: Optional[str] = Field(None, description="PSD mode (rosin_rammler, log_normal, fuller, custom)")
    psd_d50: Optional[float] = Field(None, ge=0.0, le=1000.0, description="D50 particle size (μm)")
    psd_n: Optional[float] = Field(None, ge=0.0, le=10.0, description="Distribution parameter")
    psd_dmax: Optional[float] = Field(None, ge=0.0, le=1000.0, description="Maximum particle size (μm)")
    psd_median: Optional[float] = Field(None, ge=0.0, le=1000.0, description="Median particle size (μm)")
    psd_spread: Optional[float] = Field(None, ge=0.0, le=10.0, description="Distribution spread parameter")
    psd_exponent: Optional[float] = Field(None, ge=0.0, le=2.0, description="Exponent parameter")
    psd_custom_points: Optional[str] = Field(None, description="Custom PSD points as JSON")
    
    description: Optional[str] = Field(None, max_length=512, description="Limestone description")
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class LimestoneResponse(BaseModel):
    """Pydantic model for limestone API responses."""
    
    name: str
    specific_gravity: Optional[float]
    specific_surface_area: Optional[float]
    distribute_phases_by: Optional[int]
    
    # Chemical composition
    caco3_content: Optional[float]
    
    # PSD data accessed through relationship
    psd_data_id: Optional[int]
    
    # Reaction parameters
    activation_energy: Optional[float]
    
    description: Optional[str]
    source: Optional[str]
    notes: Optional[str]
    total_phase_fraction: Optional[float]
    has_complete_phase_data: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True