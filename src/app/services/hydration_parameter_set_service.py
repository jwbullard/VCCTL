#!/usr/bin/env python3
"""
Hydration Parameter Set Service for VCCTL

Provides business logic for hydration parameter set management and CRUD operations.
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.service import DatabaseService
from app.models.hydration_parameter_set import HydrationParameterSet, HydrationParameterSetCreate, HydrationParameterSetUpdate, HydrationParameterSetResponse
from app.services.base_service import BaseService, ServiceError, NotFoundError, AlreadyExistsError, ValidationError


class HydrationParameterSetService(BaseService[HydrationParameterSet, HydrationParameterSetCreate, HydrationParameterSetUpdate]):
    """
    Service for managing hydration parameter sets.
    
    Provides CRUD operations, validation, and business logic
    for hydration simulation parameter configurations in the VCCTL system.
    """
    
    def __init__(self, db_service: DatabaseService):
        super().__init__(HydrationParameterSet, db_service)
        self.logger = logging.getLogger('VCCTL.HydrationParameterSetService')
    
    def get_all(self) -> List[HydrationParameterSet]:
        """Get all hydration parameter sets ordered by creation date (newest first)."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(HydrationParameterSet).order_by(HydrationParameterSet.created_at.desc()).all()
        except Exception as e:
            self.logger.error(f"Failed to get all hydration parameter sets: {e}")
            raise ServiceError(f"Failed to retrieve hydration parameter sets: {e}")
    
    def get_templates(self) -> List[HydrationParameterSet]:
        """Get all template hydration parameter sets."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(HydrationParameterSet).filter(
                    HydrationParameterSet.is_template == True
                ).order_by(HydrationParameterSet.name).all()
        except Exception as e:
            self.logger.error(f"Failed to get template hydration parameter sets: {e}")
            raise ServiceError(f"Failed to retrieve template hydration parameter sets: {e}")
    
    def get_by_id(self, param_set_id: int) -> Optional[HydrationParameterSet]:
        """Get hydration parameter set by ID."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(HydrationParameterSet).filter(
                    HydrationParameterSet.id == param_set_id
                ).first()
        except Exception as e:
            self.logger.error(f"Failed to get hydration parameter set by ID {param_set_id}: {e}")
            raise ServiceError(f"Failed to retrieve hydration parameter set: {e}")
    
    def get_by_name(self, name: str) -> Optional[HydrationParameterSet]:
        """Get hydration parameter set by name."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(HydrationParameterSet).filter(
                    HydrationParameterSet.name == name
                ).first()
        except Exception as e:
            self.logger.error(f"Failed to get hydration parameter set by name '{name}': {e}")
            raise ServiceError(f"Failed to retrieve hydration parameter set: {e}")
    
    def search(self, query: str) -> List[HydrationParameterSet]:
        """Search hydration parameter sets by name or description."""
        try:
            with self.db_service.get_read_only_session() as session:
                search_pattern = f"%{query}%"
                return session.query(HydrationParameterSet).filter(
                    (HydrationParameterSet.name.ilike(search_pattern)) |
                    (HydrationParameterSet.description.ilike(search_pattern))
                ).order_by(HydrationParameterSet.created_at.desc()).all()
        except Exception as e:
            self.logger.error(f"Failed to search hydration parameter sets with query '{query}': {e}")
            raise ServiceError(f"Failed to search hydration parameter sets: {e}")
    
    def create(self, param_set_data: HydrationParameterSetCreate) -> HydrationParameterSet:
        """Create a new hydration parameter set."""
        try:
            with self.db_service.get_session() as session:
                # Check if name already exists
                existing = session.query(HydrationParameterSet).filter(
                    HydrationParameterSet.name == param_set_data.name
                ).first()
                
                if existing:
                    raise AlreadyExistsError(f"Hydration parameter set with name '{param_set_data.name}' already exists")
                
                # Create new parameter set
                param_set = HydrationParameterSet(
                    name=param_set_data.name,
                    description=param_set_data.description,
                    max_time_hours=param_set_data.max_time_hours,
                    curing_conditions=param_set_data.curing_conditions,
                    time_calibration=param_set_data.time_calibration,
                    advanced_settings=param_set_data.advanced_settings,
                    db_modifications=param_set_data.db_modifications,
                    notes=param_set_data.notes,
                    is_template=param_set_data.is_template
                )
                
                session.add(param_set)
                session.commit()
                session.refresh(param_set)
                
                self.logger.info(f"Created hydration parameter set: {param_set.name} (ID: {param_set.id})")
                return param_set
                
        except AlreadyExistsError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create hydration parameter set: {e}")
            raise ServiceError(f"Failed to create hydration parameter set: {e}")
    
    def update(self, param_set_id: int, param_set_data: HydrationParameterSetUpdate) -> HydrationParameterSet:
        """Update an existing hydration parameter set."""
        try:
            with self.db_service.get_session() as session:
                param_set = session.query(HydrationParameterSet).filter(
                    HydrationParameterSet.id == param_set_id
                ).first()
                
                if not param_set:
                    raise NotFoundError(f"Hydration parameter set with ID {param_set_id} not found")
                
                # Check if new name conflicts with existing (if name is being changed)
                if param_set_data.name and param_set_data.name != param_set.name:
                    existing = session.query(HydrationParameterSet).filter(
                        HydrationParameterSet.name == param_set_data.name,
                        HydrationParameterSet.id != param_set_id
                    ).first()
                    
                    if existing:
                        raise AlreadyExistsError(f"Hydration parameter set with name '{param_set_data.name}' already exists")
                
                # Update fields
                if param_set_data.name is not None:
                    param_set.name = param_set_data.name
                if param_set_data.description is not None:
                    param_set.description = param_set_data.description
                if param_set_data.max_time_hours is not None:
                    param_set.max_time_hours = param_set_data.max_time_hours
                if param_set_data.curing_conditions is not None:
                    param_set.curing_conditions = param_set_data.curing_conditions
                if param_set_data.time_calibration is not None:
                    param_set.time_calibration = param_set_data.time_calibration
                if param_set_data.advanced_settings is not None:
                    param_set.advanced_settings = param_set_data.advanced_settings
                if param_set_data.db_modifications is not None:
                    param_set.db_modifications = param_set_data.db_modifications
                if param_set_data.notes is not None:
                    param_set.notes = param_set_data.notes
                if param_set_data.is_template is not None:
                    param_set.is_template = param_set_data.is_template
                
                param_set.updated_at = datetime.utcnow()
                
                session.commit()
                session.refresh(param_set)
                
                self.logger.info(f"Updated hydration parameter set: {param_set.name} (ID: {param_set.id})")
                return param_set
                
        except (NotFoundError, AlreadyExistsError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to update hydration parameter set: {e}")
            raise ServiceError(f"Failed to update hydration parameter set: {e}")
    
    def delete(self, param_set_id: int) -> bool:
        """Delete a hydration parameter set."""
        try:
            with self.db_service.get_session() as session:
                param_set = session.query(HydrationParameterSet).filter(
                    HydrationParameterSet.id == param_set_id
                ).first()
                
                if not param_set:
                    raise NotFoundError(f"Hydration parameter set with ID {param_set_id} not found")
                
                param_set_name = param_set.name
                session.delete(param_set)
                session.commit()
                
                self.logger.info(f"Deleted hydration parameter set: {param_set_name} (ID: {param_set_id})")
                return True
                
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to delete hydration parameter set: {e}")
            raise ServiceError(f"Failed to delete hydration parameter set: {e}")
    
    def duplicate(self, param_set_id: int, new_name: str) -> HydrationParameterSet:
        """Create a duplicate of an existing hydration parameter set with a new name."""
        try:
            with self.db_service.get_session() as session:
                # Get original parameter set
                original = session.query(HydrationParameterSet).filter(
                    HydrationParameterSet.id == param_set_id
                ).first()
                
                if not original:
                    raise NotFoundError(f"Hydration parameter set with ID {param_set_id} not found")
                
                # Check if new name already exists
                existing = session.query(HydrationParameterSet).filter(
                    HydrationParameterSet.name == new_name
                ).first()
                
                if existing:
                    raise AlreadyExistsError(f"Hydration parameter set with name '{new_name}' already exists")
                
                # Create duplicate
                duplicate = HydrationParameterSet(
                    name=new_name,
                    description=f"Copy of {original.name}" if not original.description else f"Copy of {original.name}: {original.description}",
                    max_time_hours=original.max_time_hours,
                    curing_conditions=original.curing_conditions.copy() if original.curing_conditions else {},
                    time_calibration=original.time_calibration.copy() if original.time_calibration else {},
                    advanced_settings=original.advanced_settings.copy() if original.advanced_settings else {},
                    db_modifications=original.db_modifications.copy() if original.db_modifications else {},
                    notes=original.notes,
                    is_template=False  # Duplicates are never templates by default
                )
                
                session.add(duplicate)
                session.commit()
                session.refresh(duplicate)
                
                self.logger.info(f"Duplicated hydration parameter set: {original.name} -> {new_name} (ID: {duplicate.id})")
                return duplicate
                
        except (NotFoundError, AlreadyExistsError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to duplicate hydration parameter set: {e}")
            raise ServiceError(f"Failed to duplicate hydration parameter set: {e}")