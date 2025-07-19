#!/usr/bin/env python3
"""
Cement Model for VCCTL

Represents cement materials with composition, properties, and binary data.
Converted from Java JPA entity to SQLAlchemy model.
"""

from typing import Optional
from sqlalchemy import Column, String, Float, LargeBinary, Text, Integer, Boolean
from pydantic import BaseModel, Field, field_validator, model_validator

from app.database.base import Base


class Cement(Base):
    """
    Cement model representing Portland cement materials.
    
    Contains cement composition data, particle size distributions,
    binary data files, and alkali characteristics.
    """
    
    __tablename__ = 'cement'
    
    # Primary key - auto-incrementing integer ID
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Cement name - unique but not primary key
    name = Column(String(64), nullable=False, unique=True)
    
    # Particle size distribution reference
    psd = Column(String(64), nullable=True)
    
    # Binary data columns (BLOB equivalents)
    pfc = Column(LargeBinary, nullable=True, doc="Phase fraction data")
    gif = Column(LargeBinary, nullable=True, doc="GIF image data")
    legend_gif = Column(LargeBinary, nullable=True, doc="Legend GIF image data")
    sil = Column(LargeBinary, nullable=True, doc="Silica data")
    c3s = Column(LargeBinary, nullable=True, doc="C3S phase data")
    c3a = Column(LargeBinary, nullable=True, doc="C3A phase data")
    n2o = Column(LargeBinary, nullable=True, doc="Na2O data")
    k2o = Column(LargeBinary, nullable=True, doc="K2O data")
    alu = Column(LargeBinary, nullable=True, doc="Aluminum data")
    txt = Column(LargeBinary, nullable=True, doc="Text data")
    xrd = Column(LargeBinary, nullable=True, doc="XRD data")
    inf = Column(LargeBinary, nullable=True, doc="Information data")
    c4f = Column(LargeBinary, nullable=True, doc="C4AF phase data")
    
    # Gypsum fractions (mass fractions)
    dihyd = Column(Float, nullable=True, doc="Dihydrate gypsum mass fraction")
    anhyd = Column(Float, nullable=True, doc="Anhydrite gypsum mass fraction")
    hemihyd = Column(Float, nullable=True, doc="Hemihydrate gypsum mass fraction")
    
    # Gypsum fractions (volume fractions)
    dihyd_volume_fraction = Column(Float, nullable=True, doc="Dihydrate gypsum volume fraction")
    anhyd_volume_fraction = Column(Float, nullable=True, doc="Anhydrite gypsum volume fraction")
    hemihyd_volume_fraction = Column(Float, nullable=True, doc="Hemihydrate gypsum volume fraction")
    
    # Alkali characteristics
    alkali_file = Column(String(64), nullable=True, default='lowalkali', 
                        doc="Alkali characteristics file reference")
    
    # Phase composition (mass fractions)
    c3s_mass_fraction = Column(Float, nullable=True, doc="C3S (Tricalcium Silicate) mass fraction")
    c2s_mass_fraction = Column(Float, nullable=True, doc="C2S (Dicalcium Silicate) mass fraction")
    c3a_mass_fraction = Column(Float, nullable=True, doc="C3A (Tricalcium Aluminate) mass fraction")
    c4af_mass_fraction = Column(Float, nullable=True, doc="C4AF (Tetracalcium Aluminoferrite) mass fraction")
    k2so4_mass_fraction = Column(Float, nullable=True, doc="K2SO4 (Potassium Sulfate) mass fraction")
    na2so4_mass_fraction = Column(Float, nullable=True, doc="Na2SO4 (Sodium Sulfate) mass fraction")
    
    # Phase composition (volume fractions)
    c3s_volume_fraction = Column(Float, nullable=True, doc="C3S (Tricalcium Silicate) volume fraction")
    c2s_volume_fraction = Column(Float, nullable=True, doc="C2S (Dicalcium Silicate) volume fraction")
    c3a_volume_fraction = Column(Float, nullable=True, doc="C3A (Tricalcium Aluminate) volume fraction")
    c4af_volume_fraction = Column(Float, nullable=True, doc="C4AF (Tetracalcium Aluminoferrite) volume fraction")
    k2so4_volume_fraction = Column(Float, nullable=True, doc="K2SO4 (Potassium Sulfate) volume fraction")
    na2so4_volume_fraction = Column(Float, nullable=True, doc="Na2SO4 (Sodium Sulfate) volume fraction")
    
    # Phase composition (surface area fractions)
    c3s_surface_fraction = Column(Float, nullable=True, doc="C3S (Tricalcium Silicate) surface area fraction")
    c2s_surface_fraction = Column(Float, nullable=True, doc="C2S (Dicalcium Silicate) surface area fraction")
    c3a_surface_fraction = Column(Float, nullable=True, doc="C3A (Tricalcium Aluminate) surface area fraction")
    c4af_surface_fraction = Column(Float, nullable=True, doc="C4AF (Tetracalcium Aluminoferrite) surface area fraction")
    k2so4_surface_fraction = Column(Float, nullable=True, doc="K2SO4 (Potassium Sulfate) surface area fraction")
    na2so4_surface_fraction = Column(Float, nullable=True, doc="Na2SO4 (Sodium Sulfate) surface area fraction")
    
    # Physical properties
    specific_gravity = Column(Float, nullable=True, default=3.15, doc="Specific gravity of cement")
    description = Column(Text, nullable=True, doc="Cement description")
    
    # Setting times removed per user request
    
    # Fineness properties
    blaine_fineness = Column(Float, nullable=True, doc="Blaine fineness (m²/kg)")
    
    # PSD parameters
    psd_mode = Column(String(64), nullable=True, doc="PSD mode (rosin_rammler, fuller, custom)")
    psd_d50 = Column(Float, nullable=True, doc="PSD D50 parameter (µm)")
    psd_n = Column(Float, nullable=True, doc="PSD n parameter")
    psd_dmax = Column(Float, nullable=True, doc="PSD Dmax parameter (µm)")
    psd_exponent = Column(Float, nullable=True, doc="PSD exponent parameter")
    psd_custom_points = Column(Text, nullable=True, doc="Custom PSD points (JSON)")
    
    # Additional UI fields
    source = Column(String(255), nullable=True, doc="Material source")
    notes = Column(String(1000), nullable=True, doc="Additional notes")
    immutable = Column(Boolean, nullable=False, default=False, doc="Whether this cement is read-only (original database cement)")
    
    def __repr__(self) -> str:
        """String representation of the cement."""
        return f"<Cement(name='{self.name}', psd='{self.psd}')>"
    
    def to_dict_extended(self) -> dict:
        """Convert to dictionary with binary data handling."""
        result = self.to_dict()
        
        # Handle binary fields - convert to base64 if needed
        binary_fields = [
            'pfc', 'gif', 'legend_gif', 'sil', 'c3s', 'c3a', 'n2o', 
            'k2o', 'alu', 'txt', 'xrd', 'inf', 'c4f'
        ]
        
        for field in binary_fields:
            value = result.get(field)
            if value is not None:
                # For now, just indicate presence of binary data
                result[field] = f"<binary_data:{len(value)}_bytes>"
        
        return result
    
    @property
    def has_phase_data(self) -> bool:
        """Check if cement has phase composition data."""
        return any([
            self.c3s_mass_fraction is not None,
            self.c2s_mass_fraction is not None,
            self.c3a_mass_fraction is not None,
            self.c4af_mass_fraction is not None
        ])
    
    @property
    def total_phase_fraction(self) -> Optional[float]:
        """Calculate total phase fraction if all values are present."""
        fractions = [
            self.c3s_mass_fraction, 
            self.c2s_mass_fraction, 
            self.c3a_mass_fraction, 
            self.c4af_mass_fraction
        ]
        valid_fractions = [f for f in fractions if f is not None]
        if len(valid_fractions) >= 3:  # Require at least 3 phases
            return sum(valid_fractions)
        return None
    
    @property
    def density(self) -> Optional[float]:
        """Calculate density from specific gravity (assuming water density = 1000 kg/m³)."""
        if self.specific_gravity is not None:
            return self.specific_gravity * 1000  # kg/m³
        return None
    
    @property
    def has_gypsum_data(self) -> bool:
        """Check if cement has gypsum fraction data."""
        return any([
            self.dihyd is not None,
            self.anhyd is not None,
            self.hemihyd is not None
        ])
    
    @property
    def total_gypsum_fraction(self) -> Optional[float]:
        """Calculate total gypsum fraction if all values are present."""
        fractions = [self.dihyd, self.anhyd, self.hemihyd]
        if all(f is not None for f in fractions):
            return sum(fractions)
        return None
    
    def validate_gypsum_fractions(self) -> bool:
        """Validate that gypsum fractions are reasonable (0-1 range)."""
        fractions = [self.dihyd, self.anhyd, self.hemihyd]
        valid_fractions = [f for f in fractions if f is not None]
        
        if not valid_fractions:
            return True  # No fractions to validate
        
        # Check individual fractions are in valid range
        if any(f < 0 or f > 1 for f in valid_fractions):
            return False
        
        # Check total doesn't exceed 1.0 if all are present
        if len(valid_fractions) == 3 and sum(valid_fractions) > 1.0:
            return False
        
        return True
    
    def validate_phase_fractions(self) -> bool:
        """Validate that phase fractions are reasonable (0-1 range and sum ≤ 1.0)."""
        fractions = [
            self.c3s_mass_fraction,
            self.c2s_mass_fraction, 
            self.c3a_mass_fraction,
            self.c4af_mass_fraction
        ]
        valid_fractions = [f for f in fractions if f is not None]
        
        if not valid_fractions:
            return True  # No fractions to validate
        
        # Check individual fractions are in valid range
        if any(f < 0 or f > 1 for f in valid_fractions):
            return False
        
        # Check total doesn't exceed 1.0 if we have significant data
        if len(valid_fractions) >= 3 and sum(valid_fractions) > 1.0:
            return False
        
        return True


class CementCreate(BaseModel):
    """Pydantic model for creating cement instances."""
    
    name: str = Field(..., max_length=64, description="Cement name (unique identifier)")
    psd: Optional[str] = Field(None, max_length=64, description="Particle size distribution reference")
    
    # Gypsum fractions (mass fractions)
    dihyd: Optional[float] = Field(None, ge=0.0, le=1.0, description="Dihydrate gypsum mass fraction")
    anhyd: Optional[float] = Field(None, ge=0.0, le=1.0, description="Anhydrite gypsum mass fraction")
    hemihyd: Optional[float] = Field(None, ge=0.0, le=1.0, description="Hemihydrate gypsum mass fraction")
    
    # Gypsum fractions (volume fractions)
    dihyd_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, description="Dihydrate gypsum volume fraction")
    anhyd_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, description="Anhydrite gypsum volume fraction")
    hemihyd_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, description="Hemihydrate gypsum volume fraction")
    
    # Alkali characteristics
    alkali_file: Optional[str] = Field('lowalkali', max_length=64, 
                                     description="Alkali characteristics file reference")
    
    # Phase composition (mass fractions)
    c3s_mass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                              description="C3S (Tricalcium Silicate) mass fraction")
    c2s_mass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                              description="C2S (Dicalcium Silicate) mass fraction")
    c3a_mass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                              description="C3A (Tricalcium Aluminate) mass fraction")
    c4af_mass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                               description="C4AF (Tetracalcium Aluminoferrite) mass fraction")
    k2so4_mass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                description="K2SO4 (Potassium Sulfate) mass fraction")
    na2so4_mass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                 description="Na2SO4 (Sodium Sulfate) mass fraction")
    
    # Phase composition (volume fractions)
    c3s_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                description="C3S (Tricalcium Silicate) volume fraction")
    c2s_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                description="C2S (Dicalcium Silicate) volume fraction")
    c3a_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                description="C3A (Tricalcium Aluminate) volume fraction")
    c4af_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                 description="C4AF (Tetracalcium Aluminoferrite) volume fraction")
    k2so4_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                  description="K2SO4 (Potassium Sulfate) volume fraction")
    na2so4_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                   description="Na2SO4 (Sodium Sulfate) volume fraction")
    
    # Phase composition (surface area fractions)
    c3s_surface_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                 description="C3S (Tricalcium Silicate) surface area fraction")
    c2s_surface_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                 description="C2S (Dicalcium Silicate) surface area fraction")
    c3a_surface_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                 description="C3A (Tricalcium Aluminate) surface area fraction")
    c4af_surface_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                  description="C4AF (Tetracalcium Aluminoferrite) surface area fraction")
    k2so4_surface_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                   description="K2SO4 (Potassium Sulfate) surface area fraction")
    na2so4_surface_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                    description="Na2SO4 (Sodium Sulfate) surface area fraction")
    
    # Physical properties
    specific_gravity: Optional[float] = Field(3.15, gt=0.0, le=5.0, 
                                            description="Specific gravity of cement")
    description: Optional[str] = Field(None, description="Cement description")
    
    # Setting times removed per user request
    
    # Fineness properties
    blaine_fineness: Optional[float] = Field(None, gt=0.0, description="Blaine fineness (m²/kg)")
    
    # PSD parameters
    psd_mode: Optional[str] = Field(None, max_length=64, description="PSD mode (rosin_rammler, fuller, custom)")
    psd_d50: Optional[float] = Field(None, gt=0.0, description="PSD D50 parameter (µm)")
    psd_n: Optional[float] = Field(None, gt=0.0, description="PSD n parameter")
    psd_dmax: Optional[float] = Field(None, gt=0.0, description="PSD Dmax parameter (µm)")
    psd_exponent: Optional[float] = Field(None, gt=0.0, description="PSD exponent parameter")
    psd_custom_points: Optional[str] = Field(None, description="Custom PSD points (JSON)")
    
    # Additional UI fields
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    immutable: Optional[bool] = Field(False, description="Whether this cement is read-only (original database cement)")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate cement name."""
        if not v or not v.strip():
            raise ValueError('Cement name cannot be empty')
        return v.strip()
    
    @field_validator('dihyd', 'anhyd', 'hemihyd')
    @classmethod
    def validate_gypsum_fractions(cls, v):
        """Validate individual gypsum fractions."""
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Gypsum fractions must be between 0 and 1')
        return v
    
    def validate_total_gypsum(self) -> bool:
        """Validate that total gypsum fractions don't exceed 1.0."""
        fractions = [self.dihyd, self.anhyd, self.hemihyd]
        valid_fractions = [f for f in fractions if f is not None]
        
        if len(valid_fractions) >= 2 and sum(valid_fractions) > 1.0:
            raise ValueError('Total gypsum fractions cannot exceed 1.0')
        
        return True
    
    @model_validator(mode='after')
    def validate_phase_fractions_total(self):
        """Validate that total phase fractions don't exceed 1.0."""
        fractions = [
            self.c3s_mass_fraction,
            self.c2s_mass_fraction,
            self.c3a_mass_fraction,
            self.c4af_mass_fraction
        ]
        valid_fractions = [f for f in fractions if f is not None]
        
        if len(valid_fractions) >= 3 and sum(valid_fractions) > 1.0:
            raise ValueError('Total phase fractions cannot exceed 1.0 (100%)')
        
        return self


class CementUpdate(BaseModel):
    """Pydantic model for updating cement instances."""
    
    name: Optional[str] = Field(None, max_length=64, description="Cement name (unique identifier)")
    psd: Optional[str] = Field(None, max_length=64, description="Particle size distribution reference")
    
    # Gypsum fractions (mass fractions)
    dihyd: Optional[float] = Field(None, ge=0.0, le=1.0, description="Dihydrate gypsum mass fraction")
    anhyd: Optional[float] = Field(None, ge=0.0, le=1.0, description="Anhydrite gypsum mass fraction")
    hemihyd: Optional[float] = Field(None, ge=0.0, le=1.0, description="Hemihydrate gypsum mass fraction")
    
    # Gypsum fractions (volume fractions)
    dihyd_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, description="Dihydrate gypsum volume fraction")
    anhyd_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, description="Anhydrite gypsum volume fraction")
    hemihyd_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, description="Hemihydrate gypsum volume fraction")
    
    # Alkali characteristics
    alkali_file: Optional[str] = Field(None, max_length=64, 
                                     description="Alkali characteristics file reference")
    
    # Phase composition (mass fractions)
    c3s_mass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                              description="C3S (Tricalcium Silicate) mass fraction")
    c2s_mass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                              description="C2S (Dicalcium Silicate) mass fraction")
    c3a_mass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                              description="C3A (Tricalcium Aluminate) mass fraction")
    c4af_mass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                               description="C4AF (Tetracalcium Aluminoferrite) mass fraction")
    k2so4_mass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                description="K2SO4 (Potassium Sulfate) mass fraction")
    na2so4_mass_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                 description="Na2SO4 (Sodium Sulfate) mass fraction")
    
    # Phase composition (volume fractions)
    c3s_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                description="C3S (Tricalcium Silicate) volume fraction")
    c2s_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                description="C2S (Dicalcium Silicate) volume fraction")
    c3a_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                description="C3A (Tricalcium Aluminate) volume fraction")
    c4af_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                 description="C4AF (Tetracalcium Aluminoferrite) volume fraction")
    k2so4_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                  description="K2SO4 (Potassium Sulfate) volume fraction")
    na2so4_volume_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                   description="Na2SO4 (Sodium Sulfate) volume fraction")
    
    # Phase composition (surface area fractions)
    c3s_surface_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                 description="C3S (Tricalcium Silicate) surface area fraction")
    c2s_surface_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                 description="C2S (Dicalcium Silicate) surface area fraction")
    c3a_surface_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                 description="C3A (Tricalcium Aluminate) surface area fraction")
    c4af_surface_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                  description="C4AF (Tetracalcium Aluminoferrite) surface area fraction")
    k2so4_surface_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                   description="K2SO4 (Potassium Sulfate) surface area fraction")
    na2so4_surface_fraction: Optional[float] = Field(None, ge=0.0, le=1.0, 
                                                    description="Na2SO4 (Sodium Sulfate) surface area fraction")
    
    # Physical properties
    specific_gravity: Optional[float] = Field(None, gt=0.0, le=5.0, 
                                            description="Specific gravity of cement")
    description: Optional[str] = Field(None, description="Cement description")
    
    # Setting times removed per user request
    
    # Fineness properties
    blaine_fineness: Optional[float] = Field(None, gt=0.0, description="Blaine fineness (m²/kg)")
    
    # PSD parameters
    psd_mode: Optional[str] = Field(None, max_length=64, description="PSD mode (rosin_rammler, fuller, custom)")
    psd_d50: Optional[float] = Field(None, gt=0.0, description="PSD D50 parameter (µm)")
    psd_n: Optional[float] = Field(None, gt=0.0, description="PSD n parameter")
    psd_dmax: Optional[float] = Field(None, gt=0.0, description="PSD Dmax parameter (µm)")
    psd_exponent: Optional[float] = Field(None, gt=0.0, description="PSD exponent parameter")
    psd_custom_points: Optional[str] = Field(None, description="Custom PSD points (JSON)")
    
    # Additional fields for UI
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    immutable: Optional[bool] = Field(None, description="Whether this cement is read-only (original database cement)")


class CementResponse(BaseModel):
    """Pydantic model for cement API responses."""
    
    name: str
    psd: Optional[str]
    dihyd: Optional[float]
    anhyd: Optional[float]
    hemihyd: Optional[float]
    alkali_file: Optional[str]
    
    # Phase composition
    c3s_mass_fraction: Optional[float]
    c2s_mass_fraction: Optional[float]
    c3a_mass_fraction: Optional[float]
    c4af_mass_fraction: Optional[float]
    
    # Physical properties
    specific_gravity: Optional[float]
    description: Optional[str]
    
    # Calculated properties
    has_phase_data: bool
    has_gypsum_data: bool
    total_gypsum_fraction: Optional[float]
    total_phase_fraction: Optional[float]
    density: Optional[float]
    
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True