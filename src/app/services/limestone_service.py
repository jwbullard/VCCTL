#!/usr/bin/env python3
"""
Limestone Service for VCCTL

Provides business logic for limestone material management.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app.database.service import DatabaseService
from app.models.limestone import Limestone, LimestoneCreate, LimestoneUpdate, LimestoneResponse
from app.services.base_service import BaseService, ServiceError, NotFoundError, AlreadyExistsError, ValidationError


class LimestoneService(BaseService[Limestone, LimestoneCreate, LimestoneUpdate]):
    """
    Service for managing limestone materials.
    
    Provides CRUD operations, validation, and specialized calculations
    for limestone materials in the VCCTL system.
    """
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(Limestone, db_service)
        self.logger = logging.getLogger('VCCTL.LimestoneService')
        self.default_psd = 'cement141'
    
    def _clean_psd_parameters(self, psd_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean PSD data to only include parameters relevant to the mode."""
        mode = psd_data.get('psd_mode')
        if not mode:
            return psd_data
            
        # Define which parameters are valid for each mode
        mode_params = {
            'rosin_rammler': ['psd_mode', 'psd_d50', 'psd_n', 'psd_dmax'],
            'log_normal': ['psd_mode', 'psd_median', 'psd_spread'],
            'fuller': ['psd_mode', 'psd_exponent', 'psd_dmax'],
            'custom': ['psd_mode', 'psd_custom_points']
        }
        
        if mode not in mode_params:
            return psd_data
        
        # Create cleaned data with only relevant parameters
        valid_params = mode_params[mode]
        cleaned_data = {}
        
        # Set mode first
        cleaned_data['psd_mode'] = mode
        
        # Add relevant parameters from input
        for param in valid_params:
            if param in psd_data:
                cleaned_data[param] = psd_data[param]
        
        # Explicitly set irrelevant PSD parameters to None
        all_psd_params = ['psd_d50', 'psd_n', 'psd_dmax', 'psd_median', 
                          'psd_spread', 'psd_exponent', 'psd_custom_points']
        for param in all_psd_params:
            if param not in valid_params:
                cleaned_data[param] = None
        
        return cleaned_data
        self.default_specific_gravity = 2.71
    
    def get_all(self) -> List[Limestone]:
        """Get all limestone materials with eagerly loaded PSD relationships."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Limestone).options(joinedload(Limestone.psd_data)).order_by(Limestone.name).all()
        except Exception as e:
            self.logger.error(f"Failed to get all limestone materials: {e}")
            raise ServiceError(f"Failed to retrieve limestone materials: {e}")
    
    def get_by_name(self, name: str) -> Optional[Limestone]:
        """Get limestone by name with eagerly loaded PSD relationship."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Limestone).options(joinedload(Limestone.psd_data)).filter_by(name=name).first()
        except Exception as e:
            self.logger.error(f"Failed to get limestone {name}: {e}")
            raise ServiceError(f"Failed to retrieve limestone: {e}")
    
    def create(self, limestone_data: LimestoneCreate) -> Limestone:
        """Create a new limestone material."""
        try:
            # Validate data
            if not limestone_data.name or not limestone_data.name.strip():
                raise ValidationError("Limestone name is required")
            
            # Check if already exists
            existing = self.get_by_name(limestone_data.name)
            if existing:
                raise AlreadyExistsError(f"Limestone '{limestone_data.name}' already exists")
            
            # Create new limestone
            with self.db_service.get_session() as session:
                # Extract PSD fields from create data if present
                create_dict = limestone_data.model_dump(exclude_unset=True)
                psd_fields = ['psd_mode', 'psd_d50', 'psd_n', 'psd_dmax', 'psd_median', 
                             'psd_spread', 'psd_exponent', 'psd_custom_points']
                psd_data = {}
                
                # Separate PSD fields from limestone fields
                for field in list(create_dict.keys()):
                    if field in psd_fields:
                        psd_data[field] = create_dict.pop(field)
                
                # Create limestone
                limestone = Limestone(**create_dict)
                
                # Handle PSD data if any PSD fields were provided
                if psd_data:
                    from app.models.psd_data import PSDData
                    # Clean PSD data to only include relevant parameters
                    cleaned_psd_data = self._clean_psd_parameters(psd_data)
                    new_psd = PSDData(**cleaned_psd_data)
                    session.add(new_psd)
                    session.flush()  # Get the ID
                    limestone.psd_data = new_psd
                    limestone.psd_data_id = new_psd.id
                
                session.add(limestone)
                session.commit()
                session.refresh(limestone)
                
                self.logger.info(f"Created limestone: {limestone.name}")
                return limestone
                
        except (AlreadyExistsError, ValidationError):
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error creating limestone: {e}")
            raise AlreadyExistsError(f"Limestone '{limestone_data.name}' already exists")
        except Exception as e:
            self.logger.error(f"Failed to create limestone: {e}")
            raise ServiceError(f"Failed to create limestone: {e}")
    
    def update(self, limestone_id: int, update_data: LimestoneUpdate) -> Limestone:
        """Update an existing limestone material."""
        try:
            with self.db_service.get_session() as session:
                limestone = session.query(Limestone).options(joinedload(Limestone.psd_data)).filter_by(id=limestone_id).first()
                
                if not limestone:
                    raise NotFoundError(f"Limestone with ID '{limestone_id}' not found")
                
                # Extract PSD fields from update data if present
                update_dict = update_data.model_dump(exclude_unset=True)
                psd_fields = ['psd_mode', 'psd_d50', 'psd_n', 'psd_dmax', 'psd_median', 
                             'psd_spread', 'psd_exponent', 'psd_custom_points']
                psd_data = {}
                
                # Separate PSD fields from limestone fields
                for field in list(update_dict.keys()):
                    if field in psd_fields:
                        psd_data[field] = update_dict.pop(field)
                
                # Handle PSD data if any PSD fields were provided
                if psd_data:
                    from app.models.psd_data import PSDData
                    
                    # Clean PSD data to only include relevant parameters
                    cleaned_psd_data = self._clean_psd_parameters(psd_data)
                    
                    if limestone.psd_data_id and limestone.psd_data:
                        # Update existing PSD data with cleaned values
                        for field, value in cleaned_psd_data.items():
                            setattr(limestone.psd_data, field, value)
                    else:
                        # Create new PSD data with cleaned values
                        new_psd = PSDData(**cleaned_psd_data)
                        session.add(new_psd)
                        session.flush()  # Get the ID
                        limestone.psd_data = new_psd
                        limestone.psd_data_id = new_psd.id
                
                # Update remaining limestone fields
                for field, value in update_dict.items():
                    if hasattr(limestone, field):
                        setattr(limestone, field, value)
                
                session.commit()
                session.refresh(limestone)
                
                self.logger.info(f"Updated limestone: {limestone.name}")
                return limestone
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update limestone {limestone_id}: {e}")
            raise ServiceError(f"Failed to update limestone: {e}")
    
    def delete(self, name: str) -> bool:
        """Delete a limestone material."""
        try:
            with self.db_service.get_session() as session:
                limestone = session.query(Limestone).filter_by(name=name).first()
                
                if not limestone:
                    raise NotFoundError(f"Limestone '{name}' not found")
                
                session.delete(limestone)
                session.commit()
                
                self.logger.info(f"Deleted limestone: {name}")
                return True
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete limestone {name}: {e}")
            raise ServiceError(f"Failed to delete limestone: {e}")
    
    def duplicate(self, source_name: str, new_name: str, description: Optional[str] = None) -> Limestone:
        """Duplicate an existing limestone with a new name."""
        try:
            # Get source limestone
            source = self.get_by_name(source_name)
            if not source:
                raise NotFoundError(f"Source limestone '{source_name}' not found")
            
            # Check if new name already exists
            if self.get_by_name(new_name):
                raise AlreadyExistsError(f"Limestone '{new_name}' already exists")
            
            # Create duplicate
            create_dict = {
                'name': new_name,
                'specific_gravity': source.specific_gravity,
                'distribute_phases_by': source.distribute_phases_by,
                'caco3_content': source.caco3_content,
                'specific_surface_area': source.specific_surface_area,
                'activation_energy': source.activation_energy,
                'description': description or f"Copy of {source.name}",
                'source': source.source,
                'notes': source.notes
            }
            
            # Copy PSD data if available
            if source.psd_data:
                create_dict.update({
                    'psd_mode': source.psd_data.psd_mode,
                    'psd_d50': source.psd_data.psd_d50,
                    'psd_n': source.psd_data.psd_n,
                    'psd_dmax': source.psd_data.psd_dmax,
                    'psd_median': source.psd_data.psd_median,
                    'psd_spread': source.psd_data.psd_spread,
                    'psd_exponent': source.psd_data.psd_exponent,
                    'psd_custom_points': source.psd_data.psd_custom_points
                })
            
            create_data = LimestoneCreate(**create_dict)
            
            return self.create(create_data)
            
        except (NotFoundError, AlreadyExistsError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to duplicate limestone {source_name}: {e}")
            raise ServiceError(f"Failed to duplicate limestone: {e}")
    
    def validate_composition(self, limestone: Limestone) -> Dict[str, Any]:
        """Validate limestone composition and return analysis."""
        try:
            analysis = {
                'is_valid': True,
                'warnings': [],
                'errors': [],
                'total_phase_fraction': limestone.total_phase_fraction,
                'has_complete_data': limestone.has_complete_phase_data
            }
            
            # Check phase fraction
            if limestone.limestone_fraction is None:
                analysis['warnings'].append("No phase fraction data")
                analysis['has_complete_data'] = False
            elif not (0 <= limestone.limestone_fraction <= 1):
                analysis['errors'].append("Phase fraction must be between 0 and 1")
                analysis['is_valid'] = False
            
            # Check specific gravity
            if limestone.specific_gravity is None:
                analysis['warnings'].append("No specific gravity data")
            elif limestone.specific_gravity <= 0:
                analysis['errors'].append("Specific gravity must be positive")
                analysis['is_valid'] = False
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to validate limestone composition: {e}")
            raise ServiceError(f"Failed to validate composition: {e}")
    
    def get_names(self) -> List[str]:
        """Get list of all limestone names."""
        try:
            with self.db_service.get_read_only_session() as session:
                return [name[0] for name in session.query(Limestone.name).order_by(Limestone.name).all()]
        except Exception as e:
            self.logger.error(f"Failed to get limestone names: {e}")
            raise ServiceError(f"Failed to retrieve limestone names: {e}")
    
    def search(self, query: str) -> List[Limestone]:
        """Search limestone materials by name or description."""
        try:
            with self.db_service.get_read_only_session() as session:
                search_pattern = f"%{query}%"
                return session.query(Limestone).filter(
                    (Limestone.name.ilike(search_pattern)) |
                    (Limestone.description.ilike(search_pattern))
                ).order_by(Limestone.name).all()
        except Exception as e:
            self.logger.error(f"Failed to search limestone materials: {e}")
            raise ServiceError(f"Failed to search limestone materials: {e}")