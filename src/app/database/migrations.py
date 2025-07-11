#!/usr/bin/env python3
"""
Database Migration Support for VCCTL

Provides database migration functionality for schema updates and data seeding.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, Integer, String, DateTime, text
from sqlalchemy.exc import SQLAlchemyError

from app.database.base import Base
from app.database.service import DatabaseService


class Migration(Base):
    """Model to track applied migrations."""
    
    __tablename__ = 'migrations'
    
    version = Column(String(50), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    applied_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Migration(version='{self.version}', name='{self.name}')>"


class MigrationManager:
    """Manages database migrations and schema updates."""
    
    def __init__(self, db_service: DatabaseService):
        """Initialize the migration manager."""
        self.db_service = db_service
        self.logger = logging.getLogger('VCCTL.Migrations')
        self.migrations_dir = Path(__file__).parent / 'migration_scripts'
        
        # Ensure migrations directory exists
        self.migrations_dir.mkdir(exist_ok=True)
    
    def initialize_migration_table(self) -> None:
        """Create the migrations tracking table if it doesn't exist."""
        try:
            # Create the migrations table
            Migration.__table__.create(bind=self.db_service.engine, checkfirst=True)
            self.logger.info("Migration tracking table initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize migration table: {e}")
            raise
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions."""
        try:
            with self.db_service.get_read_only_session() as session:
                migrations = session.query(Migration).order_by(Migration.applied_at).all()
                return [m.version for m in migrations]
        except Exception as e:
            self.logger.error(f"Failed to get applied migrations: {e}")
            return []
    
    def mark_migration_applied(self, version: str, name: str) -> None:
        """Mark a migration as applied."""
        try:
            with self.db_service.get_session() as session:
                migration = Migration(version=version, name=name)
                session.add(migration)
                session.commit()
                self.logger.info(f"Migration {version} marked as applied")
        except Exception as e:
            self.logger.error(f"Failed to mark migration {version} as applied: {e}")
            raise
    
    def create_initial_schema(self) -> None:
        """Create the initial database schema."""
        try:
            self.logger.info("Creating initial database schema...")
            
            # Create all tables
            self.db_service.create_all_tables()
            
            # Initialize migration table
            self.initialize_migration_table()
            
            # Mark initial schema as applied
            self.mark_migration_applied("001", "Initial schema")
            
            self.logger.info("Initial schema created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create initial schema: {e}")
            raise
    
    def run_sql_migration(self, sql_script: str, version: str, name: str) -> None:
        """Run a SQL migration script."""
        try:
            self.logger.info(f"Running migration {version}: {name}")
            
            with self.db_service.get_session() as session:
                # Split script into individual statements
                statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
                
                for statement in statements:
                    if statement:
                        session.execute(text(statement))
                
                # Mark migration as applied
                migration = Migration(version=version, name=name)
                session.add(migration)
                session.commit()
            
            self.logger.info(f"Migration {version} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Migration {version} failed: {e}")
            raise
    
    def seed_initial_data(self) -> None:
        """Seed the database with initial data."""
        try:
            self.logger.info("Seeding initial data...")
            
            # Check if data has already been seeded
            applied_migrations = self.get_applied_migrations()
            if "seed_001" in applied_migrations:
                self.logger.info("Initial data already seeded")
                return
            
            with self.db_service.get_session() as session:
                # This will be expanded when we have actual models
                # For now, just mark as completed
                pass
            
            # Mark seeding as completed
            self.mark_migration_applied("seed_001", "Initial data seeding")
            
            self.logger.info("Initial data seeding completed")
            
        except Exception as e:
            self.logger.error(f"Failed to seed initial data: {e}")
            raise
    
    def check_database_version(self) -> Dict[str, Any]:
        """Check the current database version and status."""
        version_info = {
            'initialized': False,
            'current_version': None,
            'applied_migrations': [],
            'schema_exists': False
        }
        
        try:
            # Check if migration table exists
            with self.db_service.get_read_only_session() as session:
                try:
                    result = session.execute(text(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='migrations'"
                    ))
                    if result.fetchone():
                        version_info['schema_exists'] = True
                        version_info['initialized'] = True
                        
                        # Get applied migrations
                        applied_migrations = self.get_applied_migrations()
                        version_info['applied_migrations'] = applied_migrations
                        
                        if applied_migrations:
                            version_info['current_version'] = applied_migrations[-1]
                
                except Exception:
                    # Migration table doesn't exist
                    pass
                    
        except Exception as e:
            self.logger.error(f"Failed to check database version: {e}")
        
        return version_info
    
    def upgrade_database(self) -> None:
        """Upgrade database to latest version."""
        try:
            version_info = self.check_database_version()
            
            if not version_info['initialized']:
                self.logger.info("Database not initialized, creating initial schema...")
                self.create_initial_schema()
                self.seed_initial_data()
            else:
                self.logger.info("Database already initialized")
                # Here we would apply any new migrations
                # For now, just log the current state
                self.logger.info(f"Current version: {version_info['current_version']}")
                self.logger.info(f"Applied migrations: {version_info['applied_migrations']}")
            
        except Exception as e:
            self.logger.error(f"Failed to upgrade database: {e}")
            raise
    
    def reset_database(self) -> None:
        """Reset the database (drop all tables and recreate)."""
        try:
            self.logger.warning("Resetting database - all data will be lost!")
            
            # Drop all tables
            self.db_service.drop_all_tables()
            
            # Recreate schema
            self.create_initial_schema()
            
            # Seed initial data
            self.seed_initial_data()
            
            self.logger.info("Database reset completed")
            
        except Exception as e:
            self.logger.error(f"Failed to reset database: {e}")
            raise


def create_migration_manager(db_service: DatabaseService = None) -> MigrationManager:
    """Create a migration manager instance."""
    from app.database.service import database_service
    return MigrationManager(db_service or database_service)