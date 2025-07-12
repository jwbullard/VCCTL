#!/usr/bin/env python3
"""
Inert Filler Service for VCCTL

Provides business logic for inert filler material management.
Converted from Java Spring service to Python.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError

from app.database.service import DatabaseService
from app.models.inert_filler import InertFiller, InertFillerCreate, InertFillerUpdate, InertFillerResponse
from app.services.base_service import BaseService, ServiceError, NotFoundError, AlreadyExistsError, ValidationError


class InertFillerService(BaseService[InertFiller, InertFillerCreate, InertFillerUpdate]):
    """
    Service for managing inert filler materials.
    
    Provides CRUD operations, validation, and property calculations
    for inert filler materials in the VCCTL system.
    """
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(InertFiller, db_service)
        self.logger = logging.getLogger('VCCTL.InertFillerService')
        self.default_psd = 'cement141'
        self.default_specific_gravity = 3.0
    
    def get_all(self) -> List[InertFiller]:
        """Get all inert filler materials."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(InertFiller).order_by(InertFiller.name).all()
        except Exception as e:
            self.logger.error(f"Failed to get all inert fillers: {e}")
            raise ServiceError(f"Failed to retrieve inert fillers: {e}")
    
    def get_by_name(self, name: str) -> Optional[InertFiller]:
        """Get inert filler by name."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(InertFiller).filter_by(name=name).first()
        except Exception as e:
            self.logger.error(f"Failed to get inert filler {name}: {e}")
            raise ServiceError(f"Failed to retrieve inert filler: {e}")
    
    def create(self, filler_data: InertFillerCreate) -> InertFiller:
        """Create a new inert filler material."""
        try:
            with self.db_service.get_session() as session:
                # Check if filler already exists
                existing = session.query(InertFiller).filter_by(name=filler_data.name).first()
                if existing:
                    raise AlreadyExistsError(f"Inert filler '{filler_data.name}' already exists")
                
                # Create filler with defaults
                filler_dict = filler_data.dict(exclude_unset=True)
                
                # Set defaults if not provided
                if 'specific_gravity' not in filler_dict:
                    filler_dict['specific_gravity'] = self.default_specific_gravity
                if 'psd' not in filler_dict:
                    filler_dict['psd'] = self.default_psd
                
                filler = InertFiller(**filler_dict)
                
                # Validate filler properties
                self._validate_filler(filler)
                
                session.add(filler)
                session.flush()  # Flush to get any database errors
                
                self.logger.info(f"Created inert filler: {filler.name}")
                return filler
                
        except AlreadyExistsError:
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error creating inert filler: {e}")
            raise ServiceError(f"Inert filler creation failed: invalid data")
        except Exception as e:
            self.logger.error(f"Failed to create inert filler: {e}")
            raise ServiceError(f"Failed to create inert filler: {e}")
    
    def update(self, name: str, filler_data: InertFillerUpdate) -> InertFiller:
        """Update an existing inert filler material."""
        try:
            with self.db_service.get_session() as session:
                filler = session.query(InertFiller).filter_by(name=name).first()
                if not filler:
                    raise NotFoundError(f"Inert filler '{name}' not found")
                
                # Update fields
                update_dict = filler_data.dict(exclude_unset=True)
                for field, value in update_dict.items():
                    setattr(filler, field, value)
                
                # Validate updated filler
                self._validate_filler(filler)
                
                session.flush()  # Flush to get any database errors
                
                self.logger.info(f"Updated inert filler: {filler.name}")
                return filler
                
        except NotFoundError:
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error updating inert filler: {e}")
            raise ServiceError(f"Inert filler update failed: invalid data")
        except Exception as e:
            self.logger.error(f"Failed to update inert filler {name}: {e}")
            raise ServiceError(f"Failed to update inert filler: {e}")
    
    def delete(self, name: str) -> bool:
        """Delete an inert filler material."""
        try:
            with self.db_service.get_session() as session:
                filler = session.query(InertFiller).filter_by(name=name).first()
                if not filler:
                    raise NotFoundError(f"Inert filler '{name}' not found")
                
                session.delete(filler)
                
                self.logger.info(f"Deleted inert filler: {name}")
                return True
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete inert filler {name}: {e}")
            raise ServiceError(f"Failed to delete inert filler: {e}")
    
    def _validate_filler(self, filler: InertFiller) -> None:
        """Validate inert filler properties."""
        # Validate specific gravity
        if not filler.is_valid_specific_gravity:
            raise ValidationError("Invalid specific gravity: must be between 2.0 and 5.0 for mineral fillers")
        
        # Validate required fields
        if not filler.name or not filler.name.strip():
            raise ValidationError("Inert filler name is required")
        
        if not filler.psd or not filler.psd.strip():
            raise ValidationError("PSD reference is required")
    
    def search_fillers(self, query: str, limit: Optional[int] = None) -> List[InertFiller]:
        """
        Search inert filler materials by name, PSD, or description.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of matching inert filler materials
        """
        try:
            with self.db_service.get_read_only_session() as session:
                search_query = session.query(InertFiller).filter(
                    (InertFiller.name.contains(query)) | 
                    (InertFiller.psd.contains(query) if query else False) |
                    (InertFiller.description.contains(query) if query else False)
                ).order_by(InertFiller.name)
                
                if limit:
                    search_query = search_query.limit(limit)
                
                return search_query.all()
                
        except Exception as e:
            self.logger.error(f"Failed to search inert fillers: {e}")
            raise ServiceError(f"Failed to search inert fillers: {e}")
    
    def get_by_material_type(self, material_type: str) -> List[InertFiller]:
        """
        Get inert fillers by material type (based on name patterns).
        
        Args:
            material_type: Material type ('quartz', 'limestone', 'silica', etc.)
            
        Returns:
            List of inert fillers matching the material type
        """
        try:
            material_type_lower = material_type.lower()
            with self.db_service.get_read_only_session() as session:
                return session.query(InertFiller).filter(
                    (InertFiller.name.contains(material_type_lower)) |
                    (InertFiller.description.contains(material_type_lower) if InertFiller.description else False)
                ).all()
                
        except Exception as e:
            self.logger.error(f"Failed to get inert fillers by material type {material_type}: {e}")
            raise ServiceError(f"Failed to retrieve inert fillers by material type: {e}")
    
    def calculate_volume_per_unit_mass(self, name: str) -> Optional[float]:
        """
        Calculate volume per unit mass for an inert filler.
        
        Args:
            name: Name of the inert filler material
            
        Returns:
            Volume per unit mass in m³/kg
        """
        try:
            filler = self.get_by_name(name)
            if not filler:
                raise NotFoundError(f"Inert filler '{name}' not found")
            
            return filler.get_volume_per_unit_mass()
            
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to calculate volume per unit mass for {name}: {e}")
            raise ServiceError(f"Failed to calculate volume per unit mass: {e}")
    
    def calculate_filler_efficiency_factor(self, name: str, cement_fineness: float = None) -> Dict[str, Any]:
        """
        Calculate filler efficiency factor based on fineness and composition.
        
        Args:
            name: Name of the inert filler material
            cement_fineness: Fineness of cement for comparison (optional)
            
        Returns:
            Dictionary with efficiency factor and calculation details
        """
        try:
            filler = self.get_by_name(name)
            if not filler:
                raise NotFoundError(f"Inert filler '{name}' not found")
            
            # Simplified filler efficiency calculation
            # Actual VCCTL may use more sophisticated models
            
            base_efficiency = 1.0
            
            # Material type factor (based on name/description)
            material_factors = {
                'quartz': 0.8,      # Lower efficiency due to inertness
                'limestone': 1.2,    # Higher efficiency due to some reactivity
                'silica': 0.9,      # Moderate efficiency
                'flyash': 1.3,      # High efficiency (though flyash isn't truly inert)
                'slag': 1.4         # Very high efficiency (though slag isn't truly inert)
            }
            
            material_factor = 1.0
            for material, factor in material_factors.items():
                if material in filler.name.lower() or (filler.description and material in filler.description.lower()):
                    material_factor = factor
                    break
            
            # Specific gravity factor (finer particles generally more efficient)
            # Higher specific gravity often correlates with finer particles for same material
            sg_factor = min(1.2, filler.specific_gravity / 2.7) if filler.specific_gravity else 1.0
            
            # Calculate overall efficiency
            efficiency_factor = base_efficiency * material_factor * sg_factor
            
            calculation_details = {
                'base_efficiency': base_efficiency,
                'material_factor': material_factor,
                'specific_gravity_factor': sg_factor,
                'overall_efficiency': efficiency_factor,
                'material_type_detected': next(
                    (material for material in material_factors.keys() 
                     if material in filler.name.lower()), 
                    'unknown'
                )
            }
            
            return calculation_details
            
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to calculate filler efficiency factor for {name}: {e}")
            raise ServiceError(f"Failed to calculate filler efficiency factor: {e}")
    
    def get_filler_statistics(self) -> Dict[str, Any]:
        """Get statistics about inert filler materials."""
        try:
            with self.db_service.get_read_only_session() as session:
                total_count = session.query(InertFiller).count()
                
                if total_count == 0:
                    return {'total_fillers': 0}
                
                fillers = session.query(InertFiller).all()
                
                # Calculate specific gravity statistics
                specific_gravities = [f.specific_gravity for f in fillers if f.specific_gravity is not None]
                avg_specific_gravity = sum(specific_gravities) / len(specific_gravities) if specific_gravities else 0
                min_specific_gravity = min(specific_gravities) if specific_gravities else 0
                max_specific_gravity = max(specific_gravities) if specific_gravities else 0
                
                # Count fillers with descriptions
                with_descriptions = len([f for f in fillers if f.has_description])
                
                # Get unique PSD types
                unique_psds = len(set(f.psd for f in fillers if f.psd))
                
                # Identify material types
                material_types = {}
                for filler in fillers:
                    detected_type = 'unknown'
                    for material_type in ['quartz', 'limestone', 'silica', 'flyash', 'slag']:
                        if material_type in filler.name.lower():
                            detected_type = material_type
                            break
                    
                    material_types[detected_type] = material_types.get(detected_type, 0) + 1
                
                return {
                    'total_fillers': total_count,
                    'with_descriptions': with_descriptions,
                    'percentage_with_descriptions': (with_descriptions / total_count * 100),
                    'average_specific_gravity': round(avg_specific_gravity, 3) if avg_specific_gravity else None,
                    'min_specific_gravity': min_specific_gravity,
                    'max_specific_gravity': max_specific_gravity,
                    'unique_psd_types': unique_psds,
                    'material_type_distribution': material_types
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get inert filler statistics: {e}")
            raise ServiceError(f"Failed to get inert filler statistics: {e}")
    
    def validate_for_concrete_mix(self, name: str, replacement_percentage: float = None, 
                                cement_type: str = None) -> Dict[str, Any]:
        """
        Validate inert filler suitability for concrete mix design.
        
        Args:
            name: Name of the inert filler material
            replacement_percentage: Percentage replacement of cement (optional)
            cement_type: Type of cement being used (optional)
            
        Returns:
            Validation results dictionary
        """
        try:
            filler = self.get_by_name(name)
            if not filler:
                raise NotFoundError(f"Inert filler '{name}' not found")
            
            validation_result = {
                'is_suitable': True,
                'warnings': [],
                'recommendations': [],
                'suitability_score': 0.0
            }
            
            score = 100.0  # Start with perfect score
            
            # Check specific gravity range
            if not filler.is_valid_specific_gravity:
                validation_result['warnings'].append("Specific gravity outside recommended range (2.0-5.0)")
                validation_result['is_suitable'] = False
                score -= 30
            
            # Check replacement percentage if provided
            if replacement_percentage is not None:
                if replacement_percentage > 20:
                    validation_result['warnings'].append("High filler content (>20%) may affect strength and workability")
                    score -= 15
                elif replacement_percentage > 30:
                    validation_result['warnings'].append("Very high filler content (>30%) not recommended for structural concrete")
                    score -= 25
                
                if replacement_percentage < 5:
                    validation_result['recommendations'].append("Low filler content - consider increasing for improved workability")
            
            # Material-specific recommendations
            if 'limestone' in filler.name.lower():
                validation_result['recommendations'].append("Limestone filler: excellent for workability and some pozzolanic activity")
                score += 10
            elif 'quartz' in filler.name.lower():
                validation_result['recommendations'].append("Quartz filler: chemically inert, good for dimensional stability")
                score += 5
            elif 'silica' in filler.name.lower():
                validation_result['recommendations'].append("Silica filler: may provide some pozzolanic activity at fine sizes")
                score += 8
            
            # Check if has description for better material understanding
            if not filler.has_description:
                validation_result['warnings'].append("No description available - material properties uncertain")
                score -= 5
            
            validation_result['suitability_score'] = max(0.0, min(100.0, score))
            
            if score < 60:
                validation_result['is_suitable'] = False
            
            return validation_result
            
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to validate inert filler for concrete mix: {e}")
            raise ServiceError(f"Failed to validate inert filler for concrete mix: {e}")
    
    def get_recommended_fillers_for_application(self, application: str) -> List[Dict[str, Any]]:
        """
        Get recommended fillers for specific applications.
        
        Args:
            application: Application type ('high_strength', 'workability', 'durability', etc.)
            
        Returns:
            List of recommended fillers with suitability scores
        """
        try:
            all_fillers = self.get_all()
            recommendations = []
            
            for filler in all_fillers:
                suitability = 0.0
                reasons = []
                
                if application == 'high_strength':
                    if 'silica' in filler.name.lower():
                        suitability = 85.0
                        reasons.append("Silica fume provides high strength gain")
                    elif 'limestone' in filler.name.lower():
                        suitability = 70.0
                        reasons.append("Limestone filler provides moderate strength contribution")
                    else:
                        suitability = 60.0
                        reasons.append("General filler effect")
                
                elif application == 'workability':
                    if 'limestone' in filler.name.lower():
                        suitability = 90.0
                        reasons.append("Limestone excellent for workability improvement")
                    elif filler.specific_gravity and filler.specific_gravity > 2.8:
                        suitability = 75.0
                        reasons.append("Higher specific gravity helps with workability")
                    else:
                        suitability = 65.0
                        reasons.append("Standard filler workability benefit")
                
                elif application == 'durability':
                    if 'quartz' in filler.name.lower():
                        suitability = 85.0
                        reasons.append("Quartz provides excellent chemical resistance")
                    elif 'limestone' in filler.name.lower():
                        suitability = 75.0
                        reasons.append("Limestone provides good durability")
                    else:
                        suitability = 70.0
                        reasons.append("General durability contribution")
                
                else:
                    suitability = 70.0  # Default for unknown applications
                    reasons.append("General purpose filler")
                
                recommendations.append({
                    'filler': filler,
                    'suitability_score': suitability,
                    'reasons': reasons
                })
            
            # Sort by suitability score (highest first)
            recommendations.sort(key=lambda x: x['suitability_score'], reverse=True)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to get recommended fillers for {application}: {e}")
            raise ServiceError(f"Failed to get recommendations: {e}")