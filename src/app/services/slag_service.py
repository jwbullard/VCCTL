#!/usr/bin/env python3
"""
Slag Service for VCCTL

Provides business logic for slag material management.
Converted from Java Spring service to Python.
"""

import logging
import math
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.exc import IntegrityError

from app.database.service import DatabaseService
from app.models.slag import Slag, SlagCreate, SlagUpdate, SlagResponse
from app.services.base_service import BaseService, ServiceError, NotFoundError, AlreadyExistsError, ValidationError


class SlagService(BaseService[Slag, SlagCreate, SlagUpdate]):
    """
    Service for managing slag materials.
    
    Provides CRUD operations, validation, and specialized calculations
    for ground granulated blast-furnace slag (GGBS) materials in the VCCTL system.
    """
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(Slag, db_service)
        self.logger = logging.getLogger('VCCTL.SlagService')
        self.default_psd = 'cement141'
        self.default_specific_gravity = 2.87
    
    def get_all(self) -> List[Slag]:
        """Get all slag materials."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Slag).order_by(Slag.name).all()
        except Exception as e:
            self.logger.error(f"Failed to get all slag materials: {e}")
            raise ServiceError(f"Failed to retrieve slag materials: {e}")
    
    def get_by_name(self, name: str) -> Optional[Slag]:
        """Get slag by name."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Slag).filter_by(name=name).first()
        except Exception as e:
            self.logger.error(f"Failed to get slag {name}: {e}")
            raise ServiceError(f"Failed to retrieve slag: {e}")
    
    def create(self, slag_data: SlagCreate) -> Slag:
        """Create a new slag material."""
        try:
            with self.db_service.get_session() as session:
                # Check if slag already exists
                existing = session.query(Slag).filter_by(name=slag_data.name).first()
                if existing:
                    raise AlreadyExistsError(f"Slag '{slag_data.name}' already exists")
                
                # Create slag with defaults
                slag_dict = slag_data.dict(exclude_unset=True)
                
                # Set defaults if not provided
                if 'specific_gravity' not in slag_dict:
                    slag_dict['specific_gravity'] = self.default_specific_gravity
                if 'psd' not in slag_dict:
                    slag_dict['psd'] = self.default_psd
                
                slag = Slag(**slag_dict)
                
                # Validate slag properties
                self._validate_slag(slag)
                
                session.add(slag)
                session.flush()  # Flush to get any database errors
                
                self.logger.info(f"Created slag: {slag.name}")
                return slag
                
        except AlreadyExistsError:
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error creating slag: {e}")
            raise ServiceError(f"Slag creation failed: invalid data")
        except Exception as e:
            self.logger.error(f"Failed to create slag: {e}")
            raise ServiceError(f"Failed to create slag: {e}")
    
    def update(self, name: str, slag_data: SlagUpdate) -> Slag:
        """Update an existing slag material."""
        try:
            with self.db_service.get_session() as session:
                slag = session.query(Slag).filter_by(name=name).first()
                if not slag:
                    raise NotFoundError(f"Slag '{name}' not found")
                
                # Update fields
                update_dict = slag_data.dict(exclude_unset=True)
                for field, value in update_dict.items():
                    setattr(slag, field, value)
                
                # Validate updated slag
                self._validate_slag(slag)
                
                session.flush()  # Flush to get any database errors
                
                self.logger.info(f"Updated slag: {slag.name}")
                return slag
                
        except NotFoundError:
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error updating slag: {e}")
            raise ServiceError(f"Slag update failed: invalid data")
        except Exception as e:
            self.logger.error(f"Failed to update slag {name}: {e}")
            raise ServiceError(f"Failed to update slag: {e}")
    
    def delete(self, name: str) -> bool:
        """Delete a slag material."""
        try:
            with self.db_service.get_session() as session:
                slag = session.query(Slag).filter_by(name=name).first()
                if not slag:
                    raise NotFoundError(f"Slag '{name}' not found")
                
                session.delete(slag)
                
                self.logger.info(f"Deleted slag: {name}")
                return True
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete slag {name}: {e}")
            raise ServiceError(f"Failed to delete slag: {e}")
    
    def _validate_slag(self, slag: Slag) -> None:
        """Validate slag properties."""
        # Validate molecular ratios
        if not slag.validate_molecular_ratios():
            raise ValidationError("Invalid molecular ratios: ratios must be within reasonable bounds")
        
        # Validate specific gravity
        if slag.specific_gravity is not None and slag.specific_gravity <= 0:
            raise ValidationError("Specific gravity must be positive")
        
        # Validate required fields
        if not slag.name or not slag.name.strip():
            raise ValidationError("Slag name is required")
    
    def calculate_activation_energy(self, name: str, temperature: float = 25.0) -> Optional[float]:
        """
        Calculate activation energy for slag hydration.
        
        Args:
            name: Name of the slag material
            temperature: Temperature in Celsius
            
        Returns:
            Calculated activation energy in J/mol
        """
        try:
            slag = self.get_by_name(name)
            if not slag:
                raise NotFoundError(f"Slag '{name}' not found")
            
            return slag.calculate_activation_energy(temperature)
            
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to calculate activation energy for {name}: {e}")
            raise ServiceError(f"Failed to calculate activation energy: {e}")
    
    def get_slag_with_complete_molecular_data(self) -> List[Slag]:
        """Get all slag materials that have complete molecular composition data."""
        try:
            with self.db_service.get_read_only_session() as session:
                return [slag for slag in session.query(Slag).all() 
                       if slag.has_complete_molecular_data]
        except Exception as e:
            self.logger.error(f"Failed to get slag with complete molecular data: {e}")
            raise ServiceError(f"Failed to retrieve slag with complete molecular data: {e}")
    
    def get_slag_with_complete_hp_data(self) -> List[Slag]:
        """Get all slag materials that have complete hydration product data."""
        try:
            with self.db_service.get_read_only_session() as session:
                return [slag for slag in session.query(Slag).all() 
                       if slag.has_complete_hp_data]
        except Exception as e:
            self.logger.error(f"Failed to get slag with complete HP data: {e}")
            raise ServiceError(f"Failed to retrieve slag with complete HP data: {e}")
    
    def get_slag_with_reactivity_data(self) -> List[Slag]:
        """Get all slag materials that have reactivity data."""
        try:
            with self.db_service.get_read_only_session() as session:
                return [slag for slag in session.query(Slag).all() 
                       if slag.has_reactivity_data]
        except Exception as e:
            self.logger.error(f"Failed to get slag with reactivity data: {e}")
            raise ServiceError(f"Failed to retrieve slag with reactivity data: {e}")
    
    def calculate_reactivity_factor(self, name: str, fineness_factor: float = 1.0, 
                                  chemical_factor: float = 1.0) -> float:
        """
        Calculate overall reactivity factor for slag.
        
        Args:
            name: Name of the slag material
            fineness_factor: Factor based on particle fineness (default 1.0)
            chemical_factor: Factor based on chemical composition (default 1.0)
            
        Returns:
            Overall reactivity factor
        """
        try:
            slag = self.get_by_name(name)
            if not slag:
                raise NotFoundError(f"Slag '{name}' not found")
            
            if not slag.has_reactivity_data:
                raise ValidationError(f"Slag '{name}' does not have reactivity data")
            
            base_reactivity = slag.base_slag_reactivity or 1.0
            
            # Calculate overall reactivity factor
            # This is a simplified calculation - actual VCCTL may use more complex formulas
            overall_reactivity = base_reactivity * fineness_factor * chemical_factor
            
            return overall_reactivity
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to calculate reactivity factor for {name}: {e}")
            raise ServiceError(f"Failed to calculate reactivity factor: {e}")
    
    def calculate_degree_of_hydration(self, name: str, time_hours: float, 
                                    temperature: float = 25.0) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate degree of hydration for slag at given time and temperature.
        
        Args:
            name: Name of the slag material
            time_hours: Time in hours
            temperature: Temperature in Celsius
            
        Returns:
            Tuple of (degree_of_hydration, calculation_details)
        """
        try:
            slag = self.get_by_name(name)
            if not slag:
                raise NotFoundError(f"Slag '{name}' not found")
            
            if not slag.has_reactivity_data:
                raise ValidationError(f"Slag '{name}' does not have reactivity data")
            
            # Simplified degree of hydration calculation
            # Actual VCCTL uses more sophisticated kinetic models
            
            activation_energy = slag.calculate_activation_energy(temperature)
            base_reactivity = slag.base_slag_reactivity or 1.0
            
            # Temperature factor (Arrhenius equation)
            R = 8.314  # Gas constant J/(mol·K)
            T_ref = 298.15  # Reference temperature (25°C) in Kelvin
            T_actual = temperature + 273.15  # Actual temperature in Kelvin
            
            if activation_energy:
                temp_factor = math.exp(-activation_energy/R * (1/T_actual - 1/T_ref))
            else:
                temp_factor = 1.0
            
            # Time-dependent hydration (simplified exponential approach)
            rate_constant = base_reactivity * temp_factor * 0.01  # Simplified rate constant
            degree_of_hydration = 1 - math.exp(-rate_constant * time_hours)
            
            # Cap at realistic maximum (slag typically doesn't reach 100% hydration)
            max_hydration = 0.85  # 85% maximum
            degree_of_hydration = min(degree_of_hydration, max_hydration)
            
            calculation_details = {
                'activation_energy_j_mol': activation_energy,
                'base_reactivity': base_reactivity,
                'temperature_factor': temp_factor,
                'rate_constant': rate_constant,
                'time_hours': time_hours,
                'temperature_celsius': temperature,
                'max_hydration': max_hydration
            }
            
            return degree_of_hydration, calculation_details
            
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to calculate degree of hydration for {name}: {e}")
            raise ServiceError(f"Failed to calculate degree of hydration: {e}")
    
    def search_slag(self, query: str, limit: Optional[int] = None) -> List[Slag]:
        """
        Search slag materials by name, PSD, or description.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of matching slag materials
        """
        try:
            with self.db_service.get_read_only_session() as session:
                search_query = session.query(Slag).filter(
                    (Slag.name.contains(query)) | 
                    (Slag.psd.contains(query) if query else False) |
                    (Slag.description.contains(query) if query else False)
                ).order_by(Slag.name)
                
                if limit:
                    search_query = search_query.limit(limit)
                
                return search_query.all()
                
        except Exception as e:
            self.logger.error(f"Failed to search slag: {e}")
            raise ServiceError(f"Failed to search slag: {e}")
    
    def get_slag_statistics(self) -> Dict[str, Any]:
        """Get statistics about slag materials."""
        try:
            with self.db_service.get_read_only_session() as session:
                total_count = session.query(Slag).count()
                
                if total_count == 0:
                    return {'total_slag': 0}
                
                slag_materials = session.query(Slag).all()
                
                with_molecular_data = len([s for s in slag_materials if s.has_complete_molecular_data])
                with_hp_data = len([s for s in slag_materials if s.has_complete_hp_data])
                with_reactivity_data = len([s for s in slag_materials if s.has_reactivity_data])
                
                # Calculate specific gravity statistics
                specific_gravities = [s.specific_gravity for s in slag_materials if s.specific_gravity is not None]
                avg_specific_gravity = sum(specific_gravities) / len(specific_gravities) if specific_gravities else 0
                
                # Calculate CaO/SiO2 ratio statistics
                casi_ratios = [s.casi_mol_ratio for s in slag_materials if s.casi_mol_ratio is not None]
                avg_casi_ratio = sum(casi_ratios) / len(casi_ratios) if casi_ratios else 0
                
                # Get unique PSD types
                unique_psds = len(set(s.psd for s in slag_materials if s.psd))
                
                return {
                    'total_slag': total_count,
                    'with_complete_molecular_data': with_molecular_data,
                    'with_complete_hp_data': with_hp_data,
                    'with_reactivity_data': with_reactivity_data,
                    'percentage_with_molecular_data': (with_molecular_data / total_count * 100),
                    'percentage_with_hp_data': (with_hp_data / total_count * 100),
                    'percentage_with_reactivity_data': (with_reactivity_data / total_count * 100),
                    'average_specific_gravity': round(avg_specific_gravity, 3) if avg_specific_gravity else None,
                    'average_casi_ratio': round(avg_casi_ratio, 3) if avg_casi_ratio else None,
                    'unique_psd_types': unique_psds
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get slag statistics: {e}")
            raise ServiceError(f"Failed to get slag statistics: {e}")
    
    def validate_for_concrete_mix(self, name: str, cement_type: str = None, 
                                replacement_percentage: float = None) -> Dict[str, Any]:
        """
        Validate slag suitability for concrete mix design.
        
        Args:
            name: Name of the slag material
            cement_type: Type of cement to be replaced (optional)
            replacement_percentage: Percentage replacement of cement (optional)
            
        Returns:
            Validation results dictionary
        """
        try:
            slag = self.get_by_name(name)
            if not slag:
                raise NotFoundError(f"Slag '{name}' not found")
            
            validation_result = {
                'is_suitable': True,
                'warnings': [],
                'recommendations': [],
                'suitability_score': 0.0
            }
            
            score = 100.0  # Start with perfect score
            
            # Check if has reactivity data
            if not slag.has_reactivity_data:
                validation_result['warnings'].append("No reactivity data available")
                score -= 20
            
            # Check specific gravity range
            if slag.specific_gravity:
                if slag.specific_gravity < 2.8 or slag.specific_gravity > 3.0:
                    validation_result['warnings'].append("Specific gravity outside typical range (2.8-3.0)")
                    score -= 10
            
            # Check CaO/SiO2 ratio for reactivity
            if slag.casi_mol_ratio:
                if slag.casi_mol_ratio < 1.0:
                    validation_result['warnings'].append("Low CaO/SiO2 ratio may indicate lower reactivity")
                    score -= 15
                elif slag.casi_mol_ratio > 1.4:
                    validation_result['recommendations'].append("High CaO/SiO2 ratio - good for reactivity")
                    score += 5
            
            # Check replacement percentage if provided
            if replacement_percentage is not None:
                if replacement_percentage > 50:
                    validation_result['warnings'].append("High replacement percentage (>50%) may affect early strength")
                    score -= 10
                elif replacement_percentage > 80:
                    validation_result['warnings'].append("Very high replacement percentage (>80%) not recommended")
                    score -= 20
            
            # Check if has HP data for long-term performance prediction
            if slag.has_complete_hp_data:
                validation_result['recommendations'].append("Complete hydration product data available for accurate modeling")
                score += 10
            
            validation_result['suitability_score'] = max(0.0, min(100.0, score))
            
            if score < 60:
                validation_result['is_suitable'] = False
            
            return validation_result
            
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to validate slag for concrete mix: {e}")
            raise ServiceError(f"Failed to validate slag for concrete mix: {e}")