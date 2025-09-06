#!/usr/bin/env python3
"""
Silica Fume Model for VCCTL

Represents silica fume materials with single-phase composition and properties.
"""

from typing import Optional
from sqlalchemy import Column, String, Float, Integer, CheckConstraint, Text, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, field_validator

from app.database.base import Base


class SilicaFume(Base):
    """
    Silica fume model representing ultra-fine supplementary cementitious materials.
    
    Contains silica fume composition data and physical properties.
    Silica fume is treated as a single-phase material.
    """
    
    __tablename__ = 'silica_fume'
    
    # Use integer ID as primary key (inherited from Base)
    # Name is now just a regular field that can be updated
    name = Column(String(64), nullable=False, unique=True)
    
    # Physical properties
    specific_gravity = Column(Float, nullable=True, default=2.22, 
                            doc="Specific gravity of silica fume material")
    
    # Chemical composition
    silica_content = Column(Float, nullable=True, default=92.0,
                           doc="Silicon dioxide content percentage (typically 85-98%)")
    
    # Physical properties
    specific_surface_area = Column(Float, nullable=True, default=20000.0,
                                   doc="Specific surface area in m²/kg (typically 15,000-40,000)")
    
    # PSD relationship (replaces embedded PSD fields)
    psd_data_id = Column(Integer, ForeignKey('psd_data.id'), nullable=True)
    psd_data = relationship('PSDData', backref='silica_fume_materials')
    
    # Phase distribution parameters
    distribute_phases_by = Column(Integer, nullable=True,
                                doc="Method for phase distribution")
    
    # Silica fume is a single-phase material (100% silica) 
    # silica_fume_fraction field removed - always implicitly 1.0
    
    # Reaction parameters
    activation_energy = Column(Float, nullable=True, default=54000.0,
                              doc="Activation energy (J/mol)")
    
    # Description and metadata
    description = Column(String(512), nullable=True,
                        doc="Silica fume description and notes")
    source = Column(String(255), nullable=True, doc="Material source")
    notes = Column(String(1000), nullable=True, doc="Additional notes")
    
    # Add constraint for specific gravity
    __table_args__ = (
        CheckConstraint('specific_gravity >= 0.0', name='check_specific_gravity_positive'),
    )
    
    def __repr__(self) -> str:
        """String representation of the silica fume."""
        return f"<SilicaFume(name='{self.name}', specific_gravity={self.specific_gravity})>"
    
    def build_phase_distribution_input(self) -> str:
        """
        Build phase distribution input string for simulation.
        
        Returns a formatted string with phase distribution parameters.
        """
        return (
            f"{self.distribute_phases_by or 0}\n"
            f"1.0\n"  # Silica fume is always 100% silica phase
        )
    
    @property
    def phase_fractions(self) -> dict:
        """Get all phase fractions as a dictionary."""
        return {
            'silica_fume': 1.0  # Always 100% silica phase
        }
    
    @property
    def total_phase_fraction(self) -> Optional[float]:
        """Calculate total phase fraction."""
        return 1.0  # Always 100% for single-phase material
    
    @property
    def has_complete_phase_data(self) -> bool:
        """Check if silica fume has complete phase composition data."""
        return True  # Always complete for single-phase material
    
    def validate_phase_fractions(self) -> bool:
        """Validate that phase fractions are reasonable (0-1 range)."""
        return True  # Always valid for single-phase material


class SilicaFumeCreate(BaseModel):
    """Pydantic model for creating silica fume instances."""
    
    name: str = Field(..., max_length=64, description="Silica fume name (unique identifier)")
    specific_gravity: Optional[float] = Field(2.22, ge=0.0, description="Specific gravity")
    silica_content: Optional[float] = Field(92.0, ge=80.0, le=100.0, description="SiO2 content percentage")
    specific_surface_area: Optional[float] = Field(20000.0, ge=10000.0, le=40000.0, description="Specific surface area m²/kg")
    
    distribute_phases_by: Optional[int] = Field(None, description="Phase distribution method")
    
    # Silica fume is single-phase material - no fraction field needed
    
    # Reaction parameters
    activation_energy: Optional[float] = Field(54000.0, gt=0.0, description="Activation energy (J/mol)")
    
    description: Optional[str] = Field(None, max_length=512, description="Silica fume description")
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate silica fume name."""
        if not v or not v.strip():
            raise ValueError('Silica fume name cannot be empty')
        return v.strip()
    
    @field_validator('specific_gravity')
    @classmethod
    def validate_specific_gravity(cls, v):
        """Validate specific gravity."""
        if v is not None and v < 0:
            raise ValueError('Specific gravity cannot be negative')
        return v


class SilicaFumeUpdate(BaseModel):
    """Pydantic model for updating silica fume instances."""
    
    name: Optional[str] = Field(None, max_length=64, description="Silica fume name")
    specific_gravity: Optional[float] = Field(None, ge=0.0, description="Specific gravity")
    silica_content: Optional[float] = Field(None, ge=80.0, le=100.0, description="SiO2 content percentage")
    specific_surface_area: Optional[float] = Field(None, ge=10000.0, le=40000.0, description="Specific surface area m²/kg")
    
    distribute_phases_by: Optional[int] = Field(None, description="Phase distribution method")
    
    # Silica fume is single-phase material - no fraction field needed
    
    # Reaction parameters
    activation_energy: Optional[float] = Field(None, gt=0.0, description="Activation energy (J/mol)")
    
    description: Optional[str] = Field(None, max_length=512, description="Silica fume description")
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class SilicaFumeResponse(BaseModel):
    """Pydantic model for silica fume API responses."""
    
    name: str
    specific_gravity: Optional[float]
    silica_content: Optional[float]
    specific_surface_area: Optional[float]
    
    # PSD data accessed through relationship
    psd_data_id: Optional[int]
    
    distribute_phases_by: Optional[int]
    # silica_fume_fraction removed - always 1.0
    
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