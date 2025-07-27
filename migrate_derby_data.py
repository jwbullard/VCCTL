#!/usr/bin/env python3
"""
Derby to SQLite Migration Script for VCCTL

This script migrates data from Apache Derby databases to SQLite for the VCCTL application.
Since direct Derby connectivity is not available, this script provides multiple approaches:

1. Derby SQL export commands (to be run manually)
2. CSV import functionality 
3. Direct data insertion methods

Usage:
    python migrate_derby_data.py --derby-path /path/to/derby/data --export-csv
    python migrate_derby_data.py --import-csv /path/to/exported/csv
"""

import os
import sys
import csv
import sqlite3
import logging
import argparse
import binascii
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Increase CSV field size limit for large Derby exports
csv.field_size_limit(sys.maxsize)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from app.database.service import DatabaseService
from app.database.migrations import MigrationManager
from app.database.config import get_database_config


class DerbyMigrationTool:
    """Tool for migrating data from Apache Derby to SQLite."""
    
    def __init__(self, derby_data_path: Path, sqlite_db_path: Path):
        """Initialize the migration tool."""
        self.derby_data_path = Path(derby_data_path)
        self.sqlite_db_path = Path(sqlite_db_path)
        self.logger = logging.getLogger('DerbyMigration')
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Initialize database service
        self.db_service = DatabaseService()
        self.migration_manager = MigrationManager(self.db_service)
        
        # Derby database paths
        self.derby_databases = {
            'cement': self.derby_data_path / 'database' / 'vcctl_cement',
            'operation': self.derby_data_path / 'database' / 'vcctl_operation', 
            'user': self.derby_data_path / 'database' / 'vcctl_user'
        }
    
    def _decode_hex_field(self, hex_data: str) -> Optional[bytes]:
        """Decode hex string to binary data."""
        if not hex_data or not hex_data.strip():
            return None
        try:
            return binascii.unhexlify(hex_data.strip())
        except Exception as e:
            self.logger.warning(f"Failed to decode hex data: {e}")
            return None
    
    def generate_derby_export_sql(self, output_dir: Path) -> None:
        """Generate SQL commands to export Derby data to CSV files."""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Table mappings for each Derby database
        table_mappings = {
            'cement': [
                'AGGREGATE',
                'AGGREGATE_SIEVE', 
                'CEMENT',
                'FLY_ASH',
                'SLAG',
                'INERT_FILLER',
                'GRADING',
                'PARTICLE_SHAPE_SET',
                'DB_FILE'
            ],
            'operation': [
                'OPERATION'
            ],
            'user': [
                'USER_DATA'  # If applicable
            ]
        }
        
        sql_script_path = output_dir / 'derby_export_commands.sql'
        
        with open(sql_script_path, 'w') as f:
            f.write("-- Derby Database Export Commands\n")
            f.write("-- Run these commands in Derby ij tool\n\n")
            
            for db_name, tables in table_mappings.items():
                derby_path = self.derby_databases[db_name]
                f.write(f"-- Connect to {db_name} database\n")
                f.write(f"CONNECT 'jdbc:derby:{derby_path}';\n\n")
                
                for table in tables:
                    csv_file = output_dir / f"{table.lower()}.csv"
                    f.write(f"-- Export {table} table\n")
                    f.write(f"CALL SYSCS_UTIL.SYSCS_EXPORT_TABLE('APP', '{table}', '{csv_file}', null, null, null);\n\n")
                
                f.write("DISCONNECT;\n\n")
        
        self.logger.info(f"Derby export SQL commands written to: {sql_script_path}")
        
        # Also create a shell script to run the exports
        shell_script_path = output_dir / 'run_derby_export.sh'
        with open(shell_script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Derby Data Export Script\n")
            f.write("# Requires Apache Derby installation with ij tool\n\n")
            f.write("DERBY_HOME=${DERBY_HOME:-/opt/derby}\n")
            f.write("DERBY_CLASSPATH=$DERBY_HOME/lib/derby.jar:$DERBY_HOME/lib/derbytools.jar\n\n")
            f.write(f"java -cp $DERBY_CLASSPATH org.apache.derby.tools.ij {sql_script_path}\n")
        
        os.chmod(shell_script_path, 0o755)
        self.logger.info(f"Derby export shell script written to: {shell_script_path}")
    
    def import_csv_data(self, csv_dir: Path) -> None:
        """Import data from CSV files exported from Derby."""
        csv_dir = Path(csv_dir)
        
        if not csv_dir.exists():
            raise FileNotFoundError(f"CSV directory not found: {csv_dir}")
        
        # Ensure database schema exists
        self.migration_manager.upgrade_database()
        
        # Import tables in dependency order
        import_order = [
            'particle_shape_set',
            'db_file', 
            'cement',
            'fly_ash',
            'slag',
            'inert_filler',
            'aggregate',
            'grading',
            'aggregate_sieve',
            'operation'
        ]
        
        for table_name in import_order:
            csv_file = csv_dir / f"{table_name}.csv"
            if csv_file.exists():
                self.logger.info(f"Importing {table_name} from {csv_file}")
                self._import_table_from_csv(table_name, csv_file)
            else:
                self.logger.warning(f"CSV file not found: {csv_file}")
        
        self.logger.info("CSV data import completed")
    
    def _import_table_from_csv(self, table_name: str, csv_file: Path) -> None:
        """Import a single table from CSV file."""
        try:
            # Define column mappings for CSV files without headers
            column_mappings = {
                'cement': ['NAME', 'PSD', 'PFC', 'GIF', 'LEGEND_GIF', 'SIL', 'C3S', 'C3A', 'N2O', 'K2O', 'ALU', 'TXT', 'XRD', 'INF', 'C4F', 'DESCRIPTION', 'SPECIFIC_GRAVITY', 'DESCRIPTION2', 'ALKALI_FILE'],
                'slag': ['NAME', 'SPECIFIC_GRAVITY', 'PSD', 'AL2O3', 'CAO', 'FE2O3', 'K2O', 'MGO', 'NA2O', 'SO3', 'SIO2', 'TIO2', 'P2O5', 'DESCRIPTION'],
                'aggregate': ['DISPLAY_NAME', 'NAME', 'TYPE', 'SPECIFIC_GRAVITY', 'BULK_MODULUS', 'SHEAR_MODULUS', 'CONDUCTIVITY', 'IMAGE', 'TXT', 'INF', 'SHAPE_STATS'],
                'inert_filler': ['NAME', 'SPECIFIC_GRAVITY', 'PSD', 'DESCRIPTION'],
                'particle_shape_set': ['NAME'],
                'grading': ['NAME', 'TYPE', 'GRADING', 'MAX_DIAMETER']
            }
            
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                raw_rows = list(reader)
                
            if not raw_rows:
                self.logger.warning(f"No data found in {csv_file}")
                return
                
            # Convert raw rows to dictionary using column mappings
            if table_name in column_mappings:
                columns = column_mappings[table_name]
                rows = []
                for raw_row in raw_rows:
                    if raw_row:  # Skip empty rows
                        row_dict = {}
                        for i, col_name in enumerate(columns):
                            if i < len(raw_row):
                                row_dict[col_name] = raw_row[i].strip('"').strip()
                            else:
                                row_dict[col_name] = ''
                        rows.append(row_dict)
            else:
                # Fall back to DictReader if we don't have column mapping
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
            
            if not rows:
                self.logger.warning(f"No data found in {csv_file}")
                return
            
            self.logger.info(f"Found {len(rows)} rows in {table_name}")
            
            # Import using appropriate method based on table
            if table_name == 'cement':
                self._import_cement_data(rows)
            elif table_name == 'aggregate':
                self._import_aggregate_data(rows)
            elif table_name == 'fly_ash':
                self._import_fly_ash_data(rows)
            elif table_name == 'slag':
                self._import_slag_data(rows)
            elif table_name == 'inert_filler':
                self._import_inert_filler_data(rows)
            elif table_name == 'grading':
                self._import_grading_data(rows)
            elif table_name == 'aggregate_sieve':
                self._import_aggregate_sieve_data(rows)
            elif table_name == 'particle_shape_set':
                self._import_particle_shape_set_data(rows)
            elif table_name == 'db_file':
                self._import_db_file_data(rows)
            elif table_name == 'operation':
                self._import_operation_data(rows)
            else:
                self.logger.warning(f"No import method for table: {table_name}")
                
        except Exception as e:
            self.logger.error(f"Failed to import {table_name}: {e}")
    
    def _import_cement_data(self, rows: List[Dict[str, Any]]) -> None:
        """Import cement data."""
        from app.models.cement import Cement
        
        with self.db_service.get_session() as session:
            for i, row in enumerate(rows):
                try:
                    name = row.get('NAME', '').strip()
                    if not name:  # Skip empty names
                        self.logger.warning(f"Skipping cement row {i+1} with empty name")
                        continue
                        
                    # Map Derby columns to SQLite model
                    # Handle specific gravity - use default if not provided or empty
                    specific_gravity_str = row.get('SPECIFIC_GRAVITY', '').strip()
                    try:
                        specific_gravity = float(specific_gravity_str) if specific_gravity_str else 3.15
                    except ValueError:
                        specific_gravity = 3.15
                        
                    # Debug: Check what data we have for this record
                    if name == 'cementotc':
                        self.logger.info(f"Debug cementotc: PFC='{row.get('PFC', '')[:50]}', GIF='{row.get('GIF', '')[:50]}'")
                        
                    cement = Cement(
                        name=name,
                        psd=row.get('PSD', ''),
                        alkali_file=row.get('ALKALI_FILE', ''),
                        specific_gravity=specific_gravity,
                        description=row.get('DESCRIPTION', ''),
                        # Decode binary fields from hex data
                        pfc=self._decode_hex_field(row.get('PFC', '')),
                        gif=self._decode_hex_field(row.get('GIF', '')),
                        legend_gif=self._decode_hex_field(row.get('LEGEND_GIF', '')),
                        sil=self._decode_hex_field(row.get('SIL', '')),
                        c3s=self._decode_hex_field(row.get('C3S', '')),
                        c3a=self._decode_hex_field(row.get('C3A', '')),
                        n2o=self._decode_hex_field(row.get('N2O', '')),
                        k2o=self._decode_hex_field(row.get('K2O', '')),
                        alu=self._decode_hex_field(row.get('ALU', '')),
                        txt=self._decode_hex_field(row.get('TXT', '')),
                        xrd=self._decode_hex_field(row.get('XRD', '')),
                        inf=self._decode_hex_field(row.get('INF', '')),
                        c4f=self._decode_hex_field(row.get('C4F', '')),
                    )
                    
                    # Check if already exists
                    existing = session.query(Cement).filter_by(name=cement.name).first()
                    if not existing:
                        session.add(cement)
                        if name == 'cementotc':
                            self.logger.info(f"Added new cementotc record")
                    else:
                        # Update existing record with new data
                        existing.psd = cement.psd
                        existing.alkali_file = cement.alkali_file
                        existing.specific_gravity = cement.specific_gravity
                        existing.description = cement.description
                        # Update binary fields
                        existing.pfc = cement.pfc
                        existing.gif = cement.gif
                        existing.legend_gif = cement.legend_gif
                        existing.sil = cement.sil
                        existing.c3s = cement.c3s
                        existing.c3a = cement.c3a
                        existing.n2o = cement.n2o
                        existing.k2o = cement.k2o
                        existing.alu = cement.alu
                        existing.txt = cement.txt
                        existing.xrd = cement.xrd
                        existing.inf = cement.inf
                        existing.c4f = cement.c4f
                        
                        if name == 'cementotc':
                            self.logger.info(f"Updated existing cementotc record with enhanced data")
                        
                except Exception as e:
                    self.logger.error(f"Failed to import cement row {i+1}: {e}")
                    continue
            
            session.commit()
    
    def _import_aggregate_data(self, rows: List[Dict[str, Any]]) -> None:
        """Import aggregate data."""
        from app.models.aggregate import Aggregate
        
        with self.db_service.get_session() as session:
            for row in rows:
                try:
                    aggregate = Aggregate(
                        display_name=row.get('DISPLAY_NAME', ''),
                        name=row.get('NAME', ''),
                        type=int(row.get('TYPE', 1)) if row.get('TYPE') else 1,
                        specific_gravity=float(row.get('SPECIFIC_GRAVITY', 2.65)) if row.get('SPECIFIC_GRAVITY') else 2.65,
                        # Add other fields as needed
                    )
                    
                    existing = session.query(Aggregate).filter_by(display_name=aggregate.display_name).first()
                    if not existing:
                        session.add(aggregate)
                        
                except Exception as e:
                    self.logger.error(f"Failed to import aggregate row: {e}")
                    continue
            
            session.commit()
    
    def _import_fly_ash_data(self, rows: List[Dict[str, Any]]) -> None:
        """Import fly ash data."""
        from app.models.fly_ash import FlyAsh
        
        with self.db_service.get_session() as session:
            for row in rows:
                try:
                    fly_ash = FlyAsh(
                        name=row.get('NAME', ''),
                        specific_gravity=float(row.get('SPECIFIC_GRAVITY', 2.77)) if row.get('SPECIFIC_GRAVITY') else 2.77,
                        psd=row.get('PSD', ''),
                        # Add other fields as needed
                    )
                    
                    existing = session.query(FlyAsh).filter_by(name=fly_ash.name).first()
                    if not existing:
                        session.add(fly_ash)
                        
                except Exception as e:
                    self.logger.error(f"Failed to import fly ash row: {e}")
                    continue
            
            session.commit()
    
    def _import_slag_data(self, rows: List[Dict[str, Any]]) -> None:
        """Import slag data."""
        from app.models.slag import Slag
        
        with self.db_service.get_session() as session:
            for row in rows:
                try:
                    slag = Slag(
                        name=row.get('NAME', ''),
                        specific_gravity=float(row.get('SPECIFIC_GRAVITY', 2.87)) if row.get('SPECIFIC_GRAVITY') else 2.87,
                        psd=row.get('PSD', ''),
                        # Add other fields as needed
                    )
                    
                    existing = session.query(Slag).filter_by(name=slag.name).first()
                    if not existing:
                        session.add(slag)
                        
                except Exception as e:
                    self.logger.error(f"Failed to import slag row: {e}")
                    continue
            
            session.commit()
    
    def _import_inert_filler_data(self, rows: List[Dict[str, Any]]) -> None:
        """Import inert filler data."""
        from app.models.inert_filler import InertFiller
        
        with self.db_service.get_session() as session:
            for i, row in enumerate(rows):
                try:
                    name = row.get('NAME', '').strip()
                    if not name:  # Skip empty names
                        self.logger.warning(f"Skipping inert filler row {i+1} with empty name")
                        continue
                        
                    filler = InertFiller(
                        name=name,
                        specific_gravity=float(row.get('SPECIFIC_GRAVITY', 3.0)) if row.get('SPECIFIC_GRAVITY') else 3.0,
                        psd=row.get('PSD', ''),
                        # Add other fields as needed
                    )
                    
                    existing = session.query(InertFiller).filter_by(name=filler.name).first()
                    if not existing:
                        session.add(filler)
                        
                except Exception as e:
                    self.logger.error(f"Failed to import inert filler row {i+1}: {e}")
                    continue
            
            session.commit()
    
    def _import_grading_data(self, rows: List[Dict[str, Any]]) -> None:
        """Import grading data."""
        from app.models.grading import Grading
        
        with self.db_service.get_session() as session:
            for i, row in enumerate(rows):
                try:
                    name = row.get('NAME', '').strip()
                    if not name:  # Skip empty names
                        self.logger.warning(f"Skipping grading row {i+1} with empty name")
                        continue
                        
                    grading = Grading(
                        name=name,
                        max_diameter=float(row.get('MAX_DIAMETER', 25.0)) if row.get('MAX_DIAMETER') else 25.0,
                        # Add other fields as needed
                    )
                    
                    existing = session.query(Grading).filter_by(name=grading.name).first()
                    if not existing:
                        session.add(grading)
                        
                except Exception as e:
                    self.logger.error(f"Failed to import grading row {i+1}: {e}")
                    continue
            
            session.commit()
    
    def _import_aggregate_sieve_data(self, rows: List[Dict[str, Any]]) -> None:
        """Import aggregate sieve data."""
        from app.models.aggregate_sieve import AggregateSieve
        
        with self.db_service.get_session() as session:
            for row in rows:
                try:
                    sieve = AggregateSieve(
                        # Add appropriate field mappings based on your model
                        # This is a placeholder - adjust based on actual schema
                        sieve_size=float(row.get('SIEVE_SIZE', 0)) if row.get('SIEVE_SIZE') else 0,
                        percent_passing=float(row.get('PERCENT_PASSING', 0)) if row.get('PERCENT_PASSING') else 0,
                    )
                    
                    session.add(sieve)
                        
                except Exception as e:
                    self.logger.error(f"Failed to import aggregate sieve row: {e}")
                    continue
            
            session.commit()
    
    def _import_particle_shape_set_data(self, rows: List[Dict[str, Any]]) -> None:
        """Import particle shape set data."""
        from app.models.particle_shape_set import ParticleShapeSet
        
        with self.db_service.get_session() as session:
            for i, row in enumerate(rows):
                try:
                    name = row.get('NAME', '').strip()
                    if not name:  # Skip empty names
                        self.logger.warning(f"Skipping particle shape set row {i+1} with empty name")
                        continue
                        
                    shape_set = ParticleShapeSet(
                        name=name,
                        # Add other fields as needed
                    )
                    
                    existing = session.query(ParticleShapeSet).filter_by(name=shape_set.name).first()
                    if not existing:
                        session.add(shape_set)
                        
                except Exception as e:
                    self.logger.error(f"Failed to import particle shape set row {i+1}: {e}")
                    continue
            
            session.commit()
    
    def _import_db_file_data(self, rows: List[Dict[str, Any]]) -> None:
        """Import database file data."""
        from app.models.db_file import DbFile
        
        with self.db_service.get_session() as session:
            for row in rows:
                try:
                    db_file = DbFile(
                        name=row.get('NAME', ''),
                        file_path=row.get('FILE_PATH', ''),
                        # Add other fields as needed
                    )
                    
                    existing = session.query(DbFile).filter_by(name=db_file.name).first()
                    if not existing:
                        session.add(db_file)
                        
                except Exception as e:
                    self.logger.error(f"Failed to import db file row: {e}")
                    continue
            
            session.commit()
    
    def _import_operation_data(self, rows: List[Dict[str, Any]]) -> None:
        """Import operation data."""
        from app.models.operation import Operation
        
        with self.db_service.get_session() as session:
            for row in rows:
                try:
                    operation = Operation(
                        name=row.get('NAME', ''),
                        # Add other fields based on your Operation model
                    )
                    
                    existing = session.query(Operation).filter_by(name=operation.name).first()
                    if not existing:
                        session.add(operation)
                        
                except Exception as e:
                    self.logger.error(f"Failed to import operation row: {e}")
                    continue
            
            session.commit()
    
    def validate_migration(self) -> Dict[str, Any]:
        """Validate the migrated data."""
        return self.migration_manager.validate_migration()
    
    def create_backup(self) -> Path:
        """Create a backup of the current SQLite database."""
        config = get_database_config()
        return config.backup_database()


def main():
    """Main migration script."""
    parser = argparse.ArgumentParser(description='Migrate Derby data to SQLite for VCCTL')
    parser.add_argument('--derby-path', required=True, help='Path to Derby data directory')
    parser.add_argument('--export-csv', action='store_true', help='Generate Derby export commands')
    parser.add_argument('--import-csv', help='Import from CSV directory')
    parser.add_argument('--output-dir', default='derby_export', help='Output directory for exports')
    parser.add_argument('--backup', action='store_true', help='Create backup before migration')
    
    args = parser.parse_args()
    
    # Setup paths
    vcctl_dir = Path(__file__).parent
    sqlite_db_path = vcctl_dir / 'src' / 'data' / 'database' / 'vcctl.db'
    derby_data_path = Path(args.derby_path)
    
    # Initialize migration tool
    migrator = DerbyMigrationTool(derby_data_path, sqlite_db_path)
    
    try:
        if args.backup:
            backup_path = migrator.create_backup()
            print(f"Database backup created: {backup_path}")
        
        if args.export_csv:
            output_dir = Path(args.output_dir)
            migrator.generate_derby_export_sql(output_dir)
            print(f"Derby export commands generated in: {output_dir}")
            print("Next steps:")
            print("1. Install Apache Derby")
            print("2. Run the generated shell script to export CSV files")
            print("3. Run this script with --import-csv to import the data")
        
        elif args.import_csv:
            csv_dir = Path(args.import_csv)
            migrator.import_csv_data(csv_dir)
            
            # Validate migration
            validation = migrator.validate_migration()
            print(f"Migration validation: {validation['status']}")
            if validation['table_counts']:
                print("Table record counts:")
                for table, count in validation['table_counts'].items():
                    print(f"  {table}: {count}")
        
        else:
            print("Please specify either --export-csv or --import-csv")
            parser.print_help()
    
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()