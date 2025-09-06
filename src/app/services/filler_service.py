#!/usr/bin/env python3
"""
Filler Service for VCCTL

Provides business logic for filler material management.
Simplified from InertFillerService for cleaner UI terminology.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError

from app.database.service import DatabaseService
from app.models.filler import Filler, FillerCreate, FillerUpdate, FillerResponse
from app.services.base_service import BaseService, ServiceError, NotFoundError, AlreadyExistsError, ValidationError


class FillerService(BaseService[Filler, FillerCreate, FillerUpdate]):
    """
    Service for managing filler materials.
    
    Provides CRUD operations, validation, and property calculations
    for filler materials in the VCCTL system.
    """
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(Filler, db_service)
        self.logger = logging.getLogger('VCCTL.FillerService')
        self.default_psd = 'cement141'
        self.default_specific_gravity = 3.0
    
    def get_all(self) -> List[Filler]:
        """Get all filler materials."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Filler).order_by(Filler.name).all()
        except Exception as e:
            self.logger.error(f"Failed to get all fillers: {e}")
            raise ServiceError(f"Failed to retrieve fillers: {e}")
    
    def get_by_name(self, name: str) -> Optional[Filler]:
        """Get filler by name (primary key)."""
        if not name or not name.strip():
            raise ValidationError("Name is required")
        
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(Filler).filter(Filler.name == name.strip()).first()
        except Exception as e:
            self.logger.error(f"Failed to get filler {name}: {e}")
            raise ServiceError(f"Failed to retrieve filler: {e}")
    
    def create(self, filler_data: FillerCreate) -> FillerResponse:
        """Create a new filler material."""
        try:
            # Validate required fields
            if not filler_data.name or not filler_data.name.strip():
                raise ValidationError("Name is required")
            
            # Check if filler already exists
            existing = self.get_by_name(filler_data.name)
            if existing:
                raise AlreadyExistsError(f"Filler '{filler_data.name}' already exists")
            
            # Create filler
            with self.db_service.get_session() as session:
                filler = Filler(**filler_data.model_dump())
                session.add(filler)
                session.commit()
                session.refresh(filler)
                
                self.logger.info(f"Created filler: {filler.name}")
                return FillerResponse.model_validate(filler)
                
        except (AlreadyExistsError, ValidationError):
            raise
        except IntegrityError as e:
            self.logger.error(f"Integrity error creating filler {filler_data.name}: {e}")
            raise AlreadyExistsError(f"Filler '{filler_data.name}' already exists")
        except Exception as e:
            self.logger.error(f"Failed to create filler {filler_data.name}: {e}")
            raise ServiceError(f"Failed to create filler: {e}")
    
    def update(self, filler_id: int, update_data: FillerUpdate) -> FillerResponse:
        """Update an existing filler material."""
        try:
            with self.db_service.get_session() as session:
                filler = session.query(Filler).filter(Filler.id == filler_id).first()
                if not filler:
                    raise NotFoundError(f"Filler with ID '{filler_id}' not found")
                
                # Update fields
                update_dict = update_data.model_dump(exclude_unset=True)
                for field, value in update_dict.items():
                    setattr(filler, field, value)
                
                session.commit()
                session.refresh(filler)
                
                self.logger.info(f"Updated filler: {filler.name}")
                return FillerResponse.model_validate(filler)
                
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to update filler {name}: {e}")
            raise ServiceError(f"Failed to update filler: {e}")
    
    def delete(self, name: str) -> bool:
        """Delete a filler material."""
        if not name or not name.strip():
            raise ValidationError("Name is required")
        
        try:
            with self.db_service.get_session() as session:
                filler = session.query(Filler).filter(Filler.name == name.strip()).first()
                if not filler:
                    raise NotFoundError(f"Filler '{name}' not found")
                
                session.delete(filler)
                session.commit()
                
                self.logger.info(f"Deleted filler: {name}")
                return True
                
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete filler {name}: {e}")
            raise ServiceError(f"Failed to delete filler: {e}")
    
    def get_names(self) -> List[str]:
        """Get all filler names for dropdowns."""
        try:
            with self.db_service.get_read_only_session() as session:
                return [name[0] for name in session.query(Filler.name).order_by(Filler.name).all()]
        except Exception as e:
            self.logger.error(f"Failed to get filler names: {e}")
            raise ServiceError(f"Failed to retrieve filler names: {e}")
    
    def exists(self, name: str) -> bool:
        """Check if a filler exists."""
        try:
            return self.get_by_name(name) is not None
        except ServiceError:
            return False
    
    def validate_filler_data(self, filler_data: FillerCreate) -> None:
        """Validate filler data before creation."""
        if not filler_data.name or not filler_data.name.strip():
            raise ValidationError("Name is required")
        
        # Additional validation rules
        if filler_data.specific_gravity is not None:
            if filler_data.specific_gravity <= 0:
                raise ValidationError("Specific gravity must be positive")
            if filler_data.specific_gravity >= 10:
                raise ValidationError("Specific gravity must be less than 10")
        
        if filler_data.specific_surface_area is not None:
            if filler_data.specific_surface_area < 0:
                raise ValidationError("Specific surface area cannot be negative")
        
        # Validate particle size distribution consistency
        d10 = filler_data.diameter_percentile_10
        d50 = filler_data.diameter_percentile_50
        d90 = filler_data.diameter_percentile_90
        
        if d10 is not None and d50 is not None and d10 >= d50:
            raise ValidationError("D10 must be less than D50")
        
        if d50 is not None and d90 is not None and d50 >= d90:
            raise ValidationError("D50 must be less than D90")
        
        if d10 is not None and d90 is not None and d10 >= d90:
            raise ValidationError("D10 must be less than D90")