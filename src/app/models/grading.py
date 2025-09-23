#!/usr/bin/env python3
"""
Grading Model for VCCTL

Represents particle size distribution curves for aggregates.
Converted from Java JPA entity to SQLAlchemy model.
"""

from typing import Optional, List, Dict
import json
from datetime import datetime
from sqlalchemy import Column, String, Float, LargeBinary, Enum, event, JSON, DateTime, Integer, Text
from pydantic import BaseModel, Field, field_validator, model_validator
import enum

from app.database.base import Base


class GradingType(str, enum.Enum):
    """Enumeration for grading types."""
    COARSE = "COARSE"
    FINE = "FINE"


class Grading(Base):
    """
    Grading model representing particle size distribution curves.
    
    Contains grading data for coarse and fine aggregates,
    including sieve analysis data and maximum particle diameter.
    """
    
    __tablename__ = 'grading'
    
    # Override the inherited id column - don't use it for this model
    id = None
    
    # Use name as primary key to match existing database table structure
    name = Column(String(64), primary_key=True, doc="User-defined grading name")
    
    # Grading type (COARSE or FINE)
    type = Column(Enum(GradingType), nullable=True, doc="Grading type classification")
    
    # Legacy binary grading data (kept for backward compatibility)
    grading = Column(LargeBinary, nullable=True, doc="Legacy binary grading data")
    
    # NEW: JSON field for structured sieve data
    sieve_data = Column(JSON, nullable=True, doc="Sieve analysis data as [(size_mm, percent_retained), ...]")
    
    # Maximum particle diameter
    max_diameter = Column(Float, nullable=True, doc="Maximum particle diameter (mm)")
    
    # NEW: Additional metadata fields
    description = Column(Text, nullable=True, doc="User description of the grading")
    aggregate_id = Column(Integer, nullable=True, doc="Reference to associated aggregate material")
    is_standard = Column(Integer, nullable=True, default=0, doc="Flag for standard/system gradings (1=true)")
    
    # NEW: Timestamps
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow, doc="Creation timestamp")
    modified_at = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow, doc="Last modification timestamp")
    
    def __repr__(self) -> str:
        """String representation of the grading."""
        return f"<Grading(name='{self.name}', type={self.type})>"
    
    @property
    def grading_text(self) -> Optional[str]:
        """Get grading data as text string."""
        if self.grading:
            try:
                # Decode binary data to text
                text = self.grading.decode('utf-8')
                # Process escape sequences
                return text.replace('\\t', '\t').replace('\\n', '\n')
            except (UnicodeDecodeError, AttributeError):
                return None
        return None
    
    @grading_text.setter
    def grading_text(self, value: str):
        """Set grading data from text string."""
        if value:
            self.grading = value.encode('utf-8')
        else:
            self.grading = None
    
    @property
    def is_coarse_grading(self) -> bool:
        """Check if this is a coarse aggregate grading."""
        return self.type == GradingType.COARSE
    
    @property
    def is_fine_grading(self) -> bool:
        """Check if this is a fine aggregate grading."""
        return self.type == GradingType.FINE
    
    @property
    def has_grading_data(self) -> bool:
        """Check if grading has sieve analysis data."""
        return (self.sieve_data is not None and len(self.sieve_data) > 0) or (self.grading is not None and len(self.grading) > 0)
    
    @property
    def is_system_grading(self) -> bool:
        """Check if this is a system/standard grading."""
        return self.is_standard == 1
    
    @property
    def sieve_points(self) -> List[tuple]:
        """Get sieve data as list of (size_mm, percent_retained) tuples."""
        if self.sieve_data:
            return [tuple(point) for point in self.sieve_data]
        return []
    
    @sieve_points.setter
    def sieve_points(self, points: List[tuple]):
        """Set sieve data from list of (size_mm, percent_retained) tuples."""
        if points:
            self.sieve_data = [list(point) for point in points]
            # Update max diameter from largest sieve size
            self.max_diameter = max(point[0] for point in points) if points else None
        else:
            self.sieve_data = None
            self.max_diameter = None
    
    def parse_grading_data(self) -> Optional[List[Dict[str, float]]]:
        """
        Parse grading data into sieve analysis format.
        
        Expected format: tab-separated values with sieve size and percent passing.
        
        Returns:
            List of dictionaries with 'sieve_size' and 'percent_retained' keys
        """
        if not self.grading_text:
            return None
        
        try:
            lines = self.grading_text.strip().split('\n')
            sieve_data = []
            
            for line in lines:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        try:
                            sieve_size = float(parts[0])
                            percent_retained = float(parts[1])
                            sieve_data.append({
                                'sieve_size': sieve_size,
                                'percent_retained': percent_retained
                            })
                        except ValueError:
                            continue  # Skip invalid lines
            
            return sieve_data if sieve_data else None
            
        except Exception:
            return None
    
    def set_grading_data(self, sieve_data: List[Dict[str, float]]):
        """
        Set grading data from sieve analysis format.

        Args:
            sieve_data: List of dictionaries with 'sieve_size' and 'percent_retained'
        """
        if not sieve_data:
            self.grading_text = None
            return
        
        lines = []
        for item in sieve_data:
            sieve_size = item.get('sieve_size', 0.0)
            percent_retained = item.get('percent_retained', 0.0)
            lines.append(f"{sieve_size}\t{percent_retained}")
        
        self.grading_text = '\n'.join(lines)
    
    def validate_grading_data(self) -> bool:
        """Validate that grading data is reasonable."""
        sieve_data = self.parse_grading_data()
        if not sieve_data:
            return True  # No data to validate
        
        # Check that percent passing values are between 0 and 100
        for item in sieve_data:
            percent = item.get('percent_retained', 0)
            if percent < 0 or percent > 100:
                return False
        
        # Check that sieve sizes are positive
        for item in sieve_data:
            size = item.get('sieve_size', 0)
            if size < 0:
                return False
        
        # Check that percent retained values are reasonable
        # (no specific monotonic requirement for individual retained percentages)
        sorted_data = sorted(sieve_data, key=lambda x: x['sieve_size'], reverse=True)
        for i in range(1, len(sorted_data)):
            if sorted_data[i]['percent_retained'] > sorted_data[i-1]['percent_retained']:
                # Allow normal variations in percent retained
                if sorted_data[i]['percent_retained'] - sorted_data[i-1]['percent_retained'] > 100:
                    return False
        
        return True
    
    def get_sieve_data(self) -> Optional[List[Dict[str, float]]]:
        """
        Get sieve data in dictionary format from JSON field.
        
        Returns:
            List of dictionaries with 'sieve_size' and 'percent_retained' keys
        """
        if not self.sieve_data:
            return None
        
        result = []
        for point in self.sieve_data:
            if len(point) >= 2:
                result.append({
                    'sieve_size': float(point[0]),
                    'percent_retained': float(point[1])
                })
        
        return result if result else None
    
    def set_sieve_data(self, sieve_data: List[Dict[str, float]]):
        """
        Set sieve data from dictionary format to JSON field.
        
        Args:
            sieve_data: List of dictionaries with 'sieve_size' and 'percent_retained'
        """
        if not sieve_data:
            self.sieve_data = None
            self.max_diameter = None
            return
        
        # Convert to [size, percent] pairs
        points = []
        for item in sieve_data:
            size = float(item.get('sieve_size', 0.0))
            percent = float(item.get('percent_retained', 0.0))
            points.append([size, percent])
        
        self.sieve_data = points
        # Update max diameter
        self.max_diameter = max(point[0] for point in points) if points else None
        
        # Update modified timestamp
        self.modified_at = datetime.utcnow()
    
    def to_gdg_format(self) -> str:
        """
        Convert sieve data to .gdg file format.
        
        Returns:
            Tab-delimited string: "size_mm\tpercent_retained\n..."
        """
        if not self.sieve_data:
            return ""
        
        lines = []
        # Sort by sieve size (largest first for standard format)
        sorted_points = sorted(self.sieve_data, key=lambda x: x[0], reverse=True)
        
        for point in sorted_points:
            size_mm = point[0]
            percent_retained = point[1]
            lines.append(f"{size_mm}\t{percent_retained}")
        
        return '\n'.join(lines)
    
    @classmethod
    def from_gdg_format(cls, gdg_content: str, name: str, grading_type: GradingType, 
                       description: str = None) -> 'Grading':
        """
        Create Grading instance from .gdg file content.
        
        Args:
            gdg_content: Tab-delimited content "size\tpercent\nsize\tpercent..."
            name: Name for the grading
            grading_type: FINE or COARSE
            description: Optional description
            
        Returns:
            Grading instance
        """
        grading = cls(
            name=name,
            type=grading_type,
            description=description
        )
        
        if not gdg_content.strip():
            return grading
        
        # Parse content into sieve data
        points = []
        lines = gdg_content.strip().split('\n')
        
        for line in lines:
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2:
                    try:
                        size = float(parts[0])
                        percent = float(parts[1])
                        points.append([size, percent])
                    except ValueError:
                        continue  # Skip invalid lines
        
        if points:
            grading.sieve_data = points
            grading.max_diameter = max(point[0] for point in points)
        
        return grading


# Event listener to set grading_text after loading from database
@event.listens_for(Grading, 'load')
def set_grading_text_on_load(target, context):
    """Set grading_text property when loading from database."""
    # This ensures grading_text is available after loading
    if hasattr(target, 'grading') and target.grading:
        # The property getter will handle the conversion
        pass


class GradingCreate(BaseModel):
    """Pydantic model for creating grading instances."""
    
    name: str = Field(..., max_length=64, description="Grading name (unique identifier)")
    type: Optional[GradingType] = Field(None, description="Grading type (COARSE or FINE)")
    grading_text: Optional[str] = Field(None, description="Grading data as text")
    max_diameter: Optional[float] = Field(None, gt=0.0, description="Maximum diameter (mm)")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate grading name."""
        if not v or not v.strip():
            raise ValueError('Grading name cannot be empty')
        return v.strip()
    
    @field_validator('max_diameter')
    @classmethod
    def validate_max_diameter(cls, v):
        """Validate maximum diameter."""
        if v is not None and v <= 0:
            raise ValueError('Maximum diameter must be positive')
        return v


class GradingUpdate(BaseModel):
    """Pydantic model for updating grading instances."""
    
    type: Optional[GradingType] = Field(None, description="Grading type")
    grading_text: Optional[str] = Field(None, description="Grading data as text")
    max_diameter: Optional[float] = Field(None, gt=0.0, description="Maximum diameter (mm)")


class GradingResponse(BaseModel):
    """Pydantic model for grading API responses."""
    
    name: str
    type: Optional[str]
    grading_text: Optional[str]
    max_diameter: Optional[float]
    is_coarse_grading: bool
    is_fine_grading: bool
    has_grading_data: bool
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True