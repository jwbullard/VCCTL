#!/usr/bin/env python3
"""
Cement Model for VCCTL

Represents cement materials with composition, properties, and binary data.
Converted from Java JPA entity to SQLAlchemy model.
"""

from typing import Optional
from sqlalchemy import Column, String, Float, LargeBinary
from pydantic import BaseModel, Field, validator

from app.database.base import Base


class Cement(Base):
    """
    Cement model representing Portland cement materials.
    
    Contains cement composition data, particle size distributions,
    binary data files, and alkali characteristics.
    """
    
    __tablename__ = 'cement'
    
    # Override base model id with string primary key
    id = None
    
    # Primary key - cement name (unique identifier)
    name = Column(String(64), primary_key=True, nullable=False, unique=True)
    
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
    
    # Alkali characteristics
    alkali_file = Column(String(64), nullable=True, default='lowalkali', 
                        doc="Alkali characteristics file reference")
    
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
            self.c3s is not None,
            self.c3a is not None,
            self.c4f is not None
        ])
    
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


class CementCreate(BaseModel):
    """Pydantic model for creating cement instances."""
    
    name: str = Field(..., max_length=64, description="Cement name (unique identifier)")
    psd: Optional[str] = Field(None, max_length=64, description="Particle size distribution reference")
    
    # Gypsum fractions
    dihyd: Optional[float] = Field(None, ge=0.0, le=1.0, description="Dihydrate gypsum mass fraction")
    anhyd: Optional[float] = Field(None, ge=0.0, le=1.0, description="Anhydrite gypsum mass fraction")
    hemihyd: Optional[float] = Field(None, ge=0.0, le=1.0, description="Hemihydrate gypsum mass fraction")
    
    # Alkali characteristics
    alkali_file: Optional[str] = Field('lowalkali', max_length=64, 
                                     description="Alkali characteristics file reference")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate cement name."""
        if not v or not v.strip():
            raise ValueError('Cement name cannot be empty')
        return v.strip()
    
    @validator('dihyd', 'anhyd', 'hemihyd')
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


class CementUpdate(BaseModel):
    """Pydantic model for updating cement instances."""
    
    psd: Optional[str] = Field(None, max_length=64, description="Particle size distribution reference")
    
    # Gypsum fractions
    dihyd: Optional[float] = Field(None, ge=0.0, le=1.0, description="Dihydrate gypsum mass fraction")
    anhyd: Optional[float] = Field(None, ge=0.0, le=1.0, description="Anhydrite gypsum mass fraction")
    hemihyd: Optional[float] = Field(None, ge=0.0, le=1.0, description="Hemihydrate gypsum mass fraction")
    
    # Alkali characteristics
    alkali_file: Optional[str] = Field(None, max_length=64, 
                                     description="Alkali characteristics file reference")


class CementResponse(BaseModel):
    """Pydantic model for cement API responses."""
    
    name: str
    psd: Optional[str]
    dihyd: Optional[float]
    anhyd: Optional[float]
    hemihyd: Optional[float]
    alkali_file: Optional[str]
    has_phase_data: bool
    has_gypsum_data: bool
    total_gypsum_fraction: Optional[float]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True