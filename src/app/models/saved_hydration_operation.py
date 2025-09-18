#!/usr/bin/env python3
"""
Saved Hydration Operation Model for VCCTL

Represents complete hydration operation configurations saved for reuse and modification.
Similar to SavedMixDesign but for hydration operations.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, Integer, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from app.database.base import Base


class SavedHydrationOperation(Base):
    """
    Saved Hydration Operation model representing complete hydration configurations.

    Contains all hydration parameters including source microstructure reference,
    curing conditions, time calibration, advanced settings, and database modifications.
    Auto-saved before each hydration execution to enable reuse and modification.
    """

    __tablename__ = 'saved_hydration_operations'

    # Primary key - auto-incrementing integer ID
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Operation identification
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Operation metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_template = Column(Boolean, nullable=False, default=False)

    # Source microstructure reference
    source_microstructure_name = Column(String(255), nullable=False)
    source_microstructure_path = Column(String(500), nullable=True)

    # Core simulation parameters
    max_time_hours = Column(Float, nullable=False, default=168.0)

    # Complete hydration configuration stored as JSON
    curing_conditions = Column(JSON, nullable=False, default=dict)
    time_calibration = Column(JSON, nullable=False, default=dict)
    advanced_settings = Column(JSON, nullable=False, default=dict)
    temperature_profile = Column(JSON, nullable=False, default=dict)
    database_modifications = Column(JSON, nullable=False, default=dict)

    # Additional UI state for complete restoration
    ui_parameters = Column(JSON, nullable=False, default=dict)

    # Notes for additional information
    notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SavedHydrationOperation(id={self.id}, name='{self.name}', source='{self.source_microstructure_name}')>"


# Pydantic models for API and validation
class SavedHydrationOperationBase(BaseModel):
    """Base model for saved hydration operation data."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    source_microstructure_name: str = Field(..., min_length=1, max_length=255)
    source_microstructure_path: Optional[str] = None
    max_time_hours: float = Field(default=168.0, ge=0.1, le=8760.0)  # 0.1 hour to 1 year
    curing_conditions: Dict[str, Any] = Field(default_factory=dict)
    time_calibration: Dict[str, Any] = Field(default_factory=dict)
    advanced_settings: Dict[str, Any] = Field(default_factory=dict)
    temperature_profile: Dict[str, Any] = Field(default_factory=dict)
    database_modifications: Dict[str, Any] = Field(default_factory=dict)
    ui_parameters: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None
    is_template: bool = False


class SavedHydrationOperationCreate(SavedHydrationOperationBase):
    """Model for creating a new saved hydration operation."""
    pass


class SavedHydrationOperationUpdate(BaseModel):
    """Model for updating an existing saved hydration operation."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    source_microstructure_name: Optional[str] = Field(None, min_length=1, max_length=255)
    source_microstructure_path: Optional[str] = None
    max_time_hours: Optional[float] = Field(None, ge=0.1, le=8760.0)
    curing_conditions: Optional[Dict[str, Any]] = None
    time_calibration: Optional[Dict[str, Any]] = None
    advanced_settings: Optional[Dict[str, Any]] = None
    temperature_profile: Optional[Dict[str, Any]] = None
    database_modifications: Optional[Dict[str, Any]] = None
    ui_parameters: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    is_template: Optional[bool] = None


class SavedHydrationOperationResponse(SavedHydrationOperationBase):
    """Model for saved hydration operation responses."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True