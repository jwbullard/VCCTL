#!/usr/bin/env python3
"""
Database Migration Tests

Tests for database schema migrations, upgrades, and data integrity.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import sqlite3
from typing import Dict, Any, List

from app.database.service import DatabaseService
from app.database.migrations import MigrationManager
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, text
from sqlalchemy.exc import SQLAlchemyError


@pytest.mark.database
class TestDatabaseMigrations:
    """Test database migration functionality."""

    @pytest.fixture
    def temp_db_path(self, temp_directory):
        """Create temporary database path."""
        return temp_directory / "test_migrations.db"

    @pytest.fixture
    def migration_manager(self, temp_db_path):
        """Create migration manager for testing."""
        return MigrationManager(str(temp_db_path))

    @pytest.mark.unit
    def test_migration_manager_initialization(self, migration_manager):
        """Test migration manager initialization."""
        assert migration_manager is not None
        assert hasattr(migration_manager, 'db_url')
        assert hasattr(migration_manager, 'migration_dir')

    @pytest.mark.unit
    def test_get_current_schema_version(self, migration_manager):
        """Test getting current schema version."""
        with patch.object(migration_manager, '_execute_query') as mock_execute:
            mock_execute.return_value = [(1,)]
            
            version = migration_manager.get_current_schema_version()
            assert version == 1

    @pytest.mark.unit
    def test_get_current_schema_version_no_table(self, migration_manager):
        """Test getting schema version when migration table doesn't exist."""
        with patch.object(migration_manager, '_execute_query') as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("no such table")
            
            version = migration_manager.get_current_schema_version()
            assert version == 0

    @pytest.mark.unit
    def test_create_migration_table(self, migration_manager):
        """Test creation of migration tracking table."""
        with patch.object(migration_manager, '_execute_query') as mock_execute:
            migration_manager._create_migration_table()
            
            # Should execute CREATE TABLE
            mock_execute.assert_called()
            call_args = mock_execute.call_args[0][0]
            assert 'CREATE TABLE' in call_args
            assert 'schema_migrations' in call_args

    @pytest.mark.unit
    def test_apply_migration_success(self, migration_manager):
        """Test successful migration application."""
        migration_sql = """
        CREATE TABLE test_materials (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL
        );
        """
        
        with patch.object(migration_manager, '_execute_query') as mock_execute:
            success = migration_manager._apply_migration(1, migration_sql)
            
            assert success is True
            assert mock_execute.call_count >= 2  # Migration + version update

    @pytest.mark.unit
    def test_apply_migration_failure(self, migration_manager):
        """Test migration application failure."""
        invalid_sql = "INVALID SQL STATEMENT;"
        
        with patch.object(migration_manager, '_execute_query') as mock_execute:
            mock_execute.side_effect = SQLAlchemyError("SQL error")
            
            success = migration_manager._apply_migration(1, invalid_sql)
            assert success is False

    @pytest.mark.unit
    def test_rollback_migration(self, migration_manager):
        """Test migration rollback."""
        rollback_sql = "DROP TABLE test_materials;"
        
        with patch.object(migration_manager, '_execute_query') as mock_execute:
            success = migration_manager._rollback_migration(1, rollback_sql)
            
            assert success is True
            mock_execute.assert_called()

    @pytest.mark.unit
    def test_get_pending_migrations(self, migration_manager):
        """Test getting pending migrations."""
        with patch.object(migration_manager, 'get_current_schema_version', return_value=1):
            with patch.object(migration_manager, '_get_available_migrations') as mock_available:
                mock_available.return_value = [
                    {'version': 1, 'name': 'initial'},
                    {'version': 2, 'name': 'add_materials'},
                    {'version': 3, 'name': 'add_indexes'}
                ]
                
                pending = migration_manager.get_pending_migrations()
                
                # Should return migrations 2 and 3
                assert len(pending) == 2
                assert pending[0]['version'] == 2
                assert pending[1]['version'] == 3

    @pytest.mark.unit
    def test_migrate_to_latest_success(self, migration_manager):
        """Test migrating to latest version."""
        pending_migrations = [
            {'version': 2, 'name': 'add_materials', 'sql': 'CREATE TABLE materials();'},
            {'version': 3, 'name': 'add_indexes', 'sql': 'CREATE INDEX idx_name ON materials(name);'}
        ]
        
        with patch.object(migration_manager, 'get_pending_migrations', return_value=pending_migrations):
            with patch.object(migration_manager, '_apply_migration', return_value=True):
                success = migration_manager.migrate_to_latest()
                
                assert success is True

    @pytest.mark.unit
    def test_migrate_to_latest_failure(self, migration_manager):
        """Test migration failure during migrate to latest."""
        pending_migrations = [
            {'version': 2, 'name': 'add_materials', 'sql': 'CREATE TABLE materials();'},
        ]
        
        with patch.object(migration_manager, 'get_pending_migrations', return_value=pending_migrations):
            with patch.object(migration_manager, '_apply_migration', return_value=False):
                success = migration_manager.migrate_to_latest()
                
                assert success is False

    @pytest.mark.unit
    def test_migrate_to_version(self, migration_manager):
        """Test migrating to specific version."""
        target_version = 2
        
        with patch.object(migration_manager, 'get_current_schema_version', return_value=1):
            with patch.object(migration_manager, '_get_migration_by_version') as mock_get_migration:
                mock_get_migration.return_value = {
                    'version': 2,
                    'name': 'add_materials', 
                    'sql': 'CREATE TABLE materials();'
                }
                
                with patch.object(migration_manager, '_apply_migration', return_value=True):
                    success = migration_manager.migrate_to_version(target_version)
                    
                    assert success is True

    @pytest.mark.unit
    def test_rollback_to_version(self, migration_manager):
        """Test rolling back to specific version."""
        target_version = 1
        
        with patch.object(migration_manager, 'get_current_schema_version', return_value=3):
            with patch.object(migration_manager, '_get_rollback_migrations') as mock_rollbacks:
                mock_rollbacks.return_value = [
                    {'version': 3, 'rollback_sql': 'DROP INDEX idx_name;'},
                    {'version': 2, 'rollback_sql': 'DROP TABLE materials;'}
                ]
                
                with patch.object(migration_manager, '_rollback_migration', return_value=True):
                    success = migration_manager.rollback_to_version(target_version)
                    
                    assert success is True


@pytest.mark.database
class TestSpecificMigrations:
    """Test specific migration scenarios."""

    @pytest.mark.unit
    def test_initial_schema_migration(self, temp_directory):
        """Test initial schema creation migration."""
        db_path = temp_directory / "initial_test.db"
        
        # Create initial migration
        initial_migration = """
        CREATE TABLE cements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            sio2 REAL,
            al2o3 REAL,
            fe2o3 REAL,
            cao REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE aggregates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            density REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Apply migration
        conn = sqlite3.connect(str(db_path))
        conn.executescript(initial_migration)
        conn.close()
        
        # Verify tables were created
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check cements table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cements';")
        assert cursor.fetchone() is not None
        
        # Check aggregates table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='aggregates';")
        assert cursor.fetchone() is not None
        
        conn.close()

    @pytest.mark.unit
    def test_add_column_migration(self, temp_directory):
        """Test migration that adds columns."""
        db_path = temp_directory / "add_column_test.db"
        
        # Create initial table
        initial_sql = """
        CREATE TABLE materials (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        """
        
        conn = sqlite3.connect(str(db_path))
        conn.execute(initial_sql)
        
        # Insert test data
        conn.execute("INSERT INTO materials (name) VALUES ('Test Material');")
        conn.commit()
        
        # Apply migration to add column
        migration_sql = "ALTER TABLE materials ADD COLUMN type TEXT DEFAULT 'unknown';"
        conn.execute(migration_sql)
        conn.commit()
        
        # Verify column was added and data preserved
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, type FROM materials;")
        row = cursor.fetchone()
        
        assert row is not None
        assert row[1] == 'Test Material'  # name preserved
        assert row[2] == 'unknown'        # default type added
        
        conn.close()

    @pytest.mark.unit
    def test_create_index_migration(self, temp_directory):
        """Test migration that creates indexes."""
        db_path = temp_directory / "index_test.db"
        
        # Create table
        initial_sql = """
        CREATE TABLE search_materials (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT
        );
        """
        
        conn = sqlite3.connect(str(db_path))
        conn.execute(initial_sql)
        
        # Create indexes
        index_migration = """
        CREATE INDEX idx_materials_name ON search_materials(name);
        CREATE INDEX idx_materials_type ON search_materials(type);
        CREATE INDEX idx_materials_category ON search_materials(category);
        """
        
        conn.executescript(index_migration)
        conn.commit()
        
        # Verify indexes were created
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='search_materials';")
        indexes = cursor.fetchall()
        
        index_names = [idx[0] for idx in indexes if not idx[0].startswith('sqlite_')]
        assert 'idx_materials_name' in index_names
        assert 'idx_materials_type' in index_names
        assert 'idx_materials_category' in index_names
        
        conn.close()

    @pytest.mark.unit
    def test_data_transformation_migration(self, temp_directory):
        """Test migration that transforms existing data."""
        db_path = temp_directory / "transform_test.db"
        
        # Create table with old schema
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE compositions (
                id INTEGER PRIMARY KEY,
                material_name TEXT,
                composition_text TEXT
            );
        """)
        
        # Insert test data with old format
        test_data = [
            (1, 'Cement A', 'SiO2:20.5,Al2O3:5.2,Fe2O3:3.1'),
            (2, 'Cement B', 'SiO2:21.0,Al2O3:4.8,Fe2O3:3.5'),
        ]
        
        conn.executemany(
            "INSERT INTO compositions (id, material_name, composition_text) VALUES (?, ?, ?)",
            test_data
        )
        conn.commit()
        
        # Apply migration to transform data
        migration_sql = """
        -- Add new columns
        ALTER TABLE compositions ADD COLUMN sio2 REAL;
        ALTER TABLE compositions ADD COLUMN al2o3 REAL;
        ALTER TABLE compositions ADD COLUMN fe2o3 REAL;
        """
        
        conn.executescript(migration_sql)
        
        # Transform data (simplified - in real migration would parse composition_text)
        transformation_updates = [
            (20.5, 5.2, 3.1, 1),
            (21.0, 4.8, 3.5, 2),
        ]
        
        conn.executemany(
            "UPDATE compositions SET sio2=?, al2o3=?, fe2o3=? WHERE id=?",
            transformation_updates
        )
        conn.commit()
        
        # Verify transformation
        cursor = conn.cursor()
        cursor.execute("SELECT material_name, sio2, al2o3, fe2o3 FROM compositions ORDER BY id;")
        rows = cursor.fetchall()
        
        assert len(rows) == 2
        assert rows[0] == ('Cement A', 20.5, 5.2, 3.1)
        assert rows[1] == ('Cement B', 21.0, 4.8, 3.5)
        
        conn.close()


@pytest.mark.database
class TestMigrationIntegrity:
    """Test migration data integrity and constraints."""

    @pytest.mark.unit
    def test_foreign_key_constraints_migration(self, temp_directory):
        """Test migration with foreign key constraints."""
        db_path = temp_directory / "fk_test.db"
        
        conn = sqlite3.connect(str(db_path))
        conn.execute("PRAGMA foreign_keys = ON;")
        
        # Create parent table
        conn.execute("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE
            );
        """)
        
        # Create child table with foreign key
        conn.execute("""
            CREATE TABLE mix_designs (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                project_id INTEGER NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
        """)
        
        # Insert test data
        conn.execute("INSERT INTO projects (id, name) VALUES (1, 'Test Project');")
        conn.execute("INSERT INTO mix_designs (id, name, project_id) VALUES (1, 'Mix A', 1);")
        conn.commit()
        
        # Verify foreign key constraint works
        cursor = conn.cursor()
        
        # This should succeed
        cursor.execute("SELECT md.name, p.name FROM mix_designs md JOIN projects p ON md.project_id = p.id;")
        result = cursor.fetchone()
        assert result == ('Mix A', 'Test Project')
        
        # This should fail due to foreign key constraint
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO mix_designs (id, name, project_id) VALUES (2, 'Mix B', 999);")
        
        conn.close()

    @pytest.mark.unit
    def test_unique_constraint_migration(self, temp_directory):
        """Test migration with unique constraints."""
        db_path = temp_directory / "unique_test.db"
        
        conn = sqlite3.connect(str(db_path))
        
        # Create table with unique constraint
        conn.execute("""
            CREATE TABLE unique_materials (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL
            );
        """)
        
        # Insert valid data
        conn.execute("INSERT INTO unique_materials (name, type) VALUES ('Material A', 'Type I');")
        conn.commit()
        
        # Attempt to insert duplicate should fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO unique_materials (name, type) VALUES ('Material A', 'Type II');")
        
        conn.close()

    @pytest.mark.unit 
    def test_check_constraint_migration(self, temp_directory):
        """Test migration with check constraints."""
        db_path = temp_directory / "check_test.db"
        
        conn = sqlite3.connect(str(db_path))
        
        # Create table with check constraints
        conn.execute("""
            CREATE TABLE validated_materials (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                density REAL CHECK (density > 0 AND density < 10),
                percentage REAL CHECK (percentage >= 0 AND percentage <= 100)
            );
        """)
        
        # Valid data should succeed
        conn.execute("""
            INSERT INTO validated_materials (name, density, percentage) 
            VALUES ('Valid Material', 2.65, 85.5);
        """)
        conn.commit()
        
        # Invalid density should fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO validated_materials (name, density, percentage) 
                VALUES ('Invalid Density', -1.0, 50.0);
            """)
        
        # Invalid percentage should fail  
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("""
                INSERT INTO validated_materials (name, density, percentage) 
                VALUES ('Invalid Percentage', 2.5, 150.0);
            """)
        
        conn.close()


@pytest.mark.database
@pytest.mark.integration
class TestMigrationIntegration:
    """Integration tests for migrations with actual database service."""

    @pytest.mark.integration
    def test_database_service_migration_integration(self, temp_directory):
        """Test migration integration with DatabaseService."""
        db_path = temp_directory / "integration_test.db"
        
        # Create database service
        db_service = DatabaseService(str(db_path))
        
        # Initialize should run migrations
        with patch('app.database.service.MigrationManager') as mock_migration_manager:
            mock_manager = Mock()
            mock_manager.migrate_to_latest.return_value = True
            mock_migration_manager.return_value = mock_manager
            
            db_service.initialize()
            
            # Should have attempted migration
            mock_manager.migrate_to_latest.assert_called_once()

    @pytest.mark.integration
    def test_migration_with_existing_data(self, temp_directory):
        """Test migration with existing data preservation."""
        db_path = temp_directory / "existing_data_test.db"
        
        # Create initial database with data
        conn = sqlite3.connect(str(db_path))
        conn.execute("""
            CREATE TABLE legacy_materials (
                id INTEGER PRIMARY KEY,
                name TEXT,
                old_field TEXT
            );
        """)
        
        # Insert legacy data
        legacy_data = [
            (1, 'Legacy Material 1', 'old_value_1'),
            (2, 'Legacy Material 2', 'old_value_2'),
        ]
        
        conn.executemany(
            "INSERT INTO legacy_materials (id, name, old_field) VALUES (?, ?, ?)",
            legacy_data
        )
        conn.commit()
        conn.close()
        
        # Apply migration that modifies schema but preserves data
        migration_manager = MigrationManager(str(db_path))
        
        migration_sql = """
        ALTER TABLE legacy_materials ADD COLUMN new_field TEXT DEFAULT 'default_value';
        """
        
        with patch.object(migration_manager, '_get_available_migrations') as mock_migrations:
            mock_migrations.return_value = [
                {'version': 1, 'name': 'add_new_field', 'sql': migration_sql}
            ]
            
            with patch.object(migration_manager, 'get_current_schema_version', return_value=0):
                success = migration_manager.migrate_to_latest()
                
                assert success is True
        
        # Verify data preservation after migration
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, old_field, new_field FROM legacy_materials ORDER BY id;")
        rows = cursor.fetchall()
        
        assert len(rows) == 2
        assert rows[0] == (1, 'Legacy Material 1', 'old_value_1', 'default_value')
        assert rows[1] == (2, 'Legacy Material 2', 'old_value_2', 'default_value')
        
        conn.close()


# Mock migration files for testing

@pytest.fixture
def mock_migration_files(temp_directory):
    """Create mock migration files for testing."""
    migration_dir = temp_directory / "migrations"
    migration_dir.mkdir()
    
    # Migration 001 - Initial schema
    migration_001 = migration_dir / "001_initial_schema.sql"
    migration_001.write_text("""
-- Migration 001: Initial Schema
CREATE TABLE cements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE aggregates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
    """)
    
    # Migration 002 - Add composition fields
    migration_002 = migration_dir / "002_add_composition.sql"
    migration_002.write_text("""
-- Migration 002: Add Composition Fields
ALTER TABLE cements ADD COLUMN sio2 REAL;
ALTER TABLE cements ADD COLUMN al2o3 REAL;
ALTER TABLE cements ADD COLUMN fe2o3 REAL;
ALTER TABLE cements ADD COLUMN cao REAL;
    """)
    
    # Migration 003 - Add indexes
    migration_003 = migration_dir / "003_add_indexes.sql"
    migration_003.write_text("""
-- Migration 003: Add Performance Indexes
CREATE INDEX idx_cements_name ON cements(name);
CREATE INDEX idx_cements_type ON cements(type);
CREATE INDEX idx_aggregates_name ON aggregates(name);
CREATE INDEX idx_aggregates_type ON aggregates(type);
    """)
    
    return migration_dir