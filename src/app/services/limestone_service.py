#!/usr/bin/env python3
"""
Limestone Service for VCCTL

Provides business logic for limestone material management.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError

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
        self.default_specific_gravity = 2.71
    
    def get_all(self) -> List[Limestone]:
        """Get all limestone materials."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Limestone).order_by(Limestone.name).all()
        except Exception as e:
            self.logger.error(f"Failed to get all limestone materials: {e}")
            raise ServiceError(f"Failed to retrieve limestone materials: {e}")
    
    def get_by_name(self, name: str) -> Optional[Limestone]:
        """Get limestone by name."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Limestone).filter_by(name=name).first()
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
                limestone = Limestone(**limestone_data.model_dump())
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
    
    def update(self, name: str, update_data: LimestoneUpdate) -> Limestone:
        """Update an existing limestone material."""
        try:
            with self.db_service.get_session() as session:
                limestone = session.query(Limestone).filter_by(name=name).first()
                
                if not limestone:
                    raise NotFoundError(f"Limestone '{name}' not found")
                
                # Update fields
                update_dict = update_data.model_dump(exclude_unset=True)
                for field, value in update_dict.items():
                    setattr(limestone, field, value)
                
                session.commit()
                session.refresh(limestone)
                
                self.logger.info(f"Updated limestone: {name}")
                return limestone
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to update limestone {name}: {e}")
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
            create_data = LimestoneCreate(
                name=new_name,
                specific_gravity=source.specific_gravity,
                psd=source.psd,
                distribute_phases_by=source.distribute_phases_by,
                limestone_fraction=source.limestone_fraction,
                description=description or f"Copy of {source.name}"
            )
            
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