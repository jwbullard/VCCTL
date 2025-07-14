#!/usr/bin/env python3
"""
Grading Model for VCCTL

Represents particle size distribution curves for aggregates.
Converted from Java JPA entity to SQLAlchemy model.
"""

from typing import Optional, List, Dict
import json
from sqlalchemy import Column, String, Float, LargeBinary, Enum, event
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
    
    # Override base model id with string primary key
    id = None
    
    # Primary key - grading name (unique identifier)
    name = Column(String(64), primary_key=True, nullable=False, unique=True)
    
    # Grading type (COARSE or FINE)
    type = Column(Enum(GradingType), nullable=True, doc="Grading type classification")
    
    # Binary grading data (sieve analysis)
    grading = Column(LargeBinary, nullable=True, doc="Binary grading data")
    
    # Maximum particle diameter
    max_diameter = Column(Float, nullable=True, doc="Maximum particle diameter (mm)")
    
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
        return self.grading is not None and len(self.grading) > 0
    
    def parse_grading_data(self) -> Optional[List[Dict[str, float]]]:
        """
        Parse grading data into sieve analysis format.
        
        Expected format: tab-separated values with sieve size and percent passing.
        
        Returns:
            List of dictionaries with 'sieve_size' and 'percent_passing' keys
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
                            percent_passing = float(parts[1])
                            sieve_data.append({
                                'sieve_size': sieve_size,
                                'percent_passing': percent_passing
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
            sieve_data: List of dictionaries with 'sieve_size' and 'percent_passing'
        """
        if not sieve_data:
            self.grading_text = None
            return
        
        lines = []
        for item in sieve_data:
            sieve_size = item.get('sieve_size', 0.0)
            percent_passing = item.get('percent_passing', 0.0)
            lines.append(f"{sieve_size}\t{percent_passing}")
        
        self.grading_text = '\n'.join(lines)
    
    def validate_grading_data(self) -> bool:
        """Validate that grading data is reasonable."""
        sieve_data = self.parse_grading_data()
        if not sieve_data:
            return True  # No data to validate
        
        # Check that percent passing values are between 0 and 100
        for item in sieve_data:
            percent = item.get('percent_passing', 0)
            if percent < 0 or percent > 100:
                return False
        
        # Check that sieve sizes are positive
        for item in sieve_data:
            size = item.get('sieve_size', 0)
            if size < 0:
                return False
        
        # Check that percent passing generally decreases with sieve size
        # (larger sieves should have higher percent passing)
        sorted_data = sorted(sieve_data, key=lambda x: x['sieve_size'], reverse=True)
        for i in range(1, len(sorted_data)):
            if sorted_data[i]['percent_passing'] > sorted_data[i-1]['percent_passing']:
                # Allow some tolerance for measurement errors
                if sorted_data[i]['percent_passing'] - sorted_data[i-1]['percent_passing'] > 5:
                    return False
        
        return True


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