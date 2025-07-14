#!/usr/bin/env python3
"""
Fly Ash Model for VCCTL

Represents fly ash materials with composition, properties, and phase distributions.
Converted from Java JPA entity to SQLAlchemy model.
"""

from typing import Optional
from sqlalchemy import Column, String, Float, Integer, CheckConstraint
from pydantic import BaseModel, Field, field_validator, model_validator

from app.database.base import Base


class FlyAsh(Base):
    """
    Fly ash model representing supplementary cementitious materials.
    
    Contains fly ash composition data, phase distributions,
    and physical properties like specific gravity.
    """
    
    __tablename__ = 'fly_ash'
    
    # Override base model id with string primary key
    id = None
    
    # Primary key - fly ash name (unique identifier)
    name = Column(String(64), primary_key=True, nullable=False, unique=True)
    
    # Physical properties
    specific_gravity = Column(Float, nullable=True, default=2.77, 
                            doc="Specific gravity of fly ash material")
    
    # Particle size distribution reference
    psd = Column(String(64), nullable=True, default='cement141',
                doc="Particle size distribution reference")
    
    # Phase distribution parameters
    distribute_phases_by = Column(Integer, nullable=True,
                                doc="Method for phase distribution")
    
    # Phase fractions (mass fractions)
    aluminosilicate_glass_fraction = Column(Float, nullable=True,
                                          doc="Aluminosilicate glass mass fraction")
    calcium_aluminum_disilicate_fraction = Column(Float, nullable=True,
                                                 doc="Calcium aluminum disilicate mass fraction")
    tricalcium_aluminate_fraction = Column(Float, nullable=True,
                                         doc="Tricalcium aluminate mass fraction")
    calcium_chloride_fraction = Column(Float, nullable=True,
                                     doc="Calcium chloride mass fraction")
    silica_fraction = Column(Float, nullable=True,
                           doc="Silica mass fraction")
    anhydrate_fraction = Column(Float, nullable=True,
                              doc="Anhydrate mass fraction")
    
    # Description
    description = Column(String(512), nullable=True,
                        doc="Fly ash description and notes")
    
    # Add constraint for specific gravity
    __table_args__ = (
        CheckConstraint('specific_gravity >= 0.0', name='check_specific_gravity_positive'),
    )
    
    def __repr__(self) -> str:
        """String representation of the fly ash."""
        return f"<FlyAsh(name='{self.name}', specific_gravity={self.specific_gravity})>"
    
    def build_phase_distribution_input(self) -> str:
        """
        Build phase distribution input string for simulation.
        
        Returns a formatted string with phase distribution parameters
        matching the Java implementation.
        """
        return (
            f"{self.distribute_phases_by or 0}\n"
            f"{self.aluminosilicate_glass_fraction or 0.0}\n"
            f"{self.calcium_aluminum_disilicate_fraction or 0.0}\n"
            f"{self.tricalcium_aluminate_fraction or 0.0}\n"
            f"{self.calcium_chloride_fraction or 0.0}\n"
            f"{self.silica_fraction or 0.0}\n"
            f"{self.anhydrate_fraction or 0.0}\n"
        )
    
    @property
    def phase_fractions(self) -> dict:
        """Get all phase fractions as a dictionary."""
        return {
            'aluminosilicate_glass': self.aluminosilicate_glass_fraction,
            'calcium_aluminum_disilicate': self.calcium_aluminum_disilicate_fraction,
            'tricalcium_aluminate': self.tricalcium_aluminate_fraction,
            'calcium_chloride': self.calcium_chloride_fraction,
            'silica': self.silica_fraction,
            'anhydrate': self.anhydrate_fraction
        }
    
    @property
    def total_phase_fraction(self) -> Optional[float]:
        """Calculate total phase fraction if all values are present."""
        fractions = [
            self.aluminosilicate_glass_fraction,
            self.calcium_aluminum_disilicate_fraction,
            self.tricalcium_aluminate_fraction,
            self.calcium_chloride_fraction,
            self.silica_fraction,
            self.anhydrate_fraction
        ]
        
        valid_fractions = [f for f in fractions if f is not None]
        if len(valid_fractions) == len(fractions):
            return sum(valid_fractions)
        return None
    
    @property
    def has_complete_phase_data(self) -> bool:
        """Check if fly ash has complete phase composition data."""
        fractions = [
            self.aluminosilicate_glass_fraction,
            self.calcium_aluminum_disilicate_fraction,
            self.tricalcium_aluminate_fraction,
            self.calcium_chloride_fraction,
            self.silica_fraction,
            self.anhydrate_fraction
        ]
        return all(f is not None for f in fractions)
    
    def validate_phase_fractions(self) -> bool:
        """Validate that phase fractions are reasonable (0-1 range and sum <= 1)."""
        fractions = [
            self.aluminosilicate_glass_fraction,
            self.calcium_aluminum_disilicate_fraction,
            self.tricalcium_aluminate_fraction,
            self.calcium_chloride_fraction,
            self.silica_fraction,
            self.anhydrate_fraction
        ]
        
        valid_fractions = [f for f in fractions if f is not None]
        
        if not valid_fractions:
            return True  # No fractions to validate
        
        # Check individual fractions are in valid range
        if any(f < 0 or f > 1 for f in valid_fractions):
            return False
        
        # Check total doesn't exceed 1.0 if we have a significant number of fractions
        if len(valid_fractions) >= 3 and sum(valid_fractions) > 1.0:
            return False
        
        return True


class FlyAshCreate(BaseModel):
    """Pydantic model for creating fly ash instances."""
    
    name: str = Field(..., max_length=64, description="Fly ash name (unique identifier)")
    specific_gravity: Optional[float] = Field(2.77, ge=0.0, description="Specific gravity")
    psd: Optional[str] = Field('cement141', max_length=64, 
                              description="Particle size distribution reference")
    distribute_phases_by: Optional[int] = Field(None, description="Phase distribution method")
    
    # Phase fractions
    aluminosilicate_glass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                           description="Aluminosilicate glass fraction")
    calcium_aluminum_disilicate_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                                 description="Calcium aluminum disilicate fraction")
    tricalcium_aluminate_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                          description="Tricalcium aluminate fraction")
    calcium_chloride_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                      description="Calcium chloride fraction")
    silica_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                           description="Silica fraction")
    anhydrate_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                              description="Anhydrate fraction")
    
    description: Optional[str] = Field(None, max_length=512, description="Fly ash description")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate fly ash name."""
        if not v or not v.strip():
            raise ValueError('Fly ash name cannot be empty')
        return v.strip()
    
    @field_validator('specific_gravity')
    @classmethod
    def validate_specific_gravity(cls, v):
        """Validate specific gravity."""
        if v is not None and v < 0:
            raise ValueError('Specific gravity cannot be negative')
        return v
    
    @model_validator(mode='after')
    def validate_phase_fractions_total(self):
        """Validate that phase fractions don't exceed 100%."""
        fractions = [
            self.aluminosilicate_glass_fraction,
            self.calcium_aluminum_disilicate_fraction,
            self.tricalcium_aluminate_fraction,
            self.calcium_chloride_fraction,
            self.silica_fraction,
            self.anhydrate_fraction
        ]
        
        valid_fractions = [f for f in fractions if f is not None]
        
        if len(valid_fractions) >= 3 and sum(valid_fractions) > 1.0:
            raise ValueError('Total phase fractions cannot exceed 1.0 (100%)')
        
        return self


class FlyAshUpdate(BaseModel):
    """Pydantic model for updating fly ash instances."""
    
    specific_gravity: Optional[float] = Field(None, ge=0.0, description="Specific gravity")
    psd: Optional[str] = Field(None, max_length=64, 
                              description="Particle size distribution reference")
    distribute_phases_by: Optional[int] = Field(None, description="Phase distribution method")
    
    # Phase fractions
    aluminosilicate_glass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                           description="Aluminosilicate glass fraction")
    calcium_aluminum_disilicate_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                                 description="Calcium aluminum disilicate fraction")
    tricalcium_aluminate_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                          description="Tricalcium aluminate fraction")
    calcium_chloride_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                                      description="Calcium chloride fraction")
    silica_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                           description="Silica fraction")
    anhydrate_fraction: Optional[float] = Field(None, ge=0.0, le=1.0,
                                              description="Anhydrate fraction")
    
    description: Optional[str] = Field(None, max_length=512, description="Fly ash description")


class FlyAshResponse(BaseModel):
    """Pydantic model for fly ash API responses."""
    
    name: str
    specific_gravity: Optional[float]
    psd: Optional[str]
    distribute_phases_by: Optional[int]
    aluminosilicate_glass_fraction: Optional[float]
    calcium_aluminum_disilicate_fraction: Optional[float]
    tricalcium_aluminate_fraction: Optional[float]
    calcium_chloride_fraction: Optional[float]
    silica_fraction: Optional[float]
    anhydrate_fraction: Optional[float]
    description: Optional[str]
    total_phase_fraction: Optional[float]
    has_complete_phase_data: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True