#!/usr/bin/env python3
"""
Silica Fume Model for VCCTL

Represents silica fume materials with single-phase composition and properties.
"""

from typing import Optional
from sqlalchemy import Column, String, Float, Integer, CheckConstraint, Text
from pydantic import BaseModel, Field, field_validator

from app.database.base import Base


class SilicaFume(Base):
    """
    Silica fume model representing ultra-fine supplementary cementitious materials.
    
    Contains silica fume composition data and physical properties.
    Silica fume is treated as a single-phase material.
    """
    
    __tablename__ = 'silica_fume'
    
    # Override base model id with string primary key
    id = None
    
    # Primary key - silica fume name (unique identifier)
    name = Column(String(64), primary_key=True, nullable=False, unique=True)
    
    # Physical properties
    specific_gravity = Column(Float, nullable=True, default=2.22, 
                            doc="Specific gravity of silica fume material")
    
    # Particle size distribution reference
    psd = Column(String(64), nullable=True, default='cement141',
                doc="Particle size distribution reference")
    
    # Custom PSD data points (JSON format)
    psd_custom_points = Column(Text, nullable=True, 
                              doc="Custom PSD points stored as JSON")
    
    # Phase distribution parameters
    distribute_phases_by = Column(Integer, nullable=True,
                                doc="Method for phase distribution")
    
    # Single phase fraction (silica fume is essentially pure silica)
    silica_fume_fraction = Column(Float, nullable=True, default=1.0,
                                doc="Silica fume phase mass fraction")
    
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
            f"{self.silica_fume_fraction or 1.0}\n"
        )
    
    @property
    def phase_fractions(self) -> dict:
        """Get all phase fractions as a dictionary."""
        return {
            'silica_fume': self.silica_fume_fraction
        }
    
    @property
    def total_phase_fraction(self) -> Optional[float]:
        """Calculate total phase fraction."""
        return self.silica_fume_fraction
    
    @property
    def has_complete_phase_data(self) -> bool:
        """Check if silica fume has complete phase composition data."""
        return self.silica_fume_fraction is not None
    
    def validate_phase_fractions(self) -> bool:
        """Validate that phase fractions are reasonable (0-1 range)."""
        if self.silica_fume_fraction is None:
            return True
        
        return 0 <= self.silica_fume_fraction <= 1


class SilicaFumeCreate(BaseModel):
    """Pydantic model for creating silica fume instances."""
    
    name: str = Field(..., max_length=64, description="Silica fume name (unique identifier)")
    specific_gravity: Optional[float] = Field(2.22, ge=0.0, description="Specific gravity")
    psd: Optional[str] = Field('cement141', max_length=64, 
                              description="Particle size distribution reference")
    psd_custom_points: Optional[str] = Field(None, 
                                           description="Custom PSD points stored as JSON")
    distribute_phases_by: Optional[int] = Field(None, description="Phase distribution method")
    
    # Single phase fraction
    silica_fume_fraction: Optional[float] = Field(1.0, ge=0.0, le=1.0,
                                                 description="Silica fume phase fraction")
    
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
    
    specific_gravity: Optional[float] = Field(None, ge=0.0, description="Specific gravity")
    psd: Optional[str] = Field(None, max_length=64, 
                              description="Particle size distribution reference")
    psd_custom_points: Optional[str] = Field(None, 
                                           description="Custom PSD points stored as JSON")
    distribute_phases_by: Optional[int] = Field(None, description="Phase distribution method")
    
    # Single phase fraction
    silica_fume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                 description="Silica fume phase fraction")
    
    # Reaction parameters
    activation_energy: Optional[float] = Field(None, gt=0.0, description="Activation energy (J/mol)")
    
    description: Optional[str] = Field(None, max_length=512, description="Silica fume description")
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class SilicaFumeResponse(BaseModel):
    """Pydantic model for silica fume API responses."""
    
    name: str
    specific_gravity: Optional[float]
    psd: Optional[str]
    distribute_phases_by: Optional[int]
    silica_fume_fraction: Optional[float]
    
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