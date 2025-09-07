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
from sqlalchemy.orm import joinedload

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
        """Get all slag materials with eagerly loaded PSD relationships."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Slag).options(joinedload(Slag.psd_data)).order_by(Slag.name).all()
        except Exception as e:
            self.logger.error(f"Failed to get all slag materials: {e}")
            raise ServiceError(f"Failed to retrieve slag materials: {e}")
    
    def get_by_name(self, name: str) -> Optional[Slag]:
        """Get slag by name with eagerly loaded PSD relationship."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Slag).options(joinedload(Slag.psd_data)).filter_by(name=name).first()
        except Exception as e:
            self.logger.error(f"Failed to get slag {name}: {e}")
            raise ServiceError(f"Failed to retrieve slag: {e}")
    
    def create(self, slag_data: SlagCreate) -> Slag:
        """Create a new slag material."""
        try:
            # Validate data
            if not slag_data.name or not slag_data.name.strip():
                raise ValidationError("Slag name is required")
            
            # Check if already exists
            existing = self.get_by_name(slag_data.name)
            if existing:
                raise AlreadyExistsError(f"Slag '{slag_data.name}' already exists")
            
            # Create new slag
            with self.db_service.get_session() as session:
                # Extract PSD fields from create data if present
                create_dict = slag_data.model_dump(exclude_unset=True)
                psd_fields = ['psd_mode', 'psd_d50', 'psd_n', 'psd_dmax', 'psd_median', 
                             'psd_spread', 'psd_exponent', 'psd_custom_points']
                psd_data = {}
                
                # Separate PSD fields from slag fields
                for field in list(create_dict.keys()):
                    if field in psd_fields:
                        psd_data[field] = create_dict.pop(field)
                
                # Create slag
                slag = Slag(**create_dict)
                
                # Handle PSD data if any PSD fields were provided
                if psd_data:
                    from app.models.psd_data import PSDData
                    new_psd = PSDData(**psd_data)
                    session.add(new_psd)
                    session.flush()  # Get the ID
                    slag.psd_data = new_psd
                    slag.psd_data_id = new_psd.id
                
                session.add(slag)
                session.commit()
                session.refresh(slag)
                
                self.logger.info(f"Created slag: {slag.name}")
                return slag
                
        except (AlreadyExistsError, ValidationError):
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error creating slag: {e}")
            raise AlreadyExistsError(f"Slag '{slag_data.name}' already exists")
        except Exception as e:
            self.logger.error(f"Failed to create slag: {e}")
            raise ServiceError(f"Failed to create slag: {e}")
    
    def update(self, slag_id: int, update_data: SlagUpdate) -> Slag:
        """Update an existing slag material."""
        try:
            with self.db_service.get_session() as session:
                slag = session.query(Slag).options(joinedload(Slag.psd_data)).filter_by(id=slag_id).first()
                
                if not slag:
                    raise NotFoundError(f"Slag with ID '{slag_id}' not found")
                
                # Extract PSD fields from update data if present
                update_dict = update_data.model_dump(exclude_unset=True)
                psd_fields = ['psd_mode', 'psd_d50', 'psd_n', 'psd_dmax', 'psd_median', 
                             'psd_spread', 'psd_exponent', 'psd_custom_points']
                psd_data = {}
                
                # Separate PSD fields from slag fields
                for field in list(update_dict.keys()):
                    if field in psd_fields:
                        psd_data[field] = update_dict.pop(field)
                
                # Handle PSD data if any PSD fields were provided
                if psd_data:
                    from app.models.psd_data import PSDData
                    
                    if slag.psd_data_id and slag.psd_data:
                        # Update existing PSD data
                        for field, value in psd_data.items():
                            setattr(slag.psd_data, field, value)
                    else:
                        # Create new PSD data
                        new_psd = PSDData(**psd_data)
                        session.add(new_psd)
                        session.flush()  # Get the ID
                        slag.psd_data = new_psd
                        slag.psd_data_id = new_psd.id
                
                # Update remaining slag fields
                for field, value in update_dict.items():
                    if hasattr(slag, field):
                        setattr(slag, field, value)
                
                session.commit()
                session.refresh(slag)
                
                self.logger.info(f"Updated slag: {slag.name}")
                return slag
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update slag {slag_id}: {e}")
            raise ServiceError(f"Failed to update slag: {e}")
    
    def delete(self, name: str) -> bool:
        """Delete a slag material."""
        try:
            with self.db_service.get_session() as session:
                slag = session.query(Slag).filter_by(name=name).first()
                
                if not slag:
                    raise NotFoundError(f"Slag '{name}' not found")
                
                session.delete(slag)
                session.commit()
                
                self.logger.info(f"Deleted slag: {name}")
                return True
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete slag {name}: {e}")
            raise ServiceError(f"Failed to delete slag: {e}")
    
    def duplicate(self, source_name: str, new_name: str, description: Optional[str] = None) -> Slag:
        """Duplicate an existing slag with a new name."""
        try:
            # Get source slag
            source = self.get_by_name(source_name)
            if not source:
                raise NotFoundError(f"Source slag '{source_name}' not found")
            
            # Check if new name already exists
            if self.get_by_name(new_name):
                raise AlreadyExistsError(f"Slag '{new_name}' already exists")
            
            # Create duplicate
            create_data = SlagCreate(
                name=new_name,
                specific_gravity=source.specific_gravity,
                glass_content=source.glass_content,
                specific_surface_area=source.specific_surface_area,
                activation_energy=source.activation_energy,
                reactivity_factor=source.reactivity_factor,
                rate_constant=source.rate_constant,
                molecular_mass=source.molecular_mass,
                casi_mol_ratio=source.casi_mol_ratio,
                si_per_mole=source.si_per_mole,
                base_slag_reactivity=source.base_slag_reactivity,
                c3a_per_mole=source.c3a_per_mole,
                hp_molecular_mass=source.hp_molecular_mass,
                hp_density=source.hp_density,
                hp_casi_mol_ratio=source.hp_casi_mol_ratio,
                hp_h2o_si_mol_ratio=source.hp_h2o_si_mol_ratio,
                description=description or f"Copy of {source.name}"
            )
            
            return self.create(create_data)
            
        except (NotFoundError, AlreadyExistsError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to duplicate slag {source_name}: {e}")
            raise ServiceError(f"Failed to duplicate slag: {e}")
    
    def validate_composition(self, slag: Slag) -> Dict[str, Any]:
        """Validate slag composition and return analysis."""
        try:
            analysis = {
                'is_valid': True,
                'warnings': [],
                'errors': [],
                'has_complete_molecular_data': slag.has_complete_molecular_data,
                'has_complete_hp_data': slag.has_complete_hp_data,
                'has_reactivity_data': slag.has_reactivity_data
            }
            
            # Check molecular ratios
            if not slag.validate_molecular_ratios():
                analysis['errors'].append("Invalid molecular ratios")
                analysis['is_valid'] = False
            
            # Check specific gravity
            if slag.specific_gravity is None:
                analysis['warnings'].append("No specific gravity data")
            elif slag.specific_gravity <= 0:
                analysis['errors'].append("Specific gravity must be positive")
                analysis['is_valid'] = False
            
            # Check completeness
            if not slag.has_complete_molecular_data:
                analysis['warnings'].append("Incomplete molecular data")
            
            if not slag.has_reactivity_data:
                analysis['warnings'].append("No reactivity data")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to validate slag composition: {e}")
            raise ServiceError(f"Failed to validate composition: {e}")
    
    def get_names(self) -> List[str]:
        """Get list of all slag names."""
        try:
            with self.db_service.get_read_only_session() as session:
                return [name[0] for name in session.query(Slag.name).order_by(Slag.name).all()]
        except Exception as e:
            self.logger.error(f"Failed to get slag names: {e}")
            raise ServiceError(f"Failed to retrieve slag names: {e}")
    
    def search(self, query: str) -> List[Slag]:
        """Search slag materials by name or description."""
        try:
            with self.db_service.get_read_only_session() as session:
                search_pattern = f"%{query}%"
                return session.query(Slag).filter(
                    (Slag.name.ilike(search_pattern)) |
                    (Slag.description.ilike(search_pattern))
                ).order_by(Slag.name).all()
        except Exception as e:
            self.logger.error(f"Failed to search slag materials: {e}")
            raise ServiceError(f"Failed to search slag materials: {e}")