#!/usr/bin/env python3
"""
Fly Ash Service for VCCTL

Provides business logic for fly ash material management.
Converted from Java Spring service to Python.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError

from app.database.service import DatabaseService
from app.models.fly_ash import FlyAsh, FlyAshCreate, FlyAshUpdate, FlyAshResponse
from app.services.base_service import BaseService, ServiceError, NotFoundError, AlreadyExistsError, ValidationError


class FlyAshService(BaseService[FlyAsh, FlyAshCreate, FlyAshUpdate]):
    """
    Service for managing fly ash materials.
    
    Provides CRUD operations, validation, and specialized calculations
    for fly ash materials in the VCCTL system.
    """
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(FlyAsh, db_service)
        self.logger = logging.getLogger('VCCTL.FlyAshService')
        self.default_psd = 'cement141'
        self.default_specific_gravity = 2.77
    
    def get_all(self) -> List[FlyAsh]:
        """Get all fly ash materials."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(FlyAsh).order_by(FlyAsh.name).all()
        except Exception as e:
            self.logger.error(f"Failed to get all fly ash materials: {e}")
            raise ServiceError(f"Failed to retrieve fly ash materials: {e}")
    
    def get_by_name(self, name: str) -> Optional[FlyAsh]:
        """Get fly ash by name."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(FlyAsh).filter_by(name=name).first()
        except Exception as e:
            self.logger.error(f"Failed to get fly ash {name}: {e}")
            raise ServiceError(f"Failed to retrieve fly ash: {e}")
    
    def create(self, fly_ash_data: FlyAshCreate) -> FlyAsh:
        """Create a new fly ash material."""
        try:
            with self.db_service.get_session() as session:
                # Check if fly ash already exists
                existing = session.query(FlyAsh).filter_by(name=fly_ash_data.name).first()
                if existing:
                    raise AlreadyExistsError(f"Fly ash '{fly_ash_data.name}' already exists")
                
                # Create fly ash with defaults
                fly_ash_dict = fly_ash_data.dict(exclude_unset=True)
                
                # Set defaults if not provided
                if 'specific_gravity' not in fly_ash_dict:
                    fly_ash_dict['specific_gravity'] = self.default_specific_gravity
                if 'psd' not in fly_ash_dict:
                    fly_ash_dict['psd'] = self.default_psd
                
                fly_ash = FlyAsh(**fly_ash_dict)
                
                # Validate fly ash properties
                self._validate_fly_ash(fly_ash)
                
                session.add(fly_ash)
                session.flush()  # Flush to get any database errors
                
                self.logger.info(f"Created fly ash: {fly_ash.name}")
                return fly_ash
                
        except AlreadyExistsError:
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error creating fly ash: {e}")
            raise ServiceError(f"Fly ash creation failed: invalid data")
        except Exception as e:
            self.logger.error(f"Failed to create fly ash: {e}")
            raise ServiceError(f"Failed to create fly ash: {e}")
    
    def update(self, fly_ash_id: int, fly_ash_data: FlyAshUpdate) -> FlyAsh:
        """Update an existing fly ash material."""
        try:
            with self.db_service.get_session() as session:
                fly_ash = session.query(FlyAsh).filter_by(id=fly_ash_id).first()
                if not fly_ash:
                    raise NotFoundError(f"Fly ash with ID '{fly_ash_id}' not found")
                
                # Update fields
                update_dict = fly_ash_data.dict(exclude_unset=True)
                for field, value in update_dict.items():
                    setattr(fly_ash, field, value)
                
                # Validate updated fly ash
                self._validate_fly_ash(fly_ash)
                
                session.flush()  # Flush to get any database errors
                
                self.logger.info(f"Updated fly ash: {fly_ash.name}")
                return fly_ash
                
        except NotFoundError:
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error updating fly ash: {e}")
            raise ServiceError(f"Fly ash update failed: invalid data")
        except Exception as e:
            self.logger.error(f"Failed to update fly ash {fly_ash_id}: {e}")
            raise ServiceError(f"Failed to update fly ash: {e}")
    
    def delete(self, name: str) -> bool:
        """Delete a fly ash material."""
        try:
            with self.db_service.get_session() as session:
                fly_ash = session.query(FlyAsh).filter_by(name=name).first()
                if not fly_ash:
                    raise NotFoundError(f"Fly ash '{name}' not found")
                
                session.delete(fly_ash)
                
                self.logger.info(f"Deleted fly ash: {name}")
                return True
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete fly ash {name}: {e}")
            raise ServiceError(f"Failed to delete fly ash: {e}")
    
    def _validate_fly_ash(self, fly_ash: FlyAsh) -> None:
        """Validate fly ash properties."""
        # Validate phase fractions
        if not fly_ash.validate_phase_fractions():
            raise ValidationError("Invalid phase fractions: values must be between 0 and 1, and total cannot exceed 1.0")
        
        # Validate specific gravity
        if fly_ash.specific_gravity is not None and fly_ash.specific_gravity < 0:
            raise ValidationError("Specific gravity cannot be negative")
        
        # Validate required fields
        if not fly_ash.name or not fly_ash.name.strip():
            raise ValidationError("Fly ash name is required")
    
    def get_fly_ash_with_complete_phase_data(self) -> List[FlyAsh]:
        """Get all fly ash materials that have complete phase composition data."""
        try:
            with self.db_service.get_read_only_session() as session:
                return [fa for fa in session.query(FlyAsh).all() 
                       if fa.has_complete_phase_data]
        except Exception as e:
            self.logger.error(f"Failed to get fly ash with complete phase data: {e}")
            raise ServiceError(f"Failed to retrieve fly ash with complete phase data: {e}")
    
    def search_fly_ash(self, query: str, limit: Optional[int] = None) -> List[FlyAsh]:
        """
        Search fly ash materials by name, PSD, or description.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of matching fly ash materials
        """
        try:
            with self.db_service.get_read_only_session() as session:
                search_query = session.query(FlyAsh).filter(
                    (FlyAsh.name.contains(query)) | 
                    (FlyAsh.psd.contains(query) if query else False) |
                    (FlyAsh.description.contains(query) if query else False)
                ).order_by(FlyAsh.name)
                
                if limit:
                    search_query = search_query.limit(limit)
                
                return search_query.all()
                
        except Exception as e:
            self.logger.error(f"Failed to search fly ash: {e}")
            raise ServiceError(f"Failed to search fly ash: {e}")
    
    def get_by_class_type(self, class_type: str) -> List[FlyAsh]:
        """
        Get fly ash materials by class type (based on name patterns).
        
        Args:
            class_type: Class type ('f' for Class F, 'c' for Class C)
            
        Returns:
            List of fly ash materials matching the class type
        """
        try:
            class_type_lower = class_type.lower()
            with self.db_service.get_read_only_session() as session:
                return session.query(FlyAsh).filter(
                    FlyAsh.name.contains(f'class_{class_type_lower}') |
                    FlyAsh.description.contains(f'Class {class_type.upper()}')
                ).all()
                
        except Exception as e:
            self.logger.error(f"Failed to get fly ash by class type {class_type}: {e}")
            raise ServiceError(f"Failed to retrieve fly ash by class type: {e}")
    
    def calculate_phase_distribution_input(self, name: str) -> str:
        """
        Generate phase distribution input string for a fly ash material.
        
        Args:
            name: Name of the fly ash material
            
        Returns:
            Formatted phase distribution input string
        """
        try:
            fly_ash = self.get_by_name(name)
            if not fly_ash:
                raise NotFoundError(f"Fly ash '{name}' not found")
            
            return fly_ash.build_phase_distribution_input()
            
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to calculate phase distribution input for {name}: {e}")
            raise ServiceError(f"Failed to calculate phase distribution input: {e}")
    
    def get_fly_ash_statistics(self) -> Dict[str, Any]:
        """Get statistics about fly ash materials."""
        try:
            with self.db_service.get_read_only_session() as session:
                total_count = session.query(FlyAsh).count()
                
                if total_count == 0:
                    return {'total_fly_ash': 0}
                
                fly_ash_materials = session.query(FlyAsh).all()
                
                with_complete_phase_data = len([fa for fa in fly_ash_materials if fa.has_complete_phase_data])
                
                # Calculate specific gravity statistics
                specific_gravities = [fa.specific_gravity for fa in fly_ash_materials if fa.specific_gravity is not None]
                avg_specific_gravity = sum(specific_gravities) / len(specific_gravities) if specific_gravities else 0
                min_specific_gravity = min(specific_gravities) if specific_gravities else 0
                max_specific_gravity = max(specific_gravities) if specific_gravities else 0
                
                # Get unique PSD types
                unique_psds = len(set(fa.psd for fa in fly_ash_materials if fa.psd))
                
                # Count by class type (approximate)
                class_f_count = len([fa for fa in fly_ash_materials if 'class_f' in fa.name.lower()])
                class_c_count = len([fa for fa in fly_ash_materials if 'class_c' in fa.name.lower()])
                
                return {
                    'total_fly_ash': total_count,
                    'with_complete_phase_data': with_complete_phase_data,
                    'percentage_with_complete_phase_data': (with_complete_phase_data / total_count * 100),
                    'average_specific_gravity': round(avg_specific_gravity, 3) if avg_specific_gravity else None,
                    'min_specific_gravity': min_specific_gravity,
                    'max_specific_gravity': max_specific_gravity,
                    'unique_psd_types': unique_psds,
                    'estimated_class_f_count': class_f_count,
                    'estimated_class_c_count': class_c_count
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get fly ash statistics: {e}")
            raise ServiceError(f"Failed to get fly ash statistics: {e}")
    
    def validate_phase_fractions_for_mix(self, name: str, mix_fraction: float) -> Dict[str, Any]:
        """
        Validate that phase fractions are appropriate for use in a mix.
        
        Args:
            name: Name of the fly ash material
            mix_fraction: Fraction of total binder that this fly ash represents
            
        Returns:
            Validation results dictionary
        """
        try:
            fly_ash = self.get_by_name(name)
            if not fly_ash:
                raise NotFoundError(f"Fly ash '{name}' not found")
            
            validation_result = {
                'is_valid': True,
                'warnings': [],
                'errors': [],
                'phase_fractions': fly_ash.phase_fractions
            }
            
            # Check if has complete phase data
            if not fly_ash.has_complete_phase_data:
                validation_result['warnings'].append("Incomplete phase composition data")
            
            # Check mix fraction bounds
            if mix_fraction < 0 or mix_fraction > 1:
                validation_result['errors'].append("Mix fraction must be between 0 and 1")
                validation_result['is_valid'] = False
            
            # Check if total phase fraction exceeds reasonable limits
            total_fraction = fly_ash.total_phase_fraction
            if total_fraction and total_fraction > 1.0:
                validation_result['errors'].append("Total phase fractions exceed 100%")
                validation_result['is_valid'] = False
            
            # Check if specific gravity is reasonable
            if fly_ash.specific_gravity and (fly_ash.specific_gravity < 2.0 or fly_ash.specific_gravity > 4.0):
                validation_result['warnings'].append("Specific gravity outside typical range (2.0-4.0)")
            
            return validation_result
            
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to validate phase fractions for mix: {e}")
            raise ServiceError(f"Failed to validate phase fractions: {e}")