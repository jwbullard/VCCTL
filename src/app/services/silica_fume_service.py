#!/usr/bin/env python3
"""
Silica Fume Service for VCCTL

Provides business logic for silica fume material management.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError

from app.database.service import DatabaseService
from app.models.silica_fume import SilicaFume, SilicaFumeCreate, SilicaFumeUpdate, SilicaFumeResponse
from app.services.base_service import BaseService, ServiceError, NotFoundError, AlreadyExistsError, ValidationError


class SilicaFumeService(BaseService[SilicaFume, SilicaFumeCreate, SilicaFumeUpdate]):
    """
    Service for managing silica fume materials.
    
    Provides CRUD operations, validation, and specialized calculations
    for silica fume materials in the VCCTL system.
    """
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(SilicaFume, db_service)
        self.logger = logging.getLogger('VCCTL.SilicaFumeService')
        self.default_psd = 'cement141'
        self.default_specific_gravity = 2.22
    
    def get_all(self) -> List[SilicaFume]:
        """Get all silica fume materials."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(SilicaFume).order_by(SilicaFume.name).all()
        except Exception as e:
            self.logger.error(f"Failed to get all silica fume materials: {e}")
            raise ServiceError(f"Failed to retrieve silica fume materials: {e}")
    
    def get_by_name(self, name: str) -> Optional[SilicaFume]:
        """Get silica fume by name."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(SilicaFume).filter_by(name=name).first()
        except Exception as e:
            self.logger.error(f"Failed to get silica fume {name}: {e}")
            raise ServiceError(f"Failed to retrieve silica fume: {e}")
    
    def create(self, silica_fume_data: SilicaFumeCreate) -> SilicaFume:
        """Create a new silica fume material."""
        try:
            # Validate data
            if not silica_fume_data.name or not silica_fume_data.name.strip():
                raise ValidationError("Silica fume name is required")
            
            # Check if already exists
            existing = self.get_by_name(silica_fume_data.name)
            if existing:
                raise AlreadyExistsError(f"Silica fume '{silica_fume_data.name}' already exists")
            
            # Create new silica fume
            with self.db_service.get_session() as session:
                silica_fume = SilicaFume(**silica_fume_data.model_dump())
                session.add(silica_fume)
                session.commit()
                session.refresh(silica_fume)
                
                self.logger.info(f"Created silica fume: {silica_fume.name}")
                return silica_fume
                
        except (AlreadyExistsError, ValidationError):
            raise
        except IntegrityError as e:
            self.logger.error(f"Database integrity error creating silica fume: {e}")
            raise AlreadyExistsError(f"Silica fume '{silica_fume_data.name}' already exists")
        except Exception as e:
            self.logger.error(f"Failed to create silica fume: {e}")
            raise ServiceError(f"Failed to create silica fume: {e}")
    
    def update(self, silica_fume_id: int, update_data: SilicaFumeUpdate) -> SilicaFume:
        """Update an existing silica fume material."""
        try:
            with self.db_service.get_session() as session:
                silica_fume = session.query(SilicaFume).filter_by(id=silica_fume_id).first()
                
                if not silica_fume:
                    raise NotFoundError(f"Silica fume with ID '{silica_fume_id}' not found")
                
                # Update fields
                update_dict = update_data.model_dump(exclude_unset=True)
                for field, value in update_dict.items():
                    setattr(silica_fume, field, value)
                
                session.commit()
                session.refresh(silica_fume)
                
                self.logger.info(f"Updated silica fume: {silica_fume.name}")
                return silica_fume
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update silica fume {silica_fume_id}: {e}")
            raise ServiceError(f"Failed to update silica fume: {e}")
    
    def delete(self, name: str) -> bool:
        """Delete a silica fume material."""
        try:
            with self.db_service.get_session() as session:
                silica_fume = session.query(SilicaFume).filter_by(name=name).first()
                
                if not silica_fume:
                    raise NotFoundError(f"Silica fume '{name}' not found")
                
                session.delete(silica_fume)
                session.commit()
                
                self.logger.info(f"Deleted silica fume: {name}")
                return True
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete silica fume {name}: {e}")
            raise ServiceError(f"Failed to delete silica fume: {e}")
    
    def duplicate(self, source_name: str, new_name: str, description: Optional[str] = None) -> SilicaFume:
        """Duplicate an existing silica fume with a new name."""
        try:
            # Get source silica fume
            source = self.get_by_name(source_name)
            if not source:
                raise NotFoundError(f"Source silica fume '{source_name}' not found")
            
            # Check if new name already exists
            if self.get_by_name(new_name):
                raise AlreadyExistsError(f"Silica fume '{new_name}' already exists")
            
            # Create duplicate
            create_data = SilicaFumeCreate(
                name=new_name,
                specific_gravity=source.specific_gravity,
                psd=source.psd,
                distribute_phases_by=source.distribute_phases_by,
                silica_fume_fraction=source.silica_fume_fraction,
                description=description or f"Copy of {source.name}"
            )
            
            return self.create(create_data)
            
        except (NotFoundError, AlreadyExistsError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to duplicate silica fume {source_name}: {e}")
            raise ServiceError(f"Failed to duplicate silica fume: {e}")
    
    def validate_composition(self, silica_fume: SilicaFume) -> Dict[str, Any]:
        """Validate silica fume composition and return analysis."""
        try:
            analysis = {
                'is_valid': True,
                'warnings': [],
                'errors': [],
                'total_phase_fraction': silica_fume.total_phase_fraction,
                'has_complete_data': silica_fume.has_complete_phase_data
            }
            
            # Check phase fraction
            if silica_fume.silica_fume_fraction is None:
                analysis['warnings'].append("No phase fraction data")
                analysis['has_complete_data'] = False
            elif not (0 <= silica_fume.silica_fume_fraction <= 1):
                analysis['errors'].append("Phase fraction must be between 0 and 1")
                analysis['is_valid'] = False
            
            # Check specific gravity
            if silica_fume.specific_gravity is None:
                analysis['warnings'].append("No specific gravity data")
            elif silica_fume.specific_gravity <= 0:
                analysis['errors'].append("Specific gravity must be positive")
                analysis['is_valid'] = False
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Failed to validate silica fume composition: {e}")
            raise ServiceError(f"Failed to validate composition: {e}")
    
    def get_names(self) -> List[str]:
        """Get list of all silica fume names."""
        try:
            with self.db_service.get_read_only_session() as session:
                return [name[0] for name in session.query(SilicaFume.name).order_by(SilicaFume.name).all()]
        except Exception as e:
            self.logger.error(f"Failed to get silica fume names: {e}")
            raise ServiceError(f"Failed to retrieve silica fume names: {e}")
    
    def search(self, query: str) -> List[SilicaFume]:
        """Search silica fume materials by name or description."""
        try:
            with self.db_service.get_read_only_session() as session:
                search_pattern = f"%{query}%"
                return session.query(SilicaFume).filter(
                    (SilicaFume.name.ilike(search_pattern)) |
                    (SilicaFume.description.ilike(search_pattern))
                ).order_by(SilicaFume.name).all()
        except Exception as e:
            self.logger.error(f"Failed to search silica fume materials: {e}")
            raise ServiceError(f"Failed to search silica fume materials: {e}")