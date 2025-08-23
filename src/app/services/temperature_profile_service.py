#!/usr/bin/env python3
"""
Temperature Profile Service

Manages temperature profiles for hydration simulations, including database storage,
retrieval, and integration with predefined profiles.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.exc import IntegrityError

from app.services.base_service import BaseService, ServiceError, ValidationError
from app.models.temperature_profile import TemperatureProfileDB
from app.services.hydration_service import TemperatureProfile, TemperaturePoint


class TemperatureProfileService(BaseService):
    """Service for managing temperature profiles."""
    
    def __init__(self, db_service):
        super().__init__(TemperatureProfileDB, db_service)
        self.logger = logging.getLogger(__name__)
    
    def save_profile(self, profile: TemperatureProfile, overwrite: bool = False) -> TemperatureProfileDB:
        """
        Save a temperature profile to the database.
        
        Args:
            profile: TemperatureProfile object to save
            overwrite: If True, overwrites existing profile with same name
            
        Returns:
            Saved TemperatureProfileDB object
            
        Raises:
            ValidationError: If profile is invalid
            ServiceError: If save operation fails
        """
        try:
            # Validate profile
            if not profile.name or not profile.name.strip():
                raise ValidationError("Profile name cannot be empty")
            
            if not profile.points:
                raise ValidationError("Profile must have at least one temperature point")
            
            # Check for reserved names (predefined profiles)
            predefined_names = {
                "Constant 25°C", "Isothermal 20°C", "Isothermal 30°C", 
                "ASTM C 1074", "Heat of Hydration", "Custom"
            }
            if profile.name in predefined_names:
                raise ValidationError(f"Profile name '{profile.name}' is reserved for predefined profiles")
            
            with self.db_service.get_session() as session:
                # Check if profile with same name exists
                existing = session.query(TemperatureProfileDB).filter_by(name=profile.name).first()
                
                if existing:
                    if not overwrite:
                        raise ServiceError(f"Profile '{profile.name}' already exists. Use overwrite=True to replace it.")
                    
                    # Update existing profile
                    existing.update_from_temperature_profile(profile)
                    session.commit()
                    self.logger.info(f"Updated temperature profile: {profile.name}")
                    return existing
                else:
                    # Create new profile
                    db_profile = TemperatureProfileDB.from_temperature_profile(profile, is_predefined=False)
                    session.add(db_profile)
                    session.commit()
                    self.logger.info(f"Saved new temperature profile: {profile.name}")
                    return db_profile
                    
        except IntegrityError as e:
            raise ServiceError(f"Database error saving profile '{profile.name}': {e}")
        except Exception as e:
            self.logger.error(f"Failed to save temperature profile '{profile.name}': {e}")
            raise ServiceError(f"Failed to save temperature profile: {e}")
    
    def get_profile(self, name: str) -> Optional[TemperatureProfile]:
        """
        Get a temperature profile by name.
        
        Args:
            name: Name of the profile to retrieve
            
        Returns:
            TemperatureProfile object or None if not found
        """
        try:
            # First check predefined profiles
            predefined = self._get_predefined_profiles()
            if name in predefined:
                return predefined[name]
            
            # Then check database
            with self.db_service.get_session() as session:
                db_profile = session.query(TemperatureProfileDB).filter_by(name=name).first()
                if db_profile:
                    return db_profile.to_temperature_profile()
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get temperature profile '{name}': {e}")
            return None
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """
        List all available temperature profiles (predefined + custom).
        
        Returns:
            List of profile dictionaries with name, description, and source info
        """
        try:
            profiles = []
            
            # Add predefined profiles
            predefined = self._get_predefined_profiles()
            for name, profile in predefined.items():
                profiles.append({
                    'name': name,
                    'description': profile.description,
                    'is_predefined': True,
                    'point_count': len(profile.points),
                    'created_at': None,
                    'updated_at': None
                })
            
            # Add custom profiles from database
            with self.db_service.get_session() as session:
                db_profiles = session.query(TemperatureProfileDB).filter_by(is_predefined=False).all()
                for db_profile in db_profiles:
                    profiles.append({
                        'name': db_profile.name,
                        'description': db_profile.description or "",
                        'is_predefined': False,
                        'point_count': len(db_profile.to_temperature_profile().points),
                        'created_at': db_profile.created_at,
                        'updated_at': db_profile.updated_at
                    })
            
            # Sort by name
            profiles.sort(key=lambda p: p['name'])
            return profiles
            
        except Exception as e:
            self.logger.error(f"Failed to list temperature profiles: {e}")
            return []
    
    def delete_profile(self, name: str) -> bool:
        """
        Delete a custom temperature profile.
        
        Args:
            name: Name of the profile to delete
            
        Returns:
            True if deleted, False if not found or cannot delete
        """
        try:
            # Cannot delete predefined profiles
            predefined = self._get_predefined_profiles()
            if name in predefined:
                raise ServiceError(f"Cannot delete predefined profile '{name}'")
            
            with self.db_service.get_session() as session:
                db_profile = session.query(TemperatureProfileDB).filter_by(name=name, is_predefined=False).first()
                if db_profile:
                    session.delete(db_profile)
                    session.commit()
                    self.logger.info(f"Deleted temperature profile: {name}")
                    return True
                else:
                    self.logger.warning(f"Temperature profile not found for deletion: {name}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to delete temperature profile '{name}': {e}")
            return False
    
    def get_profile_names(self) -> List[str]:
        """
        Get list of all profile names for dropdown menus.
        
        Returns:
            List of profile names
        """
        try:
            profiles = self.list_profiles()
            return [profile['name'] for profile in profiles]
        except Exception as e:
            self.logger.error(f"Failed to get profile names: {e}")
            return []
    
    def _get_predefined_profiles(self) -> Dict[str, TemperatureProfile]:
        """Get predefined temperature profiles (same as HydrationService)."""
        return {
            "Constant 25°C": TemperatureProfile(
                "Constant 25°C",
                "Constant temperature at 25°C",
                [TemperaturePoint(0.0, 25.0), TemperaturePoint(168.0, 25.0)]
            ),
            "Isothermal 20°C": TemperatureProfile(
                "Isothermal 20°C", 
                "Constant temperature at 20°C",
                [TemperaturePoint(0.0, 20.0), TemperaturePoint(168.0, 20.0)]
            ),
            "Isothermal 30°C": TemperatureProfile(
                "Isothermal 30°C",
                "Constant temperature at 30°C", 
                [TemperaturePoint(0.0, 30.0), TemperaturePoint(168.0, 30.0)]
            ),
            "ASTM C 1074": TemperatureProfile(
                "ASTM C 1074",
                "Standard temperature profile for adiabatic calorimetry",
                [
                    TemperaturePoint(0.0, 23.0),
                    TemperaturePoint(24.0, 35.0),
                    TemperaturePoint(72.0, 45.0),
                    TemperaturePoint(168.0, 50.0)
                ]
            ),
            "Heat of Hydration": TemperatureProfile(
                "Heat of Hydration",
                "Typical heat of hydration profile for cement",
                [
                    TemperaturePoint(0.0, 25.0),
                    TemperaturePoint(12.0, 35.0),
                    TemperaturePoint(48.0, 55.0),
                    TemperaturePoint(96.0, 45.0),
                    TemperaturePoint(168.0, 30.0)
                ]
            )
        }
    
    def initialize_predefined_profiles(self) -> None:
        """
        Initialize predefined profiles in database if they don't exist.
        This is called during database initialization.
        """
        try:
            predefined = self._get_predefined_profiles()
            
            with self.db_service.get_session() as session:
                for name, profile in predefined.items():
                    existing = session.query(TemperatureProfileDB).filter_by(name=name, is_predefined=True).first()
                    if not existing:
                        db_profile = TemperatureProfileDB.from_temperature_profile(profile, is_predefined=True)
                        session.add(db_profile)
                
                session.commit()
                self.logger.info(f"Initialized {len(predefined)} predefined temperature profiles")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize predefined profiles: {e}")
    
    # Abstract method implementations required by BaseService
    def get_all(self) -> List[TemperatureProfileDB]:
        """Get all temperature profiles from database."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(TemperatureProfileDB).all()
        except Exception as e:
            self.logger.error(f"Failed to get all temperature profiles: {e}")
            return []
    
    def get_by_name(self, name: str) -> Optional[TemperatureProfileDB]:
        """Get temperature profile by name."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(TemperatureProfileDB).filter_by(name=name).first()
        except Exception as e:
            self.logger.error(f"Failed to get temperature profile '{name}': {e}")
            return None
    
    def create(self, create_data) -> TemperatureProfileDB:
        """Create new temperature profile."""
        # For now, redirect to save_profile method
        return self.save_profile(create_data, overwrite=False)
    
    def update(self, name: str, update_data) -> TemperatureProfileDB:
        """Update existing temperature profile."""
        # For now, redirect to save_profile method
        return self.save_profile(update_data, overwrite=True)
    
    def delete(self, name: str) -> bool:
        """Delete temperature profile."""
        return self.delete_profile(name)
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """Get list of all temperature profiles with basic info."""
        try:
            with self.db_service.get_read_only_session() as session:
                profiles = session.query(TemperatureProfileDB).all()
                return [{"name": p.name, "is_predefined": p.is_predefined} for p in profiles]
        except Exception as e:
            self.logger.error(f"Failed to list temperature profiles: {e}")
            return []
    
    def get_profile(self, name: str) -> Optional[TemperatureProfile]:
        """Get temperature profile as TemperatureProfile object."""
        try:
            db_profile = self.get_by_name(name)
            if db_profile:
                return db_profile.to_temperature_profile()
            return None
        except Exception as e:
            self.logger.error(f"Failed to get temperature profile '{name}': {e}")
            return None