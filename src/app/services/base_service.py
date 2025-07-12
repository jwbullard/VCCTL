#!/usr/bin/env python3
"""
Base Service for VCCTL

Provides common service functionality and error handling.
"""

import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Type
from sqlalchemy.orm import Session

from app.database.service import DatabaseService
from app.database.base import Base


# Type variables for generic service
ModelType = TypeVar('ModelType', bound=Base)
CreateSchemaType = TypeVar('CreateSchemaType')
UpdateSchemaType = TypeVar('UpdateSchemaType')


class ServiceError(Exception):
    """Base exception for service layer errors."""
    pass


class NotFoundError(ServiceError):
    """Exception raised when a resource is not found."""
    pass


class AlreadyExistsError(ServiceError):
    """Exception raised when trying to create a resource that already exists."""
    pass


class ValidationError(ServiceError):
    """Exception raised when validation fails."""
    pass


class BaseService(ABC, Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base service class providing common CRUD operations.
    
    This abstract base class provides a foundation for all service classes
    in the VCCTL application, ensuring consistent patterns and error handling.
    """
    
    def __init__(self, model_class: Type[ModelType], db_service: DatabaseService):
        """
        Initialize the base service.
        
        Args:
            model_class: SQLAlchemy model class
            db_service: Database service instance
        """
        self.model_class = model_class
        self.db_service = db_service
        self.logger = logging.getLogger(f'VCCTL.{self.__class__.__name__}')
    
    @abstractmethod
    def get_all(self) -> List[ModelType]:
        """Get all entities of this type."""
        pass
    
    @abstractmethod
    def get_by_name(self, name: str) -> Optional[ModelType]:
        """Get entity by name/id."""
        pass
    
    @abstractmethod
    def create(self, create_data: CreateSchemaType) -> ModelType:
        """Create a new entity."""
        pass
    
    @abstractmethod
    def update(self, name: str, update_data: UpdateSchemaType) -> ModelType:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    def delete(self, name: str) -> bool:
        """Delete an entity."""
        pass
    
    def exists(self, name: str) -> bool:
        """Check if an entity exists by name."""
        try:
            entity = self.get_by_name(name)
            return entity is not None
        except Exception as e:
            self.logger.error(f"Error checking if {name} exists: {e}")
            return False
    
    def get_count(self) -> int:
        """Get total count of entities."""
        try:
            with self.db_service.get_read_only_session() as session:
                return session.query(self.model_class).count()
        except Exception as e:
            self.logger.error(f"Failed to get count: {e}")
            raise ServiceError(f"Failed to get count: {e}")
    
    def validate_name(self, name: str) -> None:
        """Validate entity name."""
        if not name or not name.strip():
            raise ValidationError("Name cannot be empty")
        
        if len(name.strip()) > 64:  # Assuming 64 char limit
            raise ValidationError("Name cannot exceed 64 characters")
        
        # Additional name validation can be added here
    
    def _handle_database_error(self, error: Exception, operation: str) -> None:
        """Handle database errors consistently."""
        self.logger.error(f"Database error during {operation}: {error}")
        raise ServiceError(f"Database operation failed: {operation}")
    
    def _log_operation(self, operation: str, entity_name: str = None) -> None:
        """Log service operations."""
        if entity_name:
            self.logger.info(f"{operation}: {entity_name}")
        else:
            self.logger.info(operation)