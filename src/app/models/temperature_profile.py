#!/usr/bin/env python3
"""
Temperature Profile Database Model

Provides database storage for custom temperature profiles used in hydration simulations.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from app.database.base import Base


class TemperatureProfileDB(Base):
    """Database model for storing temperature profiles."""
    __tablename__ = 'temperature_profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    points_json = Column(Text, nullable=False)  # JSON array of {time_hours, temperature_celsius}
    is_predefined = Column(Boolean, default=False)  # True for built-in profiles, False for user-created
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<TemperatureProfileDB(id={self.id}, name='{self.name}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'points': json.loads(self.points_json) if self.points_json else [],
            'is_predefined': self.is_predefined,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_temperature_profile(cls, profile, is_predefined: bool = False):
        """Create database model from TemperatureProfile object."""
        from app.services.hydration_service import TemperatureProfile
        
        if not isinstance(profile, TemperatureProfile):
            raise ValueError("profile must be a TemperatureProfile object")
        
        # Convert points to JSON
        points_data = [
            {'time_hours': point.time_hours, 'temperature_celsius': point.temperature_celsius}
            for point in profile.points
        ]
        
        return cls(
            name=profile.name,
            description=profile.description,
            points_json=json.dumps(points_data),
            is_predefined=is_predefined
        )
    
    def to_temperature_profile(self):
        """Convert to TemperatureProfile object."""
        from app.services.hydration_service import TemperatureProfile, TemperaturePoint
        
        points_data = json.loads(self.points_json) if self.points_json else []
        points = [
            TemperaturePoint(
                time_hours=point['time_hours'],
                temperature_celsius=point['temperature_celsius']
            )
            for point in points_data
        ]
        
        return TemperatureProfile(
            name=self.name,
            description=self.description or "",
            points=points
        )
    
    def update_from_temperature_profile(self, profile):
        """Update this model from a TemperatureProfile object."""
        from app.services.hydration_service import TemperatureProfile
        
        if not isinstance(profile, TemperatureProfile):
            raise ValueError("profile must be a TemperatureProfile object")
        
        # Convert points to JSON
        points_data = [
            {'time_hours': point.time_hours, 'temperature_celsius': point.temperature_celsius}
            for point in profile.points
        ]
        
        self.name = profile.name
        self.description = profile.description
        self.points_json = json.dumps(points_data)
        self.updated_at = datetime.utcnow()