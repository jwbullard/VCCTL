#!/usr/bin/env python3
"""
Aggregate Sieve Model for VCCTL

Represents sieve specifications for aggregate analysis.
Converted from Java JPA entity to SQLAlchemy model.
"""

from typing import Optional
from sqlalchemy import Column, String, Numeric, Index, Enum
from pydantic import BaseModel, Field, validator
import enum

from app.database.base import Base


class SieveType(str, enum.Enum):
    """Enumeration for sieve types."""
    COARSE = "COARSE"
    FINE = "FINE"


class AggregateSieve(Base):
    """
    Aggregate sieve model representing sieve specifications.
    
    Contains sieve size ranges and type classifications
    for aggregate particle size analysis.
    """
    
    __tablename__ = 'aggregate_sieve'
    
    # Override base model id with string primary key
    id = None
    
    # Primary key - sieve label (unique identifier)
    label = Column(String(64), primary_key=True, nullable=False, unique=True)
    
    # Size range in millimeters
    min_millimeters = Column(Numeric(6, 3), nullable=True, 
                           doc="Minimum opening size in millimeters")
    max_millimeters = Column(Numeric(6, 3), nullable=True,
                           doc="Maximum opening size in millimeters")
    
    # Sieve type (COARSE or FINE)
    type = Column(Enum(SieveType), nullable=True, doc="Sieve type classification")
    
    # Define table indexes
    __table_args__ = (
        Index('aggregate_sieve_type', 'type'),
    )
    
    def __repr__(self) -> str:
        """String representation of the aggregate sieve."""
        return f"<AggregateSieve(label='{self.label}', type={self.type})>"
    
    @property
    def is_coarse_sieve(self) -> bool:
        """Check if this is a coarse aggregate sieve."""
        return self.type == SieveType.COARSE
    
    @property
    def is_fine_sieve(self) -> bool:
        """Check if this is a fine aggregate sieve."""
        return self.type == SieveType.FINE
    
    @property
    def size_range(self) -> Optional[float]:
        """Calculate size range (max - min) in millimeters."""
        if self.min_millimeters is not None and self.max_millimeters is not None:
            return float(self.max_millimeters - self.min_millimeters)
        return None
    
    @property
    def average_size(self) -> Optional[float]:
        """Calculate average size ((max + min) / 2) in millimeters."""
        if self.min_millimeters is not None and self.max_millimeters is not None:
            return float((self.max_millimeters + self.min_millimeters) / 2)
        return None
    
    @property
    def is_standard_sieve(self) -> bool:
        """Check if this is a standard ASTM sieve size."""
        # Standard ASTM sieve sizes (opening in mm)
        standard_sizes = [
            0.075, 0.15, 0.3, 0.6, 1.18, 2.36, 4.75, 9.5, 
            12.5, 19.0, 25.0, 37.5, 50.0, 75.0, 100.0
        ]
        
        if self.max_millimeters is not None:
            # Check if max size matches any standard size (within tolerance)
            tolerance = 0.01  # 0.01 mm tolerance
            for standard_size in standard_sizes:
                if abs(float(self.max_millimeters) - standard_size) < tolerance:
                    return True
        
        return False
    
    def calculate_fraction_retained(self, material_passing: dict) -> float:
        """
        Calculate fraction retained on this sieve.
        
        Args:
            material_passing: Dictionary with sieve sizes as keys and 
                            percent passing as values
                            
        Returns:
            Fraction retained on this sieve (0.0 - 1.0)
        """
        if not material_passing or self.max_millimeters is None:
            return 0.0
        
        # Find the percent passing this sieve and the next larger sieve
        sieve_size = float(self.max_millimeters)
        
        # Get percent passing this sieve
        percent_passing_this = material_passing.get(sieve_size, 0.0)
        
        # Find next larger sieve
        larger_sieves = [size for size in material_passing.keys() if size > sieve_size]
        
        if larger_sieves:
            next_larger_size = min(larger_sieves)
            percent_passing_larger = material_passing.get(next_larger_size, 100.0)
        else:
            percent_passing_larger = 100.0  # No larger sieve, assume 100% passing
        
        # Fraction retained = (% passing larger sieve - % passing this sieve) / 100
        fraction_retained = (percent_passing_larger - percent_passing_this) / 100.0
        
        return max(0.0, min(1.0, fraction_retained))  # Clamp to [0, 1]
    
    def validate_size_range(self) -> bool:
        """Validate that size range is reasonable."""
        if self.min_millimeters is not None and self.max_millimeters is not None:
            # Max should be greater than min
            if self.max_millimeters <= self.min_millimeters:
                return False
            
            # Sizes should be positive
            if self.min_millimeters < 0 or self.max_millimeters < 0:
                return False
            
            # Range should be reasonable (not too large)
            if self.max_millimeters > 150.0:  # 150mm is very large for concrete aggregates
                return False
        
        return True


class AggregateSieveCreate(BaseModel):
    """Pydantic model for creating aggregate sieve instances."""
    
    label: str = Field(..., max_length=64, description="Sieve label (unique identifier)")
    min_millimeters: Optional[float] = Field(None, ge=0.0, description="Minimum size (mm)")
    max_millimeters: Optional[float] = Field(None, ge=0.0, description="Maximum size (mm)")
    type: Optional[SieveType] = Field(None, description="Sieve type (COARSE or FINE)")
    
    @validator('label')
    def validate_label(cls, v):
        """Validate sieve label."""
        if not v or not v.strip():
            raise ValueError('Sieve label cannot be empty')
        return v.strip()
    
    @validator('max_millimeters')
    def validate_max_size(cls, v, values):
        """Validate maximum size."""
        if v is not None:
            min_size = values.get('min_millimeters')
            if min_size is not None and v <= min_size:
                raise ValueError('Maximum size must be greater than minimum size')
            
            if v > 150.0:
                raise ValueError('Maximum size is unreasonably large for concrete aggregates')
        
        return v


class AggregateSieveUpdate(BaseModel):
    """Pydantic model for updating aggregate sieve instances."""
    
    min_millimeters: Optional[float] = Field(None, ge=0.0, description="Minimum size (mm)")
    max_millimeters: Optional[float] = Field(None, ge=0.0, description="Maximum size (mm)")
    type: Optional[SieveType] = Field(None, description="Sieve type (COARSE or FINE)")


class AggregateSieveResponse(BaseModel):
    """Pydantic model for aggregate sieve API responses."""
    
    label: str
    min_millimeters: Optional[float]
    max_millimeters: Optional[float]
    type: Optional[str]
    is_coarse_sieve: bool
    is_fine_sieve: bool
    size_range: Optional[float]
    average_size: Optional[float]
    is_standard_sieve: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True