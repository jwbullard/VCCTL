#!/usr/bin/env python3
"""
Saved Hydration Operation Service for VCCTL

Service for managing saved hydration operation configurations.
Provides autosave functionality similar to mix design autosave.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.service import DatabaseService
from app.models.saved_hydration_operation import (
    SavedHydrationOperation,
    SavedHydrationOperationCreate,
    SavedHydrationOperationUpdate
)
from app.services.base_service import BaseService, ServiceError


class SavedHydrationOperationService(BaseService):
    """Service for managing saved hydration operations."""

    def __init__(self, database_service: DatabaseService):
        super().__init__(database_service)
        self.logger = logging.getLogger(self.__class__.__name__)

    def create(self, hydration_data: SavedHydrationOperationCreate) -> SavedHydrationOperation:
        """Create a new saved hydration operation."""
        try:
            with self.database_service.get_session() as session:
                saved_hydration = SavedHydrationOperation(**hydration_data.model_dump())
                session.add(saved_hydration)
                session.commit()
                session.refresh(saved_hydration)

                self.logger.info(f"Created saved hydration operation: {saved_hydration.name}")
                return saved_hydration

        except IntegrityError as e:
            self.logger.error(f"Saved hydration operation creation failed (integrity error): {e}")
            raise ServiceError(f"Saved hydration operation with name '{hydration_data.name}' already exists")
        except Exception as e:
            self.logger.error(f"Failed to create saved hydration operation: {e}")
            raise ServiceError(f"Failed to create saved hydration operation: {e}")

    def get_all(self, include_templates: bool = True) -> List[SavedHydrationOperation]:
        """Get all saved hydration operations."""
        try:
            with self.database_service.get_session() as session:
                query = session.query(SavedHydrationOperation)
                if not include_templates:
                    query = query.filter(SavedHydrationOperation.is_template == False)

                return query.order_by(SavedHydrationOperation.updated_at.desc()).all()

        except Exception as e:
            self.logger.error(f"Failed to get saved hydration operations: {e}")
            raise ServiceError(f"Failed to get saved hydration operations: {e}")

    def get_by_id(self, hydration_id: int) -> Optional[SavedHydrationOperation]:
        """Get a saved hydration operation by ID."""
        try:
            with self.database_service.get_session() as session:
                return session.query(SavedHydrationOperation).filter(
                    SavedHydrationOperation.id == hydration_id
                ).first()

        except Exception as e:
            self.logger.error(f"Failed to get saved hydration operation by ID {hydration_id}: {e}")
            raise ServiceError(f"Failed to get saved hydration operation: {e}")

    def get_by_name(self, name: str) -> Optional[SavedHydrationOperation]:
        """Get a saved hydration operation by name."""
        try:
            with self.database_service.get_session() as session:
                return session.query(SavedHydrationOperation).filter(
                    SavedHydrationOperation.name == name
                ).first()

        except Exception as e:
            self.logger.error(f"Failed to get saved hydration operation by name '{name}': {e}")
            raise ServiceError(f"Failed to get saved hydration operation: {e}")

    def update(self, hydration_id: int, hydration_data: SavedHydrationOperationUpdate) -> Optional[SavedHydrationOperation]:
        """Update an existing saved hydration operation."""
        try:
            with self.database_service.get_session() as session:
                saved_hydration = session.query(SavedHydrationOperation).filter(
                    SavedHydrationOperation.id == hydration_id
                ).first()

                if not saved_hydration:
                    return None

                # Update fields that are provided
                update_data = hydration_data.model_dump(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(saved_hydration, key, value)

                saved_hydration.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(saved_hydration)

                self.logger.info(f"Updated saved hydration operation: {saved_hydration.name}")
                return saved_hydration

        except IntegrityError as e:
            self.logger.error(f"Saved hydration operation update failed (integrity error): {e}")
            raise ServiceError("Hydration operation name already exists")
        except Exception as e:
            self.logger.error(f"Failed to update saved hydration operation: {e}")
            raise ServiceError(f"Failed to update saved hydration operation: {e}")

    def delete(self, hydration_id: int) -> bool:
        """Delete a saved hydration operation."""
        try:
            with self.database_service.get_session() as session:
                saved_hydration = session.query(SavedHydrationOperation).filter(
                    SavedHydrationOperation.id == hydration_id
                ).first()

                if not saved_hydration:
                    return False

                session.delete(saved_hydration)
                session.commit()

                self.logger.info(f"Deleted saved hydration operation: {saved_hydration.name}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to delete saved hydration operation: {e}")
            raise ServiceError(f"Failed to delete saved hydration operation: {e}")

    def delete_by_name(self, name: str) -> bool:
        """Delete a saved hydration operation by name."""
        try:
            with self.database_service.get_session() as session:
                saved_hydration = session.query(SavedHydrationOperation).filter(
                    SavedHydrationOperation.name == name
                ).first()

                if not saved_hydration:
                    return False

                session.delete(saved_hydration)
                session.commit()

                self.logger.info(f"Deleted saved hydration operation: {name}")
                return True

        except Exception as e:
            self.logger.error(f"Failed to delete saved hydration operation '{name}': {e}")
            raise ServiceError(f"Failed to delete saved hydration operation: {e}")

    def duplicate(self, hydration_id: int, new_name: str) -> Optional[SavedHydrationOperation]:
        """Duplicate an existing saved hydration operation with a new name."""
        try:
            original = self.get_by_id(hydration_id)
            if not original:
                return None

            # Create duplicate data
            duplicate_data = SavedHydrationOperationCreate(
                name=new_name,
                description=f"Copy of {original.name}",
                source_microstructure_name=original.source_microstructure_name,
                source_microstructure_path=original.source_microstructure_path,
                max_time_hours=original.max_time_hours,
                curing_conditions=original.curing_conditions,
                time_calibration=original.time_calibration,
                advanced_settings=original.advanced_settings,
                temperature_profile=original.temperature_profile,
                database_modifications=original.database_modifications,
                ui_parameters=original.ui_parameters,
                notes=original.notes,
                is_template=False  # Duplicates are not templates
            )

            return self.create(duplicate_data)

        except Exception as e:
            self.logger.error(f"Failed to duplicate saved hydration operation: {e}")
            raise ServiceError(f"Failed to duplicate saved hydration operation: {e}")

    def auto_save_before_execution(self, hydration_config: Dict[str, Any]) -> Optional[int]:
        """
        Auto-save hydration configuration before execution.
        Similar to mix design autosave functionality.
        Returns the saved hydration operation ID if successful.
        """
        try:
            base_name = hydration_config.get('operation_name', 'Unnamed_Hydration')
            if not base_name:
                self.logger.warning("No operation name provided for hydration autosave")
                return None

            # Check for existing hydration with same name
            existing = self.get_by_name(base_name)
            unique_name = base_name

            # Generate unique name if needed
            if existing:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                unique_name = f"{base_name}_{timestamp}"

            # Create autosave data
            autosave_data = SavedHydrationOperationCreate(
                name=unique_name,
                description=f"Auto-saved before execution on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                source_microstructure_name=hydration_config.get('source_microstructure', {}).get('name', 'Unknown'),
                source_microstructure_path=hydration_config.get('source_microstructure', {}).get('path', ''),
                max_time_hours=hydration_config.get('max_time_hours', 168.0),
                curing_conditions=hydration_config.get('curing_conditions', {}),
                time_calibration=hydration_config.get('time_calibration', {}),
                advanced_settings=hydration_config.get('advanced_settings', {}),
                temperature_profile=hydration_config.get('temperature_profile', {}),
                database_modifications=hydration_config.get('database_modifications', {}),
                ui_parameters=hydration_config,  # Store complete UI state
                notes=f"Auto-saved hydration configuration",
                is_template=False
            )

            saved_hydration = self.create(autosave_data)
            self.logger.info(f"Auto-saved hydration operation: {unique_name} (ID: {saved_hydration.id})")
            return saved_hydration.id

        except Exception as e:
            self.logger.error(f"Failed to auto-save hydration operation: {e}")
            return None