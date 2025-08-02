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
            
            # Create seed data
            self._create_seed_data()
            
            # Mark seeding as completed
            self.mark_migration_applied("seed_001", "Initial data seeding")
            
            self.logger.info("Initial data seeding completed")
            
        except Exception as e:
            self.logger.error(f"Failed to seed initial data: {e}")
            raise
    
    def _create_seed_data(self) -> None:
        """Create basic seed data for the application."""
        seed_operations = [
            self._create_particle_shape_sets,
            self._create_basic_aggregates,
            self._create_basic_cements,
            self._create_basic_fly_ash,
            self._create_basic_slag,
            self._create_basic_fillers,
            self._create_basic_gradings,
        ]
        
        for operation in seed_operations:
            try:
                operation()
            except Exception as e:
                self.logger.error(f"Failed to create seed data with {operation.__name__}: {e}")
    
    def _create_particle_shape_sets(self) -> None:
        """Create basic particle shape sets."""
        from app.models import ParticleShapeSet
        
        shapes = ['sphere', 'ellipsoid', 'cube', 'irregular', 'angular', 'rounded']
        
        with self.db_service.get_session() as session:
            for shape in shapes:
                existing = session.query(ParticleShapeSet).filter_by(name=shape).first()
                if not existing:
                    shape_set = ParticleShapeSet(name=shape)
                    session.add(shape_set)
    
    def _create_basic_aggregates(self) -> None:
        """Create basic aggregate materials."""
        from app.models import Aggregate
        
        aggregates = [
            {'display_name': 'standard_coarse', 'name': 'Standard Coarse Aggregate', 'type': 1, 'specific_gravity': 2.65},
            {'display_name': 'standard_fine', 'name': 'Standard Fine Aggregate', 'type': 2, 'specific_gravity': 2.60},
        ]
        
        with self.db_service.get_session() as session:
            for agg_data in aggregates:
                existing = session.query(Aggregate).filter_by(display_name=agg_data['display_name']).first()
                if not existing:
                    aggregate = Aggregate(**agg_data)
                    session.add(aggregate)
    
    def _create_basic_cements(self) -> None:
        """Create basic cement materials."""
        from app.models import Cement
        
        cements = [
            {'name': 'portland_cement_type_i', 'psd': 'cement141', 'alkali_file': 'lowalkali'},
            {'name': 'portland_cement_type_ii', 'psd': 'cement141', 'alkali_file': 'lowalkali'},
        ]
        
        with self.db_service.get_session() as session:
            for cement_data in cements:
                existing = session.query(Cement).filter_by(name=cement_data['name']).first()
                if not existing:
                    cement = Cement(**cement_data)
                    session.add(cement)
    
    def _create_basic_fly_ash(self) -> None:
        """Create basic fly ash materials."""
        from app.models import FlyAsh
        
        fly_ashes = [
            {'name': 'class_f_fly_ash', 'specific_gravity': 2.77, 'psd': 'cement141'},
            {'name': 'class_c_fly_ash', 'specific_gravity': 2.80, 'psd': 'cement141'},
        ]
        
        with self.db_service.get_session() as session:
            for fa_data in fly_ashes:
                existing = session.query(FlyAsh).filter_by(name=fa_data['name']).first()
                if not existing:
                    fly_ash = FlyAsh(**fa_data)
                    session.add(fly_ash)
    
    def _create_basic_slag(self) -> None:
        """Create basic slag materials."""
        from app.models import Slag
        
        slags = [
            {'name': 'ggbs_grade_80', 'specific_gravity': 2.87, 'psd': 'cement141'},
            {'name': 'ggbs_grade_100', 'specific_gravity': 2.90, 'psd': 'cement141'},
        ]
        
        with self.db_service.get_session() as session:
            for slag_data in slags:
                existing = session.query(Slag).filter_by(name=slag_data['name']).first()
                if not existing:
                    slag = Slag(**slag_data)
                    session.add(slag)
    
    def _create_basic_fillers(self) -> None:
        """Create basic inert filler materials."""
        from app.models import InertFiller
        
        fillers = [
            {'name': 'quartz', 'specific_gravity': 2.65, 'psd': 'cement141'},
            {'name': 'limestone', 'specific_gravity': 2.70, 'psd': 'cement141'},
        ]
        
        with self.db_service.get_session() as session:
            for filler_data in fillers:
                existing = session.query(InertFiller).filter_by(name=filler_data['name']).first()
                if not existing:
                    filler = InertFiller(**filler_data)
                    session.add(filler)
    
    def _create_basic_gradings(self) -> None:
        """Create basic grading curves."""
        from app.models import Grading, GradingType
        
        gradings = [
            {'name': 'standard_coarse_grading', 'type': GradingType.COARSE, 'max_diameter': 25.0},
            {'name': 'standard_fine_grading', 'type': GradingType.FINE, 'max_diameter': 4.75},
        ]
        
        with self.db_service.get_session() as session:
            for grading_data in gradings:
                existing = session.query(Grading).filter_by(name=grading_data['name']).first()
                if not existing:
                    grading = Grading(**grading_data)
                    session.add(grading)
    
    def _apply_mix_design_migration(self) -> None:
        """Apply migration to add mix_design table."""
        try:
            self.logger.info("Creating mix_design table...")
            
            # Create the SQL for mix_design table
            mix_design_sql = """
            CREATE TABLE IF NOT EXISTS mix_design (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(128) NOT NULL UNIQUE,
                description TEXT,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                water_binder_ratio REAL NOT NULL DEFAULT 0.0,
                total_water_content REAL NOT NULL DEFAULT 0.0,
                air_content REAL NOT NULL DEFAULT 0.0,
                water_volume_fraction REAL NOT NULL DEFAULT 0.0,
                air_volume_fraction REAL NOT NULL DEFAULT 0.0,
                system_size INTEGER NOT NULL DEFAULT 100,
                random_seed INTEGER NOT NULL DEFAULT -1,
                cement_shape_set VARCHAR(64) DEFAULT 'spherical',
                aggregate_shape_set VARCHAR(64) DEFAULT 'spherical',
                components TEXT NOT NULL DEFAULT '[]',
                calculated_properties TEXT DEFAULT '{}',
                notes TEXT,
                is_template BOOLEAN NOT NULL DEFAULT 0
            )
            """
            
            # Run the migration
            self.run_sql_migration(mix_design_sql, "002_add_mix_design_table", "Add mix_design table for saved mix designs")
            
            # Create some template mix designs
            self._seed_template_mix_designs()
            
            self.logger.info("mix_design table migration completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to apply mix_design migration: {e}")
            raise
    
    def _seed_template_mix_designs(self) -> None:
        """Create template mix designs for users."""
        try:
            self.logger.info("Seeding template mix designs...")
            
            template_designs = [
                {
                    'name': 'Standard Cement Paste (W/B=0.40)',
                    'description': 'Basic cement paste template with W/B ratio of 0.40',
                    'water_binder_ratio': 0.40,
                    'total_water_content': 400.0,
                    'air_content': 0.0,
                    'water_volume_fraction': 0.40,
                    'air_volume_fraction': 0.0,
                    'system_size': 100,
                    'random_seed': -1,
                    'cement_shape_set': 'spherical',
                    'aggregate_shape_set': 'spherical',
                    'components': '[{"material_name": "cement140", "material_type": "CEMENT", "mass_fraction": 1.0, "volume_fraction": 0.6, "specific_gravity": 3.15}]',
                    'calculated_properties': '{"paste_volume_fraction": 1.0, "powder_volume_fraction": 0.6, "aggregate_volume_fraction": 0.0, "binder_content": 1000.0, "water_content": 400.0}',
                    'notes': 'Template for cement paste studies and microstructure generation',
                    'is_template': 1
                },
                {
                    'name': 'High Performance Paste (W/B=0.30)',
                    'description': 'High performance cement paste with low W/B ratio',
                    'water_binder_ratio': 0.30,
                    'total_water_content': 300.0,
                    'air_content': 0.0,
                    'water_volume_fraction': 0.30,
                    'air_volume_fraction': 0.0,
                    'system_size': 100,
                    'random_seed': -1,
                    'cement_shape_set': 'spherical',
                    'aggregate_shape_set': 'spherical',
                    'components': '[{"material_name": "cement140", "material_type": "CEMENT", "mass_fraction": 1.0, "volume_fraction": 0.7, "specific_gravity": 3.15}]',
                    'calculated_properties': '{"paste_volume_fraction": 1.0, "powder_volume_fraction": 0.7, "aggregate_volume_fraction": 0.0, "binder_content": 1000.0, "water_content": 300.0}',
                    'notes': 'High performance paste for durability studies',
                    'is_template': 1
                },
                {
                    'name': 'Cement + Fly Ash Blend (W/B=0.45)',
                    'description': 'Binary paste with 20% fly ash replacement',
                    'water_binder_ratio': 0.45,
                    'total_water_content': 450.0,
                    'air_content': 0.0,
                    'water_volume_fraction': 0.45,
                    'air_volume_fraction': 0.0,
                    'system_size': 100,
                    'random_seed': -1,
                    'cement_shape_set': 'spherical',
                    'aggregate_shape_set': 'spherical',
                    'components': '[{"material_name": "cement140", "material_type": "CEMENT", "mass_fraction": 0.8, "volume_fraction": 0.48, "specific_gravity": 3.15}, {"material_name": "fa80", "material_type": "FLYASH", "mass_fraction": 0.2, "volume_fraction": 0.12, "specific_gravity": 2.2}]',
                    'calculated_properties': '{"paste_volume_fraction": 1.0, "powder_volume_fraction": 0.6, "aggregate_volume_fraction": 0.0, "binder_content": 1000.0, "water_content": 450.0}',
                    'notes': 'Binary paste for sustainability studies',
                    'is_template': 1
                }
            ]
            
            insert_statements = []
            for design in template_designs:
                values = []
                for key in ['name', 'description', 'water_binder_ratio', 'total_water_content', 'air_content', 
                           'water_volume_fraction', 'air_volume_fraction', 'system_size', 'random_seed',
                           'cement_shape_set', 'aggregate_shape_set', 'components', 'calculated_properties', 
                           'notes', 'is_template']:
                    value = design[key]
                    if isinstance(value, str):
                        # Escape single quotes in strings
                        value = value.replace("'", "''")
                        values.append(f"'{value}'")
                    elif value is None:
                        values.append('NULL')
                    else:
                        values.append(str(value))
                
                insert_sql = f"""
                INSERT OR IGNORE INTO mix_design 
                (name, description, water_binder_ratio, total_water_content, air_content, 
                 water_volume_fraction, air_volume_fraction, system_size, random_seed,
                 cement_shape_set, aggregate_shape_set, components, calculated_properties, 
                 notes, is_template, created_at, updated_at)
                VALUES ({', '.join(values)}, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
                insert_statements.append(insert_sql)
            
            # Execute all insert statements
            with self.db_service.get_session() as session:
                for statement in insert_statements:
                    try:
                        session.execute(text(statement))
                    except Exception as e:
                        self.logger.warning(f"Failed to insert template mix design: {e}")
                        # Continue with other templates
            
            self.logger.info("Template mix designs seeded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to seed template mix designs: {e}")
            # Don't raise - this is optional seeding
    
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
                # Apply any new migrations
                applied_migrations = version_info['applied_migrations']
                
                # Check for mix_design table migration
                if "002_add_mix_design_table" not in applied_migrations:
                    self.logger.info("Applying mix_design table migration...")
                    self._apply_mix_design_migration()
                
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
    
    def migrate_from_h2_database(self, h2_db_path: Path) -> None:
        """
        Migrate data from H2 database to SQLite.
        
        This method extracts data from the original H2 database and
        converts it to SQLite format.
        """
        try:
            self.logger.info(f"Starting migration from H2 database: {h2_db_path}")
            
            # Check if migration has already been done
            applied_migrations = self.get_applied_migrations()
            if "h2_migration_001" in applied_migrations:
                self.logger.info("H2 migration already completed")
                return
            
            # This would require H2 database driver which is complex in Python
            # For now, we'll implement the Flyway script approach
            self.logger.warning("Direct H2 database migration not yet implemented")
            self.logger.info("Please use migrate_from_flyway_scripts() instead")
            
            # Mark as attempted
            self.mark_migration_applied("h2_migration_001", "H2 database migration (attempted)")
            
        except Exception as e:
            self.logger.error(f"Failed to migrate from H2 database: {e}")
            raise
    
    def migrate_from_flyway_scripts(self, flyway_scripts_dir: Path) -> None:
        """
        Migrate data from Flyway SQL scripts to SQLite.
        
        This method processes the original H2 Flyway scripts and converts
        the data to SQLite format.
        """
        try:
            self.logger.info(f"Starting migration from Flyway scripts: {flyway_scripts_dir}")
            
            # Check if migration has already been done
            applied_migrations = self.get_applied_migrations()
            if "flyway_migration_001" in applied_migrations:
                self.logger.info("Flyway migration already completed")
                return
            
            if not flyway_scripts_dir.exists():
                raise FileNotFoundError(f"Flyway scripts directory not found: {flyway_scripts_dir}")
            
            # Process data insertion scripts in order
            data_scripts = [
                "V7__Insert_data_aggregate.sql",
                "V8__Insert_data_cement.sql", 
                "V9__Insert_data_db_file.sql",
                "V10__Insert_data_fly_ash.sql",
                "V11__Insert_data_slag.sql",
                "V13__Insert_data_inert_filler.sql",
                "V15__Insert_data_particle_shape_set.sql",
                "V17__Insert_data_aggregate_sieves.sql",
                "V19__Insert_grading_data.sql"
            ]
            
            for script_name in data_scripts:
                script_path = flyway_scripts_dir / script_name
                if script_path.exists():
                    self.logger.info(f"Processing script: {script_name}")
                    self._process_flyway_data_script(script_path)
                else:
                    self.logger.warning(f"Script not found: {script_name}")
            
            # Mark migration as completed
            self.mark_migration_applied("flyway_migration_001", "Flyway scripts migration")
            
            self.logger.info("Flyway migration completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to migrate from Flyway scripts: {e}")
            raise
    
    def _process_flyway_data_script(self, script_path: Path) -> None:
        """Process a single Flyway data insertion script."""
        try:
            with open(script_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Convert H2-specific syntax to SQLite
            sqlite_content = self._convert_h2_to_sqlite(content)
            
            # Execute the converted script in chunks to handle large files
            self._execute_large_sql_script(sqlite_content, script_path.name)
            
        except Exception as e:
            self.logger.error(f"Failed to process script {script_path.name}: {e}")
            # Don't re-raise to allow other scripts to continue
    
    def _convert_h2_to_sqlite(self, h2_sql: str) -> str:
        """Convert H2 SQL to SQLite-compatible SQL."""
        # Basic H2 to SQLite conversions
        conversions = [
            # Data types
            ('BINARY LARGE OBJECT', 'BLOB'),
            ('DOUBLE PRECISION', 'REAL'),
            ('INTEGER NOT NULL AUTO_INCREMENT', 'INTEGER PRIMARY KEY AUTOINCREMENT'),
            ('TIMESTAMP', 'DATETIME'),
            
            # Functions and syntax
            ('CURRENT_TIMESTAMP()', 'CURRENT_TIMESTAMP'),
            ('TRUE', '1'),
            ('FALSE', '0'),
            
            # Binary data handling (H2 uses x'...' format which SQLite also supports)
            # No conversion needed for hexadecimal blob literals
            
            # Character data
            ('CHARACTER VARYING', 'VARCHAR'),
            ('CHARACTER LARGE OBJECT', 'TEXT'),
            
            # Remove or modify unsupported features
            ('SET REFERENTIAL_INTEGRITY', '-- SET REFERENTIAL_INTEGRITY'),
            ('SET AUTOCOMMIT', '-- SET AUTOCOMMIT'),
        ]
        
        sqlite_sql = h2_sql
        for h2_syntax, sqlite_syntax in conversions:
            sqlite_sql = sqlite_sql.replace(h2_syntax, sqlite_syntax)
        
        return sqlite_sql
    
    def _execute_large_sql_script(self, sql_content: str, script_name: str) -> None:
        """Execute large SQL scripts in manageable chunks."""
        try:
            # Split into statements
            statements = []
            current_statement = ""
            in_string = False
            escape_next = False
            
            for char in sql_content:
                if escape_next:
                    current_statement += char
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    current_statement += char
                    continue
                
                if char == "'" and not escape_next:
                    in_string = not in_string
                
                current_statement += char
                
                if char == ';' and not in_string:
                    stmt = current_statement.strip()
                    if stmt and not stmt.startswith('--'):
                        statements.append(stmt[:-1])  # Remove the semicolon
                    current_statement = ""
            
            # Add any remaining statement
            if current_statement.strip():
                statements.append(current_statement.strip())
            
            self.logger.info(f"Executing {len(statements)} statements from {script_name}")
            
            # Execute in batches
            batch_size = 50  # Adjust based on performance
            for i in range(0, len(statements), batch_size):
                batch = statements[i:i+batch_size]
                self._execute_statement_batch(batch, script_name, i)
                
        except Exception as e:
            self.logger.error(f"Failed to execute large SQL script {script_name}: {e}")
            raise
    
    def _execute_statement_batch(self, statements: List[str], script_name: str, batch_start: int) -> None:
        """Execute a batch of SQL statements."""
        try:
            with self.db_service.get_session() as session:
                for i, statement in enumerate(statements):
                    try:
                        if statement.strip():
                            session.execute(text(statement))
                    except Exception as e:
                        stmt_num = batch_start + i + 1
                        self.logger.warning(f"Failed to execute statement {stmt_num} in {script_name}: {e}")
                        # Continue with next statement
                        
        except Exception as e:
            self.logger.error(f"Failed to execute batch from {script_name}: {e}")
            raise
    
    def validate_migration(self) -> Dict[str, Any]:
        """Validate the migrated data integrity."""
        validation_results = {
            'status': 'success',
            'errors': [],
            'warnings': [],
            'table_counts': {},
            'data_integrity': {}
        }
        
        try:
            with self.db_service.get_session() as session:
                # Check each table
                from app.models import get_all_models
                
                for model_class in get_all_models():
                    table_name = model_class.__tablename__
                    
                    try:
                        count = session.query(model_class).count()
                        validation_results['table_counts'][table_name] = count
                        
                        # Basic validation for each model
                        if hasattr(model_class, 'validate_gypsum_fractions'):
                            # Cement validation
                            invalid_count = 0
                            for item in session.query(model_class).all():
                                if not item.validate_gypsum_fractions():
                                    invalid_count += 1
                            if invalid_count > 0:
                                validation_results['warnings'].append(
                                    f"{table_name}: {invalid_count} items with invalid gypsum fractions"
                                )
                        
                        elif hasattr(model_class, 'validate_phase_fractions'):
                            # FlyAsh validation
                            invalid_count = 0
                            for item in session.query(model_class).all():
                                if not item.validate_phase_fractions():
                                    invalid_count += 1
                            if invalid_count > 0:
                                validation_results['warnings'].append(
                                    f"{table_name}: {invalid_count} items with invalid phase fractions"
                                )
                        
                        elif hasattr(model_class, 'validate_mechanical_properties'):
                            # Aggregate validation
                            invalid_count = 0
                            for item in session.query(model_class).all():
                                if not item.validate_mechanical_properties():
                                    invalid_count += 1
                            if invalid_count > 0:
                                validation_results['warnings'].append(
                                    f"{table_name}: {invalid_count} items with invalid mechanical properties"
                                )
                        
                    except Exception as e:
                        validation_results['errors'].append(f"Error validating {table_name}: {e}")
                
                if validation_results['errors']:
                    validation_results['status'] = 'error'
                elif validation_results['warnings']:
                    validation_results['status'] = 'warning'
                
        except Exception as e:
            validation_results['status'] = 'error'
            validation_results['errors'].append(f"General validation error: {e}")
        
        return validation_results


def create_migration_manager(db_service: DatabaseService = None) -> MigrationManager:
    """Create a migration manager instance."""
    from app.database.service import database_service
    return MigrationManager(db_service or database_service)