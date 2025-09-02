#!/usr/bin/env python3
"""
VCCTL Database Package

Provides database connectivity, models, and migration support.
"""

from app.database.config import DatabaseConfig, default_config
from app.database.base import Base, BaseModel, SessionLocal
from app.database.service import DatabaseService, database_service
from app.database.migrations import MigrationManager, Migration, create_migration_manager

# Models are registered with SQLAlchemy when they are imported by the application
# No need to import them here, avoiding circular import issues

__all__ = [
    'DatabaseConfig',
    'default_config',
    'Base',
    'BaseModel',
    'SessionLocal',
    'DatabaseService',
    'database_service',
    'MigrationManager',
    'Migration',
    'create_migration_manager'
]