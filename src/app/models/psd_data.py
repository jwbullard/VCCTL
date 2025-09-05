#!/usr/bin/env python3
"""
PSD Data Model for VCCTL

Unified Particle Size Distribution model that can be embedded in all material types.
This ensures consistent PSD handling across all materials (cement, filler, fly_ash, limestone, silica_fume, slag).
"""

from typing import Optional
from sqlalchemy import Column, String, Float, Integer, Text, CheckConstraint
from pydantic import BaseModel, Field, field_validator

from app.database.base import Base


class PSDData(Base):
    """
    Unified Particle Size Distribution model.
    
    Contains all PSD-related fields that can be shared across all material types.
    This eliminates duplication and ensures consistency in PSD handling.
    """
    
    __tablename__ = 'psd_data'
    
    # Use integer ID as primary key (inherited from Base)
    
    # Basic PSD reference
    psd_reference = Column(String(64), nullable=True, default='default',
                          doc="Particle size distribution reference name")
    
    # Custom PSD data points (JSON format)
    psd_custom_points = Column(Text, nullable=True,
                              doc="Custom PSD points stored as JSON")
    
    # PSD Mode/Type - using string for consistency with cement model
    psd_mode = Column(String(64), nullable=True, default='log_normal',
                     doc="PSD mode (rosin_rammler, log_normal, fuller, custom)")
    
    # Rosin-Rammler parameters
    psd_d50 = Column(Float, nullable=True,
                    doc="D50 particle size (μm) for Rosin-Rammler distribution")
    psd_n = Column(Float, nullable=True,
                  doc="Distribution parameter for Rosin-Rammler")
    psd_dmax = Column(Float, nullable=True,
                     doc="Maximum particle size (μm)")
    
    # Log-normal parameters
    psd_median = Column(Float, nullable=True,
                       doc="Median particle size (μm) for log-normal distribution")
    psd_spread = Column(Float, nullable=True,
                       doc="Distribution spread parameter for log-normal")
    
    # Fuller-Thompson parameter
    psd_exponent = Column(Float, nullable=True,
                         doc="Exponent parameter for Fuller-Thompson distribution")
    
    # Diameter percentile parameters (for consistency across all materials)
    diameter_percentile_10 = Column(Float, nullable=True,
                                   doc="10th percentile diameter (μm)")
    diameter_percentile_50 = Column(Float, nullable=True,
                                   doc="50th percentile diameter (μm)")
    diameter_percentile_90 = Column(Float, nullable=True,
                                   doc="90th percentile diameter (μm)")
    
    # Constraints for data validation
    __table_args__ = (
        CheckConstraint('psd_d50 >= 0 AND psd_d50 <= 1000', name='check_psd_d50_range'),
        CheckConstraint('psd_n >= 0 AND psd_n <= 10', name='check_psd_n_range'),
        CheckConstraint('psd_dmax >= 0 AND psd_dmax <= 1000', name='check_psd_dmax_range'),
        CheckConstraint('psd_median >= 0 AND psd_median <= 1000', name='check_psd_median_range'),
        CheckConstraint('psd_spread >= 0 AND psd_spread <= 10', name='check_psd_spread_range'),
        CheckConstraint('psd_exponent >= 0 AND psd_exponent <= 2', name='check_psd_exponent_range'),
        CheckConstraint('diameter_percentile_10 >= 0 AND diameter_percentile_10 <= 1000', 
                       name='check_diameter_p10_range'),
        CheckConstraint('diameter_percentile_50 >= 0 AND diameter_percentile_50 <= 1000', 
                       name='check_diameter_p50_range'),
        CheckConstraint('diameter_percentile_90 >= 0 AND diameter_percentile_90 <= 1000', 
                       name='check_diameter_p90_range'),
    )
    
    def __repr__(self) -> str:
        """String representation of PSD data."""
        return f"<PSDData(mode='{self.psd_mode}', reference='{self.psd_reference}')>"
    
    def get_distribution_summary(self) -> str:
        """Get a human-readable summary of the PSD configuration."""
        if self.psd_mode == 'rosin_rammler' and self.psd_d50:
            return f"Rosin-Rammler (D50={self.psd_d50:.1f}μm, n={self.psd_n or 1.0:.1f})"
        elif self.psd_mode == 'log_normal' and self.psd_median:
            return f"Log-Normal (median={self.psd_median:.1f}μm, spread={self.psd_spread or 1.0:.1f})"
        elif self.psd_mode == 'fuller' and self.psd_exponent:
            return f"Fuller-Thompson (exponent={self.psd_exponent:.2f})"
        elif self.psd_mode == 'custom':
            return "Custom Distribution"
        else:
            return f"Default ({self.psd_reference or 'none'})"
    
    def validate_consistency(self) -> bool:
        """Validate that PSD parameters are consistent with the selected mode."""
        if self.psd_mode == 'rosin_rammler':
            return self.psd_d50 is not None and self.psd_n is not None
        elif self.psd_mode == 'log_normal':
            return self.psd_median is not None and self.psd_spread is not None
        elif self.psd_mode == 'fuller':
            return self.psd_exponent is not None
        elif self.psd_mode == 'custom':
            return self.psd_custom_points is not None
        return True  # Default mode doesn't require specific parameters


class PSDDataCreate(BaseModel):
    """Pydantic model for creating PSD data."""
    
    psd_reference: Optional[str] = Field('default', max_length=64, 
                                        description="PSD reference name")
    psd_custom_points: Optional[str] = Field(None, 
                                           description="Custom PSD points as JSON")
    psd_mode: Optional[str] = Field('log_normal', max_length=64,
                                   description="PSD mode (rosin_rammler, log_normal, fuller, custom)")
    
    # Rosin-Rammler parameters
    psd_d50: Optional[float] = Field(None, ge=0.0, le=1000.0,
                                    description="D50 particle size (μm)")
    psd_n: Optional[float] = Field(None, ge=0.0, le=10.0,
                                  description="Distribution parameter")
    psd_dmax: Optional[float] = Field(None, ge=0.0, le=1000.0,
                                     description="Maximum particle size (μm)")
    
    # Log-normal parameters
    psd_median: Optional[float] = Field(None, ge=0.0, le=1000.0,
                                       description="Median particle size (μm)")
    psd_spread: Optional[float] = Field(None, ge=0.0, le=10.0,
                                       description="Distribution spread parameter")
    
    # Fuller-Thompson parameter
    psd_exponent: Optional[float] = Field(None, ge=0.0, le=2.0,
                                         description="Exponent parameter")
    
    # Diameter percentiles
    diameter_percentile_10: Optional[float] = Field(None, ge=0.0, le=1000.0,
                                                   description="10th percentile diameter (μm)")
    diameter_percentile_50: Optional[float] = Field(None, ge=0.0, le=1000.0,
                                                   description="50th percentile diameter (μm)")
    diameter_percentile_90: Optional[float] = Field(None, ge=0.0, le=1000.0,
                                                   description="90th percentile diameter (μm)")
    
    @field_validator('psd_mode')
    @classmethod
    def validate_psd_mode(cls, v):
        """Validate PSD mode."""
        valid_modes = ['rosin_rammler', 'log_normal', 'fuller', 'custom', 'default']
        if v and v not in valid_modes:
            raise ValueError(f'PSD mode must be one of: {valid_modes}')
        return v


class PSDDataUpdate(BaseModel):
    """Pydantic model for updating PSD data."""
    
    psd_reference: Optional[str] = Field(None, max_length=64,
                                        description="PSD reference name")
    psd_custom_points: Optional[str] = Field(None,
                                           description="Custom PSD points as JSON")
    psd_mode: Optional[str] = Field(None, max_length=64,
                                   description="PSD mode")
    
    # All parameters are optional for updates
    psd_d50: Optional[float] = Field(None, ge=0.0, le=1000.0,
                                    description="D50 particle size (μm)")
    psd_n: Optional[float] = Field(None, ge=0.0, le=10.0,
                                  description="Distribution parameter")
    psd_dmax: Optional[float] = Field(None, ge=0.0, le=1000.0,
                                     description="Maximum particle size (μm)")
    psd_median: Optional[float] = Field(None, ge=0.0, le=1000.0,
                                       description="Median particle size (μm)")
    psd_spread: Optional[float] = Field(None, ge=0.0, le=10.0,
                                       description="Distribution spread parameter")
    psd_exponent: Optional[float] = Field(None, ge=0.0, le=2.0,
                                         description="Exponent parameter")
    diameter_percentile_10: Optional[float] = Field(None, ge=0.0, le=1000.0,
                                                   description="10th percentile diameter (μm)")
    diameter_percentile_50: Optional[float] = Field(None, ge=0.0, le=1000.0,
                                                   description="50th percentile diameter (μm)")
    diameter_percentile_90: Optional[float] = Field(None, ge=0.0, le=1000.0,
                                                   description="90th percentile diameter (μm)")


class PSDDataResponse(BaseModel):
    """Pydantic model for PSD data API responses."""
    
    id: int
    psd_reference: Optional[str]
    psd_custom_points: Optional[str]
    psd_mode: Optional[str]
    psd_d50: Optional[float]
    psd_n: Optional[float]
    psd_dmax: Optional[float]
    psd_median: Optional[float]
    psd_spread: Optional[float]
    psd_exponent: Optional[float]
    diameter_percentile_10: Optional[float]
    diameter_percentile_50: Optional[float]
    diameter_percentile_90: Optional[float]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True