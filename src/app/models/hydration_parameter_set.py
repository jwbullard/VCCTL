#!/usr/bin/env python3
"""
Hydration Parameter Set Model for VCCTL

Represents saved hydration simulation parameter configurations for quick reuse.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, Integer, Boolean, DateTime, JSON
from pydantic import BaseModel, Field, field_validator

from app.database.base import Base


class HydrationParameterSet(Base):
    """
    Hydration Parameter Set model representing saved hydration simulation configurations.
    
    Contains all hydration simulation parameters including curing conditions,
    time calibration, advanced settings, and database modifications.
    """
    
    __tablename__ = 'hydration_parameter_sets'
    
    # Primary key - auto-incrementing integer ID
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Parameter set identification
    name = Column(String(128), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Parameter set metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_template = Column(Boolean, nullable=False, default=False)
    
    # Core simulation parameters
    max_time_hours = Column(Float, nullable=False, default=168.0)
    
    # Curing conditions - stored as JSON for flexibility
    curing_conditions = Column(JSON, nullable=False, default=dict)
    
    # Time calibration settings
    time_calibration = Column(JSON, nullable=False, default=dict)
    
    # Advanced settings
    advanced_settings = Column(JSON, nullable=False, default=dict)
    
    # Database parameter modifications
    db_modifications = Column(JSON, nullable=False, default=dict)
    
    # Notes for additional information
    notes = Column(Text, nullable=True)
    
    def __repr__(self) -> str:
        return f"<HydrationParameterSet(id={self.id}, name='{self.name}', created_at={self.created_at})>"


# Pydantic models for API and validation
class HydrationParameterSetBase(BaseModel):
    """Base model for hydration parameter set data."""
    name: str = Field(..., min_length=1, max_length=128)
    description: Optional[str] = None
    max_time_hours: float = Field(default=168.0, ge=0.1, le=8760.0)  # 0.1 hour to 1 year
    curing_conditions: Dict[str, Any] = Field(default_factory=dict)
    time_calibration: Dict[str, Any] = Field(default_factory=dict)
    advanced_settings: Dict[str, Any] = Field(default_factory=dict)
    db_modifications: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    is_template: bool = False


class HydrationParameterSetCreate(HydrationParameterSetBase):
    """Model for creating a new hydration parameter set."""
    pass


class HydrationParameterSetUpdate(BaseModel):
    """Model for updating an existing hydration parameter set."""
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    max_time_hours: Optional[float] = Field(None, ge=0.1, le=8760.0)
    curing_conditions: Optional[Dict[str, Any]] = None
    time_calibration: Optional[Dict[str, Any]] = None
    advanced_settings: Optional[Dict[str, Any]] = None
    db_modifications: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    is_template: Optional[bool] = None


class HydrationParameterSetResponse(HydrationParameterSetBase):
    """Model for hydration parameter set responses."""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True