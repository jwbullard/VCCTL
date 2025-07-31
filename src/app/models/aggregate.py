#!/usr/bin/env python3
"""
Aggregate Model for VCCTL

Represents aggregate materials with physical and mechanical properties.
Converted from Java JPA entity to SQLAlchemy model.
"""

from typing import Optional
from sqlalchemy import Column, String, Float, Integer, LargeBinary, Index
from pydantic import BaseModel, Field, field_validator, model_validator

from app.database.base import Base


class Aggregate(Base):
    """
    Aggregate model representing coarse and fine aggregates.
    
    Contains aggregate properties including mechanical characteristics,
    thermal properties, and binary data for images and analysis.
    """
    
    __tablename__ = 'aggregate'
    
    # Override base model id with string primary key
    id = None
    
    # Primary key - display name (unique identifier)
    display_name = Column(String(64), primary_key=True, nullable=False, unique=True)
    
    # Name for internal reference (indexed)
    name = Column(String(64), nullable=True, default='')
    
    # Aggregate type (coarse=1, fine=2, etc.)
    type = Column(Integer, nullable=True, doc="Aggregate type classification")
    
    # Physical properties
    specific_gravity = Column(Float, nullable=True, default=2.65,
                            doc="Specific gravity of aggregate")
    
    # Mechanical properties
    bulk_modulus = Column(Float, nullable=True,
                         doc="Bulk modulus (GPa)")
    shear_modulus = Column(Float, nullable=True,
                          doc="Shear modulus (GPa)")
    
    # Thermal properties
    conductivity = Column(Float, nullable=True, default=0.0,
                         doc="Thermal conductivity (W/m·K)")
    
    # Binary data columns
    image = Column(LargeBinary, nullable=True, doc="Aggregate image data")
    txt = Column(LargeBinary, nullable=True, doc="Text analysis data")
    inf = Column(LargeBinary, nullable=True, doc="Information data")
    shape_stats = Column(LargeBinary, nullable=True, doc="Shape statistics data")
    
    # Additional UI fields
    source = Column(String(255), nullable=True, doc="Material source")
    description = Column(String(1000), nullable=True, doc="Basic description")
    properties_description = Column(String(1000), nullable=True, doc="Properties tab description")
    notes = Column(String(1000), nullable=True, doc="Additional notes")
    immutable = Column(Integer, nullable=True, default=0, doc="Immutable flag (1=true, 0=false)")
    
    # Define table indexes
    __table_args__ = (
        Index('aggregate_name_index', 'name'),
    )
    
    def __repr__(self) -> str:
        """String representation of the aggregate."""
        return f"<Aggregate(display_name='{self.display_name}', type={self.type})>"
    
    @property
    def is_coarse_aggregate(self) -> bool:
        """Check if this is a coarse aggregate (type 1)."""
        return self.type == 1
    
    @property
    def is_fine_aggregate(self) -> bool:
        """Check if this is a fine aggregate (type 2)."""
        return self.type == 2
    
    @property
    def has_mechanical_properties(self) -> bool:
        """Check if aggregate has mechanical property data."""
        return any([
            self.bulk_modulus is not None,
            self.shear_modulus is not None
        ])
    
    @property
    def has_shape_data(self) -> bool:
        """Check if aggregate has shape analysis data."""
        return self.shape_stats is not None
    
    @property
    def elastic_modulus(self) -> Optional[float]:
        """Calculate elastic modulus from bulk and shear moduli."""
        if self.bulk_modulus is not None and self.shear_modulus is not None:
            # E = 9KG/(3K + G) where K = bulk modulus, G = shear modulus
            k, g = self.bulk_modulus, self.shear_modulus
            if k > 0 and g > 0:
                return (9 * k * g) / (3 * k + g)
        return None
    
    @property
    def poisson_ratio(self) -> Optional[float]:
        """Calculate Poisson's ratio from bulk and shear moduli."""
        if self.bulk_modulus is not None and self.shear_modulus is not None:
            # ν = (3K - 2G)/(6K + 2G) where K = bulk modulus, G = shear modulus
            k, g = self.bulk_modulus, self.shear_modulus
            if k > 0 and g > 0 and (6 * k + 2 * g) != 0:
                return (3 * k - 2 * g) / (6 * k + 2 * g)
        return None
    
    def validate_mechanical_properties(self) -> bool:
        """Validate that mechanical properties are reasonable."""
        if self.bulk_modulus is not None and self.bulk_modulus < 0:
            return False
        if self.shear_modulus is not None and self.shear_modulus < 0:
            return False
        if self.specific_gravity is not None and self.specific_gravity <= 0:
            return False
        return True


class AggregateCreate(BaseModel):
    """Pydantic model for creating aggregate instances."""
    
    display_name: str = Field(..., max_length=64, description="Aggregate display name")
    name: Optional[str] = Field('', max_length=64, description="Internal name")
    type: Optional[int] = Field(None, description="Aggregate type (1=coarse, 2=fine)")
    specific_gravity: Optional[float] = Field(2.65, gt=0.0, description="Specific gravity")
    bulk_modulus: Optional[float] = Field(None, ge=0.0, description="Bulk modulus (GPa)")
    shear_modulus: Optional[float] = Field(None, ge=0.0, description="Shear modulus (GPa)")
    conductivity: Optional[float] = Field(0.0, ge=0.0, description="Thermal conductivity")
    
    # Binary data fields
    image: Optional[bytes] = Field(None, description="Aggregate image data")
    txt: Optional[bytes] = Field(None, description="Text analysis data")
    inf: Optional[bytes] = Field(None, description="Information data")
    shape_stats: Optional[bytes] = Field(None, description="Shape statistics data")
    
    # Additional UI fields
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    description: Optional[str] = Field(None, max_length=1000, description="Basic description")
    properties_description: Optional[str] = Field(None, max_length=1000, description="Properties tab description")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    immutable: Optional[bool] = Field(False, description="Immutable flag")
    
    @field_validator('display_name')
    @classmethod
    def validate_display_name(cls, v):
        """Validate aggregate display name."""
        if not v or not v.strip():
            raise ValueError('Aggregate display name cannot be empty')
        return v.strip()
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Validate aggregate type."""
        if v is not None and v not in [1, 2]:
            raise ValueError('Aggregate type must be 1 (coarse) or 2 (fine)')
        return v


class AggregateUpdate(BaseModel):
    """Pydantic model for updating aggregate instances."""
    
    name: Optional[str] = Field(None, max_length=64, description="Internal name")
    type: Optional[int] = Field(None, description="Aggregate type (1=coarse, 2=fine)")
    specific_gravity: Optional[float] = Field(None, gt=0.0, description="Specific gravity")
    bulk_modulus: Optional[float] = Field(None, ge=0.0, description="Bulk modulus (GPa)")
    shear_modulus: Optional[float] = Field(None, ge=0.0, description="Shear modulus (GPa)")
    conductivity: Optional[float] = Field(None, ge=0.0, description="Thermal conductivity")
    
    # Additional fields for UI
    source: Optional[str] = Field(None, max_length=255, description="Material source")
    description: Optional[str] = Field(None, max_length=1000, description="Basic description")
    properties_description: Optional[str] = Field(None, max_length=1000, description="Properties tab description")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    immutable: Optional[bool] = Field(False, description="Immutable flag")


class AggregateResponse(BaseModel):
    """Pydantic model for aggregate API responses."""
    
    display_name: str
    name: Optional[str]
    type: Optional[int]
    specific_gravity: Optional[float]
    bulk_modulus: Optional[float]
    shear_modulus: Optional[float]
    conductivity: Optional[float]
    is_coarse_aggregate: bool
    is_fine_aggregate: bool
    has_mechanical_properties: bool
    has_shape_data: bool
    elastic_modulus: Optional[float]
    poisson_ratio: Optional[float]
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True