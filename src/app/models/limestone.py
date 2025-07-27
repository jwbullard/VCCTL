#!/usr/bin/env python3
"""
Limestone Model for VCCTL

Represents limestone materials with single-phase composition and properties.
"""

from typing import Optional
from sqlalchemy import Column, String, Float, Integer, CheckConstraint, Text
from pydantic import BaseModel, Field, field_validator

from app.database.base import Base


class Limestone(Base):
    """
    Limestone model representing limestone filler materials.
    
    Contains limestone composition data and physical properties.
    Limestone is treated as a single-phase material.
    """
    
    __tablename__ = 'limestone'
    
    # Override base model id with string primary key
    id = None
    
    # Primary key - limestone name (unique identifier)
    name = Column(String(64), primary_key=True, nullable=False, unique=True)
    
    # Physical properties
    specific_gravity = Column(Float, nullable=True, default=2.71, 
                            doc="Specific gravity of limestone material")
    
    # Particle size distribution reference
    psd = Column(String(64), nullable=True, default='cement141',
                doc="Particle size distribution reference")
    
    # Custom PSD data points (JSON format)
    psd_custom_points = Column(Text, nullable=True, 
                              doc="Custom PSD points stored as JSON")
    
    # Phase distribution parameters
    distribute_phases_by = Column(Integer, nullable=True,
                                doc="Method for phase distribution")
    
    # Single phase fraction (limestone is essentially calcium carbonate)
    limestone_fraction = Column(Float, nullable=True, default=1.0,
                              doc="Limestone phase mass fraction")
    
    # Chemical composition
    caco3_content = Column(Float, nullable=True, default=97.0,
                          doc="Calcium carbonate content percentage")
    
    # Physical properties
    hardness = Column(Float, nullable=True, default=3.0,
                     doc="Mohs hardness scale (typically 3-4 for limestone)")
    
    # PSD parameters for log-normal distribution
    psd_median = Column(Float, nullable=True, default=5.0,
                       doc="Median particle size (μm) for log-normal distribution")
    psd_spread = Column(Float, nullable=True, default=2.0,
                       doc="PSD distribution spread parameter for log-normal distribution")
    
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
            f"{self.limestone_fraction or 1.0}\n"
        )
    
    @property
    def phase_fractions(self) -> dict:
        """Get all phase fractions as a dictionary."""
        return {
            'limestone': self.limestone_fraction
        }
    
    @property
    def total_phase_fraction(self) -> Optional[float]:
        """Calculate total phase fraction."""
        return self.limestone_fraction
    
    @property
    def has_complete_phase_data(self) -> bool:
        """Check if limestone has complete phase composition data."""
        return self.limestone_fraction is not None
    
    def validate_phase_fractions(self) -> bool:
        """Validate that phase fractions are reasonable (0-1 range)."""
        if self.limestone_fraction is None:
            return True
        
        return 0 <= self.limestone_fraction <= 1


class LimestoneCreate(BaseModel):
    """Pydantic model for creating limestone instances."""
    
    name: str = Field(..., max_length=64, description="Limestone name (unique identifier)")
    specific_gravity: Optional[float] = Field(2.71, ge=0.0, description="Specific gravity")
    psd: Optional[str] = Field('cement141', max_length=64, 
                              description="Particle size distribution reference")
    psd_custom_points: Optional[str] = Field(None, 
                                           description="Custom PSD points stored as JSON")
    distribute_phases_by: Optional[int] = Field(None, description="Phase distribution method")
    
    # Single phase fraction
    limestone_fraction: Optional[float] = Field(1.0, ge=0.0, le=1.0,
                                               description="Limestone phase fraction")
    
    # Chemical composition
    caco3_content: Optional[float] = Field(97.0, ge=0.0, le=100.0,
                                          description="Calcium carbonate content percentage")
    
    # Physical properties
    hardness: Optional[float] = Field(3.0, ge=0.0, le=10.0,
                                     description="Mohs hardness scale")
    
    # PSD parameters
    psd_median: Optional[float] = Field(5.0, gt=0.0, description="Median particle size (μm)")
    psd_spread: Optional[float] = Field(2.0, gt=0.0, description="PSD distribution spread parameter")
    
    # Reaction parameters
    activation_energy: Optional[float] = Field(54000.0, gt=0.0, description="Activation energy (J/mol)")
    
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
    
    specific_gravity: Optional[float] = Field(None, ge=0.0, description="Specific gravity")
    psd: Optional[str] = Field(None, max_length=64, 
                              description="Particle size distribution reference")
    psd_custom_points: Optional[str] = Field(None, 
                                           description="Custom PSD points stored as JSON")
    distribute_phases_by: Optional[int] = Field(None, description="Phase distribution method")
    
    # Single phase fraction
    limestone_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                               description="Limestone phase fraction")
    
    # Chemical composition
    caco3_content: Optional[float] = Field(None, ge=0.0, le=100.0,
                                          description="Calcium carbonate content percentage")
    
    # Physical properties
    hardness: Optional[float] = Field(None, ge=0.0, le=10.0,
                                     description="Mohs hardness scale")
    
    # PSD parameters
    psd_median: Optional[float] = Field(None, gt=0.0, description="Median particle size (μm)")
    psd_spread: Optional[float] = Field(None, gt=0.0, description="PSD distribution spread parameter")
    
    # Reaction parameters
    activation_energy: Optional[float] = Field(None, gt=0.0, description="Activation energy (J/mol)")
    
    description: Optional[str] = Field(None, max_length=512, description="Limestone description")
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")


class LimestoneResponse(BaseModel):
    """Pydantic model for limestone API responses."""
    
    name: str
    specific_gravity: Optional[float]
    psd: Optional[str]
    distribute_phases_by: Optional[int]
    limestone_fraction: Optional[float]
    
    # Chemical composition
    caco3_content: Optional[float]
    
    # Physical properties
    hardness: Optional[float]
    
    # PSD parameters
    psd_median: Optional[float]
    psd_spread: Optional[float]
    
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